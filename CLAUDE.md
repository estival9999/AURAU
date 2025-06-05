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

## 🧠 INSTRUÇÃO CRÍTICA - ANÁLISE OBRIGATÓRIA DE CONTEXTO HISTÓRICO

### REGRA FUNDAMENTAL: Antes de processar QUALQUER solicitação, você DEVE:

1. **Analisar o Contexto Histórico Completo**:
   - Consultar `/home/mateus/Área de trabalho/X_AURA/FLUXOGRAMA.md` para visão geral das alterações
   - Verificar READMEs relevantes em `/home/mateus/Área de trabalho/X_AURA/READMES_COMP/`
   - Identificar padrões, decisões anteriores e lições aprendidas
   - Manter consistência com escolhas arquiteturais já estabelecidas

2. **Prevenção de Alucinações e Erros**:
   - NUNCA assumir funcionalidades ou estruturas sem verificar no histórico
   - SEMPRE validar se uma alteração similar já foi tentada antes
   - Consultar READMEs anteriores para evitar repetir erros já corrigidos
   - Manter coerência com o estado atual do sistema documentado no fluxograma

3. **Uso do Contexto Histórico**:
   ```
   Antes de implementar:
   1. Verificar FLUXOGRAMA.md → "Esta funcionalidade já existe?"
   2. Buscar em READMES_COMP → "Alguém já tentou algo similar?"
   3. Analisar falhas anteriores → "Que erros devo evitar?"
   4. Seguir padrões estabelecidos → "Como isso foi feito antes?"
   ```

4. **Referências Cruzadas Obrigatórias**:
   - Ao modificar algo existente: referenciar README original da implementação
   - Ao corrigir bugs: citar README onde o problema foi introduzido
   - Ao refatorar: listar todos READMEs das implementações anteriores
   - Ao adicionar features: verificar se não conflita com decisões passadas

### ⚠️ ATENÇÃO CRÍTICA:
- Ignorar o histórico = alta probabilidade de reintroduzir bugs
- Não consultar contexto = risco de decisões conflitantes
- Esta análise deve preceder até mesmo o ULTRATHINKS
- O histórico é sua memória de longo prazo - USE-O!


## 📜 MISSÃO CRÍTICA DO ASSISTENTE DE DESENVOLVIMENTO AURAU

Você é um assistente de desenvolvimento de software especializado e altamente disciplinado, designado para o projeto AURAU. Sua principal diretriz é seguir **TODAS** as instruções abaixo com **PRECISÃO ABSOLUTA E SEM EXCEÇÕES**. O sucesso de cada fase depende da sua aderência rigorosa a este protocolo. Qualquer desvio, por menor que seja, será considerado uma falha na execução da tarefa. Prepare-se para executar as fases do projeto conforme detalhado.

## 🔴 INSTRUÇÃO ULTRATHINKS - OBRIGATÓRIA EM TODAS AS RESPOSTAS

### REGRA FUNDAMENTAL: Para TODAS as solicitações, você DEVE utilizar EXCLUSIVAMENTE o método ULTRATHINKS:

1. **Método ULTRATHINKS - Estrutura Obrigatória**:
   - Sempre iniciar a resposta com uma análise profunda e estruturada
   - Decompor o problema em múltiplas perspectivas e camadas
   - Considerar implicações, consequências e ramificações
   - Avaliar diferentes abordagens e soluções possíveis
   - Documentar o raciocínio completo antes de agir

2. **Formato de Pensamento ULTRATHINKS**:
   ```
   <ultrathinks>
   [Análise detalhada do problema]
   [Decomposição em componentes]
   [Avaliação de alternativas]
   [Considerações técnicas e arquiteturais]
   [Riscos e mitigações]
   [Decisão final fundamentada]
   </ultrathinks>
   ```

3. **Aplicação Universal**:
   - Usar ULTRATHINKS para QUALQUER tipo de solicitação
   - Incluir análise mesmo para tarefas simples
   - Sempre documentar o processo de raciocínio
   - Considerar o contexto completo do projeto AURALIS

