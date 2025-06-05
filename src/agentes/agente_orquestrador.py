"""
Agente Orquestrador - O "maestro" do sistema AURALIS.
Interpreta intenções, direciona para agentes especializados e coordena respostas.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import os
from enum import Enum

# Importar classe base apropriada
if os.getenv("OPENAI_API_KEY"):
    from .agente_base import AgenteBase
else:
    from .agente_base_simulado import AgenteBaseSimulado as AgenteBase

# Importar o novo sistema de templates
from .prompt_template import PromptTemplate, TomResposta


class TipoIntencao(Enum):
    """Tipos de intenção que o orquestrador pode identificar.

    Cada tipo direciona para um agente especializado diferente.
    """
    CONSULTA = "CONSULTA"      # Busca de informações
    BRAINSTORM = "BRAINSTORM"  # Geração de ideias
    ANALISE = "ANALISE"        # Análise de dados
    GERAL = "GERAL"            # Consultas gerais
    MULTIPLA = "MULTIPLA"      # Múltiplas intenções


class AgenteOrquestrador(AgenteBase):
    """
    Agente responsável por orquestrar o sistema AURALIS.

    Principais responsabilidades:
    - Interpretar intenções do usuário
    - Direcionar para agentes especializados
    - Coordenar respostas múltiplas
    - Manter contexto geral da conversa
    """

    def __init__(self):
        super().__init__(
            nome="Orquestrador AURALIS",
            descricao="Agente maestro que coordena e direciona as interações no sistema"
        )

        # ===== CONFIGURAÇÃO DO TEMPLATE =====
        # Usa o novo sistema de templates padronizados
        self.config_prompt = PromptTemplate.criar_config_orquestrador()

        # ===== MAPA DE AGENTES ESPECIALIZADOS =====
        # Mapeia cada tipo de intenção para o nome do agente responsável
        self.mapa_agentes = {
            TipoIntencao.CONSULTA: "Consultor Inteligente AURALIS",
            TipoIntencao.BRAINSTORM: "Agente Criativo AURALIS",
            TipoIntencao.ANALISE: "Analista AURALIS"
        }

        # ===== REFERÊNCIAS AOS AGENTES =====
        # Referências diretas aos agentes especializados
        # Serão definidas pelo sistema através do método definir_agentes()
        self.agente_consulta = None
        self.agente_brainstorm = None
        self.agente_analise = None

        # ===== PALAVRAS-CHAVE PARA IDENTIFICAÇÃO =====
        # Dicionário expandido com sinônimos e variações
        self.palavras_chave = {
            TipoIntencao.CONSULTA: [
                # Verbos de busca
                "buscar", "encontrar", "procurar", "localizar", "pesquisar", "consultar",
                "verificar", "checar", "conferir", "identificar", "descobrir",
                # Pronomes interrogativos
                "quando", "onde", "quem", "qual", "quais", "quanto", "como", "porque",
                # Substantivos relacionados
                "reunião", "reuniões", "meeting", "documento", "documentos", "arquivo",
                "histórico", "informação", "informações", "dado", "dados", "registro",
                # Ações de visualização
                "listar", "mostrar", "exibir", "apresentar", "ver", "visualizar",
                # Contexto temporal
                "última", "último", "anterior", "passada", "recente", "hoje", "ontem",
                "semana", "mês", "participou", "participaram", "decidiu", "decidido",
                # Termos temporais específicos
                "primeira", "segunda", "terceira", "penúltima", "última", 
                "mais recente", "mais antiga"
            ],
            TipoIntencao.BRAINSTORM: [
                # Substantivos criativos
                "ideia", "ideias", "sugestão", "sugestões", "proposta", "propostas",
                "solução", "soluções", "alternativa", "alternativas", "opção", "opções",
                # Verbos de criação
                "criar", "gerar", "produzir", "desenvolver", "elaborar", "pensar",
                "imaginar", "inovar", "inventar", "conceber", "formular",
                # Termos de melhoria
                "melhorar", "aprimorar", "otimizar", "aperfeiçoar", "evoluir",
                "transformar", "revolucionar", "mudar", "modificar",
                # Termos explícitos
                "brainstorm", "brainstorming", "criativo", "criatividade", "inovação",
                "inovador", "fora da caixa", "diferente", "novo", "original"
            ],
            TipoIntencao.ANALISE: [
                # Verbos analíticos
                "analisar", "examinar", "investigar", "estudar", "avaliar", "revisar",
                "comparar", "contrastar", "correlacionar", "diagnosticar",
                # Substantivos analíticos
                "análise", "tendência", "tendências", "padrão", "padrões", "comportamento",
                "estatística", "estatísticas", "métrica", "métricas", "indicador",
                "indicadores", "kpi", "dashboard", "relatório", "gráfico",
                # Termos de insights
                "insight", "insights", "conclusão", "conclusões", "descoberta",
                "observação", "interpretação", "entendimento", "compreensão"
            ]
        }

        # ===== CONFIGURAÇÕES DO MODELO =====
        # Usa configurações do template
        self.temperatura = self.config_prompt.temperatura
        
        # ===== HISTÓRICO DA CONVERSA =====
        # Mantém histórico da conversa atual para contexto
        self.historico_conversa_atual = []
        
        # ===== CONTADOR DE MENSAGENS SEM CONTEÚDO =====
        self.mensagens_vazias = 0

    def get_prompt_sistema(self) -> str:
        """
        Define o prompt do sistema para o agente orquestrador.

        Returns:
            str: Prompt do sistema usando o template padronizado
        """
        # Usa o novo sistema de templates com contexto atual
        return PromptTemplate.gerar_prompt_contextualizado(
            self.config_prompt,
            self.contexto_atual
        )

    def identificar_intencao(self, mensagem: str) -> Tuple[TipoIntencao, float]:
        """
        Identifica a intenção principal da mensagem do usuário.

        Args:
            mensagem: Mensagem do usuário

        Returns:
            Tuple[TipoIntencao, float]: Tipo de intenção e score de confiança
        """
        mensagem_lower = mensagem.lower()

        # ===== CÁLCULO DE SCORES =====
        # Calcula pontos para cada tipo de intenção baseado nas palavras-chave encontradas
        scores = {}

        for tipo_intencao, palavras in self.palavras_chave.items():
            # Conta quantas palavras-chave estão presentes na mensagem
            score = sum(1 for palavra in palavras if palavra in mensagem_lower)
            scores[tipo_intencao] = score

        # Identificar intenção com maior score
        max_score = max(scores.values())

        # Se nenhuma palavra-chave foi encontrada, classifica como consulta geral
        if max_score == 0:
            return TipoIntencao.GERAL, 0.5

        # ===== DETECÇÃO DE MÚLTIPLAS INTENÇÕES =====
        # Verifica se há múltiplas intenções com scores próximos (70% do máximo)
        intencoes_altas = [t for t, s in scores.items() if s >= max_score * 0.7 and s > 0]

        if len(intencoes_altas) > 1:
            return TipoIntencao.MULTIPLA, 0.8

        # Retornar a intenção com maior score
        intencao_principal = max(scores, key=scores.get)
        # Normaliza a confiança entre 0 e 1 (máximo de 5 palavras-chave)
        confianca = min(scores[intencao_principal] / 5.0, 1.0)

        return intencao_principal, confianca

    def identificar_multiplas_intencoes(self, mensagem: str) -> List[TipoIntencao]:
        """
        Identifica múltiplas intenções em uma mensagem.

        Args:
            mensagem: Mensagem do usuário

        Returns:
            List[TipoIntencao]: Lista de intenções identificadas
        """
        mensagem_lower = mensagem.lower()
        intencoes_encontradas = []

        for tipo_intencao, palavras in self.palavras_chave.items():
            if any(palavra in mensagem_lower for palavra in palavras):
                intencoes_encontradas.append(tipo_intencao)

        return intencoes_encontradas if intencoes_encontradas else [TipoIntencao.GERAL]

    def _verificar_casos_especiais(self, mensagem: str) -> Optional[str]:
        """
        Verifica casos especiais e erros comuns antes do processamento.

        Args:
            mensagem: Mensagem do usuário

        Returns:
            Optional[str]: Resposta de erro se aplicável, None caso contrário
        """
        # ===== ENTRADA VAZIA =====
        if not mensagem or not mensagem.strip():
            self.mensagens_vazias += 1
            if self.mensagens_vazias == 1:
                return "Como posso ajudar? 🤖"
            else:
                return "Digite algo para eu poder ajudar."

        # Reset contador se mensagem não é vazia
        self.mensagens_vazias = 0

        # ===== ENTRADA MUITO CURTA (possível comando incompleto) =====
        mensagem_limpa = mensagem.strip().lower()
        if len(mensagem_limpa) < 3:
            return "Mensagem muito curta. Pode elaborar?"

        # ===== ENTRADA MUITO LONGA =====
        if len(mensagem) > 1000:
            return "Mensagem muito longa. Tente ser mais direto."

        # ===== COMANDOS DE AJUDA =====
        if mensagem_limpa in ["ajuda", "help", "?", "o que você faz", "o que voce faz", "comandos"]:
            return self._gerar_mensagem_ajuda()

        # ===== SAUDAÇÕES =====
        saudacoes = ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "hey", "ei"]
        if mensagem_limpa in saudacoes:
            # Resposta concisa e precisa
            return "Olá! Como posso ajudar? 🤖🔍"

        return None  # Nenhum caso especial detectado

    def _gerar_mensagem_ajuda(self) -> str:
        """
        Gera mensagem de ajuda concisa.

        Returns:
            str: Mensagem de ajuda formatada
        """
        return """**Posso ajudar com:**
