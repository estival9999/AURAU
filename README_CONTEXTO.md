# Contexto da Pasta: X_AURA

**Última Atualização:** 2025-06-03T21:38:12.718831

## Propósito
Coleção de utilitários e funções

## Arquivos Python (2)

### FRONT.py
**Descrição:** Sistema de Reuniões - Versão Linux Corrigida
Resolução fixa: 320x240 pixels
Interface otimizada para...

- **Linhas:** 982
- **Complexidade:** 40
- **Classes:** SistemaTFT
- **Principais Funções:** __init__, centralizar_janela, executar, transicao_rapida, mostrar_login
  *(e mais 26 funções)*

### main.py
**Descrição:** AURALIS Backend Integration
Main module that bridges the frontend GUI with the AI agent system...

- **Linhas:** 652
- **Complexidade:** 90
- **Classes:** AURALISBackend
- **Principais Funções:** __init__, authenticate, logout, get_meeting_history, get_meeting_details
  *(e mais 20 funções)*

## Relações Entre Arquivos
- main.py importa from src.agentes.sistema_agentes import SistemaAgentes
- main.py importa from src.database.supabase_handler import SupabaseHandler

## Pontos de Atenção
- ⚠️ Alta complexidade em FRONT.py (complexidade: 40)
- ⚠️ Arquivo extenso: FRONT.py (982 linhas)
- ⚠️ Alta complexidade em main.py (complexidade: 90)
- ⚠️ Arquivo extenso: main.py (652 linhas)

---
*Gerado automaticamente por auto_compile.py em 2025-06-03 21:38:12*