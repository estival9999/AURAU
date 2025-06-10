# 🔍 Instruções para Testar Busca Híbrida RAG no Supabase

## ✅ Status da Configuração

### Concluído:
1. ✅ Dependências Python instaladas
2. ✅ Credenciais do Supabase configuradas no `.env`
3. ✅ Base de conhecimento carregada (25 chunks)
4. ✅ Scripts de teste criados

### ⚠️ Ação Necessária:
Existe um erro na função SQL que precisa ser corrigido antes de executar os testes.

## 🛠️ Passos para Completar o Teste

### 1. Corrigir Função SQL no Supabase

1. Acesse o [SQL Editor do Supabase](https://supabase.com/dashboard/project/swwvnpqpsqzdxikqrnvr/sql)
2. Execute o conteúdo do arquivo `supabase_hybrid_search_fix.sql`
3. Isso corrigirá o erro de ambiguidade na função de busca

### 2. Executar Teste Completo

No terminal, execute:

```bash
cd "/home/mateus/Área de trabalho/XXX"
source venv/bin/activate
python testar_busca_hibrida.py
```

## 📊 O que o Teste Demonstra

### 1. **Comparação de Métodos**
O teste compara diferentes configurações de peso:
- **Apenas Full-Text**: Busca exata por palavras
- **Apenas Semântico**: Busca por significado
- **Híbrido Balanceado**: Combina ambos
- **Variações de Peso**: Diferentes ênfases

### 2. **Tipos de Query Testados**
- Perguntas conceituais
- Busca por palavras-chave
- Queries técnicas
- Perguntas naturais

### 3. **Métricas Analisadas**
- Tempo de resposta
- Relevância dos resultados (score)
- Qualidade da resposta RAG

## 🎯 Por que Busca Híbrida é Mais Eficiente

### 1. **Cobertura Completa**
- **Full-text** encontra menções exatas (ex: "AURALIS", "Pantaneta")
- **Semântica** entende contexto (ex: "sistema de gravação" ≈ "registro de reuniões")

### 2. **Flexibilidade**
- Ajuste de pesos permite otimizar para diferentes casos
- Queries técnicas → mais peso full-text
- Perguntas naturais → mais peso semântico

### 3. **Algoritmo RRF**
- Combina rankings de forma inteligente
- Itens bem ranqueados em ambos métodos recebem score alto
- Reduz viés de um único método

## 📈 Resultados Esperados

Após executar o teste, você verá:

1. **Taxa de Sucesso**: ~100% dos chunks carregados
2. **Tempo de Busca**: <1 segundo por query
3. **Qualidade**: Respostas contextuais e precisas
4. **Comparação**: Diferenças claras entre métodos

## 🔧 Troubleshooting

### Se encontrar erros:

1. **Erro de ambiguidade SQL**: Execute o fix SQL fornecido
2. **Erro de API OpenAI**: Verifique a chave API no `.env`
3. **Erro de conexão Supabase**: Verifique URL e chave

### Logs de Sucesso:
```
✅ Carregamento concluído!
📊 Resumo:
   - Chunks bem-sucedidos: 25
   - Taxa de sucesso: 100.0%
```

## 🚀 Próximos Passos

1. Experimente ajustar os pesos para seu caso de uso
2. Adicione mais documentos à base
3. Implemente cache para queries frequentes
4. Configure monitoramento de performance

## 💡 Dica Final

A busca híbrida é especialmente eficaz quando você tem:
- Documentos técnicos com terminologia específica
- Usuários que fazem perguntas de formas variadas
- Necessidade de precisão E compreensão contextual

Execute o teste e observe como diferentes configurações afetam os resultados!