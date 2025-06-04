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


class TipoIntencao(Enum):
    """Tipos de intenção que o orquestrador pode identificar"""
    CONSULTA = "CONSULTA"
    BRAINSTORM = "BRAINSTORM"
    ANALISE = "ANALISE"
    GERAL = "GERAL"
    MULTIPLA = "MULTIPLA"


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
        
        # Mapa de agentes disponíveis
        self.mapa_agentes = {
            TipoIntencao.CONSULTA: "Consultor Inteligente AURALIS",
            TipoIntencao.BRAINSTORM: "Agente Criativo AURALIS",
            TipoIntencao.ANALISE: "Analista AURALIS"
        }
        
        # Referências diretas aos agentes (serão definidas pelo sistema)
        self.agente_consulta = None
        self.agente_brainstorm = None
        self.agente_analise = None
        
        # Palavras-chave para identificação de intenções
        self.palavras_chave = {
            TipoIntencao.CONSULTA: [
                "buscar", "encontrar", "procurar", "localizar", "quando", "onde",
                "quem", "qual", "reunião", "documento", "histórico", "informação",
                "listar", "mostrar", "exibir", "consultar", "verificar"
            ],
            TipoIntencao.BRAINSTORM: [
                "ideia", "ideias", "sugestão", "sugerir", "propor", "criar",
                "inovar", "solução", "alternativa", "criativo", "brainstorm",
                "pensar", "imaginar", "possibilidade", "opção", "melhorar"
            ],
            TipoIntencao.ANALISE: [
                "analisar", "análise", "tendência", "padrão", "comparar",
                "estatística", "métrica", "indicador", "avaliar", "revisar",
                "examinar", "investigar", "estudar", "relatório", "dashboard"
            ]
        }
        
        # Configurações
        self.temperatura = 0.3  # Mais determinístico para orquestração
        
    def get_prompt_sistema(self) -> str:
        """
        Define o prompt do sistema para o agente orquestrador.
        
        Returns:
            str: Prompt do sistema
        """
        return """Você é o Orquestrador do sistema AURALIS, um assistente inteligente para gestão de reuniões e conhecimento corporativo.

Seu papel é:
1. Analisar as perguntas dos usuários e identificar suas intenções
2. Determinar qual tipo de resposta é mais apropriada:
   - CONSULTA: Para buscar informações em reuniões ou base de conhecimento
   - BRAINSTORM: Para gerar ideias e soluções criativas
   - ANÁLISE: Para analisar padrões e tendências
   - GERAL: Para respostas diretas que você pode fornecer

3. Formatar as respostas de forma clara e profissional
4. Manter o contexto da conversa
5. Coordenar múltiplos agentes quando necessário

Diretrizes importantes:
- Sempre identifique claramente a intenção antes de processar
- Se uma pergunta tiver múltiplas intenções, processe cada uma separadamente
- Mantenha um tom profissional mas amigável
- Use formatação clara (bullets, numeração) quando apropriado
- Sempre responda em português brasileiro
- Se não tiver certeza da intenção, peça esclarecimentos

Formato de resposta quando delegar:
- Indique claramente qual agente está sendo consultado
- Apresente a resposta de forma integrada
- Adicione contexto ou explicações quando necessário"""
    
    def identificar_intencao(self, mensagem: str) -> Tuple[TipoIntencao, float]:
        """
        Identifica a intenção principal da mensagem do usuário.
        
        Args:
            mensagem: Mensagem do usuário
            
        Returns:
            Tuple[TipoIntencao, float]: Tipo de intenção e score de confiança
        """
        mensagem_lower = mensagem.lower()
        
        # Calcular scores para cada tipo de intenção
        scores = {}
        
        for tipo_intencao, palavras in self.palavras_chave.items():
            score = sum(1 for palavra in palavras if palavra in mensagem_lower)
            scores[tipo_intencao] = score
        
        # Identificar intenção com maior score
        max_score = max(scores.values())
        
        # Se nenhuma palavra-chave foi encontrada, é uma consulta geral
        if max_score == 0:
            return TipoIntencao.GERAL, 0.5
        
        # Verificar se há múltiplas intenções com scores altos
        intencoes_altas = [t for t, s in scores.items() if s >= max_score * 0.7 and s > 0]
        
        if len(intencoes_altas) > 1:
            return TipoIntencao.MULTIPLA, 0.8
        
        # Retornar a intenção com maior score
        intencao_principal = max(scores, key=scores.get)
        confianca = min(scores[intencao_principal] / 5.0, 1.0)  # Normalizar confiança
        
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
        
        # Identificar intenção
        intencao, confianca = self.identificar_intencao(mensagem)
        
        # Log para debug
        print(f"[ORQUESTRADOR] Intenção identificada: {intencao.value} (confiança: {confianca:.2f})")
        
        # Processar baseado na intenção
        if intencao == TipoIntencao.MULTIPLA:
            # Processar múltiplas intenções
            intencoes = self.identificar_multiplas_intencoes(mensagem)
            resposta = self._processar_multiplas_intencoes(mensagem, intencoes, contexto)
            
        elif intencao == TipoIntencao.GERAL:
            # Responder diretamente
            resposta = self._processar_consulta_geral(mensagem, contexto)
            
        else:
            # Delegar para agente específico
            resposta = self._delegar_para_agente(mensagem, intencao, contexto)
        
        # Adicionar ao histórico
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
        
        # Introdução
        respostas.append("Identifiquei múltiplos aspectos na sua solicitação. Vou abordar cada um:\n")
        
        # Processar cada intenção
        for i, intencao in enumerate(intencoes, 1):
            if intencao == TipoIntencao.GERAL:
                continue
                
            subtitulo = f"\n**{i}. {self._get_titulo_intencao(intencao)}**\n"
            respostas.append(subtitulo)
            
            # Delegar para agente apropriado
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
        # Verificar se temos referência direta ao agente
        if intencao == TipoIntencao.CONSULTA and self.agente_consulta:
            return self.agente_consulta.processar_mensagem(mensagem, contexto)
            
        elif intencao == TipoIntencao.BRAINSTORM and self.agente_brainstorm:
            return self.agente_brainstorm.processar_mensagem(mensagem, contexto)
            
        elif intencao == TipoIntencao.ANALISE and self.agente_analise:
            # Se não temos agente de análise, usar consulta
            agente = self.agente_analise or self.agente_consulta
            if agente:
                return agente.processar_mensagem(mensagem, contexto)
        
        # Fallback: processar localmente
        return self._processar_localmente(mensagem, intencao, contexto)
    
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
        # Preparar prompt com contexto
        prompt = f"""Como Orquestrador do AURALIS, processe esta solicitação de tipo {intencao.value}:

Mensagem do usuário: {mensagem}

Contexto disponível:
{self.formatar_contexto(contexto)}

Forneça uma resposta apropriada, clara e profissional."""
        
        # Obter resposta do LLM
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

