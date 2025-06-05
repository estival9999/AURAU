"""
Agente de Consulta Inteligente - Especialista em busca e recuperação de informações.
Realiza buscas semânticas, correlaciona dados e apresenta informações relevantes.
"""

from typing import Dict, List, Any, Optional, Tuple
import os
import re
from datetime import datetime, timedelta
from collections import Counter

# Importar classe base apropriada
if os.getenv("OPENAI_API_KEY"):
    from .agente_base import AgenteBase
else:
    from .agente_base_simulado import AgenteBaseSimulado as AgenteBase

# Importar o novo sistema de templates
from .prompt_template import PromptTemplate, TomResposta

# Importar handlers do Supabase
try:
    from ..database.supabase_handler import SupabaseHandler
    from ..database.embeddings_handler import EmbeddingsHandler
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    raise RuntimeError("Sistema requer Supabase e handlers configurados")


class AgenteConsultaInteligente(AgenteBase):
    """
    Agente especializado em busca e recuperação de informações no sistema AURALIS.

    Responsabilidades:
    - Buscar em reuniões passadas
    - Consultar base de conhecimento
    - Realizar buscas semânticas
    - Correlacionar informações de múltiplas fontes
    - Calcular relevância e ranquear resultados
    """

    def __init__(self, supabase_client=None):
        super().__init__(
            nome="Consultor Inteligente AURALIS",
            descricao="Especialista em busca semântica e recuperação de informações relevantes"
        )

        # ===== CONFIGURAÇÃO DO TEMPLATE =====
        # Usa o novo sistema de templates padronizados
        self.config_prompt = PromptTemplate.criar_config_consulta()

        # ===== CONFIGURAÇÕES ESPECÍFICAS =====
        # Usa configurações do template
        self.temperatura = self.config_prompt.temperatura
        self.max_resultados = 10  # Limite de resultados por busca

        # ===== CONFIGURAÇÃO DO SUPABASE (OBRIGATÓRIO) =====
        # APENAS Supabase - sem fallbacks
        if supabase_client:
            self.db = supabase_client
        else:
            try:
                self.db = SupabaseHandler()
                if not self.db.testar_conexao():
                    raise RuntimeError("Falha na conexão com Supabase")
            except Exception as e:
                raise RuntimeError(f"Sistema requer Supabase configurado: {e}")

        # ===== CONFIGURAÇÃO DO HANDLER DE EMBEDDINGS =====
        # Para busca semântica avançada
        try:
            self.embeddings_handler = EmbeddingsHandler(self.db.client)
        except Exception as e:
            print(f"[AVISO] Handler de embeddings não disponível: {e}")
            self.embeddings_handler = None

        # ===== DICIONÁRIO DE SINÔNIMOS =====
        # Usado para expandir termos de busca e melhorar resultados
        self.sinonimos = {
            "reunião": ["meeting", "encontro", "sessão", "conferência"],
            "projeto": ["project", "iniciativa", "programa", "empreendimento"],
            "decisão": ["decision", "resolução", "determinação", "deliberação"],
            "equipe": ["team", "time", "grupo", "squad"],
            "prazo": ["deadline", "data limite", "vencimento", "término"],
            "tarefa": ["task", "atividade", "trabalho", "demanda"],
            "problema": ["issue", "questão", "desafio", "dificuldade"],
            "solução": ["solution", "resolução", "resposta", "saída"]
        }
        
        # ===== TERMOS TEMPORAIS RELATIVOS =====
        self.termos_temporais = {
            "primeira": 1,
            "segunda": 2,
            "terceira": 3,
            "quarta": 4,
            "quinta": 5,
            "última": -1,
            "penúltima": -2,
            "antepenúltima": -3,
            "mais recente": -1,
            "mais antiga": 1
        }

        # ===== MODO DE OPERAÇÃO =====
        # SEMPRE usa banco real - sem mocks
        self.usar_banco_real = True  # Forçado para True

    def get_prompt_sistema(self) -> str:
        """
        Define o prompt do sistema para o agente de consulta.

        Returns:
            str: Prompt do sistema usando o template padronizado
        """
        # Usa o novo sistema de templates com contexto atual
        return PromptTemplate.gerar_prompt_contextualizado(
            self.config_prompt,
            self.contexto_atual
        )

    def processar_mensagem(self, mensagem: str, contexto: Dict[str, Any] = None) -> str:
        """
        Processa uma consulta de busca de informações.

        Args:
            mensagem: Consulta do usuário
            contexto: Contexto adicional

        Returns:
            str: Resposta com informações encontradas
        """
        # Atualizar contexto
        if contexto:
            self.atualizar_contexto(contexto)

        # ===== ANÁLISE DE TERMOS TEMPORAIS =====
        posicao_temporal = self._analisar_termos_temporais(mensagem)
        
        # ===== EXTRAÇÃO E EXPANSÃO DE TERMOS =====
        # Extrai termos relevantes e expande com sinônimos
        termos = self.extrair_termos_busca(mensagem)
        termos_expandidos = self.expandir_termos(termos)

        print(f"[CONSULTA] Termos de busca: {termos}")
        if posicao_temporal:
            print(f"[CONSULTA] Posição temporal identificada: {posicao_temporal}")

        # ===== BUSCA EM MÚLTIPLAS FONTES =====
        # Tenta busca semântica primeiro, fallback para busca textual
        if self.embeddings_handler:
            try:
                # Busca semântica usando embeddings
                print("[CONSULTA] Usando busca semântica com embeddings")
                resultados_semanticos = self.embeddings_handler.buscar_por_similaridade(
                    query=mensagem,
                    limite=self.max_resultados * 2,  # Buscar mais para depois filtrar
                    filtros={'user_id': self.contexto_atual.get('user_id')} if self.contexto_atual else None
                )

                # Converter resultados semânticos para formato padrão
                resultados_reunioes = self._converter_resultados_semanticos(resultados_semanticos)
                resultados_documentos = []  # TODO: Implementar busca semântica em documentos
            except Exception as e:
                print(f"[CONSULTA] Erro na busca semântica, usando busca textual: {e}")
                # Fallback para busca textual
                resultados_reunioes = self.buscar_em_reunioes(termos_expandidos)
                resultados_documentos = self.buscar_em_documentos(termos_expandidos)
        else:
            # Busca textual tradicional
            resultados_reunioes = self.buscar_em_reunioes(termos_expandidos)
            resultados_documentos = self.buscar_em_documentos(termos_expandidos)

        # ===== APLICAR FILTRO TEMPORAL SE NECESSÁRIO =====
        if posicao_temporal:
            resultados_reunioes = self._aplicar_filtro_temporal(resultados_reunioes, posicao_temporal)

        # ===== USAR HISTÓRICO DA CONVERSA PARA CONTEXTO =====
        historico = contexto.get("historico_conversa", []) if contexto else []
        if historico:
            # Analisar histórico para entender melhor o contexto
            contexto_historico = self._analisar_historico(historico)
            # Refinar resultados baseado no contexto
            resultados_reunioes = self._refinar_resultados_por_contexto(
                resultados_reunioes, 
                contexto_historico
            )

        # ===== CONSOLIDAÇÃO DOS RESULTADOS =====
        # Formata todos os resultados em uma resposta estruturada
        resposta = self.formatar_resposta_busca(
            mensagem,
            resultados_reunioes,
            resultados_documentos,
            termos,
            posicao_temporal
        )

        # Adicionar ao histórico
        self.adicionar_ao_historico(mensagem, resposta)

        return resposta

    def _analisar_termos_temporais(self, mensagem: str) -> Optional[int]:
        """
        Analisa mensagem para identificar termos temporais relativos.
        
        Args:
            mensagem: Mensagem do usuário
            
        Returns:
            Optional[int]: Posição temporal (1 = primeira, -1 = última, etc)
        """
        mensagem_lower = mensagem.lower()
        
        for termo, posicao in self.termos_temporais.items():
            if termo in mensagem_lower:
                return posicao
                
        return None

    def _aplicar_filtro_temporal(self, resultados: List[Dict], posicao: int) -> List[Dict]:
        """
        Aplica filtro temporal aos resultados.
        
        Args:
            resultados: Lista de resultados
            posicao: Posição temporal (positivo = do início, negativo = do fim)
            
        Returns:
            Lista filtrada com apenas o resultado na posição especificada
        """
        if not resultados:
            return []
            
        # Ordenar por data (mais recente primeiro)
        resultados_ordenados = sorted(
            resultados,
            key=lambda x: x['dados'].get('data', ''),
            reverse=True
        )
        
        # Se posição positiva, inverter para pegar do início
        if posicao > 0:
            resultados_ordenados = list(reversed(resultados_ordenados))
            
        # Ajustar índice baseado na posição
        if posicao > 0:
            indice = posicao - 1  # 1-based para 0-based
        else:
            indice = posicao  # Já é negativo, funciona diretamente
            
        # Verificar se índice é válido
        if abs(indice) <= len(resultados_ordenados):
            if posicao > 0:
                return [resultados_ordenados[indice]]
            else:
                return [resultados_ordenados[indice]]
        
        return []

    def _analisar_historico(self, historico: List[Dict]) -> Dict[str, Any]:
        """
        Analisa histórico da conversa para extrair contexto.
        
        Args:
            historico: Histórico de mensagens
            
        Returns:
            Dicionário com contexto extraído
        """
        contexto = {
            "topicos_mencionados": [],
            "entidades": [],
            "intencoes_previas": []
        }
        
        for msg in historico[-5:]:  # Últimas 5 mensagens
            if msg.get("role") == "user":
                # Extrair tópicos e entidades
                termos = self.extrair_termos_busca(msg.get("content", ""))
                contexto["topicos_mencionados"].extend(termos)
                
        # Remover duplicatas
        contexto["topicos_mencionados"] = list(set(contexto["topicos_mencionados"]))
        
        return contexto

    def _refinar_resultados_por_contexto(self, resultados: List[Dict], 
                                        contexto: Dict[str, Any]) -> List[Dict]:
        """
        Refina resultados baseado no contexto da conversa.
        
        Args:
            resultados: Resultados originais
            contexto: Contexto extraído do histórico
            
        Returns:
            Resultados refinados
        """
        if not contexto.get("topicos_mencionados"):
            return resultados
            
        # Recalcular relevância baseada no contexto
        for resultado in resultados:
            bonus_contexto = 0
            texto_completo = str(resultado['dados']).lower()
            
            # Dar bônus se contém tópicos do contexto
            for topico in contexto["topicos_mencionados"]:
                if topico.lower() in texto_completo:
                    bonus_contexto += 5
                    
            resultado['relevancia'] = resultado.get('relevancia', 0) + bonus_contexto
            
        # Reordenar por nova relevância
        resultados.sort(key=lambda x: x['relevancia'], reverse=True)
        
        return resultados

    def extrair_termos_busca(self, mensagem: str) -> List[str]:
        """
        Extrai termos relevantes para busca da mensagem.

        Args:
            mensagem: Mensagem do usuário

        Returns:
            List[str]: Lista de termos para busca
        """
        # ===== LISTA DE STOP WORDS EM PORTUGUÊS =====
        # Palavras comuns que não agregam valor à busca
        stop_words = {
            "o", "a", "os", "as", "de", "da", "do", "das", "dos", "em", "na", "no",
            "nas", "nos", "por", "para", "com", "sem", "sob", "sobre", "é", "são",
            "foi", "foram", "ser", "sendo", "sido", "ter", "tendo", "tido", "que",
            "qual", "quais", "quando", "onde", "quem", "como", "e", "ou", "mas",
            "se", "não", "sim", "muito", "pouco", "mais", "menos", "já", "ainda",
            "um", "uma", "uns", "umas", "minha", "primeira", "última", "penúltima"
        }

        # ===== TOKENIZAÇÃO E FILTRAGEM =====
        palavras = mensagem.lower().split()
        termos = []

        for palavra in palavras:
            # Remove pontuação mantendo apenas letras e números
            palavra_limpa = re.sub(r'[^\w\s]', '', palavra)

            # Adiciona termo se for válido (não é stop word e tem mais de 2 caracteres)
            if palavra_limpa and palavra_limpa not in stop_words and len(palavra_limpa) > 2:
                termos.append(palavra_limpa)

        # ===== IDENTIFICAÇÃO DE FRASES IMPORTANTES =====
        # Captura nomes próprios e termos compostos (ex: "Projeto AURALIS")
        frases = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', mensagem)
        termos.extend([frase.lower() for frase in frases])

        # Remove duplicatas mantendo ordem de inserção
        return list(set(termos))

    def expandir_termos(self, termos: List[str]) -> List[str]:
        """
        Expande termos de busca com sinônimos e variações.

        Args:
            termos: Lista de termos originais

        Returns:
            List[str]: Lista expandida de termos
        """
        termos_expandidos = termos.copy()

        for termo in termos:
            # ===== EXPANSÃO COM SINÔNIMOS =====
            if termo in self.sinonimos:
                termos_expandidos.extend(self.sinonimos[termo])

            # ===== VARIAÇÕES MORFOLÓGICAS SIMPLES =====
            # Tenta criar plural/singular básico
            if termo.endswith('s'):
                termos_expandidos.append(termo[:-1])  # Remove 's' para singular
            else:
                termos_expandidos.append(termo + 's')  # Adiciona 's' para plural

        return list(set(termos_expandidos))  # Remover duplicatas

    def calcular_relevancia(self, texto: str, termos: List[str],
                          titulo: str = "", autor: str = "") -> int:
        """
        Calcula score de relevância de um texto para os termos de busca.

        Args:
            texto: Texto para analisar
            termos: Termos de busca
            titulo: Título do documento/reunião
            autor: Autor/participante

        Returns:
            int: Score de relevância
        """
        texto_completo = f"{titulo} {autor} {texto}".lower()
        relevancia = 0

        # ===== CÁLCULO DE RELEVÂNCIA POR TERMO =====
        for termo in termos:
            termo_lower = termo.lower()

            # Conta ocorrências do termo no texto
            ocorrencias = texto_completo.count(termo_lower)
            relevancia += ocorrencias

            # Bônus se o termo aparece no título (peso 5)
            if termo_lower in titulo.lower():
                relevancia += 5

            # Bônus se o termo é o nome do autor (peso 3)
            if termo_lower in autor.lower():
                relevancia += 3

            # Bônus especial para correspondência exata de frases (peso 10)
            if len(termo.split()) > 1 and termo_lower in texto_completo:
                relevancia += 10

        return relevancia

    def buscar_em_reunioes(self, termos: List[str]) -> List[Dict[str, Any]]:
        """
        Busca termos em reuniões.

        Args:
            termos: Termos de busca

        Returns:
            List[Dict]: Reuniões encontradas com relevância
        """
        # ===== BUSCA APENAS NO BANCO REAL - SEM FALLBACKS =====
        if not self.db:
            raise RuntimeError("Sistema requer conexão com Supabase")

        try:
            # Obtém ID do usuário do contexto
            user_id = self.contexto_atual.get('user_id') if self.contexto_atual else None

            # Busca usando o handler do Supabase
            reunioes = self.db.buscar_reunioes_por_texto(
                termos_busca=termos,
                user_id=user_id,
                limit=self.max_resultados * 2  # Buscar mais para depois filtrar
            )

            # Formata resultados do banco
            resultados = []
            for reuniao in reunioes:
                # Adapta formato do banco para formato esperado
                dados_adaptados = {
                    "id": reuniao.get('id'),
                    "titulo": reuniao.get('title', ''),
                    "data": reuniao.get('start_time', '')[:10] if reuniao.get('start_time') else '',
                    "hora": reuniao.get('start_time', '')[11:16] if reuniao.get('start_time') else '',
                    "duracao": f"{reuniao.get('duration_seconds', 0) // 60} min",
                    "participantes": reuniao.get('participants', []),
                    "pauta": reuniao.get('key_points', []),
                    "decisoes": reuniao.get('decisions', []),
                    "transcricao": reuniao.get('transcription_full', ''),
                    "tags": []  # TODO: Extrair tags do conteúdo
                }

                resultados.append({
                    "tipo": "reunião",
                    "relevancia": reuniao.get('relevance', 1),
                    "dados": dados_adaptados,
                    "trechos_relevantes": self.extrair_trechos_relevantes(
                        reuniao.get('transcription_full', ''),
                        termos
                    )
                })

            # ===== ORDENAÇÃO E LIMITAÇÃO =====
            # Ordena por relevância decrescente e limita resultados
            resultados.sort(key=lambda x: x['relevancia'], reverse=True)

            return resultados[:self.max_resultados]

        except Exception as e:
            raise RuntimeError(f"Erro ao buscar no Supabase: {e}")

    def buscar_em_documentos(self, termos: List[str]) -> List[Dict[str, Any]]:
        """
        Busca termos em documentos.

        Args:
            termos: Termos de busca

        Returns:
            List[Dict]: Documentos encontrados com relevância
        """
        # ===== BUSCA APENAS NO BANCO REAL - SEM FALLBACKS =====
        if not self.db:
            raise RuntimeError("Sistema requer conexão com Supabase")

        try:
            # Obtém departamento do usuário se disponível
            department = None
            if self.contexto_atual and 'user_data' in self.contexto_atual:
                department = self.contexto_atual['user_data'].get('department')

            # Busca documentos no Supabase
            documentos = self.db.buscar_documentos(
                termos_busca=termos,
                department=department,
                limit=self.max_resultados
            )

            # Formata resultados
            resultados = []
            for doc in documentos:
                dados_adaptados = {
                    "id": doc.get('id'),
                    "titulo": doc.get('title', ''),
                    "tipo": doc.get('doc_type', 'documento'),
                    "data_criacao": doc.get('created_at', '')[:10] if doc.get('created_at') else '',
                    "autor": "Sistema",  # TODO: Buscar nome do autor pelo ID
                    "conteudo": doc.get('content_full', ''),
                    "tags": doc.get('tags', [])
                }

                # Calcula relevância
                relevancia = self.calcular_relevancia(
                    dados_adaptados['conteudo'],
                    termos,
                    dados_adaptados['titulo'],
                    dados_adaptados['autor']
                )

                resultados.append({
                    "tipo": "documento",
                    "relevancia": relevancia,
                    "dados": dados_adaptados,
                    "trechos_relevantes": self.extrair_trechos_relevantes(
                        doc.get('content_full', ''),
                        termos
                    )
                })

            # Ordena por relevância
            resultados.sort(key=lambda x: x['relevancia'], reverse=True)
            return resultados[:self.max_resultados]

        except Exception as e:
            raise RuntimeError(f"Erro ao buscar documentos no Supabase: {e}")

    def extrair_trechos_relevantes(self, texto: str, termos: List[str],
                                  contexto_chars: int = 100) -> List[str]:
        """
        Extrai trechos do texto que contêm os termos de busca.

        Args:
            texto: Texto completo
            termos: Termos para destacar
            contexto_chars: Número de caracteres de contexto

        Returns:
            List[str]: Trechos relevantes
        """
        trechos = []
        texto_lower = texto.lower()

        for termo in termos:
            termo_lower = termo.lower()

            # Encontrar todas as ocorrências
            inicio = 0
            while True:
                pos = texto_lower.find(termo_lower, inicio)
                if pos == -1:
                    break

                # ===== EXTRAÇÃO DE TRECHO COM CONTEXTO =====
                # Define limites do trecho considerando o contexto
                inicio_trecho = max(0, pos - contexto_chars)
                fim_trecho = min(len(texto), pos + len(termo) + contexto_chars)

                trecho = texto[inicio_trecho:fim_trecho]

                # Adiciona reticências para indicar truncamento
                if inicio_trecho > 0:
                    trecho = "..." + trecho
                if fim_trecho < len(texto):
                    trecho = trecho + "..."

                # Destaca o termo encontrado usando markdown
                trecho_destacado = trecho.replace(
                    termo,
                    f"**{termo}**"
                )

                if trecho_destacado not in trechos:
                    trechos.append(trecho_destacado)

                inicio = pos + 1

                # Limita a 3 trechos por termo para evitar excesso
                if len(trechos) >= 3:
                    break

        # Retorna no máximo 5 trechos no total
        return trechos[:5]

    def formatar_resposta_busca(self, consulta: str, resultados_reunioes: List[Dict],
                               resultados_documentos: List[Dict], termos: List[str],
                               posicao_temporal: Optional[int] = None) -> str:
        """
        Formata a resposta da busca de forma clara e estruturada.

        Args:
            consulta: Consulta original do usuário
            resultados_reunioes: Resultados de reuniões
            resultados_documentos: Resultados de documentos
            termos: Termos de busca utilizados
            posicao_temporal: Posição temporal aplicada

        Returns:
            str: Resposta formatada
        """
        # ===== VERIFICAÇÃO DE RESULTADOS VAZIOS =====
        if not resultados_reunioes and not resultados_documentos:
            return self._formatar_resposta_vazia(consulta, termos)

        # ===== CONSTRUÇÃO DA RESPOSTA FORMATADA =====
        partes = []

        # ===== SEÇÃO DE REUNIÕES =====
        if resultados_reunioes:
            # Se foi aplicado filtro temporal, ajustar mensagem
            if posicao_temporal:
                termo_temporal = self._get_termo_temporal(posicao_temporal)
                if len(resultados_reunioes) == 1:
                    partes.append(f"📅 **{termo_temporal.title()} reunião encontrada:**\n")
                else:
                    partes.append("📅 **Reunião encontrada:**\n")
            else:
                total = len(resultados_reunioes)
                partes.append(f"📅 **{total} reuniã{'o' if total == 1 else 'ões'} encontrada{'s' if total > 1 else ''}:**\n")

            # Mostra reuniões encontradas
            for i, resultado in enumerate(resultados_reunioes[:3], 1):
                reuniao = resultado['dados']
                partes.append(f"**{reuniao['titulo']}**")
                partes.append(f"Data: {reuniao['data']} às {reuniao['hora']} - Duração: {reuniao['duracao']}")
                
                if reuniao['participantes']:
                    partes.append(f"Participantes: {', '.join(reuniao['participantes'][:3])}")

                # Trechos relevantes apenas se não for busca temporal
                if not posicao_temporal and resultado['trechos_relevantes']:
                    partes.append(f"Trecho relevante: {resultado['trechos_relevantes'][0]}")

                partes.append("")  # Linha em branco

        # ===== SEÇÃO DE DOCUMENTOS =====
        if resultados_documentos:
            partes.append(f"\n📄 **{len(resultados_documentos)} documento{'s' if len(resultados_documentos) > 1 else ''} encontrado{'s' if len(resultados_documentos) > 1 else ''}:**\n")

            # Mostra apenas os 2 documentos mais relevantes
            for i, resultado in enumerate(resultados_documentos[:2], 1):
                doc = resultado['dados']
                partes.append(f"**{doc['titulo']}**")
                partes.append(f"Tipo: {doc['tipo']} - Data: {doc['data_criacao']}")

                # Trecho relevante
                if resultado['trechos_relevantes']:
                    partes.append(f"Trecho: {resultado['trechos_relevantes'][0]}")

                partes.append("")

        return "\n".join(partes).strip()

    def _get_termo_temporal(self, posicao: int) -> str:
        """
        Retorna o termo temporal baseado na posição.
        
        Args:
            posicao: Posição temporal
            
        Returns:
            Termo temporal correspondente
        """
        # Inverter o dicionário para buscar por valor
        for termo, pos in self.termos_temporais.items():
            if pos == posicao:
                return termo
        return "Posição {posicao}"

    def _formatar_resposta_vazia(self, consulta: str, termos: List[str]) -> str:
        """
        Formata resposta quando não há resultados.

        Args:
            consulta: Consulta original
            termos: Termos utilizados

        Returns:
            str: Resposta formatada
        """
        # ===== MENSAGEM CONCISA PARA BUSCA SEM RESULTADOS =====
        return "Não encontrei resultados para sua busca. Tente usar outros termos ou seja mais específico."

    def buscar_por_periodo(self, data_inicio: str, data_fim: str) -> List[Dict[str, Any]]:
        """
        Busca reuniões em um período específico.

        Args:
            data_inicio: Data inicial (YYYY-MM-DD)
            data_fim: Data final (YYYY-MM-DD)

        Returns:
            List[Dict]: Reuniões no período
        """
        # ===== BUSCA NO BANCO REAL SE DISPONÍVEL =====
        if self.usar_banco_real:
            try:
                user_id = self.contexto_atual.get('user_id') if self.contexto_atual else None

                # Busca todas as reuniões do usuário
                reunioes = self.db.buscar_reunioes_usuario(user_id, limit=100)

                # Filtra por período
                resultados = []
                for reuniao in reunioes:
                    data_reuniao = reuniao.get('start_time', '')[:10]
                    if data_inicio <= data_reuniao <= data_fim:
                        dados_adaptados = {
                            "id": reuniao.get('id'),
                            "titulo": reuniao.get('title', ''),
                            "data": data_reuniao,
                            "hora": reuniao.get('start_time', '')[11:16] if reuniao.get('start_time') else '',
                            "duracao": f"{reuniao.get('duration_seconds', 0) // 60} min",
                            "participantes": reuniao.get('participants', []),
                            "pauta": reuniao.get('key_points', []),
                            "decisoes": reuniao.get('decisions', []),
                            "transcricao": reuniao.get('transcription_full', ''),
                            "tags": []
                        }

                        resultados.append({
                            "tipo": "reunião",
                            "dados": dados_adaptados
                        })

                return resultados

            except Exception as e:
                print(f"[ERRO] Falha ao buscar por período: {e}")

        return []

    def buscar_por_participante(self, nome_participante: str) -> List[Dict[str, Any]]:
        """
        Busca reuniões de um participante específico.

        Args:
            nome_participante: Nome do participante

        Returns:
            List[Dict]: Reuniões do participante
        """
        if not self.db:
            return []
            
        try:
            # Buscar reuniões que contenham o nome do participante
            reunioes = self.db.buscar_reunioes_por_texto(
                termos_busca=[nome_participante],
                user_id=self.contexto_atual.get('user_id') if self.contexto_atual else None,
                limit=self.max_resultados
            )
            
            # Formatar resultados
            resultados = []
            for reuniao in reunioes:
                dados_adaptados = {
                    "id": reuniao.get('id'),
                    "titulo": reuniao.get('title', ''),
                    "data": reuniao.get('start_time', '')[:10] if reuniao.get('start_time') else '',
                    "hora": reuniao.get('start_time', '')[11:16] if reuniao.get('start_time') else '',
                    "duracao": f"{reuniao.get('duration_seconds', 0) // 60} min",
                    "participantes": reuniao.get('participants', []),
                    "pauta": reuniao.get('key_points', []),
                    "decisoes": reuniao.get('decisions', []),
                    "transcricao": reuniao.get('transcription_full', ''),
                }
                
                resultados.append({
                    "tipo": "reunião",
                    "dados": dados_adaptados
                })
                
            return resultados
            
        except Exception as e:
            print(f"[ERRO] Falha ao buscar por participante: {e}")
            return []

    def gerar_resumo_topico(self, topico: str, num_items: int = 5) -> str:
        """
        Gera um resumo sobre um tópico específico.

        Args:
            topico: Tópico para resumir
            num_items: Número de itens para incluir

        Returns:
            str: Resumo formatado
        """
        # ===== BUSCA INICIAL SOBRE O TÓPICO =====
        termos = self.extrair_termos_busca(topico)
        resultados_reunioes = self.buscar_em_reunioes(termos)

        # Retorna mensagem se não há dados suficientes
        if not resultados_reunioes:
            return f"Não encontrei informações sobre '{topico}'."

        # ===== EXTRAÇÃO E AGREGAÇÃO DE DADOS =====
        # Coleta todas as informações relevantes das reuniões encontradas
        todas_decisoes = []
        todos_participantes = []
        todas_datas = []

        for resultado in resultados_reunioes[:num_items]:
            reuniao = resultado['dados']
            todas_decisoes.extend(reuniao['decisoes'])
            todos_participantes.extend(reuniao['participantes'])
            todas_datas.append(reuniao['data'])

        # ===== ANÁLISE DE FREQUÊNCIA =====
        # Identifica os 3 participantes mais ativos no tópico
        participantes_freq = Counter(todos_participantes).most_common(3)

        # ===== FORMATAÇÃO DO RESUMO =====
        resumo = [
            f"📊 **Resumo: {topico}**\n",
            f"**Total de reuniões:** {len(resultados_reunioes)}",
            f"**Período:** {min(todas_datas)} a {max(todas_datas)}\n",
            "**Principais participantes:**"
        ]

        for participante, freq in participantes_freq:
            resumo.append(f"• {participante} ({freq} reuniões)")

        # ===== LISTA DE DECISÕES RELEVANTES =====
        resumo.append("\n**Principais pontos:**")
        # Mostra até 5 decisões que contêm os termos do tópico
        pontos_mostrados = 0
        for decisao in todas_decisoes:
            if any(t.lower() in decisao.lower() for t in termos):
                resumo.append(f"• {decisao}")
                pontos_mostrados += 1
                if pontos_mostrados >= 5:
                    break

        return "\n".join(resumo)

    def _converter_resultados_semanticos(self, resultados_semanticos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converte resultados da busca semântica para o formato esperado.

        Args:
            resultados_semanticos: Resultados da busca por embeddings

        Returns:
            Lista no formato padrão do agente
        """
        resultados_convertidos = []

        for resultado in resultados_semanticos:
            meeting_data = resultado.get('meeting_data', {})

            if meeting_data:
                # Adaptar formato para o esperado pelo agente
                dados_adaptados = {
                    "id": meeting_data.get('id'),
                    "titulo": meeting_data.get('title', ''),
                    "data": meeting_data.get('start_time', '')[:10] if meeting_data.get('start_time') else '',
                    "hora": meeting_data.get('start_time', '')[11:16] if meeting_data.get('start_time') else '',
                    "duracao": f"{meeting_data.get('duration_seconds', 0) // 60} min",
                    "participantes": meeting_data.get('participants', []),
                    "pauta": meeting_data.get('key_points', []),
                    "decisoes": meeting_data.get('decisions', []),
                    "transcricao": meeting_data.get('transcription_full', ''),
                    "tags": []
                }

                resultados_convertidos.append({
                    "tipo": "reunião",
                    "relevancia": resultado.get('similarity', 0) * 100,  # Converter para escala 0-100
                    "dados": dados_adaptados,
                    "trechos_relevantes": [resultado.get('chunk_text', '')[:200] + "..."] if resultado.get('chunk_text') else []
                })

        return resultados_convertidos

    def __repr__(self):
        return f"AgenteConsultaInteligente(max_resultados={self.max_resultados})"
