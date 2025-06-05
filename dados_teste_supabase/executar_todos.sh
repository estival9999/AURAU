#!/bin/bash
# Script para executar todos os scripts de inserção de dados em ordem

echo "🚀 INICIANDO INSERÇÃO DE DADOS DE TESTE NO SUPABASE"
echo "=================================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se estamos no diretório correto
if [ ! -f "../.env" ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado no diretório pai${NC}"
    echo "Por favor, execute este script do diretório dados_teste_supabase/"
    exit 1
fi

# Função para executar script e verificar resultado
executar_script() {
    script=$1
    descricao=$2
    
    echo -e "${YELLOW}▶️  Executando: $descricao${NC}"
    echo "----------------------------------------"
    
    python3 $script
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $descricao concluído com sucesso!${NC}"
    else
        echo -e "${RED}❌ Erro ao executar $descricao${NC}"
        echo "Deseja continuar? (s/n)"
        read resposta
        if [ "$resposta" != "s" ]; then
            exit 1
        fi
    fi
    
    echo ""
    echo "Pressione ENTER para continuar..."
    read
    clear
}

# Executar scripts em ordem
clear
echo "🚀 SISTEMA AURALIS - INSERÇÃO DE DADOS DE TESTE"
echo "=============================================="
echo ""
echo "Este script irá:"
echo "1. Inserir usuários de teste"
echo "2. Inserir reuniões com transcrições"
echo "3. Inserir interações com IA"
echo "4. Testar conexões e verificar dados"
echo ""
echo "Pressione ENTER para iniciar..."
read

# 1. Inserir usuários
executar_script "01_inserir_usuarios.py" "Inserção de Usuários"

# 2. Inserir reuniões
executar_script "02_inserir_reunioes.py" "Inserção de Reuniões"

# 3. Inserir interações com IA
executar_script "03_inserir_interacoes_ia.py" "Inserção de Interações com IA"

# 4. Testar conexão e verificar dados
executar_script "04_testar_conexao.py" "Teste de Conexão e Verificação"

# Resumo final
echo ""
echo "=================================================="
echo -e "${GREEN}✅ PROCESSO CONCLUÍDO!${NC}"
echo "=================================================="
echo ""
echo "Próximos passos:"
echo "1. Verificar os dados no painel do Supabase"
echo "2. Testar as funcionalidades do FRONT.py"
echo "3. Remover esta pasta após confirmação"
echo ""
echo "Para remover os dados de teste, execute:"
echo "rm -rf dados_teste_supabase/"
echo ""