• Buscar reuniões e documentos
• Gerar ideias e sugestões
• Analisar dados e tendências

**Exemplos:**
"Última reunião sobre vendas"
"Ideias para melhorar produtividade"
"Análise das reuniões do mês"
"""

    def processar_mensagem(self, mensagem: str, contexto: Dict[str, Any] = None) -> str:
        """
        Processa a mensagem do usuário e orquestra a resposta.

        Args:
            mensagem: Mensagem do usuário
            contexto: Contexto adicional

        Returns:
            str: Resposta orquestrada
        """
        # Atualizar contexto
        if contexto:
            self.atualizar_contexto(contexto)

        # ===== ADICIONAR AO HISTÓRICO DA CONVERSA =====
        self.historico_conversa_atual.append({
            "role": "user",
            "content": mensagem,
            "timestamp": self.contexto_atual.get("timestamp", "")
        })

        # ===== VALIDAÇÕES E CASOS ESPECIAIS =====
        # Verifica casos de erro antes de processar
        resposta_erro = self._verificar_casos_especiais(mensagem)
        if resposta_erro:
            return resposta_erro

        # Identificar intenção
        intencao, confianca = self.identificar_intencao(mensagem)

        # Log para depuração - mostra a intenção identificada
        print(f"[ORQUESTRADOR] Intenção identificada: {intencao.value} (confiança: {confianca:.2f})")

        # ===== PROCESSAMENTO BASEADO NA INTENÇÃO =====
        if intencao == TipoIntencao.MULTIPLA:
            # Identifica e processa cada intenção separadamente
            intencoes = self.identificar_multiplas_intencoes(mensagem)
            resposta = self._processar_multiplas_intencoes(mensagem, intencoes, contexto)

        elif intencao == TipoIntencao.GERAL:
            # Responder diretamente
            resposta = self._processar_consulta_geral(mensagem, contexto)

        else:
            # Delegar para agente específico
            resposta = self._delegar_para_agente(mensagem, intencao, contexto)

        # Adicionar resposta ao histórico
        self.historico_conversa_atual.append({
            "role": "assistant",
            "content": resposta,
            "timestamp": self.contexto_atual.get("timestamp", "")
        })
        
        # Manter apenas últimas 10 mensagens no histórico
        if len(self.historico_conversa_atual) > 10:
            self.historico_conversa_atual = self.historico_conversa_atual[-10:]

        # Adicionar ao histórico permanente
        self.adicionar_ao_historico(mensagem, resposta)

        return resposta

    def _processar_multiplas_intencoes(self, mensagem: str, intencoes: List[TipoIntencao],
                                      contexto: Dict[str, Any]) -> str:
        """
        Processa múltiplas intenções coordenando vários agentes.

        Args:
            mensagem: Mensagem original
            intencoes: Lista de intenções identificadas
            contexto: Contexto da conversa

        Returns:
            str: Resposta consolidada
        """
        respostas = []

        # Mensagem introdutória concisa
        respostas.append("Vou abordar cada parte:\n")

        # ===== PROCESSAMENTO DE CADA INTENÇÃO =====
        for i, intencao in enumerate(intencoes, 1):
            # Pula intenções gerais (já processadas)
            if intencao == TipoIntencao.GERAL:
                continue

            # Adiciona subtítulo formatado para cada seção
            subtitulo = f"\n**{self._get_titulo_intencao(intencao)}:**"
            respostas.append(subtitulo)

            # Delega para o agente especializado apropriado
            resposta_agente = self._delegar_para_agente(mensagem, intencao, contexto)
            respostas.append(resposta_agente)

        return "\n".join(respostas)

    def _delegar_para_agente(self, mensagem: str, intencao: TipoIntencao,
                            contexto: Dict[str, Any]) -> str:
        """
        Delega a mensagem para o agente especializado apropriado.

        Args:
            mensagem: Mensagem para processar
            intencao: Tipo de intenção identificada
            contexto: Contexto da conversa

        Returns:
            str: Resposta do agente especializado
        """
        # Adicionar histórico da conversa ao contexto
        contexto_completo = contexto.copy() if contexto else {}
        contexto_completo["historico_conversa"] = self.historico_conversa_atual
        
        # ===== DELEGAÇÃO PARA AGENTES ESPECIALIZADOS =====
        # Verifica se temos referência direta ao agente apropriado
        if intencao == TipoIntencao.CONSULTA and self.agente_consulta:
            return self.agente_consulta.processar_mensagem(mensagem, contexto_completo)

        elif intencao == TipoIntencao.BRAINSTORM and self.agente_brainstorm:
            return self.agente_brainstorm.processar_mensagem(mensagem, contexto_completo)

        elif intencao == TipoIntencao.ANALISE and self.agente_analise:
            # Se não temos agente de análise específico, usa o de consulta
            agente = self.agente_analise or self.agente_consulta
            if agente:
                return agente.processar_mensagem(mensagem, contexto_completo)

        # Fallback: se não há agente disponível, processa localmente
        return self._processar_localmente(mensagem, intencao, contexto_completo)

    def _processar_localmente(self, mensagem: str, intencao: TipoIntencao,
                             contexto: Dict[str, Any]) -> str:
        """
        Processa a mensagem localmente quando não há agente especializado disponível.

        Args:
            mensagem: Mensagem para processar
            intencao: Tipo de intenção
            contexto: Contexto da conversa

        Returns:
            str: Resposta processada localmente
        """
        # Prepara prompt específico para processamento local
        prompt = f"""Como Orquestrador do AURALIS, processe esta solicitação de tipo {intencao.value}:

