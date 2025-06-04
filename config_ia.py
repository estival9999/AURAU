"""
Configuração para usar IA real ou simulada
"""

import os

def configurar_ia_temporaria():
    """
    Configura temporariamente o sistema para usar respostas mais elaboradas
    mesmo sem OpenAI API key.
    
    Em produção, você deve:
    1. Obter uma API key em https://platform.openai.com/api-keys
    2. Configurar em .env: OPENAI_API_KEY=sk-sua-chave-aqui
    """
    
    # Se não há API key, usa modo simulado melhorado
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OpenAI API Key não configurada")
        print("   O sistema usará respostas simuladas mais elaboradas")
        print("   Para usar IA real, configure OPENAI_API_KEY em .env")
        
        # Ativa modo simulado melhorado
        os.environ["SIMULADO_MELHORADO"] = "True"
    else:
        print("✅ OpenAI API Key detectada - usando IA real")

# Respostas simuladas melhoradas por tipo de pergunta
RESPOSTAS_SIMULADAS = {
    "ajuda": """Sou o assistente AURALIS, especializado em análise de reuniões corporativas.

Posso ajudá-lo com:
• 📋 Buscar informações em reuniões anteriores
• 💡 Gerar ideias criativas para desafios
• 📊 Analisar padrões e tendências
• 📝 Criar resumos executivos
• 🎯 Identificar ações e responsáveis

Como posso auxiliar você hoje?""",
    
    "buscar": """Analisando o histórico de reuniões...

Encontrei 3 reuniões relevantes:
1. **Planejamento Q1** (15/01) - Discussão sobre metas trimestrais
2. **Sprint Review** (12/01) - Análise de entregas do sprint
3. **Kickoff Projeto X** (10/01) - Início do novo projeto

Gostaria de analisar alguma reunião específica?""",
    
    "ideias": """Aplicando técnicas de brainstorming...

💡 **Ideias Geradas:**
1. **Gamificação**: Implementar sistema de pontos para engajamento
2. **Reuniões Híbridas**: Combinar presencial e remoto
3. **IA Assistente**: Usar IA para pré-análise de pautas
4. **Dashboard Visual**: Criar painéis interativos
5. **Microlearning**: Sessões de 15min focadas

Qual ideia gostaria de explorar mais?""",
    
    "analise": """Analisando dados da reunião...

📊 **Análise Executiva:**
• **Duração**: 45 minutos (15min abaixo do planejado)
• **Participação**: 85% de engajamento ativo
• **Decisões**: 4 decisões tomadas, 2 pendentes
• **Sentimento**: Positivo (score: 8.2/10)
• **Próximos Passos**: 6 ações identificadas

Deseja ver detalhes específicos?""",
    
    "default": """Processando sua solicitação...

Com base no contexto fornecido, identifiquei que você está interessado em {tema}.

Posso oferecer:
• Análise detalhada do tópico
• Busca em reuniões relacionadas
• Geração de insights
• Sugestões de ações

Como gostaria de prosseguir?"""
}