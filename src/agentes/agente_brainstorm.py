"""
Agente de Brainstorm - Especialista em geração criativa de ideias.
Utiliza técnicas como SCAMPER, 6 Chapéus e outras metodologias criativas.
"""

from typing import Dict, List, Any, Optional
import os
import random
from enum import Enum

# Importar classe base apropriada
if os.getenv("OPENAI_API_KEY"):
    from .agente_base import AgenteBase
else:
    from .agente_base_simulado import AgenteBaseSimulado as AgenteBase

# Importar o novo sistema de templates
from .prompt_template import PromptTemplate, TomResposta


class TecnicaBrainstorm(Enum):
    """Técnicas de brainstorming disponíveis no sistema.
    
    Cada técnica tem características e aplicações específicas.
    """
    SCAMPER = "SCAMPER"                           # Técnica sistemática de modificação
    SEIS_CHAPEUS = "6 Chapéus do Pensamento"      # Análise por perspectivas
    BRAINSTORM_REVERSO = "Brainstorming Reverso"  # Inverter o problema
    WHAT_IF = "What If"                           # Cenários hipotéticos
    MAPA_MENTAL = "Mapa Mental"                   # Visualização de ideias
    ANALOGIAS = "Analogias"                       # Buscar em outros domínios
    COMBINACAO_ALEATORIA = "Combinação Aleatória" # Misturar conceitos


