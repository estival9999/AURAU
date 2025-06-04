"""
Mock da OpenAI para testes e desenvolvimento sem API key.
Simula comportamento básico da API OpenAI.
"""

from typing import Dict, List, Any, Optional
import time
import random
from dataclasses import dataclass, field


@dataclass
class MockMessage:
    """Representa uma mensagem no formato OpenAI"""
    role: str
    content: str


@dataclass
class MockChoice:
    """Representa uma escolha de resposta"""
    index: int
    message: MockMessage
    finish_reason: str = "stop"


@dataclass
class MockCompletion:
    """Representa uma resposta completa da API"""
    id: str = field(default_factory=lambda: f"mock-{random.randint(1000, 9999)}")
    object: str = "chat.completion"
    created: int = field(default_factory=lambda: int(time.time()))
    model: str = "gpt-3.5-turbo"
    choices: List[MockChoice] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=lambda: {
        "prompt_tokens": random.randint(50, 200),
        "completion_tokens": random.randint(100, 500),
        "total_tokens": random.randint(150, 700)
    })


class MockOpenAI:
    """
    Mock da classe OpenAI para testes.
    Simula respostas baseadas em padrões na entrada.
    """
    
    def __init__(self, api_key: str = "mock-key"):
        """
        Inicializa o mock OpenAI.
        
        Args:
            api_key: Chave da API (ignorada no mock)
        """
        self.api_key = api_key
        self.chat = MockChatCompletions()
        
        print("[MOCK OPENAI] Cliente mock inicializado")


