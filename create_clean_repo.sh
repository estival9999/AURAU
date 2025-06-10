#!/bin/bash

# Criar diretório temporário para repositório limpo
TEMP_DIR="/tmp/lightrag_clean"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Copiar apenas arquivos essenciais
cp -r .env $TEMP_DIR/
cp -r *.py $TEMP_DIR/
cp -r *.txt $TEMP_DIR/
cp -r *.md $TEMP_DIR/
cp -r *.sh $TEMP_DIR/
cp -r LightRAG $TEMP_DIR/
cp -r XXX $TEMP_DIR/
cp -r lightrag_workdir $TEMP_DIR/
cp .gitignore $TEMP_DIR/

# Remover ambientes virtuais e arquivos grandes
find $TEMP_DIR -name "*.so" -size +50M -delete
find $TEMP_DIR -name "venv" -type d -exec rm -rf {} +
find $TEMP_DIR -name "lightrag_env" -type d -exec rm -rf {} +
find $TEMP_DIR -name "__pycache__" -type d -exec rm -rf {} +
find $TEMP_DIR -name "*.pyc" -delete

# Inicializar novo repositório git
cd $TEMP_DIR
git init
git add .
git commit -m "save lightrag funcionando"
git remote add origin https://github.com/estival9999/LIGHTRAG.git
git push -u origin master --force

echo "Repositório limpo criado e enviado!"