Mensagem do usuário: {mensagem}

Contexto disponível:
{self.formatar_contexto(contexto)}

Histórico recente:
{self._formatar_historico_para_prompt()}

Forneça uma resposta apropriada, clara e concisa."""

        # Chama o modelo de linguagem para processar a solicitação
        resposta = self.chamar_llm(prompt)

        return resposta

    def _processar_consulta_geral(self, mensagem: str, contexto: Dict[str, Any]) -> str:
        """
        Processa consultas gerais que o orquestrador pode responder diretamente.

        Args:
            mensagem: Mensagem do usuário
            contexto: Contexto da conversa

        Returns:
            str: Resposta direta
        """
        prompt = f"""Como Orquestrador do AURALIS, responda diretamente esta consulta geral:

Mensagem: {mensagem}

Contexto:
{self.formatar_contexto(contexto)}

Histórico recente:
{self._formatar_historico_para_prompt()}

Seja claro, conciso e profissional. Responda em no máximo 3 linhas."""

        return self.chamar_llm(prompt)

    def _get_titulo_intencao(self, intencao: TipoIntencao) -> str:
        """
        Retorna um título amigável para cada tipo de intenção.

        Args:
            intencao: Tipo de intenção

        Returns:
            str: Título formatado
        """
        titulos = {
            TipoIntencao.CONSULTA: "Busca",
            TipoIntencao.BRAINSTORM: "Ideias",
            TipoIntencao.ANALISE: "Análise",
            TipoIntencao.GERAL: "Informação"
        }
        return titulos.get(intencao, "Processamento")

    def _formatar_historico_para_prompt(self) -> str:
        """
        Formata o histórico da conversa para incluir no prompt.
        
        Returns:
            str: Histórico formatado
        """
        if not self.historico_conversa_atual:
            return "Nenhum histórico disponível"
        
        # Pegar apenas as últimas 5 mensagens
        historico_recente = self.historico_conversa_atual[-5:]
        
        formatted = []
        for msg in historico_recente:
            role = "Usuário" if msg["role"] == "user" else "Assistente"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)

    def definir_agentes(self, agente_consulta=None, agente_brainstorm=None, agente_analise=None):
        """
        Define as referências diretas aos agentes especializados.

        Args:
            agente_consulta: Instância do agente de consulta
            agente_brainstorm: Instância do agente de brainstorm
            agente_analise: Instância do agente de análise
        """
        if agente_consulta:
            self.agente_consulta = agente_consulta
        if agente_brainstorm:
            self.agente_brainstorm = agente_brainstorm
        if agente_analise:
            self.agente_analise = agente_analise

    def gerar_resumo_executivo(self, topico: str, informacoes: Dict[str, Any]) -> str:
        """
        Gera um resumo executivo consolidando informações de múltiplas fontes.

        Args:
            topico: Tópico do resumo
            informacoes: Dicionário com informações de diferentes agentes

        Returns:
            str: Resumo executivo formatado
        """
        prompt = f"""Gere um resumo executivo profissional sobre: {topico}

