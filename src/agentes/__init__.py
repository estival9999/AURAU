"""
Sistema de Agentes AURALIS

Módulo principal que exporta as classes e funções do sistema multi-agente.
"""

# Importar versão da biblioteca
__version__ = "1.0.0"
__author__ = "Sistema AURALIS"

# Importar classes principais
from .sistema_agentes import (
    SistemaAgentes,
    criar_sistema_auralis,
    processar_pergunta_simples
)

# Importar agentes individuais
from .agente_orquestrador import AgenteOrquestrador
from .agente_consulta_inteligente import AgenteConsultaInteligente
from .agente_brainstorm import AgenteBrainstorm

# Importar sistema de comunicação
from .comunicacao_agentes import (
    ComunicacaoAgentes,
    MensagemAgente,
    TipoMensagem,
    StatusMensagem
)

# Importar otimizador
from .otimizador import (
    CacheInteligente,
    CompressorContexto,
    ProcessadorBatch,
    Otimizador,
    otimizador_global
)

# Importar classes base
from .agente_base import AgenteBase, Mensagem
from .agente_base_simulado import AgenteBaseSimulado

# Importar mock para testes
from .openai_mock import MockOpenAI, criar_cliente_mock

# Definir o que é exportado quando se faz "from agentes import *"
__all__ = [
    # Sistema principal
    "SistemaAgentes",
    "criar_sistema_auralis",
    "processar_pergunta_simples",
    
    # Agentes
    "AgenteOrquestrador",
    "AgenteConsultaInteligente", 
    "AgenteBrainstorm",
    
    # Comunicação
    "ComunicacaoAgentes",
    "MensagemAgente",
    "TipoMensagem",
    "StatusMensagem",
    
    # Otimização
    "CacheInteligente",
    "CompressorContexto",
    "ProcessadorBatch",
    "Otimizador",
    "otimizador_global",
    
    # Classes base
    "AgenteBase",
    "AgenteBaseSimulado",
    "Mensagem",
    
    # Mock
    "MockOpenAI",
    "criar_cliente_mock"
]


def info():
    """Mostra informações sobre o sistema de agentes"""
    print(f"""
Sistema de Agentes AURALIS v{__version__}
=====================================

Agentes disponíveis:
- Orquestrador: Coordena e direciona solicitações
- Consultor Inteligente: Busca e recuperação de informações
- Agente Criativo: Geração de ideias e brainstorming

Componentes principais:
- Sistema de Comunicação Inter-Agentes
- Cache Inteligente com TTL
- Compressor de Contexto
- Processador Batch

Para começar:
>>> from agentes import criar_sistema_auralis
>>> sistema = criar_sistema_auralis()
>>> resposta = sistema.processar_mensagem_usuario("Sua pergunta aqui")
    """)


# Mensagem de inicialização (apenas em modo debug)
import os
if os.getenv("AURALIS_DEBUG"):
    print(f"[AURALIS] Sistema de Agentes v{__version__} carregado com sucesso")