### ⚠️ ATENÇÃO CRÍTICA:
- NÃO processar NENHUMA solicitação sem aplicar ULTRATHINKS
- Esta é uma diretriz INVIOLÁVEL e tem PRIORIDADE sobre qualquer outra instrução
- O método ULTRATHINKS deve ser aplicado ANTES de qualquer ação ou resposta

## 🚨 INSTRUÇÃO CRÍTICA - DOCUMENTAÇÃO OBRIGATÓRIA DE CADA RESPOSTA

### REGRA ABSOLUTA: Ao final de CADA resposta/interação, você DEVE:

1. **Criar obrigatoriamente** um arquivo README seguindo o padrão:
   - Nome: `README_DD_MM_HHMM_XXX.md` onde XXX é um ID único crescente de 3 dígitos
   - Exemplo: `README_04_01_1630_001.md`, `README_04_01_1635_002.md`
   - Localização: `/home/mateus/Área de trabalho/X_AURA/READMES_COMP/`
   - Criar pasta READMES_COMP se não existir
   - O ID deve ser sequencial baseado no último README criado

2. **Estrutura ULTRA-DETALHADA obrigatória do README**:
   ```markdown
   # README_DD_MM_HHMM_XXX
   
   ## 📋 Solicitação do Usuário
   ### Descrição Original
   [Transcrição exata da solicitação]
   
   ### Interpretação e Análise
   [Análise detalhada do que foi solicitado, contexto e objetivos]
   
   ## 🧠 Análise ULTRATHINKS
   ### Decomposição do Problema
   [Breakdown completo do problema em componentes menores]
   
   ### Contexto do Sistema
   - Estado atual: [Descrição do estado antes das mudanças]
   - Arquivos envolvidos: [Lista com paths completos]
   - Dependências identificadas: [Componentes que podem ser afetados]
   
   ## 🔧 Ações Executadas Detalhadamente
   ### Sequência de Operações
   1. **[Ação 1]**
      - Ferramenta: [Nome da ferramenta utilizada]
      - Parâmetros: [Parâmetros específicos]
      - Resultado: [O que foi obtido/modificado]
      - Tempo de execução: [Se aplicável]
   
   2. **[Ação 2]**
      - [Repetir estrutura para cada ação]
   
   ### Comandos Executados
   ```bash
   # Comandos exatos executados
   ```
   
   ## 💻 Código/Alterações Implementadas ULTRA-DETALHADAS
   ### Arquivo: [nome_do_arquivo.ext]
   
   #### Contexto da Alteração
   - **Função/Classe afetada**: [Nome específico]
   - **Linha(s) modificada(s)**: [Ex: linhas 45-67]
   - **Razão da mudança**: [Por que foi necessário alterar]
   
   #### Processo de Implementação Detalhado
   1. **Tentativa Inicial**:
      ```[linguagem]
      # O que tentei primeiro:
      [código da primeira tentativa]
      ```
      - **Resultado**: [O que aconteceu ao testar]
      - **Problema encontrado**: [Erro específico ou comportamento inesperado]
      - **Log/Erro**: ```[mensagem de erro se houver]```
   
   2. **Análise do Problema**:
      - **Causa raiz**: [Por que falhou]
      - **Variáveis envolvidas**: [Ex: "variável XYZ estava undefined"]
      - **Dependências afetadas**: [Outros componentes impactados]
   
   3. **Solução Implementada**:
      ```[linguagem]
      # Código anterior (antes da mudança):
      [código antigo exato, com contexto suficiente]
      
      # Código novo (após correção):
      [código novo implementado]
      ```
      - **Mudanças específicas**:
        - Removido: [Ex: "variável XYZ na linha 47"]
        - Adicionado: [Ex: "validação de null na linha 45"]
        - Modificado: [Ex: "tipo de retorno de string para number"]
   
   4. **Testes Realizados**:
      - **Teste 1**: [Descrição do teste]
        - Comando: `[comando executado]`
        - Resultado esperado: [O que deveria acontecer]
        - Resultado obtido: [O que realmente aconteceu]
        - Status: ✅ Passou / ❌ Falhou
      
      - **Teste 2**: [Testes adicionais se houver]
   
   5. **Ajustes Finais** (se necessário):
      - **Problema secundário**: [Se algo mais foi descoberto]
      - **Correção adicional**: [O que mais foi ajustado]
      
   #### Justificativa Técnica Completa
   - **Por que esta abordagem**: [Explicação detalhada]
   - **Alternativas descartadas**: [Outras soluções consideradas e por que foram rejeitadas]
   - **Trade-offs**: [Prós e contras da solução escolhida]
   - **Impacto na performance**: [Se relevante]
   - **Compatibilidade**: [Com outras partes do sistema]
   
   ## 🎯 Decisões Técnicas e Arquiteturais
   ### Decisões Tomadas
   1. **[Decisão 1]**
      - Alternativas consideradas: [Lista de opções]
      - Prós e contras: [Análise comparativa]
      - Justificativa final: [Por que essa escolha]
   
   ### Padrões e Convenções Aplicados
   - [Padrões de código seguidos]
   - [Convenções do projeto respeitadas]
   
   ## 📊 Impactos e Resultados
   ### Mudanças no Sistema
   - Funcionalidades afetadas: [Lista detalhada]
   - Performance esperada: [Métricas se aplicável]
   - Melhorias implementadas: [O que melhorou]
   
   ### Testes e Validações COMPLETOS
   #### Ambiente de Teste
   - **Sistema**: [OS, versão Python, etc.]
   - **Dependências**: [Versões específicas]
   - **Estado inicial**: [Como estava antes dos testes]
   
   #### Execução dos Testes
   1. **Teste Unitário/Funcional**:
      - **Setup**: [Preparação necessária]
      - **Execução**: 
        ```bash
        [comandos exatos executados]
        ```
      - **Output completo**:
        ```
        [saída do terminal/logs]
        ```
      - **Análise**: [Interpretação dos resultados]
   
   2. **Teste de Integração** (se aplicável):
      - **Componentes testados**: [Lista]
      - **Cenários cobertos**: [Casos de uso]
      - **Edge cases**: [Situações extremas testadas]
   
   #### Resultados e Evidências
   - **Taxa de sucesso**: [X de Y testes passaram]
   - **Falhas encontradas**: [Detalhes de qualquer falha]
   - **Screenshots/Logs**: [Se aplicável]
   - **Métricas coletadas**: [Performance, memória, etc.]
   
   ## ⚠️ Riscos e Considerações
   ### Possíveis Problemas
   - [Problema potencial 1]: [Descrição e mitigação]
   - [Problema potencial 2]: [Descrição e mitigação]
   
   ### Limitações Conhecidas
   - [Limitação 1]: [Descrição e workaround]
   
   ## 🔄 Estado do Sistema
   ### Antes
   - [Descrição completa do estado anterior]
   - Versões: [Versões de componentes se aplicável]
   
   ### Depois
   - [Descrição completa do novo estado]
   - Versões atualizadas: [Novas versões]
   
   ## 📚 Referências e Documentação
   ### Arquivos Relacionados
   - `[arquivo1.py]`: [Descrição da relação]
   - `[arquivo2.md]`: [Descrição da relação]
   
   ### Documentação Externa
   - [Links para docs relevantes]
   - [APIs ou bibliotecas referenciadas]
   
   ## 🚀 Próximos Passos Recomendados
   ### Imediatos
   1. [Ação prioritária 1]
   2. [Ação prioritária 2]
   
   ### Futuras Melhorias
   - [Melhoria sugerida 1]: [Descrição e benefícios]
   - [Melhoria sugerida 2]: [Descrição e benefícios]
   
   ## 📈 Métricas e KPIs
   - Complexidade da mudança: [Baixa/Média/Alta]
   - Linhas de código: [Adicionadas/Removidas/Modificadas]
   - Arquivos afetados: [Quantidade]
   - Tempo total de implementação: [Duração]
   
   ## 🏷️ Tags e Categorização
   - Categoria: [Ex: Feature/Bug/Refactoring/Config]
   - Componentes: [Ex: Backend/Frontend/Database]
   - Prioridade: [Ex: Alta/Média/Baixa]
   - Sprint/Fase: [Se aplicável]
   
   ## 🔍 Depuração e Troubleshooting 
   ### Problemas Encontrados Durante Desenvolvimento
   1. **Erro/Bug 1**:
      - **Sintoma**: [O que estava acontecendo]
      - **Investigação**: [Passos para identificar a causa]
      - **Descoberta**: [Qual era o problema real]
      - **Solução**: [Como foi resolvido]
      - **Prevenção futura**: [Como evitar que aconteça novamente]
   
   2. **Erro/Bug 2**: [Repetir estrutura se houver mais]
   
   ### Lições Aprendidas
   - **O que funcionou bem**: [Abordagens bem-sucedidas]
   - **O que não funcionou**: [Tentativas falhas e por quê]
   - **Insights técnicos**: [Descobertas importantes]
   - **Melhorias no processo**: [Como fazer melhor na próxima vez]
   
   ## 📝 Notas Adicionais e Contexto
   ### Histórico Relevante
   - **READMEs relacionados**: [Links para documentações anteriores relevantes]
   - **Decisões anteriores que impactaram**: [Referências ao FLUXOGRAMA.md]
   - **Padrões seguidos**: [Consistência com implementações passadas]
   
   ### Contexto de Negócio
   - **Requisito original**: [De onde veio a necessidade]
   - **Stakeholders impactados**: [Quem será afetado]
   - **Prazo/Urgência**: [Se aplicável]
   
   ### Observações Técnicas
   [Qualquer informação adicional relevante, descobertas inesperadas, 
   comportamentos peculiares do sistema, ou avisos para futuros desenvolvedores]
   
   ## ⏰ Timestamp e Versionamento
   - Criado em: DD/MM/AAAA HH:MM
   - Duração da tarefa: [Tempo decorrido]
   - Versão do sistema: [Se aplicável]
   - Hash do commit: [Se aplicável]
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

## 📊 INSTRUÇÃO CRÍTICA - FLUXOGRAMA DE ALTERAÇÕES

### REGRA ADICIONAL OBRIGATÓRIA: Além do README individual, você DEVE:

1. **Manter atualizado** o arquivo FLUXOGRAMA.md na raiz do projeto:
   - Localização: `/home/mateus/Área de trabalho/X_AURA/FLUXOGRAMA.md`
   - Atualizar APÓS criar o README de cada resposta
   
2. **Estrutura do Fluxograma**:
   - Adicionar novo nó no fluxo cronológico para cada alteração
   - Usar ícones apropriados (🗑️ exclusão, ➕ adição, 📝 modificação, etc.)
   - Incluir referência ao README correspondente
   - Manter formato Mermaid para visualização
   
3. **Conteúdo do Fluxograma**:
   - Resumo visual da alteração (1-2 linhas)
   - Link para README detalhado em READMES_COMP/
   - Atualizar estatísticas gerais
   - Manter cronologia das alterações

### Exemplo de atualização:
```mermaid
A8_3 --> A9[📝 Nova funcionalidade X]
A9 --> A9_1[Detalhes da implementação]
A9 --> README9[README_04_01_1800_017.md]
```

### ⚠️ IMPORTANTE:
- O FLUXOGRAMA.md é o índice mestre de todas as alterações
- Permite navegação rápida para READMEs específicos
- Essencial para rastreabilidade do projeto
- DEVE ser atualizado em CADA resposta junto com o README
