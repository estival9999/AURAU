"""
Agente de Consulta Inteligente - Especialista em busca e recuperação de informações.
Realiza buscas semânticas, correlaciona dados e apresenta informações relevantes.
"""

from typing import Dict, List, Any, Optional, Tuple
import os
import re
from datetime import datetime
from collections import Counter

# Importar classe base apropriada
if os.getenv("OPENAI_API_KEY"):
    from .agente_base import AgenteBase
else:
    from .agente_base_simulado import AgenteBaseSimulado as AgenteBase

# Importar o novo sistema de templates
from .prompt_template import PromptTemplate, TomResposta

# Importar handler do Supabase
try:
    from ..database.supabase_handler import SupabaseHandler
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("[AVISO] Supabase não disponível, usando dados mock")


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
        
        # ===== MODO DE OPERAÇÃO =====
        # SEMPRE usa banco real - sem mocks
        self.usar_banco_real = True  # Forçado para True
        
        # REMOVIDO: Mock de base de dados - APENAS Supabase
        self.mock_reunioes = []  # Vazio - não será usado
            {
                "id": "001",
                "titulo": "Kickoff do Projeto AURALIS",
                "data": "2024-01-15",
                "hora": "14:00",
                "duracao": "90 min",
                "participantes": ["João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa"],
                "pauta": ["Definição de escopo", "Cronograma", "Atribuição de responsabilidades"],
                "decisoes": [
                    "Prazo de entrega definido para 30/06/2024",
                    "Maria Santos será a gerente do projeto",
                    "Reuniões semanais às segundas 10h"
                ],
                "transcricao": "João: Vamos começar definindo o escopo do projeto AURALIS...",
                "tags": ["kickoff", "projeto", "planejamento"]
            },
            {
                "id": "002",
                "titulo": "Revisão Sprint 1 - AURALIS",
                "data": "2024-01-22",
                "hora": "15:00",
                "duracao": "60 min",
                "participantes": ["Maria Santos", "Pedro Oliveira", "Lucas Mendes"],
                "pauta": ["Review das entregas", "Impedimentos", "Próximos passos"],
                "decisoes": [
                    "Sprint aprovada com 85% das tarefas concluídas",
                    "Necessário contratar mais um desenvolvedor",
                    "Ajustar estimativas para próxima sprint"
                ],
                "transcricao": "Maria: A sprint foi produtiva, mas encontramos alguns desafios...",
                "tags": ["sprint", "review", "agile"]
            },
            {
                "id": "003",
                "titulo": "Brainstorming - Funcionalidades IA",
                "data": "2024-01-25",
                "hora": "10:00",
                "duracao": "120 min",
                "participantes": ["Pedro Oliveira", "Ana Costa", "Carlos Tech", "João Silva"],
                "pauta": ["Ideação de features", "Priorização", "Viabilidade técnica"],
                "decisoes": [
                    "Implementar busca semântica como prioridade 1",
                    "Sistema de agentes para processamento inteligente",
                    "Interface de voz para próxima fase"
                ],
                "transcricao": "Ana: Precisamos pensar em como a IA pode agregar valor...",
                "tags": ["brainstorm", "ia", "funcionalidades", "inovação"]
            }
        ]
        
        self.mock_documentos = [
            {
                "id": "doc001",
                "titulo": "Plano de Projeto AURALIS",
                "tipo": "documento",
                "data_criacao": "2024-01-10",
                "autor": "João Silva",
                "conteudo": "Documento detalhando objetivos, escopo e metodologia do projeto...",
                "tags": ["planejamento", "projeto", "documentação"]
            },
            {
                "id": "doc002",
                "titulo": "Arquitetura do Sistema",
                "tipo": "documento técnico",
                "data_criacao": "2024-01-20",
                "autor": "Pedro Oliveira",
                "conteudo": "Descrição da arquitetura multi-agente, componentes e integrações...",
                "tags": ["arquitetura", "técnico", "sistema"]
            }
        ]
    
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
        
        # ===== EXTRAÇÃO E EXPANSÃO DE TERMOS =====
        # Extrai termos relevantes e expande com sinônimos
        termos = self.extrair_termos_busca(mensagem)
        termos_expandidos = self.expandir_termos(termos)
        
        print(f"[CONSULTA] Termos de busca: {termos}")
        print(f"[CONSULTA] Termos expandidos: {termos_expandidos}")
        
        # ===== BUSCA EM MÚLTIPLAS FONTES =====
        # Realiza busca em reuniões e documentos separadamente
        resultados_reunioes = self.buscar_em_reunioes(termos_expandidos)
        resultados_documentos = self.buscar_em_documentos(termos_expandidos)
        
        # ===== CONSOLIDAÇÃO DOS RESULTADOS =====
        # Formata todos os resultados em uma resposta estruturada
        resposta = self.formatar_resposta_busca(
            mensagem, 
            resultados_reunioes, 
            resultados_documentos,
            termos
        )
        
        # Adicionar ao histórico
        self.adicionar_ao_historico(mensagem, resposta)
        
        return resposta
    
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
            "um", "uma", "uns", "umas"
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
                limit=self.max_resultados
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
                               resultados_documentos: List[Dict], termos: List[str]) -> str:
        """
        Formata a resposta da busca de forma clara e estruturada.
        
        Args:
            consulta: Consulta original do usuário
            resultados_reunioes: Resultados de reuniões
            resultados_documentos: Resultados de documentos
            termos: Termos de busca utilizados
            
        Returns:
            str: Resposta formatada
        """
        # ===== VERIFICAÇÃO DE RESULTADOS VAZIOS =====
        if not resultados_reunioes and not resultados_documentos:
            return self._formatar_resposta_vazia(consulta, termos)
        
        # ===== CONSTRUÇÃO DA RESPOSTA FORMATADA =====
        partes = []
        
        # Cabeçalho com resumo dos resultados
        total_resultados = len(resultados_reunioes) + len(resultados_documentos)
        partes.append(f"🔍 **Encontrei {total_resultados} resultado(s) relevante(s) para sua busca.**\n")
        
        # ===== SEÇÃO DE REUNIÕES =====
        if resultados_reunioes:
            partes.append("### 📅 Reuniões Encontradas:\n")
            
            # Mostra apenas as 3 reuniões mais relevantes
            for i, resultado in enumerate(resultados_reunioes[:3], 1):
                reuniao = resultado['dados']
                partes.append(f"**{i}. {reuniao['titulo']}**")
                partes.append(f"   - Data: {reuniao['data']} às {reuniao['hora']}")
                partes.append(f"   - Participantes: {', '.join(reuniao['participantes'][:3])}")
                
                # ===== FILTRA DECISÕES RELEVANTES =====
                # Mostra apenas decisões que contêm os termos buscados
                decisoes_relevantes = [d for d in reuniao['decisoes'] 
                                     if any(t.lower() in d.lower() for t in termos)]
                if decisoes_relevantes:
                    partes.append(f"   - Decisões relacionadas:")
                    # Limita a 2 decisões por reunião
                    for decisao in decisoes_relevantes[:2]:
                        partes.append(f"     • {decisao}")
                
                # Trechos relevantes
                if resultado['trechos_relevantes']:
                    partes.append(f"   - Trecho relevante: {resultado['trechos_relevantes'][0]}")
                
                partes.append("")  # Linha em branco
        
        # ===== SEÇÃO DE DOCUMENTOS =====
        if resultados_documentos:
            partes.append("### 📄 Documentos Encontrados:\n")
            
            # Mostra apenas os 2 documentos mais relevantes
            for i, resultado in enumerate(resultados_documentos[:2], 1):
                doc = resultado['dados']
                partes.append(f"**{i}. {doc['titulo']}**")
                partes.append(f"   - Tipo: {doc['tipo']}")
                partes.append(f"   - Autor: {doc['autor']}")
                partes.append(f"   - Data: {doc['data_criacao']}")
                
                # Trecho relevante
                if resultado['trechos_relevantes']:
                    partes.append(f"   - Trecho: {resultado['trechos_relevantes'][0]}")
                
                partes.append("")
        
        # ===== SUGESTÕES PARA POUCOS RESULTADOS =====
        # Se encontrou poucos resultados, oferece dicas de busca
        if total_resultados < 3:
            partes.append("\n💡 **Sugestões para refinar sua busca:**")
            partes.append("- Tente usar termos mais específicos")
            partes.append("- Inclua nomes de participantes ou datas aproximadas")
            partes.append("- Use palavras-chave dos tópicos discutidos")
        
        return "\n".join(partes)
    
    def _formatar_resposta_vazia(self, consulta: str, termos: List[str]) -> str:
        """
        Formata resposta quando não há resultados.
        
        Args:
            consulta: Consulta original
            termos: Termos utilizados
            
        Returns:
            str: Resposta formatada
        """
        # ===== MENSAGEM PARA BUSCA SEM RESULTADOS =====
        resposta = [
            "🔍 **Não encontrei resultados para sua busca.**\n",
            f"Termos pesquisados: {', '.join(termos)}\n",
            "**Sugestões:**",
            "• Verifique a ortografia dos termos",
            "• Use palavras mais genéricas",
            "• Tente sinônimos ou termos relacionados",
            "• Especifique um período de tempo diferente\n",
            "Posso ajudar de outra forma? Tente reformular sua pergunta ou peça sugestões de busca."
        ]
        
        return "\n".join(resposta)
    
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
        
        # ===== FALLBACK PARA MOCK =====
        resultados = []
        
        # ===== FILTRA REUNIÕES POR PERÍODO =====
        for reuniao in self.mock_reunioes:
            # Verifica se a data da reunião está dentro do intervalo
            if data_inicio <= reuniao['data'] <= data_fim:
                resultados.append({
                    "tipo": "reunião",
                    "dados": reuniao
                })
        
        return resultados
    
    def buscar_por_participante(self, nome_participante: str) -> List[Dict[str, Any]]:
        """
        Busca reuniões de um participante específico.
        
        Args:
            nome_participante: Nome do participante
            
        Returns:
            List[Dict]: Reuniões do participante
        """
        resultados = []
        nome_lower = nome_participante.lower()
        
        # ===== BUSCA POR NOME DE PARTICIPANTE =====
        for reuniao in self.mock_reunioes:
            # Converte nomes para minúsculas para busca case-insensitive
            participantes_lower = [p.lower() for p in reuniao['participantes']]
            # Verifica se o nome buscado está contido em algum participante
            if any(nome_lower in p for p in participantes_lower):
                resultados.append({
                    "tipo": "reunião",
                    "dados": reuniao
                })
        
        return resultados
    
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
            return f"Não encontrei informações suficientes sobre '{topico}' para gerar um resumo."
        
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
            f"📊 **Resumo sobre: {topico}**\n",
            f"**Período analisado:** {min(todas_datas)} a {max(todas_datas)}",
            f"**Total de reuniões:** {len(resultados_reunioes)}\n",
            "**Principais participantes:**"
        ]
        
        for participante, freq in participantes_freq:
            resumo.append(f"• {participante} ({freq} reuniões)")
        
        # ===== LISTA DE DECISÕES RELEVANTES =====
        resumo.append("\n**Principais decisões/pontos:**")
        # Mostra até 5 decisões que contêm os termos do tópico
        for decisao in todas_decisoes[:5]:
            if any(t.lower() in decisao.lower() for t in termos):
                resumo.append(f"• {decisao}")
        
        return "\n".join(resumo)
    
    def __repr__(self):
        return f"AgenteConsultaInteligente(max_resultados={self.max_resultados})"