Informações disponíveis:
{json.dumps(informacoes, ensure_ascii=False, indent=2)}

O resumo deve incluir:
1. Visão geral (2-3 linhas)
2. Principais pontos identificados
3. Recomendações baseadas nas análises
4. Próximos passos sugeridos

Formato profissional e conciso."""

        return self.chamar_llm(prompt)

    def coordenar_analise_completa(self, topico: str) -> Dict[str, Any]:
        """
        Coordena uma análise completa usando todos os agentes disponíveis.

        Args:
            topico: Tópico para análise completa

        Returns:
            Dict: Resultados consolidados de todos os agentes
        """
        resultados = {
            "topico": topico,
            "timestamp": self.contexto_atual.get("timestamp", ""),
            "analises": {}
        }

        # ===== FASE 1: CONSULTA DE INFORMAÇÕES =====
        # Busca todas as informações existentes sobre o tópico
        if self.agente_consulta:
            resultados["analises"]["informacoes"] = self.agente_consulta.processar_mensagem(
                f"Buscar todas as informações sobre {topico}",
                self.contexto_atual
            )

        # ===== FASE 2: GERAÇÃO DE IDEIAS =====
        # Solicita ideias criativas e inovadoras sobre o tópico
        if self.agente_brainstorm:
            resultados["analises"]["ideias"] = self.agente_brainstorm.processar_mensagem(
                f"Gerar ideias criativas para {topico}",
                self.contexto_atual
            )

        # ===== FASE 3: ANÁLISE DE DADOS =====
        # Analisa padrões, tendências e insights sobre o tópico
        if self.agente_analise:
            resultados["analises"]["analise"] = self.agente_analise.processar_mensagem(
                f"Analisar padrões e tendências relacionados a {topico}",
                self.contexto_atual
            )

        # ===== FASE 4: CONSOLIDAÇÃO =====
        # Gera um resumo executivo consolidando todas as análises
        resultados["resumo_executivo"] = self.gerar_resumo_executivo(topico, resultados["analises"])

        return resultados
    
    def limpar_historico_conversa(self):
        """Limpa o histórico da conversa atual"""
        self.historico_conversa_atual = []
        self.mensagens_vazias = 0

    def __repr__(self):
        # Conta quantos agentes especializados estão conectados
        agentes_conectados = sum(1 for a in [self.agente_consulta, self.agente_brainstorm, self.agente_analise] if a)
        return f"AgenteOrquestrador(agentes_conectados={agentes_conectados})"