class MockChatCompletions:
    """Mock do endpoint chat.completions"""
    
    def __init__(self):
        """Inicializa o mock de chat completions"""
        self.respostas_padrao = {
            "consulta": [
                "Com base nas informações disponíveis, encontrei os seguintes resultados relevantes para sua busca.",
                "Analisando os dados do sistema, identifiquei as seguintes informações pertinentes.",
                "Após consultar a base de conhecimento, posso apresentar os seguintes achados."
            ],
            "brainstorm": [
                "Aqui estão algumas ideias criativas para abordar este desafio:\n\n1. Implementação de solução inovadora\n2. Abordagem disruptiva do problema\n3. Metodologia ágil adaptada",
                "Pensando de forma criativa, sugiro as seguintes abordagens:\n\n• Solução A: Foco em automação\n• Solução B: Integração de sistemas\n• Solução C: Gamificação do processo",
                "Aplicando técnicas de brainstorming, desenvolvi estas propostas:\n\n- Ideia revolucionária 1\n- Conceito transformador 2\n- Abordagem híbrida 3"
            ],
            "analise": [
                "Analisando os dados fornecidos, observo as seguintes tendências e padrões importantes.",
                "A análise detalhada revela insights significativos sobre o contexto apresentado.",
                "Com base na avaliação sistemática, posso destacar os seguintes pontos críticos."
            ],
            "default": [
                "Entendi sua solicitação e vou processar as informações adequadamente.",
                "Com base no contexto fornecido, posso auxiliar com esta questão.",
                "Analisando sua pergunta, vou fornecer a melhor resposta possível."
            ]
        }
    
    def create(self, model: str, messages: List[Dict[str, str]], 
               temperature: float = 0.7, max_tokens: int = 1000, **kwargs) -> MockCompletion:
        """
        Simula criação de uma completion.
        
        Args:
            model: Modelo a usar
            messages: Lista de mensagens
            temperature: Temperatura (criatividade)
            max_tokens: Máximo de tokens
            **kwargs: Outros parâmetros (ignorados)
            
        Returns:
            MockCompletion: Resposta simulada
        """
        # Simular delay de API
        time.sleep(random.uniform(0.1, 0.3))
        
        # Extrair última mensagem do usuário
        user_message = ""
        system_prompt = ""
        
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg["content"]
            elif msg["role"] == "system":
                system_prompt = msg["content"]
        
        # Gerar resposta baseada no conteúdo
        resposta = self._gerar_resposta(user_message, system_prompt, temperature)
        
        # Criar completion
        completion = MockCompletion(
            model=model,
            choices=[
                MockChoice(
                    index=0,
                    message=MockMessage(
                        role="assistant",
                        content=resposta
                    )
                )
            ]
        )
        
        return completion
    
    def _gerar_resposta(self, mensagem: str, system_prompt: str, temperature: float) -> str:
        """
        Gera uma resposta baseada na mensagem e prompt.
        
        Args:
            mensagem: Mensagem do usuário
            system_prompt: Prompt do sistema
            temperature: Nível de criatividade
            
        Returns:
            str: Resposta gerada
        """
        mensagem_lower = mensagem.lower()
        
        # Detectar tipo de solicitação pelo conteúdo
        if any(palavra in mensagem_lower for palavra in ["buscar", "encontrar", "procurar", "consultar"]):
            respostas = self.respostas_padrao["consulta"]
        elif any(palavra in mensagem_lower for palavra in ["ideia", "criar", "inovar", "brainstorm"]):
            respostas = self.respostas_padrao["brainstorm"]
        elif any(palavra in mensagem_lower for palavra in ["analisar", "análise", "avaliar", "tendência"]):
            respostas = self.respostas_padrao["analise"]
        else:
            respostas = self.respostas_padrao["default"]
        
        # Selecionar resposta (mais aleatória com temperatura alta)
        if temperature > 0.7:
            resposta_base = random.choice(respostas)
        else:
            resposta_base = respostas[0]
        
        # Personalizar resposta baseada no system prompt
        if "Orquestrador" in system_prompt:
            resposta = self._personalizar_orquestrador(resposta_base, mensagem)
        elif "Consultor" in system_prompt:
            resposta = self._personalizar_consultor(resposta_base, mensagem)
        elif "Criativo" in system_prompt:
            resposta = self._personalizar_criativo(resposta_base, mensagem)
        else:
            resposta = resposta_base
        
        return resposta
    
    def _personalizar_orquestrador(self, resposta_base: str, mensagem: str) -> str:
        """Personaliza resposta para o agente orquestrador"""
        return f"""[ORQUESTRADOR] Analisando sua solicitação...

{resposta_base}

Para esta solicitação, identifico que o melhor caminho é direcionar para o agente especializado apropriado.

Vou coordenar a resposta para garantir o melhor resultado possível."""
    
    def _personalizar_consultor(self, resposta_base: str, mensagem: str) -> str:
        """Personaliza resposta para o agente consultor"""
        # Simular resultados de busca
        resultados_mock = """
### Resultados Encontrados:

1. **Reunião de Planejamento Estratégico** - 15/01/2024
   - Participantes: João Silva, Maria Santos
   - Tópicos relevantes identificados
   
2. **Workshop de Inovação** - 20/01/2024
   - Discussões sobre transformação digital
   - Decisões importantes tomadas

3. **Documento: Plano de Ação 2024**
   - Autor: Pedro Oliveira
   - Contém diretrizes relevantes
"""
        
        return f"""{resposta_base}

{resultados_mock}

Estas informações foram filtradas e organizadas por relevância para sua consulta."""
    
    def _personalizar_criativo(self, resposta_base: str, mensagem: str) -> str:
        """Personaliza resposta para o agente criativo"""
        ideias_mock = """
### 💡 Ideias Geradas:

**Ideia 1: Abordagem Inovadora** ⭐⭐⭐
- Implementar solução baseada em IA adaptativa
- Benefícios: Aumento de 40% na eficiência
- Desafios: Requer treinamento da equipe

**Ideia 2: Solução Disruptiva** ⭐⭐⭐⭐⭐
- Reimaginar completamente o processo atual
- Benefícios: Transformação total do paradigma
- Desafios: Mudança cultural significativa

**Ideia 3: Melhoria Incremental** ⭐⭐
- Otimizar fluxos existentes com automação
- Benefícios: Implementação rápida e segura
- Desafios: Ganhos limitados a médio prazo
"""
        
        return f"""{resposta_base}

{ideias_mock}

Cada ideia foi desenvolvida considerando diferentes níveis de inovação e impacto organizacional."""


# Classes auxiliares para compatibilidade
class OpenAI:
    """Alias para MockOpenAI mantendo compatibilidade"""
    def __new__(cls, api_key: str = "mock-key"):
        return MockOpenAI(api_key)


# Função de conveniência
def criar_cliente_mock() -> MockOpenAI:
    """
    Cria um cliente OpenAI mock para testes.
    
    Returns:
        MockOpenAI: Cliente mock configurado
    """
    return MockOpenAI("mock-key-test")