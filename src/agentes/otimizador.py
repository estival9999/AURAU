"""
Sistema de Otimização - Cache inteligente, compressão de contexto e batch processing.
Otimiza performance e economia de recursos do sistema AURALIS.
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
import hashlib
import json
import re
import asyncio
from threading import Lock
import time


class CacheInteligente:
    """
    Sistema de cache com TTL (Time To Live) e limites de memória.
    Implementa estratégia LRU (Least Recently Used).
    """
    
    def __init__(self, max_size: int = 1000, ttl_minutos: int = 60):
        """
        Inicializa o cache inteligente.
        
        Args:
            max_size: Número máximo de entradas no cache
            ttl_minutos: Tempo de vida das entradas em minutos
        """
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutos)
        self.lock = Lock()
        
        # Estatísticas
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # Metadata do cache
        self.metadata: Dict[str, Dict[str, Any]] = {}
        
        # Iniciar limpeza periódica
        self._iniciar_limpeza_periodica()
    
    def _gerar_chave(self, *args, **kwargs) -> str:
        """
        Gera uma chave única para os argumentos fornecidos.
        
        Returns:
            str: Chave hash única
        """
        # Criar representação string dos argumentos
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        
        # Gerar hash MD5
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, chave: str) -> Optional[Any]:
        """
        Recupera um valor do cache.
        
        Args:
            chave: Chave do item
            
        Returns:
            Valor armazenado ou None
        """
        with self.lock:
            if chave not in self.cache:
                self.misses += 1
                return None
            
            # Verificar TTL
            metadata = self.metadata.get(chave, {})
            if self._expirado(metadata):
                self._remover(chave)
                self.misses += 1
                return None
            
            # Mover para o final (mais recente)
            self.cache.move_to_end(chave)
            self.hits += 1
            
            # Atualizar último acesso
            metadata["ultimo_acesso"] = datetime.now()
            
            return self.cache[chave]
    
    def set(self, chave: str, valor: Any, ttl_customizado: Optional[int] = None):
        """
        Armazena um valor no cache.
        
        Args:
            chave: Chave do item
            valor: Valor a armazenar
            ttl_customizado: TTL customizado em minutos (opcional)
        """
        with self.lock:
            # Remover se já existe
            if chave in self.cache:
                self.cache.move_to_end(chave)
            else:
                # Verificar limite de tamanho
                if len(self.cache) >= self.max_size:
                    self._evict_lru()
                
                self.cache[chave] = valor
            
            # Armazenar metadata
            ttl = timedelta(minutes=ttl_customizado) if ttl_customizado else self.ttl
            self.metadata[chave] = {
                "criado_em": datetime.now(),
                "ultimo_acesso": datetime.now(),
                "ttl": ttl,
                "tamanho_bytes": self._calcular_tamanho(valor)
            }
    
    def _expirado(self, metadata: Dict[str, Any]) -> bool:
        """Verifica se um item expirou"""
        if not metadata:
            return True
        
        criado_em = metadata.get("criado_em", datetime.now())
        ttl = metadata.get("ttl", self.ttl)
        
        return datetime.now() - criado_em > ttl
    
    def _remover(self, chave: str):
        """Remove um item do cache"""
        if chave in self.cache:
            del self.cache[chave]
        if chave in self.metadata:
            del self.metadata[chave]
    
    def _evict_lru(self):
        """Remove o item menos recentemente usado"""
        if self.cache:
            chave_antiga = next(iter(self.cache))
            self._remover(chave_antiga)
            self.evictions += 1
    
    def _calcular_tamanho(self, valor: Any) -> int:
        """Calcula tamanho aproximado em bytes"""
        try:
            return len(json.dumps(valor).encode())
        except:
            return 0
    
    def limpar(self):
        """Limpa todo o cache"""
        with self.lock:
            self.cache.clear()
            self.metadata.clear()
    
    def limpar_expirados(self):
        """Remove todos os itens expirados"""
        with self.lock:
            chaves_expiradas = []
            
            for chave, metadata in self.metadata.items():
                if self._expirado(metadata):
                    chaves_expiradas.append(chave)
            
            for chave in chaves_expiradas:
                self._remover(chave)
            
            return len(chaves_expiradas)
    
    def _iniciar_limpeza_periodica(self):
        """Inicia thread para limpeza periódica de itens expirados"""
        def limpar_periodicamente():
            while True:
                time.sleep(300)  # 5 minutos
                self.limpar_expirados()
        
        import threading
        thread = threading.Thread(target=limpar_periodicamente, daemon=True)
        thread.start()
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requisicoes = self.hits + self.misses
        taxa_hit = (self.hits / total_requisicoes * 100) if total_requisicoes > 0 else 0
        
        tamanho_total = sum(
            meta.get("tamanho_bytes", 0) 
            for meta in self.metadata.values()
        )
        
        return {
            "tamanho_atual": len(self.cache),
            "tamanho_maximo": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "taxa_hit": f"{taxa_hit:.1f}%",
            "evictions": self.evictions,
            "tamanho_total_bytes": tamanho_total,
            "tamanho_total_mb": round(tamanho_total / 1024 / 1024, 2)
        }
    
    def __repr__(self):
        stats = self.estatisticas()
        return f"CacheInteligente(size={stats['tamanho_atual']}/{self.max_size}, hit_rate={stats['taxa_hit']})"


class CompressorContexto:
    """
    Comprime contexto para economizar tokens em chamadas de LLM.
    """
    
    def __init__(self):
        """Inicializa o compressor de contexto"""
        # Palavras importantes que devem ser priorizadas
        self.palavras_importantes = {
            "erro", "falha", "crítico", "urgente", "importante",
            "conclusão", "resultado", "decisão", "ação", "prazo",
            "aprovado", "rejeitado", "pendente", "bloqueado",
            "sucesso", "problema", "solução", "recomendação"
        }
        
        # Stop words para remover (português)
        self.stop_words = {
            "o", "a", "os", "as", "um", "uma", "uns", "umas",
            "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
            "por", "para", "com", "sem", "sob", "sobre",
            "é", "são", "foi", "foram", "ser", "sendo", "sido",
            "ter", "tendo", "tido", "e", "ou", "mas", "porém",
            "que", "qual", "quais", "muito", "muitos", "pouco", "poucos"
        }
    
    def comprimir_contexto(self, contexto: str, limite_tokens: int = 2000) -> str:
        """
        Comprime contexto mantendo informações mais importantes.
        
        Args:
            contexto: Texto para comprimir
            limite_tokens: Limite aproximado de tokens
            
        Returns:
            str: Contexto comprimido
        """
        if not contexto:
            return ""
        
        # Estimar tokens (aproximadamente 4 caracteres por token)
        if len(contexto) / 4 <= limite_tokens:
            return contexto
        
        # Dividir em sentenças
        sentencas = self._dividir_sentencas(contexto)
        
        # Calcular importância de cada sentença
        sentencas_pontuadas = []
        for sentenca in sentencas:
            pontuacao = self._calcular_importancia(sentenca)
            sentencas_pontuadas.append((sentenca, pontuacao))
        
        # Ordenar por importância
        sentencas_pontuadas.sort(key=lambda x: x[1], reverse=True)
        
        # Selecionar sentenças mais importantes até o limite
        contexto_comprimido = []
        tokens_atuais = 0
        
        for sentenca, _ in sentencas_pontuadas:
            tokens_sentenca = len(sentenca) / 4
            
            if tokens_atuais + tokens_sentenca <= limite_tokens:
                contexto_comprimido.append(sentenca)
                tokens_atuais += tokens_sentenca
            else:
                break
        
        # Reorganizar em ordem original (aproximada)
        contexto_final = " ".join(contexto_comprimido)
        
        # Adicionar indicador de compressão
        if len(sentencas) > len(contexto_comprimido):
            contexto_final += f"\n[Contexto comprimido: {len(contexto_comprimido)}/{len(sentencas)} sentenças mantidas]"
        
        return contexto_final
    
    def _dividir_sentencas(self, texto: str) -> List[str]:
        """Divide texto em sentenças"""
        # Padrão simples para dividir sentenças
        sentencas = re.split(r'[.!?]+', texto)
        return [s.strip() for s in sentencas if s.strip()]
    
    def _calcular_importancia(self, sentenca: str) -> int:
        """
        Calcula score de importância de uma sentença.
        
        Args:
            sentenca: Sentença para avaliar
            
        Returns:
            int: Score de importância
        """
        score = 0
        palavras = sentenca.lower().split()
        
        # Bonus por palavras importantes
        for palavra in palavras:
            if palavra in self.palavras_importantes:
                score += 5
        
        # Penalidade por stop words
        num_stop_words = sum(1 for p in palavras if p in self.stop_words)
        score -= num_stop_words
        
        # Bonus por números (podem ser datas, valores, etc)
        if any(char.isdigit() for char in sentenca):
            score += 3
        
        # Bonus por pontuação especial (indica estrutura)
        if ':' in sentenca or '-' in sentenca:
            score += 2
        
        # Bonus por tamanho moderado (nem muito curta nem muito longa)
        if 10 <= len(palavras) <= 30:
            score += 2
        
        return score
    
    def comprimir_historico(self, historico: List[Dict[str, str]], 
                          max_mensagens: int = 10) -> List[Dict[str, str]]:
        """
        Comprime histórico de mensagens mantendo as mais relevantes.
        
        Args:
            historico: Lista de mensagens
            max_mensagens: Número máximo de mensagens
            
        Returns:
            List[Dict]: Histórico comprimido
        """
        if len(historico) <= max_mensagens:
            return historico
        
        # Manter primeira e última mensagens
        resultado = [historico[0]] if historico else []
        
        # Selecionar mensagens intermediárias importantes
        meio = historico[1:-1] if len(historico) > 2 else []
        
        # Priorizar mensagens com conteúdo importante
        mensagens_pontuadas = []
        for msg in meio:
            conteudo = msg.get("content", "")
            pontuacao = self._calcular_importancia(conteudo)
            mensagens_pontuadas.append((msg, pontuacao))
        
        # Ordenar por importância e pegar as top N
        mensagens_pontuadas.sort(key=lambda x: x[1], reverse=True)
        mensagens_selecionadas = [m[0] for m in mensagens_pontuadas[:max_mensagens-2]]
        
        resultado.extend(mensagens_selecionadas)
        
        # Adicionar última mensagem
        if len(historico) > 1:
            resultado.append(historico[-1])
        
        return resultado
    
    def resumir_texto(self, texto: str, max_chars: int = 500) -> str:
        """
        Resume um texto mantendo pontos principais.
        
        Args:
            texto: Texto para resumir
            max_chars: Máximo de caracteres
            
        Returns:
            str: Texto resumido
        """
        if len(texto) <= max_chars:
            return texto
        
        # Comprimir primeiro
        texto_comprimido = self.comprimir_contexto(texto, limite_tokens=max_chars//4)
        
        # Se ainda for muito grande, truncar
        if len(texto_comprimido) > max_chars:
            return texto_comprimido[:max_chars-3] + "..."
        
        return texto_comprimido


class ProcessadorBatch:
    """
    Processa múltiplas consultas em batch para economizar recursos.
    """
    
    def __init__(self, tamanho_batch: int = 5, timeout_segundos: int = 2):
        """
        Inicializa o processador batch.
        
        Args:
            tamanho_batch: Tamanho máximo do batch
            timeout_segundos: Tempo máximo de espera
        """
        self.tamanho_batch = tamanho_batch
        self.timeout = timeout_segundos
        self.batch_atual: List[Dict[str, Any]] = []
        self.lock = Lock()
        self.processando = False
        
        # Estatísticas
        self.total_batches = 0
        self.total_itens = 0
        self.economia_chamadas = 0
    
    async def adicionar_item(self, item: Dict[str, Any], 
                           callback: Callable) -> Any:
        """
        Adiciona item ao batch e processa quando necessário.
        
        Args:
            item: Item para processar
            callback: Função para processar o batch
            
        Returns:
            Resultado do processamento
        """
        with self.lock:
            self.batch_atual.append({
                "item": item,
                "future": asyncio.Future()
            })
            
            # Processar se atingiu tamanho máximo
            if len(self.batch_atual) >= self.tamanho_batch:
                await self._processar_batch(callback)
        
        # Aguardar resultado
        for batch_item in self.batch_atual:
            if batch_item["item"] == item:
                return await batch_item["future"]
        
        # Timeout - processar batch parcial
        await asyncio.sleep(self.timeout)
        await self._processar_batch(callback)
        
        # Tentar novamente
        for batch_item in self.batch_atual:
            if batch_item["item"] == item:
                return await batch_item["future"]
    
    async def _processar_batch(self, callback: Callable):
        """Processa o batch atual"""
        if self.processando or not self.batch_atual:
            return
        
        with self.lock:
            self.processando = True
            batch = self.batch_atual.copy()
            self.batch_atual.clear()
        
        try:
            # Agrupar itens similares
            grupos = self._agrupar_similares(batch)
            
            # Processar cada grupo
            for grupo in grupos:
                itens = [g["item"] for g in grupo]
                
                # Chamar callback com itens agrupados
                resultados = await callback(itens)
                
                # Distribuir resultados
                for i, batch_item in enumerate(grupo):
                    if i < len(resultados):
                        batch_item["future"].set_result(resultados[i])
                    else:
                        batch_item["future"].set_result(None)
                
                # Atualizar estatísticas
                self.total_batches += 1
                self.total_itens += len(grupo)
                self.economia_chamadas += len(grupo) - 1
        
        finally:
            self.processando = False
    
    def _agrupar_similares(self, batch: List[Dict]) -> List[List[Dict]]:
        """
        Agrupa itens similares para processamento conjunto.
        
        Args:
            batch: Lista de itens do batch
            
        Returns:
            List[List[Dict]]: Grupos de itens similares
        """
        if not batch:
            return []
        
        # Por simplicidade, agrupar por tipo se disponível
        grupos = defaultdict(list)
        
        for item in batch:
            tipo = item["item"].get("tipo", "default")
            grupos[tipo].append(item)
        
        return list(grupos.values())
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do processador"""
        return {
            "total_batches": self.total_batches,
            "total_itens": self.total_itens,
            "economia_chamadas": self.economia_chamadas,
            "itens_por_batch": round(self.total_itens / max(1, self.total_batches), 1),
            "taxa_economia": f"{(self.economia_chamadas / max(1, self.total_itens) * 100):.1f}%"
        }


