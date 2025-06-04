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
    Sistema de cache com TTL (Tempo de Vida) e limites de memória.
    
    Implementa estratégia LRU (Least Recently Used - Menos Recentemente Usado)
    para otimizar uso de memória e performance.
    """
    
    def __init__(self, max_size: int = 1000, ttl_minutos: int = 60):
        """
        Inicializa o cache inteligente.
        
        Args:
            max_size: Número máximo de entradas no cache
            ttl_minutos: Tempo de vida das entradas em minutos
        """
        # ===== ESTRUTURA DE DADOS =====
        self.cache: OrderedDict = OrderedDict()  # Mantém ordem de inserção
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutos)
        self.lock = Lock()  # Thread safety
        
        # ===== ESTATÍSTICAS =====
        self.hits = 0       # Acertos no cache
        self.misses = 0     # Erros no cache
        self.evictions = 0  # Itens removidos
        
        # ===== METADADOS =====
        # Armazena informações sobre cada item no cache
        self.metadata: Dict[str, Dict[str, Any]] = {}
        
        # Inicia thread de limpeza automática
        self._iniciar_limpeza_periodica()
    
    def _gerar_chave(self, *args, **kwargs) -> str:
        """
        Gera uma chave única para os argumentos fornecidos.
        
        Returns:
            str: Chave hash única
        """
        # ===== CRIAÇÃO DA CHAVE HASH =====
        # Converte todos os argumentos em string
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        
        # Gera hash MD5 único
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
            # Verifica se existe no cache
            if chave not in self.cache:
                self.misses += 1
                return None
            
            # ===== VERIFICAÇÃO DE EXPIRAÇÃO =====
            metadata = self.metadata.get(chave, {})
            if self._expirado(metadata):
                self._remover(chave)
                self.misses += 1
                return None
            
            # ===== ATUALIZAÇÃO LRU =====
            # Move item para o final (mais recente)
            self.cache.move_to_end(chave)
            self.hits += 1
            
            # Atualiza timestamp do último acesso
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
            # Se já existe, apenas move para o final
            if chave in self.cache:
                self.cache.move_to_end(chave)
            else:
                # ===== CONTROLE DE TAMANHO =====
                # Remove item mais antigo se necessário
                if len(self.cache) >= self.max_size:
                    self._evict_lru()
                
                self.cache[chave] = valor
            
            # ===== ARMAZENAMENTO DE METADADOS =====
            ttl = timedelta(minutes=ttl_customizado) if ttl_customizado else self.ttl
            self.metadata[chave] = {
                "criado_em": datetime.now(),
                "ultimo_acesso": datetime.now(),
                "ttl": ttl,
                "tamanho_bytes": self._calcular_tamanho(valor)
            }
    
    def _expirado(self, metadata: Dict[str, Any]) -> bool:
        """Verifica se um item expirou baseado no TTL."""
        if not metadata:
            return True
        
        criado_em = metadata.get("criado_em", datetime.now())
        ttl = metadata.get("ttl", self.ttl)
        
        # Verifica se o tempo desde a criação excedeu o TTL
        return datetime.now() - criado_em > ttl
    
    def _remover(self, chave: str):
        """Remove um item do cache e seus metadados."""
        if chave in self.cache:
            del self.cache[chave]
        if chave in self.metadata:
            del self.metadata[chave]
    
    def _evict_lru(self):
        """Remove o item menos recentemente usado (LRU)."""
        if self.cache:
            # Pega o primeiro item (mais antigo)
            chave_antiga = next(iter(self.cache))
            self._remover(chave_antiga)
            self.evictions += 1
    
    def _calcular_tamanho(self, valor: Any) -> int:
        """Calcula tamanho aproximado em bytes do valor."""
        try:
            # Serializa para JSON e conta bytes
            return len(json.dumps(valor).encode())
        except:
            return 0  # Retorna 0 se não conseguir serializar
    
    def limpar(self):
        """Limpa todo o cache"""
        with self.lock:
            self.cache.clear()
            self.metadata.clear()
    
    def limpar_expirados(self):
        """Remove todos os itens expirados do cache."""
        with self.lock:
            # ===== IDENTIFICAÇÃO DE ITENS EXPIRADOS =====
            chaves_expiradas = []
            
            for chave, metadata in self.metadata.items():
                if self._expirado(metadata):
                    chaves_expiradas.append(chave)
            
            # ===== REMOÇÃO EM LOTE =====
            for chave in chaves_expiradas:
                self._remover(chave)
            
            return len(chaves_expiradas)
    
    def _iniciar_limpeza_periodica(self):
        """Inicia thread para limpeza periódica de itens expirados."""
        def limpar_periodicamente():
            while True:
                time.sleep(300)  # Executa a cada 5 minutos
                self.limpar_expirados()
        
        # Cria thread daemon que não impede o programa de terminar
        import threading
        thread = threading.Thread(target=limpar_periodicamente, daemon=True)
        thread.start()
    
    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas do cache."""
        # ===== CÁLCULO DE MÉTRICAS =====
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
        # ===== PALAVRAS DE ALTA PRIORIDADE =====
        # Termos que indicam informações críticas
        self.palavras_importantes = {
            "erro", "falha", "crítico", "urgente", "importante",
            "conclusão", "resultado", "decisão", "ação", "prazo",
            "aprovado", "rejeitado", "pendente", "bloqueado",
            "sucesso", "problema", "solução", "recomendação"
        }
        
        # ===== STOP WORDS EM PORTUGUÊS =====
        # Palavras comuns que podem ser removidas
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
        
        # ===== ESTIMAÇÃO DE TOKENS =====
        # Aproximadamente 4 caracteres por token em português
        if len(contexto) / 4 <= limite_tokens:
            return contexto  # Não precisa comprimir
        
        # ===== DIVISÃO E PONTUAÇÃO =====
        sentencas = self._dividir_sentencas(contexto)
        
        # Calcula score de importância para cada sentença
        sentencas_pontuadas = []
        for sentenca in sentencas:
            pontuacao = self._calcular_importancia(sentenca)
            sentencas_pontuadas.append((sentenca, pontuacao))
        
        # ===== SELEÇÃO DAS SENTENÇAS =====
        # Ordena por importância (maior primeiro)
        sentencas_pontuadas.sort(key=lambda x: x[1], reverse=True)
        
        # Seleciona sentenças mais importantes dentro do limite
        contexto_comprimido = []
        tokens_atuais = 0
        
        for sentenca, _ in sentencas_pontuadas:
            tokens_sentenca = len(sentenca) / 4
            
            if tokens_atuais + tokens_sentenca <= limite_tokens:
                contexto_comprimido.append(sentenca)
                tokens_atuais += tokens_sentenca
            else:
                break
        
        # Junta sentenças selecionadas
        contexto_final = " ".join(contexto_comprimido)
        
        # ===== INDICADOR DE COMPRESSÃO =====
        if len(sentencas) > len(contexto_comprimido):
            contexto_final += f"\n[Contexto comprimido: {len(contexto_comprimido)}/{len(sentencas)} sentenças mantidas]"
        
        return contexto_final
    
    def _dividir_sentencas(self, texto: str) -> List[str]:
        """Divide texto em sentenças usando pontuação."""
        # Padrão regex para dividir por pontuação final
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
        
        # ===== BÔNUS POR PALAVRAS IMPORTANTES =====
        for palavra in palavras:
            if palavra in self.palavras_importantes:
                score += 5  # Alto valor para palavras críticas
        
        # ===== PENALIDADES E BÔNUS ADICIONAIS =====
        # Penaliza sentenças com muitas stop words
        num_stop_words = sum(1 for p in palavras if p in self.stop_words)
        score -= num_stop_words
        
        # Bônus por números (datas, valores, métricas)
        if any(char.isdigit() for char in sentenca):
            score += 3
        
        # Bônus por estruturação (listas, definições)
        if ':' in sentenca or '-' in sentenca:
            score += 2
        
        # Bônus por tamanho ideal
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
        
        # ===== PRESERVAÇÃO DE CONTEXTO =====
        # Sempre mantém primeira mensagem (contexto inicial)
        resultado = [historico[0]] if historico else []
        
        # Mensagens do meio para análise
        meio = historico[1:-1] if len(historico) > 2 else []
        
        # ===== SELEÇÃO POR IMPORTÂNCIA =====
        mensagens_pontuadas = []
        for msg in meio:
            conteudo = msg.get("content", "")
            pontuacao = self._calcular_importancia(conteudo)
            mensagens_pontuadas.append((msg, pontuacao))
        
        # Ordena e seleciona as mais relevantes
        mensagens_pontuadas.sort(key=lambda x: x[1], reverse=True)
        mensagens_selecionadas = [m[0] for m in mensagens_pontuadas[:max_mensagens-2]]
        
        resultado.extend(mensagens_selecionadas)
        
        # Sempre mantém última mensagem (contexto recente)
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
        
        # ===== COMPRESSÃO INTELIGENTE =====
        # Tenta comprimir mantendo conteúdo importante
        texto_comprimido = self.comprimir_contexto(texto, limite_tokens=max_chars//4)
        
        # Se ainda exceder, trunca com indicação
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
        # ===== CONFIGURAÇÕES =====
        self.tamanho_batch = tamanho_batch
        self.timeout = timeout_segundos
        self.batch_atual: List[Dict[str, Any]] = []
        self.lock = Lock()
        self.processando = False
        
        # ===== ESTATÍSTICAS =====
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
            # ===== ADIÇÃO AO BATCH =====
            self.batch_atual.append({
                "item": item,
                "future": asyncio.Future()  # Promise para resultado
            })
            
            # Processa se batch está cheio
            if len(self.batch_atual) >= self.tamanho_batch:
                await self._processar_batch(callback)
        
        # ===== AGUARDA RESULTADO =====
        for batch_item in self.batch_atual:
            if batch_item["item"] == item:
                return await batch_item["future"]
        
        # Se não processou ainda, aguarda timeout
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
            # ===== AGRUPAMENTO INTELIGENTE =====
            grupos = self._agrupar_similares(batch)
            
            # ===== PROCESSAMENTO POR GRUPO =====
            for grupo in grupos:
                itens = [g["item"] for g in grupo]
                
                # Chama callback uma vez para todo o grupo
                resultados = await callback(itens)
                
                # ===== DISTRIBUIÇÃO DOS RESULTADOS =====
                for i, batch_item in enumerate(grupo):
                    if i < len(resultados):
                        batch_item["future"].set_result(resultados[i])
                    else:
                        batch_item["future"].set_result(None)
                
                # ===== ATUALIZAÇÃO DE MÉTRICAS =====
                self.total_batches += 1
                self.total_itens += len(grupo)
                # Economia = itens processados - chamadas feitas
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
        
        # ===== AGRUPAMENTO POR TIPO =====
        # Agrupa itens similares para processamento conjunto
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
        """Inicializa o sistema de otimização."""
        # ===== COMPONENTES DO OTIMIZADOR =====
        self.cache = CacheInteligente(max_size=1000, ttl_minutos=60)
        self.compressor = CompressorContexto()
        self.batch_processor = ProcessadorBatch(tamanho_batch=5, timeout_segundos=2)
        
        # ===== MÉTRICAS GLOBAIS =====
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
            # ===== VERIFICAÇÃO DE CACHE =====
            chave = self.cache._gerar_chave(func.__name__, *args, **kwargs)
            
            # Retorna do cache se disponível
            resultado = self.cache.get(chave)
            if resultado is not None:
                return resultado
            
            # ===== EXECUÇÃO E CACHE =====
            inicio = time.time()
            resultado = func(*args, **kwargs)
            tempo_execucao = time.time() - inicio
            
            # Armazena resultado no cache
            self.cache.set(chave, resultado)
            
            # Estima economia futura (80% do tempo de execução)
            self.tempo_economizado += tempo_execucao * 0.8
            
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
        # ===== CÁLCULO DE ECONOMIA =====
        texto_original_tokens = len(texto) // 4  # Estimativa
        texto_comprimido = self.compressor.comprimir_contexto(texto, max_tokens)
        texto_comprimido_tokens = len(texto_comprimido) // 4
        
        # Calcula tokens economizados
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
        
        # ===== PROCESSAMENTO EM LOTE =====
        for consulta in consultas:
            resultado = await self.batch_processor.adicionar_item(
                {"consulta": consulta},
                processador
            )
            resultados.append(resultado)
        
        return resultados
    
    def estatisticas_completas(self) -> Dict[str, Any]:
        """Retorna estatísticas completas do sistema de otimização."""
        return {
            "cache": self.cache.estatisticas(),
            "batch": self.batch_processor.estatisticas(),
            "compressao": {
                "tokens_economizados": self.tokens_economizados,
                # Estimativa baseada no preço médio por token
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
        """Gera relatório detalhado de economia de recursos."""
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


# ===== INSTÂNCIA GLOBAL =====
# Cria instância única do otimizador para uso em todo o sistema
otimizador_global = Otimizador()