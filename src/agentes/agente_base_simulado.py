"""
Versão simulada da classe base para testes sem necessitar da API OpenAI.
Essencial para desenvolvimento offline e testes unitários.
"""

from typing import Dict, List, Any
import random
import time
from .agente_base import AgenteBase, Mensagem


class AgenteBaseSimulado(AgenteBase):
    """
    Versão simulada do AgenteBase que não requer OpenAI API.
    Útil para testes, desenvolvimento offline e economia de custos.
    """
    
    def __init__(self, nome: str, descricao: str):
        """
        Inicializa o agente simulado.
        
        Args:
            nome: Nome identificador do agente
            descricao: Descrição das capacidades do agente
        """
        # Inicializar sem tentar conectar com OpenAI
        super().__init__(nome, descricao)
        self.openai_client = None  # Forçar modo simulado
        
        # Respostas pré-definidas por padrão
        self.respostas_padrao = {
            "buscar": [
                "Encontrei 3 reuniões relevantes sobre o tema solicitado.",
                "Localizei 5 documentos que mencionam esse assunto.",
                "Identifiquei 2 reuniões recentes com discussões relacionadas."
            ],
            "ideia": [
                "Aqui estão algumas ideias criativas para o desafio apresentado:\n1. Implementar uma solução baseada em IA\n2. Criar um processo automatizado\n3. Desenvolver uma ferramenta colaborativa",
                "Sugiro as seguintes abordagens inovadoras:\n1. Gamificação do processo\n2. Integração com ferramentas existentes\n3. Criação de dashboard interativo",
                "Pensando fora da caixa, proponho:\n1. Abordagem híbrida combinando métodos tradicionais e modernos\n2. Solução modular e escalável\n3. Sistema de feedback em tempo real"
            ],
            "analisar": [
                "Analisando os dados disponíveis, identifiquei as seguintes tendências:\n- Aumento de 15% na produtividade\n- Redução de 20% no tempo de resposta\n- Melhoria na satisfação da equipe",
                "A análise revela padrões interessantes:\n- Picos de atividade às terças e quintas\n- Maior engajamento no período da manhã\n- Correlação positiva entre reuniões curtas e decisões rápidas",
                "Os indicadores mostram:\n- Evolução consistente nos últimos 3 meses\n- Áreas de oportunidade em processos específicos\n- Necessidade de alinhamento entre equipes"
            ],
            "resumir": [
                "Resumo executivo: O projeto está progredindo conforme planejado, com pequenos ajustes necessários na timeline.",
                "Em síntese: As principais decisões foram tomadas e as equipes estão alinhadas com os próximos passos.",
                "Sumário: Reunião produtiva com definições claras sobre responsabilidades e prazos."
            ],
            "default": [
                "Entendi sua solicitação. Processando as informações disponíveis...",
                "Analisando o contexto fornecido para gerar a melhor resposta...",
                "Com base nas informações disponíveis, posso ajudar com isso..."
            ]
        }
        
    def chamar_llm(self, mensagem: str, historico: List[Dict] = None) -> str:
        """
        Simula uma chamada para o modelo de linguagem.
        
        Args:
            mensagem: Mensagem para processar
            historico: Histórico de conversas (opcional)
            
        Returns:
            str: Resposta simulada baseada em padrões
        """
        # Simular delay de processamento
        time.sleep(random.uniform(0.1, 0.3))
        
        mensagem_lower = mensagem.lower()
        
        # Detectar padrões e retornar respostas apropriadas
        if any(palavra in mensagem_lower for palavra in ["buscar", "encontrar", "procurar", "localizar"]):
            resposta = random.choice(self.respostas_padrao["buscar"])
            
            # Personalizar com termos da mensagem
            if "reunião" in mensagem_lower:
                resposta += "\n\nReunião mais relevante: 'Kickoff do Projeto' - 15/01/2024"
            elif "documento" in mensagem_lower:
                resposta += "\n\nDocumento principal: 'Plano Estratégico 2024.pdf'"
                
        elif any(palavra in mensagem_lower for palavra in ["ideia", "sugestão", "propor", "criar", "inovar"]):
            resposta = random.choice(self.respostas_padrao["ideia"])
            
            # Adicionar contexto específico
            if "comunicação" in mensagem_lower:
                resposta += "\n\n4. Implementar canal de comunicação unificado\n5. Criar newsletter semanal automatizada"
            elif "produtividade" in mensagem_lower:
                resposta += "\n\n4. Automatizar tarefas repetitivas\n5. Implementar metodologia ágil adaptada"
                
        elif any(palavra in mensagem_lower for palavra in ["analisar", "análise", "tendência", "padrão"]):
            resposta = random.choice(self.respostas_padrao["analisar"])
            
        elif any(palavra in mensagem_lower for palavra in ["resumir", "resumo", "síntese", "sumário"]):
            resposta = random.choice(self.respostas_padrao["resumir"])
            
        else:
            resposta = random.choice(self.respostas_padrao["default"])
            
        # Adicionar informações do contexto se disponível
        if historico and len(historico) > 0:
            resposta += f"\n\n(Baseado em {len(historico)} interações anteriores)"
            
        return resposta
    
    def processar_mensagem(self, mensagem: str, contexto: Dict[str, Any] = None) -> str:
        """
        Processa uma mensagem no modo simulado.
        
        Args:
            mensagem: Mensagem a ser processada
            contexto: Contexto adicional
            
        Returns:
            str: Resposta simulada
        """
        # Atualizar contexto se fornecido
        if contexto:
            self.atualizar_contexto(contexto)
        
        # Gerar resposta simulada
        resposta = self.chamar_llm(mensagem)
        
        # Adicionar ao histórico
        self.adicionar_ao_historico(mensagem, resposta)
        
        return resposta
    
    def get_prompt_sistema(self) -> str:
        """
        Retorna um prompt sistema genérico para o modo simulado.
        
        Returns:
            str: Prompt do sistema
        """
        return f"""Você é {self.nome}, um agente simulado do sistema AURALIS.
        
Descrição: {self.descricao}

Este é um modo de teste/desenvolvimento. Suas respostas são pré-definidas e servem para:
1. Testar a integração do sistema
2. Desenvolver sem custos de API
3. Validar fluxos de trabalho

Responda de forma coerente com o contexto fornecido."""
    
    def simular_busca_reunioes(self, termos: List[str]) -> List[Dict[str, Any]]:
        """
        Simula uma busca em reuniões.
        
        Args:
            termos: Termos de busca
            
        Returns:
            List[Dict]: Reuniões simuladas encontradas
        """
        reunioes_simuladas = [
            {
                "id": "1",
                "titulo": "Kickoff do Projeto AURALIS",
                "data": "2024-01-15",
                "participantes": ["João Silva", "Maria Santos", "Pedro Oliveira"],
                "resumo": "Definição inicial do escopo e objetivos do projeto",
                "relevancia": random.randint(70, 100)
            },
            {
                "id": "2",
                "titulo": "Revisão de Sprint - Semana 3",
                "data": "2024-01-22",
                "participantes": ["Maria Santos", "Ana Costa"],
                "resumo": "Avaliação do progresso e ajustes no cronograma",
                "relevancia": random.randint(50, 90)
            },
            {
                "id": "3",
                "titulo": "Brainstorming - Novas Funcionalidades",
                "data": "2024-01-25",
                "participantes": ["Pedro Oliveira", "Lucas Mendes", "João Silva"],
                "resumo": "Ideação sobre features para a versão 2.0",
                "relevancia": random.randint(60, 95)
            }
        ]
        
        # Filtrar por relevância
        reunioes_relevantes = []
        for reuniao in reunioes_simuladas:
            # Simular relevância baseada nos termos
            for termo in termos:
                if termo.lower() in reuniao["titulo"].lower() or termo.lower() in reuniao["resumo"].lower():
                    reunioes_relevantes.append(reuniao)
                    break
        
        # Se não encontrou nada específico, retornar algumas aleatórias
        if not reunioes_relevantes:
            reunioes_relevantes = random.sample(reunioes_simuladas, min(2, len(reunioes_simuladas)))
        
        # Ordenar por relevância
        reunioes_relevantes.sort(key=lambda x: x["relevancia"], reverse=True)
        
        return reunioes_relevantes
    
    def simular_geracao_ideias(self, tema: str, num_ideias: int = 5) -> List[Dict[str, Any]]:
        """
        Simula a geração de ideias criativas.
        
        Args:
            tema: Tema para gerar ideias
            num_ideias: Número de ideias a gerar
            
        Returns:
            List[Dict]: Ideias geradas
        """
        tecnicas = ["SCAMPER", "Brainstorming Reverso", "What If", "6 Chapéus"]
        niveis_inovacao = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]
        
        ideias = []
        for i in range(num_ideias):
            ideias.append({
                "id": i + 1,
                "titulo": f"Ideia {i + 1}: Abordagem {'Conservadora' if i < 2 else 'Inovadora' if i < 4 else 'Radical'}",
                "descricao": f"Uma solução {'incremental' if i < 2 else 'transformadora' if i < 4 else 'disruptiva'} para {tema}",
                "tecnica_usada": random.choice(tecnicas),
                "nivel_inovacao": niveis_inovacao[min(i, 4)],
                "implementacao": f"Passo {i + 1} para implementar esta ideia...",
                "beneficios": [f"Benefício {j + 1}" for j in range(random.randint(2, 4))],
                "desafios": [f"Desafio {j + 1}" for j in range(random.randint(1, 3))]
            })
        
        return ideias
    
    def simular_analise(self, dados: str) -> Dict[str, Any]:
        """
        Simula uma análise de dados.
        
        Args:
            dados: Dados para analisar
            
        Returns:
            Dict: Resultado da análise
        """
        return {
            "resumo_executivo": "Análise concluída com insights relevantes identificados",
            "metricas": {
                "total_pontos_analisados": random.randint(50, 200),
                "tendencia_geral": random.choice(["Crescente", "Estável", "Decrescente"]),
                "confianca": f"{random.randint(75, 95)}%"
            },
            "insights": [
                "Padrão identificado nos dados do primeiro trimestre",
                "Correlação entre variáveis X e Y detectada",
                "Oportunidade de otimização no processo Z"
            ],
            "recomendacoes": [
                "Implementar monitoramento contínuo",
                "Ajustar estratégia baseada nos insights",
                "Revisar métricas mensalmente"
            ],
            "proximos_passos": [
                "Validar insights com stakeholders",
                "Criar plano de ação detalhado",
                "Definir KPIs para acompanhamento"
            ]
        }
    
    def __repr__(self):
        return f"AgenteBaseSimulado(nome='{self.nome}', modo='SIMULADO')"