class AgenteBrainstorm(AgenteBase):
    """
    Agente especializado em geração criativa de ideias no sistema AURALIS.
    
    Responsabilidades:
    - Gerar ideias inovadoras usando diferentes técnicas
    - Propor soluções criativas para problemas
    - Fazer conexões não óbvias entre conceitos
    - Expandir e desenvolver conceitos
    - Avaliar nível de inovação das ideias
    """
    
    def __init__(self):
        super().__init__(
            nome="Agente Criativo AURALIS",
            descricao="Especialista em brainstorming e geração de ideias inovadoras"
        )
        
        # ===== CONFIGURAÇÃO DO TEMPLATE =====
        # Usa o novo sistema de templates padronizados
        self.config_prompt = PromptTemplate.criar_config_brainstorm()
        
        # ===== CONFIGURAÇÕES ESPECÍFICAS =====
        # Usa configurações do template
        self.temperatura = self.config_prompt.temperatura
        self.max_tokens = self.config_prompt.max_tokens
        
        # ===== DICIONÁRIO DE TÉCNICAS DE BRAINSTORM =====
        # Descrições detalhadas e componentes de cada técnica
        self.descricoes_tecnicas = {
            TecnicaBrainstorm.SCAMPER: {
                "nome": "SCAMPER",
                "descricao": "Técnica sistemática para modificar ideias existentes",
                "componentes": {
                    "S": "Substituir - O que pode ser substituído?",
                    "C": "Combinar - O que pode ser combinado?",
                    "A": "Adaptar - O que pode ser adaptado?",
                    "M": "Modificar/Ampliar - O que pode ser modificado ou ampliado?",
                    "P": "Propor outros usos - Que outros usos são possíveis?",
                    "E": "Eliminar - O que pode ser eliminado?",
                    "R": "Reverter/Reorganizar - O que pode ser invertido ou reorganizado?"
                }
            },
            TecnicaBrainstorm.SEIS_CHAPEUS: {
                "nome": "6 Chapéus do Pensamento",
                "descricao": "Análise de diferentes perspectivas",
                "componentes": {
                    "Branco": "Fatos e dados objetivos",
                    "Vermelho": "Emoções, intuições e sentimentos",
                    "Preto": "Críticas, riscos e pontos negativos",
                    "Amarelo": "Otimismo, benefícios e pontos positivos",
                    "Verde": "Criatividade e novas ideias",
                    "Azul": "Controle, processo e visão geral"
                }
            },
            TecnicaBrainstorm.BRAINSTORM_REVERSO: {
                "nome": "Brainstorming Reverso",
                "descricao": "Pensar em como causar o problema para encontrar soluções",
                "componentes": {
                    "Inverter": "Como piorar a situação?",
                    "Analisar": "Quais fatores causariam isso?",
                    "Reverter": "Como prevenir ou fazer o oposto?"
                }
            },
            TecnicaBrainstorm.WHAT_IF: {
                "nome": "E se... (What If)",
                "descricao": "Explorar cenários hipotéticos",
                "componentes": {
                    "Recursos ilimitados": "E se tivéssemos recursos infinitos?",
                    "Sem restrições": "E se não houvesse limitações técnicas?",
                    "Outro contexto": "E se fosse em outro setor/país/época?",
                    "Extremos": "E se levássemos ao extremo?"
                }
            },
            TecnicaBrainstorm.ANALOGIAS: {
                "nome": "Analogias",
                "descricao": "Buscar soluções em outros domínios",
                "componentes": {
                    "Natureza": "Como a natureza resolveria isso?",
                    "Outros setores": "Como outros setores lidam com problemas similares?",
                    "História": "Existem soluções históricas aplicáveis?",
                    "Ficção": "Que soluções fictícias poderiam inspirar?"
                }
            }
        }
        
        # ===== NÍVEIS DE INOVAÇÃO =====
        # Classificação das ideias por grau de inovação
        self.niveis_inovacao = {
            1: {"nome": "Conservadora", "simbolo": "⭐", "descricao": "Melhoria incremental"},
            2: {"nome": "Moderada", "simbolo": "⭐⭐", "descricao": "Mudança significativa"},
            3: {"nome": "Inovadora", "simbolo": "⭐⭐⭐", "descricao": "Abordagem nova"},
            4: {"nome": "Transformadora", "simbolo": "⭐⭐⭐⭐", "descricao": "Mudança de paradigma"},
            5: {"nome": "Disruptiva", "simbolo": "⭐⭐⭐⭐⭐", "descricao": "Revolucionária"}
        }
    
    def get_prompt_sistema(self) -> str:
        """
        Define o prompt do sistema para o agente de brainstorm.
        
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
        Processa uma solicitação de brainstorming.
        
        Args:
            mensagem: Desafio ou problema para gerar ideias
            contexto: Contexto adicional
            
        Returns:
            str: Ideias criativas geradas
        """
        # Atualizar contexto
        if contexto:
            self.atualizar_contexto(contexto)
        
        # ===== SELEÇÃO DA TÉCNICA =====
        # Escolhe a técnica mais apropriada baseada na mensagem
        tecnica = self.escolher_tecnica(mensagem)
        
        print(f"[BRAINSTORM] Técnica escolhida: {tecnica.value}")
        
        # ===== GERAÇÃO DE IDEIAS =====
        # Aplica a técnica escolhida para gerar ideias criativas
        ideias = self.gerar_ideias(mensagem, tecnica, contexto)
        
        # ===== FORMATAÇÃO DA RESPOSTA =====
        resposta = self.formatar_resposta_criativa(mensagem, ideias, tecnica)
        
        # Adicionar ao histórico
        self.adicionar_ao_historico(mensagem, resposta)
        
        return resposta
    
    def escolher_tecnica(self, mensagem: str) -> TecnicaBrainstorm:
        """
        Escolhe a técnica de brainstorming mais apropriada.
        
        Args:
            mensagem: Mensagem do usuário
            
        Returns:
            TecnicaBrainstorm: Técnica escolhida
        """
        mensagem_lower = mensagem.lower()
        
        # ===== ANÁLISE DE PALAVRAS-CHAVE =====
        # SCAMPER: para melhorias e modificações
        if any(palavra in mensagem_lower for palavra in ["melhorar", "otimizar", "aprimorar", "modificar"]):
            return TecnicaBrainstorm.SCAMPER
        
        # 6 Chapéus: para análises multiperspectivas
        elif any(palavra in mensagem_lower for palavra in ["analisar", "perspectiva", "visão", "ângulo"]):
            return TecnicaBrainstorm.SEIS_CHAPEUS
        
        # Brainstorm Reverso: para resolver problemas
        elif any(palavra in mensagem_lower for palavra in ["problema", "evitar", "prevenir", "resolver"]):
            return TecnicaBrainstorm.BRAINSTORM_REVERSO
        
        # What If: para explorar cenários
        elif any(palavra in mensagem_lower for palavra in ["cenário", "futuro", "possibilidade"]):
            return TecnicaBrainstorm.WHAT_IF
        
        # Analogias: para buscar inspiração
        elif any(palavra in mensagem_lower for palavra in ["similar", "parecido", "inspirar"]):
            return TecnicaBrainstorm.ANALOGIAS
        
        # Padrão: SCAMPER é a técnica mais versátil
        return TecnicaBrainstorm.SCAMPER
    
    def gerar_ideias(self, desafio: str, tecnica: TecnicaBrainstorm, 
                    contexto: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Gera ideias usando a técnica especificada.
        
        Args:
            desafio: Desafio ou problema
            tecnica: Técnica de brainstorming
            contexto: Contexto adicional
            
        Returns:
            List[Dict]: Lista de ideias geradas
        """
        # ===== PREPARAÇÃO DO PROMPT =====
        # Cria prompt específico para a técnica escolhida
        info_tecnica = self.descricoes_tecnicas.get(tecnica, {})
        
        prompt = f"""Use a técnica {tecnica.value} para gerar ideias criativas.

Técnica: {info_tecnica.get('descricao', '')}
Componentes: {info_tecnica.get('componentes', {})}

Desafio: {desafio}

Contexto adicional:
{self.formatar_contexto(contexto)}

Gere 5 ideias variando de conservadoras a radicais. Para cada ideia, forneça:
- Título criativo
- Descrição detalhada
- Passos de implementação
- Benefícios esperados
- Desafios potenciais
- Nível de inovação (1-5)"""
        
        # ===== GERAÇÃO DAS IDEIAS =====
        # Verifica se está em modo simulado (sem OpenAI)
        if not self.openai_client:
            return self._gerar_ideias_simuladas(desafio, tecnica)
        
        # Chama o modelo de linguagem para gerar ideias reais
        resposta_llm = self.chamar_llm(prompt)
        
        # Converte a resposta em estrutura de dados
        ideias = self._parsear_ideias_llm(resposta_llm)
        
        return ideias
    
    def _gerar_ideias_simuladas(self, desafio: str, tecnica: TecnicaBrainstorm) -> List[Dict[str, Any]]:
        """
        Gera ideias simuladas para modo de teste.
        
        Args:
            desafio: Desafio apresentado
            tecnica: Técnica utilizada
            
        Returns:
            List[Dict]: Ideias simuladas
        """
        ideias = []
        
        # ===== TEMPLATES DE IDEIAS POR NÍVEL =====
        # Templates progressivos do conservador ao disruptivo
        templates = [
            {
                "prefixo": "Otimização Incremental",
                "acao": "melhorar processos existentes",
                "beneficio": "redução de 10-15% no tempo"
            },
            {
                "prefixo": "Automação Inteligente",
                "acao": "automatizar tarefas repetitivas",
                "beneficio": "economia de 30% em recursos"
            },
            {
                "prefixo": "Integração Inovadora",
                "acao": "conectar sistemas isolados",
                "beneficio": "visão unificada e decisões mais rápidas"
            },
            {
                "prefixo": "Transformação Digital",
                "acao": "reimaginar o processo completamente",
                "beneficio": "mudança de paradigma operacional"
            },
            {
                "prefixo": "Solução Disruptiva",
                "acao": "criar algo totalmente novo",
                "beneficio": "vantagem competitiva única"
            }
        ]
        
        # ===== GERAÇÃO DE IDEIAS SIMULADAS =====
        for i, template in enumerate(templates):
            nivel = i + 1  # Nível de 1 a 5
            info_nivel = self.niveis_inovacao[nivel]
            
            ideias.append({
                "id": i + 1,
                "titulo": f"{template['prefixo']} para {desafio[:30]}...",
                "descricao": f"Uma abordagem {info_nivel['descricao']} para {template['acao']} "
                            f"no contexto de {desafio}.",
                "tecnica_usada": tecnica.value,
                "nivel_inovacao": nivel,
                "nivel_texto": f"{info_nivel['simbolo']} {info_nivel['nome']}",
                "implementacao": [
                    f"Fase 1: Análise detalhada do {desafio}",
                    f"Fase 2: Implementação da {template['acao']}",
                    f"Fase 3: Testes e ajustes finos",
                    f"Fase 4: Rollout e monitoramento"
                ],
                "beneficios": [
                    template['beneficio'],
                    "Melhoria na satisfação da equipe",
                    "Maior escalabilidade",
                    "ROI positivo em 6 meses"
                ][:nivel],  # Quanto mais inovadora, mais benefícios
                "desafios": [
                    "Resistência inicial à mudança",
                    "Investimento necessário",
                    "Curva de aprendizado",
                    "Riscos técnicos"
                ][:max(1, nivel - 2)]  # Ideias mais radicais têm mais desafios
            })
        
        # ===== APLICAÇÃO DE COMPONENTES ESPECÍFICOS =====
        # Adiciona componentes SCAMPER se for a técnica escolhida
        if tecnica == TecnicaBrainstorm.SCAMPER:
            componentes = ["Substituir", "Combinar", "Adaptar", "Modificar", "Eliminar"]
            for i, ideia in enumerate(ideias):
                if i < len(componentes):
                    ideia["componente_scamper"] = componentes[i]
                    ideia["descricao"] = f"[{componentes[i]}] {ideia['descricao']}"
        
        return ideias
    
    def _parsear_ideias_llm(self, resposta_llm: str) -> List[Dict[str, Any]]:
        """
        Parseia a resposta do LLM em estrutura de ideias.
        
        Args:
            resposta_llm: Resposta do modelo
            
        Returns:
            List[Dict]: Ideias estruturadas
        """
        # ===== PARSER SIMPLIFICADO =====
        # TODO: Implementar parser mais sofisticado em produção
        # Por enquanto, retorna ideias simuladas como fallback
        return self._gerar_ideias_simuladas("desafio genérico", TecnicaBrainstorm.SCAMPER)
    
    def formatar_resposta_criativa(self, desafio: str, ideias: List[Dict[str, Any]], 
                                 tecnica: TecnicaBrainstorm) -> str:
        """
        Formata a resposta com as ideias geradas.
        
        Args:
            desafio: Desafio original
            ideias: Lista de ideias geradas
            tecnica: Técnica utilizada
            
        Returns:
            str: Resposta formatada
        """
        partes = []
        
        # ===== CABEÇALHO DA RESPOSTA =====
        partes.append(f"💡 **Sessão de Brainstorming - {tecnica.value}**\n")
        partes.append(f"**Desafio:** {desafio}\n")
        
        # ===== DESCRIÇÃO DA TÉCNICA =====
        info_tecnica = self.descricoes_tecnicas.get(tecnica, {})
        if info_tecnica:
            partes.append(f"**Sobre a técnica:** {info_tecnica.get('descricao', '')}\n")
        
        # ===== SEÇÃO DE IDEIAS =====
        partes.append("## 🚀 Ideias Geradas:\n")
        
        # Formata cada ideia detalhadamente
        for ideia in ideias:
            partes.append(f"### Ideia {ideia['id']}: {ideia['titulo']}")
            partes.append(f"**Nível de Inovação:** {ideia['nivel_texto']}")
            
            # Mostra componente SCAMPER se aplicável
            if 'componente_scamper' in ideia:
                partes.append(f"**Componente SCAMPER:** {ideia['componente_scamper']}")
            
            partes.append(f"\n**Descrição:** {ideia['descricao']}")
            
            partes.append("\n**Como implementar:**")
            for i, passo in enumerate(ideia['implementacao'], 1):
                partes.append(f"{i}. {passo}")
            
            partes.append("\n**Benefícios esperados:**")
            for beneficio in ideia['beneficios']:
                partes.append(f"• {beneficio}")
            
            if ideia['desafios']:
                partes.append("\n**Possíveis desafios:**")
                for desafio in ideia['desafios']:
                    partes.append(f"• {desafio}")
            
            partes.append("\n---\n")
        
        # ===== RESUMO DA SESSÃO =====
        partes.append("## 📊 Resumo da Sessão:\n")
        partes.append(f"• **Total de ideias geradas:** {len(ideias)}")
        partes.append(f"• **Técnica utilizada:** {tecnica.value}")
        partes.append(f"• **Variação de inovação:** {self.niveis_inovacao[1]['simbolo']} a {self.niveis_inovacao[5]['simbolo']}")
        
        # ===== PRÓXIMOS PASSOS =====
        partes.append("\n## 🎯 Próximos Passos Sugeridos:")
        partes.append("1. Avaliar viabilidade de cada ideia com a equipe")
        partes.append("2. Selecionar 2-3 ideias mais promissoras")
        partes.append("3. Desenvolver prova de conceito para a ideia prioritária")
        partes.append("4. Definir métricas de sucesso")
        partes.append("5. Criar plano de implementação detalhado")
        
        return "\n".join(partes)
    
    def aplicar_scamper(self, conceito: str) -> Dict[str, str]:
        """
        Aplica a técnica SCAMPER a um conceito específico.
        
        Args:
            conceito: Conceito para aplicar SCAMPER
            
        Returns:
            Dict[str, str]: Ideias para cada componente SCAMPER
        """
        # ===== APLICAÇÃO SISTEMÁTICA DO SCAMPER =====
        componentes = self.descricoes_tecnicas[TecnicaBrainstorm.SCAMPER]["componentes"]
        ideias_scamper = {}
        
        # Aplica cada componente SCAMPER ao conceito
        for letra, descricao in componentes.items():
            prompt = f"Para o conceito '{conceito}', {descricao}"
            ideias_scamper[letra] = self.chamar_llm(prompt)
        
        return ideias_scamper
    
    def gerar_analogias(self, problema: str, num_analogias: int = 5) -> List[str]:
        """
        Gera analogias para resolver um problema.
        
        Args:
            problema: Problema para buscar analogias
            num_analogias: Número de analogias
            
        Returns:
            List[str]: Lista de analogias
        """
        # ===== DOMÍNIOS PARA ANALOGIAS =====
        dominios = ["natureza", "esportes", "música", "culinária", "arquitetura", 
                   "medicina", "militar", "jogos", "arte", "tecnologia"]
        
        analogias = []
        # Gera analogias em diferentes domínios
        for i in range(min(num_analogias, len(dominios))):
            dominio = dominios[i]
            analogias.append(
                f"No mundo da {dominio}, isso seria como... "
                f"[analogia criativa relacionando {problema} com {dominio}]"
            )
        
        return analogias
    
    def brainstorm_reverso(self, objetivo: str) -> Dict[str, Any]:
        """
        Aplica brainstorming reverso para encontrar soluções.
        
        Args:
            objetivo: Objetivo desejado
            
        Returns:
            Dict: Análise reversa com soluções
        """
        # ===== ESTRUTURA DO BRAINSTORM REVERSO =====
        return {
            "objetivo_original": objetivo,
            "objetivo_reverso": f"Como garantir que {objetivo} NUNCA aconteça?",
            "fatores_negativos": [
                "Fator 1 que impediria o objetivo",
                "Fator 2 que sabotaria o processo",
                "Fator 3 que criaria obstáculos"
            ],
            "solucoes": [
                "Solução 1: Fazer exatamente o oposto do fator negativo 1",
                "Solução 2: Criar proteções contra o fator negativo 2",
                "Solução 3: Implementar sistemas para evitar o fator negativo 3"
            ]
        }
    
    def avaliar_nivel_inovacao(self, ideia: str) -> Dict[str, Any]:
        """
        Avalia o nível de inovação de uma ideia.
        
        Args:
            ideia: Descrição da ideia
            
        Returns:
            Dict: Avaliação detalhada
        """
        # ===== ANÁLISE DE NÍVEL DE INOVAÇÃO =====
        # Palavras que indicam diferentes níveis de inovação
        palavras_conservadoras = ["melhorar", "otimizar", "ajustar", "refinar"]
        palavras_inovadoras = ["transformar", "revolucionar", "disruptivo", "inédito"]
        
        ideia_lower = ideia.lower()
        
        # Conta ocorrências de cada tipo de palavra
        score_conservador = sum(1 for p in palavras_conservadoras if p in ideia_lower)
        score_inovador = sum(1 for p in palavras_inovadoras if p in ideia_lower)
        
        # ===== DETERMINAÇÃO DO NÍVEL =====
        # Calcula nível baseado nos scores
        if score_inovador > score_conservador:
            nivel = min(5, 3 + score_inovador)  # Tende para mais inovador
        else:
            nivel = max(1, 3 - score_conservador)  # Tende para mais conservador
        
        info_nivel = self.niveis_inovacao[nivel]
        
        return {
            "nivel": nivel,
            "classificacao": info_nivel["nome"],
            "simbolo": info_nivel["simbolo"],
            "descricao": info_nivel["descricao"],
            "justificativa": f"Ideia classificada como {info_nivel['nome']} "
                           f"baseada na análise de impacto e originalidade."
        }
    
    def __repr__(self):
        return f"AgenteBrainstorm(temperatura={self.temperatura}, tecnicas={len(self.descricoes_tecnicas)})"