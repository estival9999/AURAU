# LightRAG Integration Project

Este projeto demonstra a integração do LightRAG com um sistema de busca híbrida usando Supabase.

## Configuração

1. Clone o repositório
2. Copie `.env.example` para `.env` e configure suas chaves API
3. Instale as dependências: `pip install -r requirements.txt`
4. Execute: `python lightrag_agent_v2.py`

## Componentes

- **LightRAG**: Sistema de RAG baseado em grafos de conhecimento
- **Sistema Híbrido (XXX)**: Busca híbrida com Supabase (full-text + semântica)
- **Scripts de Integração**: Ferramentas para unir ambos os sistemas

## Visualização

Para visualizar o grafo de conhecimento:
```bash
python visualize_graph.py
```

## API

Para iniciar o servidor API:
```bash
./start_api_server.sh
```
