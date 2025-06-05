# 📊 Dados de Teste para Supabase - Sistema AURALIS

Esta pasta contém scripts para popular o banco de dados Supabase com dados de teste realistas.

## 🎯 Objetivo

Simular dados reais que seriam gerados pela interface FRONT.py durante o uso normal do sistema.

## 📁 Estrutura dos Scripts

1. **`01_inserir_usuarios.py`** - Insere 8 usuários de diferentes departamentos
2. **`02_inserir_reunioes.py`** - Insere 4 reuniões com transcrições brutas realistas
3. **`03_inserir_interacoes_ia.py`** - Insere 8 interações diferentes com o assistente AURALIS
4. **`04_testar_conexao.py`** - Verifica integridade dos dados e testa conexões

## 🚀 Como Executar

### Opção 1: Executar todos de uma vez
```bash
cd dados_teste_supabase/
./executar_todos.sh
```

### Opção 2: Executar individualmente
```bash
python3 01_inserir_usuarios.py
python3 02_inserir_reunioes.py
python3 03_inserir_interacoes_ia.py
python3 04_testar_conexao.py
```

## 📋 Pré-requisitos

- Python 3.x instalado
- Arquivo `.env` configurado com credenciais do Supabase
- Dependências: `pip install supabase python-dotenv bcrypt`

## 🗑️ Limpeza

Após confirmar que os dados foram inseridos corretamente:
```bash
cd ..
rm -rf dados_teste_supabase/
```

## ⚠️ Observações Importantes

1. **Transcrições**: São textos contínuos sem formatação, simulando gravações reais
2. **Senhas**: Todas usam "senha123" (apenas para teste)
3. **Embeddings**: Não são gerados (requerem OpenAI API)
4. **Base de Conhecimento**: Não incluída (será adicionada por outro processo)

## 📊 Dados Inseridos

- **8 Usuários**: Diversos departamentos (TI, RH, Marketing, Financeiro)
- **4 Reuniões**: Sprint planning, Daily standup, Resultados Q4, Processo seletivo
- **8 Interações IA**: Consultas variadas sobre reuniões, tarefas e análises

## 🔍 Verificação

Execute `04_testar_conexao.py` para verificar:
- Total de registros inseridos
- Integridade das relações entre tabelas
- Estatísticas gerais
- Funcionamento das conexões