Seja claro, conciso e profissional."""
        
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
            TipoIntencao.CONSULTA: "Busca de Informações",
            TipoIntencao.BRAINSTORM: "Geração de Ideias",
            TipoIntencao.ANALISE: "Análise de Dados",
            TipoIntencao.GERAL: "Informações Gerais"
        }
        return titulos.get(intencao, "Processamento")
    
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
        
        # Consultar informações existentes
        if self.agente_consulta:
            resultados["analises"]["informacoes"] = self.agente_consulta.processar_mensagem(
                f"Buscar todas as informações sobre {topico}",
                self.contexto_atual
            )
        
        # Gerar ideias criativas
        if self.agente_brainstorm:
            resultados["analises"]["ideias"] = self.agente_brainstorm.processar_mensagem(
                f"Gerar ideias criativas para {topico}",
                self.contexto_atual
            )
        
        # Análise de dados (se disponível)
        if self.agente_analise:
            resultados["analises"]["analise"] = self.agente_analise.processar_mensagem(
                f"Analisar padrões e tendências relacionados a {topico}",
                self.contexto_atual
            )
        
        # Gerar resumo executivo
        resultados["resumo_executivo"] = self.gerar_resumo_executivo(topico, resultados["analises"])
        
        return resultados
    
    def __repr__(self):
        agentes_conectados = sum(1 for a in [self.agente_consulta, self.agente_brainstorm, self.agente_analise] if a)
        return f"AgenteOrquestrador(agentes_conectados={agentes_conectados})"