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


class TecnicaBrainstorm(Enum):
    """Técnicas de brainstorming disponíveis"""
    SCAMPER = "SCAMPER"
    SEIS_CHAPEUS = "6 Chapéus do Pensamento"
    BRAINSTORM_REVERSO = "Brainstorming Reverso"
    WHAT_IF = "What If"
    MAPA_MENTAL = "Mapa Mental"
    ANALOGIAS = "Analogias"
    COMBINACAO_ALEATORIA = "Combinação Aleatória"


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
        
        # Configurações específicas
        self.temperatura = 0.9  # Alta criatividade
        self.max_tokens = 1500  # Respostas mais longas para ideias detalhadas
        
        # Descrições das técnicas
        self.descricoes_tecnicas = {
            TecnicaBrainstorm.SCAMPER: {
                "nome": "SCAMPER",
                "descricao": "Técnica sistemática para modificar ideias existentes",
                "componentes": {
                    "S": "Substitute (Substituir) - O que pode ser substituído?",
                    "C": "Combine (Combinar) - O que pode ser combinado?",
                    "A": "Adapt (Adaptar) - O que pode ser adaptado?",
                    "M": "Modify/Magnify (Modificar/Ampliar) - O que pode ser modificado ou ampliado?",
                    "P": "Put to other uses (Outros usos) - Que outros usos são possíveis?",
                    "E": "Eliminate (Eliminar) - O que pode ser eliminado?",
                    "R": "Reverse/Rearrange (Reverter/Reorganizar) - O que pode ser invertido ou reorganizado?"
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
                "nome": "What If (E se...)",
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
        
        # Templates de ideias por nível de inovação
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
            str: Prompt do sistema
        """
        return """Você é o Agente Criativo do sistema AURALIS, especializado em gerar ideias inovadoras e soluções criativas.

Seu papel é:
1. Gerar múltiplas ideias criativas para problemas apresentados
2. Fazer conexões não óbvias entre conceitos
3. Propor soluções inovadoras baseadas em informações de reuniões passadas
4. Usar diferentes técnicas de brainstorming (SCAMPER, 6 Chapéus, etc.)
5. Expandir e desenvolver conceitos

Diretrizes:
- Seja ousado e pense fora da caixa
- Apresente ideias variadas (conservadoras a radicais)
- Estruture as ideias de forma clara
- Conecte ideias com experiências passadas quando relevante
- Use analogias e metáforas para explicar conceitos
- Sempre apresente pelo menos 3-5 ideias diferentes
- Avalie o nível de inovação de cada ideia (1-5 estrelas)

Formato preferido:
### Ideia N: [Título Criativo]
**Nível de Inovação:** [estrelas]
**Descrição:** [Explicação concisa]
**Como implementar:**
1. Passo 1
2. Passo 2
3. Passo 3
**Benefícios esperados:**
- Benefício 1
- Benefício 2
**Possíveis desafios:**
- Desafio 1
- Desafio 2

Sempre responda em português brasileiro e seja entusiasmado mas profissional."""
    
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
        
        # Identificar tipo de solicitação
        tecnica = self.escolher_tecnica(mensagem)
        
        print(f"[BRAINSTORM] Técnica escolhida: {tecnica.value}")
        
        # Gerar ideias usando a técnica apropriada
        ideias = self.gerar_ideias(mensagem, tecnica, contexto)
        
        # Formatar resposta
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
        
        # Análise por palavras-chave
        if any(palavra in mensagem_lower for palavra in ["melhorar", "otimizar", "aprimorar", "modificar"]):
            return TecnicaBrainstorm.SCAMPER
        
        elif any(palavra in mensagem_lower for palavra in ["analisar", "perspectiva", "visão", "ângulo"]):
            return TecnicaBrainstorm.SEIS_CHAPEUS
        
        elif any(palavra in mensagem_lower for palavra in ["problema", "evitar", "prevenir", "resolver"]):
            return TecnicaBrainstorm.BRAINSTORM_REVERSO
        
        elif any(palavra in mensagem_lower for palavra in ["cenário", "futuro", "possibilidade"]):
            return TecnicaBrainstorm.WHAT_IF
        
        elif any(palavra in mensagem_lower for palavra in ["similar", "parecido", "inspirar"]):
            return TecnicaBrainstorm.ANALOGIAS
        
        # Default: SCAMPER é versátil
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
        # Preparar prompt específico para a técnica
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
        
        # Se estiver em modo simulado, gerar ideias mock
        if not self.openai_client:
            return self._gerar_ideias_simuladas(desafio, tecnica)
        
        # Chamar LLM para gerar ideias
        resposta_llm = self.chamar_llm(prompt)
        
        # Parsear resposta em estrutura de ideias
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
        
        # Templates base por nível de inovação
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
        
        for i, template in enumerate(templates):
            nivel = i + 1
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
                ][:nivel],  # Mais benefícios para ideias mais inovadoras
                "desafios": [
                    "Resistência inicial à mudança",
                    "Investimento necessário",
                    "Curva de aprendizado",
                    "Riscos técnicos"
                ][:max(1, nivel - 2)]  # Mais desafios para ideias mais radicais
            })
        
        # Aplicar componentes específicos da técnica
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
        # Em produção, implementar parser mais sofisticado
        # Por ora, retorna ideias simuladas como fallback
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
        
        # Cabeçalho
        partes.append(f"💡 **Sessão de Brainstorming - {tecnica.value}**\n")
        partes.append(f"**Desafio:** {desafio}\n")
        
        # Introdução sobre a técnica
        info_tecnica = self.descricoes_tecnicas.get(tecnica, {})
        if info_tecnica:
            partes.append(f"**Sobre a técnica:** {info_tecnica.get('descricao', '')}\n")
        
        # Ideias geradas
        partes.append("## 🚀 Ideias Geradas:\n")
        
        for ideia in ideias:
            partes.append(f"### Ideia {ideia['id']}: {ideia['titulo']}")
            partes.append(f"**Nível de Inovação:** {ideia['nivel_texto']}")
            
            # Componente específico da técnica (se aplicável)
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
        
        # Resumo e próximos passos
        partes.append("## 📊 Resumo da Sessão:\n")
        partes.append(f"• **Total de ideias geradas:** {len(ideias)}")
        partes.append(f"• **Técnica utilizada:** {tecnica.value}")
        partes.append(f"• **Variação de inovação:** {self.niveis_inovacao[1]['simbolo']} a {self.niveis_inovacao[5]['simbolo']}")
        
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
        componentes = self.descricoes_tecnicas[TecnicaBrainstorm.SCAMPER]["componentes"]
        ideias_scamper = {}
        
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
        dominios = ["natureza", "esportes", "música", "culinária", "arquitetura", 
                   "medicina", "militar", "jogos", "arte", "tecnologia"]
        
        analogias = []
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
        # Análise simplificada baseada em palavras-chave
        palavras_conservadoras = ["melhorar", "otimizar", "ajustar", "refinar"]
        palavras_inovadoras = ["transformar", "revolucionar", "disruptivo", "inédito"]
        
        ideia_lower = ideia.lower()
        
        score_conservador = sum(1 for p in palavras_conservadoras if p in ideia_lower)
        score_inovador = sum(1 for p in palavras_inovadoras if p in ideia_lower)
        
        # Determinar nível
        if score_inovador > score_conservador:
            nivel = min(5, 3 + score_inovador)
        else:
            nivel = max(1, 3 - score_conservador)
        
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