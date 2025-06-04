# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the AURALIS system - a sophisticated multi-agent AI architecture for processing and analyzing corporate meeting information. The system features:
- A GUI application for meeting management (FRONT.py)
- A multi-agent system architecture with OpenAI integration
- Voice recording and transcription capabilities
- AI-powered analysis and brainstorming
- Supabase database integration for persistence

## Development Commands

### Running the Application
```bash
python3 FRONT.py
```

### Dependencies
The project uses:
- customtkinter - Modern GUI framework
- openai - OpenAI API integration
- supabase - Database client
- numpy - Numerical computations
- Standard libraries: threading, datetime, math, random

Note: No requirements.txt file exists yet. Key dependencies that need to be installed:
```bash
pip install customtkinter numpy openai supabase
```

### Environment Variables
Create a `.env` file with:
```
OPENAI_API_KEY=your-api-key-here
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
DEBUG_MODE=False
```

## Architecture Overview

### 1. Multi-Agent System (src/agentes/)
The system implements a sophisticated agent architecture with:
- **Orchestrator Agent**: Interprets user intentions and delegates to specialized agents
- **Intelligent Query Agent**: Performs semantic search and information retrieval
- **Brainstorm Agent**: Generates creative ideas using techniques like SCAMPER
- **Inter-agent Communication System**: Message bus for asynchronous agent communication
- **Optimization System**: Intelligent caching, context compression, and batch processing

Key design patterns:
- Abstract base class (AgenteBase) for all agents
- Mock implementations for testing without OpenAI API
- Event-driven communication between agents
- LRU cache with TTL for performance optimization

### 2. GUI Application (FRONT.py)
A desktop application with:
- Fixed 320x240 pixel resolution optimized for small screens
- Dark theme with carefully selected color palette
- Multiple screens: Login, Main Menu, Meeting History, Recording, AI Assistant
- Audio interface with real-time particle animations
- State management for navigation and data flow
- Integrated environment variable loading

## Key Technical Details

### Agent System Integration Points
When integrating the agent system with the GUI:
- Initialize `SistemaAgentes` in main.py
- Pass user messages through `processar_mensagem_usuario()`
- Provide context including current meeting info and user data

### GUI State Management
The GUI uses these key state variables:
- `self.usuario_logado`: Current user info
- `self.frame_atual`: Active screen frame
- `self.gravando`: Recording status
- `self.contexto_reuniao`: Meeting context for AI

### Performance Considerations
- Cache hit rate target: ~85%
- Animation refresh rate: 30ms (33 FPS)
- Timer update rate: 100ms
- Maximum simultaneous particles: ~50

## Common Development Tasks

### Adding a New Agent
1. Create class inheriting from `AgenteBase`
2. Implement `get_prompt_sistema()` and `processar_mensagem()`
3. Register in `sistema_agentes.py`
4. Add to orchestrator's routing map

### Adding a New GUI Screen
1. Create `mostrar_nova_tela()` method
2. Create `_criar_nova_tela()` implementation
3. Use `self.transicao_rapida()` for navigation
4. Include standard header with `self.criar_cabecalho_voltar()`

### Modifying the Color Scheme
Update the color dictionary in `SistemaTFT.__init__()`:
```python
self.cores["nova_cor"] = "#HEXCODE"
```

## Documentation Structure

All detailed documentation has been organized in the `/docs` folder:
- `1 - README_DATABASE_SCHEMA.md` - Database schema documentation
- `2 - README_DATABASE_IMPLEMENTATION.md` - Database implementation guide
- `AGENTE - FASE 1.md` - Agent system phase 1 documentation
- `DOC_FRONT.md` - Frontend documentation
- `GERAL - README_SISTEMA_AGENTES_DETALHADO.md` - Detailed agent system documentation
- `README_INTEGRACAO_AGENTE_FRONT.md` - Frontend-Agent integration guide
- `compact.md` - Development history and context

## Important Instructions

- As instruções em `docs/compact.md` referem-se ao histórico de mensagens/alterações/modificações/incrementações/ajustes que foram tratados anteriormente, são relevantes para considerar no contexto para manter a consistência nas execuções posteriores
- Sempre gerar respostas no terminal e instruções dentro de códigos .py em português Brasil


## 📜 MISSÃO CRÍTICA DO ASSISTENTE DE DESENVOLVIMENTO AURAU

Você é um assistente de desenvolvimento de software especializado e altamente disciplinado, designado para o projeto AURAU. Sua principal diretriz é seguir **TODAS** as instruções abaixo com **PRECISÃO ABSOLUTA E SEM EXCEÇÕES**. O sucesso de cada fase depende da sua aderência rigorosa a este protocolo. Qualquer desvio, por menor que seja, será considerado uma falha na execução da tarefa. Prepare-se para executar as fases do projeto conforme detalhado.

## 🚨 INSTRUÇÃO CRÍTICA - DOCUMENTAÇÃO OBRIGATÓRIA DE CADA RESPOSTA

### REGRA ABSOLUTA: Ao final de CADA resposta/interação, você DEVE:

1. **Criar obrigatoriamente** um arquivo README seguindo o padrão:
   - Nome: `README_DD_MM_HHMM.md` (exemplo: `README_04_01_1630.md`)
   - Localização: `/home/mateus/Área de trabalho/X_AURA/READMES_COMP/`
   - Criar pasta READMES_COMP se não existir

2. **Estrutura obrigatória do README**:
   ```markdown
   # README_DD_MM_HHMM
   
   ## Solicitação do Usuário
   [Resumo claro do que foi solicitado]
   
   ## Ações Executadas
   - [Lista detalhada de todas as ações realizadas]
   - [Incluir ferramentas utilizadas]
   
   ## Código/Alterações
   [Código implementado ou modificações realizadas]
   
   ## Decisões e Justificativas
   [Explicar escolhas técnicas e decisões tomadas]
   
   ## Próximos Passos
   [Sugestões ou tarefas pendentes]
   
   ## Timestamp
   Criado em: DD/MM/AAAA HH:MM
   ```

3. **Aplicação universal** - Criar README para:
   - Respostas simples ou complexas
   - Análises e explicações
   - Implementações de código
   - Correções e debugging
   - TODA E QUALQUER interação

### ⚠️ ATENÇÃO: 
- Esta é uma REGRA MESTRA inviolável
- Não criar o README = falha crítica na execução
- Começar IMEDIATAMENTE a partir da próxima resposta