class Otimizador:
    """
    Sistema central de otimização do AURALIS.
    Integra cache, compressão e batch processing.
    """
    
    def __init__(self):
        """Inicializa o sistema de otimização"""
        self.cache = CacheInteligente(max_size=1000, ttl_minutos=60)
        self.compressor = CompressorContexto()
        self.batch_processor = ProcessadorBatch(tamanho_batch=5, timeout_segundos=2)
        
        # Estatísticas gerais
        self.tokens_economizados = 0
        self.tempo_economizado = 0.0
    
    def cache_resultado(self, func: Callable) -> Callable:
        """
        Decorator para cachear resultados de funções.
        
        Args:
            func: Função para decorar
            
        Returns:
            Função decorada com cache
        """
        def wrapper(*args, **kwargs):
            # Gerar chave do cache
            chave = self.cache._gerar_chave(func.__name__, *args, **kwargs)
            
            # Verificar cache
            resultado = self.cache.get(chave)
            if resultado is not None:
                return resultado
            
            # Executar função
            inicio = time.time()
            resultado = func(*args, **kwargs)
            tempo_execucao = time.time() - inicio
            
            # Armazenar no cache
            self.cache.set(chave, resultado)
            
            # Atualizar estatísticas
            self.tempo_economizado += tempo_execucao * 0.8  # Estimativa
            
            return resultado
        
        return wrapper
    
    def comprimir_para_llm(self, texto: str, max_tokens: int = 2000) -> Tuple[str, int]:
        """
        Comprime texto para uso em LLM.
        
        Args:
            texto: Texto original
            max_tokens: Limite de tokens
            
        Returns:
            Tuple[str, int]: Texto comprimido e tokens economizados
        """
        texto_original_tokens = len(texto) // 4
        texto_comprimido = self.compressor.comprimir_contexto(texto, max_tokens)
        texto_comprimido_tokens = len(texto_comprimido) // 4
        
        tokens_economizados = max(0, texto_original_tokens - texto_comprimido_tokens)
        self.tokens_economizados += tokens_economizados
        
        return texto_comprimido, tokens_economizados
    
    def otimizar_historico(self, historico: List[Dict[str, str]], 
                         max_mensagens: int = 10) -> List[Dict[str, str]]:
        """
        Otimiza histórico de conversas.
        
        Args:
            historico: Histórico original
            max_mensagens: Máximo de mensagens
            
        Returns:
            List[Dict]: Histórico otimizado
        """
        return self.compressor.comprimir_historico(historico, max_mensagens)
    
    async def processar_batch_consultas(self, consultas: List[str], 
                                      processador: Callable) -> List[Any]:
        """
        Processa múltiplas consultas em batch.
        
        Args:
            consultas: Lista de consultas
            processador: Função para processar
            
        Returns:
            List: Resultados processados
        """
        resultados = []
        
        for consulta in consultas:
            resultado = await self.batch_processor.adicionar_item(
                {"consulta": consulta},
                processador
            )
            resultados.append(resultado)
        
        return resultados
    
    def estatisticas_completas(self) -> Dict[str, Any]:
        """Retorna estatísticas completas do sistema de otimização"""
        return {
            "cache": self.cache.estatisticas(),
            "batch": self.batch_processor.estatisticas(),
            "compressao": {
                "tokens_economizados": self.tokens_economizados,
                "economia_estimada_usd": round(self.tokens_economizados * 0.002 / 1000, 2)
            },
            "tempo": {
                "tempo_economizado_segundos": round(self.tempo_economizado, 2),
                "tempo_economizado_minutos": round(self.tempo_economizado / 60, 1)
            }
        }
    
    def limpar_cache(self):
        """Limpa o cache do sistema"""
        self.cache.limpar()
    
    def relatorio_economia(self) -> str:
        """Gera relatório de economia de recursos"""
        stats = self.estatisticas_completas()
        
        relatorio = [
            "📊 **Relatório de Otimização AURALIS**\n",
            "### Cache:",
            f"- Taxa de acerto: {stats['cache']['taxa_hit']}",
            f"- Economia de chamadas: {stats['cache']['hits']} requisições",
            f"- Tamanho atual: {stats['cache']['tamanho_atual']} itens",
            f"- Memória utilizada: {stats['cache']['tamanho_total_mb']} MB\n",
            
            "### Batch Processing:",
            f"- Total de batches: {stats['batch']['total_batches']}",
            f"- Itens por batch: {stats['batch']['itens_por_batch']}",
            f"- Taxa de economia: {stats['batch']['taxa_economia']}",
            f"- Chamadas economizadas: {stats['batch']['economia_chamadas']}\n",
            
            "### Compressão:",
            f"- Tokens economizados: {stats['compressao']['tokens_economizados']:,}",
            f"- Economia estimada: ${stats['compressao']['economia_estimada_usd']}\n",
            
            "### Tempo:",
            f"- Tempo economizado: {stats['tempo']['tempo_economizado_minutos']} minutos"
        ]
        
        return "\n".join(relatorio)
    
    def __repr__(self):
        stats = self.estatisticas_completas()
        return f"Otimizador(cache_hit_rate={stats['cache']['taxa_hit']}, tokens_saved={self.tokens_economizados})"


# Criar instância global do otimizador
otimizador_global = Otimizador()