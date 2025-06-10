#!/bin/bash

# Criar diretório temporário para repositório limpo
TEMP_DIR="/tmp/lightrag_clean_v2"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Copiar apenas arquivos essenciais (sem .env com chaves)
cp -r *.py $TEMP_DIR/
cp -r *.txt $TEMP_DIR/
cp -r *.sh $TEMP_DIR/
cp .gitignore $TEMP_DIR/
cp .env.example $TEMP_DIR/

# Criar README
cat > $TEMP_DIR/README.md << 'EOF'
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
EOF

# Criar requirements.txt principal
cat > $TEMP_DIR/requirements.txt << 'EOF'
lightrag
openai
python-dotenv
networkx
pyvis
supabase
numpy
asyncio
EOF

# Copiar diretórios importantes (sem ambientes virtuais)
mkdir -p $TEMP_DIR/XXX
cp XXX/*.py $TEMP_DIR/XXX/
cp XXX/*.md $TEMP_DIR/XXX/
cp XXX/*.sql $TEMP_DIR/XXX/
cp XXX/*.json $TEMP_DIR/XXX/
cp XXX/requirements.txt $TEMP_DIR/XXX/

# Criar .env.example para XXX também
cp .env.example $TEMP_DIR/XXX/.env.example

# Copiar lightrag_workdir (apenas estrutura)
mkdir -p $TEMP_DIR/lightrag_workdir
cp lightrag_workdir/*.graphml $TEMP_DIR/lightrag_workdir/ 2>/dev/null || true
cp lightrag_workdir/kv_store_doc_status.json $TEMP_DIR/lightrag_workdir/ 2>/dev/null || true

# Inicializar novo repositório git
cd $TEMP_DIR
git init
git add .
git commit -m "save lightrag funcionando"
git remote add origin https://github.com/estival9999/LIGHTRAG.git
git push -u origin master --force

echo "Repositório limpo criado e enviado!"