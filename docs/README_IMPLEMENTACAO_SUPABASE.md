# 🚀 README - IMPLEMENTAÇÃO DO BANCO DE DADOS SUPABASE PARA AURALIS

## 📋 VISÃO GERAL

Este documento fornece instruções detalhadas para implementar a estrutura de banco de dados no Supabase, otimizada para o sistema AURALIS com técnicas avançadas de RAG (Retrieval-Augmented Generation).

## 🎯 OBJETIVOS DA IMPLEMENTAÇÃO

1. **Criar estrutura de dados robusta** para suportar todas as funcionalidades do FRONT.py
2. **Implementar busca semântica** com embeddings vetoriais
3. **Otimizar performance** com índices estratégicos
4. **Garantir escalabilidade** para grandes volumes de dados
5. **Facilitar integração** com o sistema de agentes IA

## 📊 ESTRUTURA DE TABELAS

### Tabelas Principais:
- **users**: Gerenciamento de usuários e autenticação
- **meetings**: Histórico de reuniões com transcrições
- **knowledge_base**: Base de conhecimento corporativo
- **ai_interactions**: Histórico de conversas com IA

## 🔧 PRÉ-REQUISITOS

1. **Conta Supabase** ativa com projeto criado
2. **Credenciais** do arquivo `.env`:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
3. **Acesso ao painel** SQL Editor do Supabase

## 📝 INSTRUÇÕES PASSO A PASSO

### PASSO 1: PREPARAR O AMBIENTE SUPABASE

1. Acesse o [Supabase Dashboard](https://app.supabase.com)
2. Entre no seu projeto
3. Navegue para **SQL Editor** no menu lateral
4. Crie uma nova query

### PASSO 2: HABILITAR EXTENSÕES NECESSÁRIAS

Execute o seguinte SQL primeiro:

```sql
-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para busca textual fuzzy
```

### PASSO 3: CRIAR AS TABELAS

#### 3.1 - Tabela de Usuários

```sql
-- Criar tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(50),
    department VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    -- Constraint para garantir username em lowercase
    CONSTRAINT username_lowercase CHECK (username = LOWER(username))
);

-- Comentários para documentação
COMMENT ON TABLE users IS 'Tabela de usuários do sistema AURALIS';
COMMENT ON COLUMN users.password_hash IS 'Senha criptografada usando bcrypt';
COMMENT ON COLUMN users.role IS 'Cargo/função do usuário na empresa';
```

#### 3.2 - Tabela de Reuniões

```sql
-- Criar tabela de reuniões
CREATE TABLE IF NOT EXISTS meetings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled',
    observations TEXT,
    
    -- Campos de transcrição e análise
    transcription_full TEXT,
    transcription_summary TEXT,
    
    -- Campos estruturados para busca eficiente
    key_points TEXT[],
    decisions TEXT[],
    action_items JSONB,
    participants TEXT[],
    
    -- Embeddings para busca semântica
    embedding vector(1536),
    
    -- Metadados
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CHECK (status IN ('scheduled', 'recording', 'paused', 'completed', 'cancelled'))
);

-- Comentários
COMMENT ON TABLE meetings IS 'Histórico de reuniões gravadas';
COMMENT ON COLUMN meetings.embedding IS 'Vetor de embeddings OpenAI para busca semântica';
COMMENT ON COLUMN meetings.action_items IS 'JSON com estrutura: [{action, responsible, deadline}]';
```

#### 3.3 - Tabela de Base de Conhecimento

```sql
-- Criar tabela de base de conhecimento
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    doc_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content_full TEXT NOT NULL,
    content_summary TEXT,
    
    -- Chunks para RAG
    content_chunks JSONB,
    
    -- Categorização e busca
    tags TEXT[],
    department VARCHAR(50),
    category VARCHAR(100),
    
    -- Versionamento
    version VARCHAR(20) DEFAULT '1.0',
    is_current BOOLEAN DEFAULT true,
    
    -- Embeddings
    chunk_embeddings JSONB,
    
    -- Metadados
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Constraints
    CHECK (doc_type IN ('policy', 'procedure', 'manual', 'guideline', 'other'))
);

-- Comentários
COMMENT ON TABLE knowledge_base IS 'Base de conhecimento corporativo para RAG';
COMMENT ON COLUMN knowledge_base.content_chunks IS 'Documento dividido em chunks: [{chunk_id, text, embedding}]';
```

#### 3.4 - Tabela de Interações com IA

```sql
-- Criar tabela de interações com IA
CREATE TABLE IF NOT EXISTS ai_interactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(id) ON DELETE SET NULL,
    
    -- Conteúdo da interação
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    
    -- Contexto utilizado para RAG
    context_used JSONB,
    
    -- Métricas
    response_time_ms INTEGER,
    tokens_used INTEGER,
    model_used VARCHAR(50),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comentários
COMMENT ON TABLE ai_interactions IS 'Histórico de conversas com AURALIS';
COMMENT ON COLUMN ai_interactions.context_used IS 'Contexto RAG: {meetings: [], knowledge: [], chunks: []}';
```

### PASSO 4: CRIAR ÍNDICES PARA OTIMIZAÇÃO

```sql
-- Índices para meetings
CREATE INDEX idx_meetings_user_id ON meetings(user_id);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_created_at ON meetings(created_at DESC);
CREATE INDEX idx_meetings_key_points ON meetings USING GIN(key_points);
CREATE INDEX idx_meetings_participants ON meetings USING GIN(participants);
CREATE INDEX idx_meetings_title_trgm ON meetings USING GIN(title gin_trgm_ops);

-- Índices para knowledge_base
CREATE INDEX idx_knowledge_tags ON knowledge_base USING GIN(tags);
CREATE INDEX idx_knowledge_department ON knowledge_base(department);
CREATE INDEX idx_knowledge_current ON knowledge_base(is_current);
CREATE INDEX idx_knowledge_title_trgm ON knowledge_base USING GIN(title gin_trgm_ops);

-- Índices para ai_interactions
CREATE INDEX idx_ai_interactions_user ON ai_interactions(user_id);
CREATE INDEX idx_ai_interactions_meeting ON ai_interactions(meeting_id);
CREATE INDEX idx_ai_interactions_created ON ai_interactions(created_at DESC);
```

### PASSO 5: CRIAR FUNÇÕES AUXILIARES

```sql
-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualização automática
CREATE TRIGGER update_meetings_updated_at 
    BEFORE UPDATE ON meetings
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at 
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

### PASSO 6: CRIAR FUNÇÕES DE BUSCA RAG

```sql
-- Função para buscar reuniões similares
CREATE OR REPLACE FUNCTION search_similar_meetings(
    query_embedding vector(1536),
    limit_results INTEGER DEFAULT 5
)
RETURNS TABLE (
    meeting_id UUID,
    title VARCHAR,
    summary TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        title,
        transcription_summary,
        1 - (embedding <=> query_embedding) as similarity
    FROM meetings
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> query_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Função para busca textual em reuniões
CREATE OR REPLACE FUNCTION search_meetings_text(
    query_text TEXT,
    user_filter UUID DEFAULT NULL,
    limit_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    meeting_id UUID,
    title VARCHAR,
    highlight TEXT,
    relevance FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        title,
        ts_headline('portuguese', 
            COALESCE(transcription_summary, '') || ' ' || COALESCE(array_to_string(key_points, ' '), ''),
            plainto_tsquery('portuguese', query_text),
            'MaxWords=50, MinWords=25'
        ) as highlight,
        ts_rank(
            to_tsvector('portuguese', 
                COALESCE(title, '') || ' ' || 
                COALESCE(transcription_summary, '') || ' ' || 
                COALESCE(array_to_string(key_points, ' '), '')
            ),
            plainto_tsquery('portuguese', query_text)
        ) as relevance
    FROM meetings
    WHERE (user_filter IS NULL OR user_id = user_filter)
      AND to_tsvector('portuguese', 
            COALESCE(title, '') || ' ' || 
            COALESCE(transcription_summary, '') || ' ' || 
            COALESCE(array_to_string(key_points, ' '), '')
          ) @@ plainto_tsquery('portuguese', query_text)
    ORDER BY relevance DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Função para buscar chunks de conhecimento
CREATE OR REPLACE FUNCTION search_knowledge_chunks(
    query_text TEXT,
    department_filter VARCHAR DEFAULT NULL,
    limit_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    doc_id UUID,
    title VARCHAR,
    chunk_text TEXT,
    chunk_index INTEGER,
    relevance FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.title,
        chunk->>'text' as chunk_text,
        (chunk->>'chunk_id')::INTEGER as chunk_index,
        ts_rank(
            to_tsvector('portuguese', chunk->>'text'),
            plainto_tsquery('portuguese', query_text)
        ) as relevance
    FROM knowledge_base kb,
         jsonb_array_elements(kb.content_chunks) as chunk
    WHERE kb.is_current = true
      AND (department_filter IS NULL OR kb.department = department_filter)
      AND to_tsvector('portuguese', chunk->>'text') @@ plainto_tsquery('portuguese', query_text)
    ORDER BY relevance DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;
```

### PASSO 7: CRIAR VIEWS ÚTEIS

```sql
-- View para estatísticas de usuários
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.full_name,
    u.department,
    COUNT(DISTINCT m.id) as total_meetings,
    COUNT(DISTINCT ai.id) as total_ai_interactions,
    MAX(m.created_at) as last_meeting,
    MAX(ai.created_at) as last_interaction
FROM users u
LEFT JOIN meetings m ON u.id = m.user_id
LEFT JOIN ai_interactions ai ON u.id = ai.user_id
GROUP BY u.id, u.username, u.full_name, u.department;

-- View para reuniões recentes com resumo
CREATE OR REPLACE VIEW recent_meetings_summary AS
SELECT 
    m.id,
    m.title,
    m.start_time,
    m.duration_seconds,
    u.full_name as organizer,
    array_length(m.participants, 1) as participant_count,
    array_length(m.decisions, 1) as decision_count,
    array_length(m.key_points, 1) as key_points_count
FROM meetings m
JOIN users u ON m.user_id = u.id
WHERE m.status = 'completed'
ORDER BY m.start_time DESC
LIMIT 100;
```

### PASSO 8: INSERIR DADOS DE TESTE

```sql
-- Inserir usuário de teste
INSERT INTO users (username, password_hash, email, full_name, role, department)
VALUES 
    ('admin', '$2b$10$YourHashHere', 'admin@auralis.com', 'Administrador', 'Admin', 'TI'),
    ('joao.silva', '$2b$10$YourHashHere', 'joao.silva@empresa.com', 'João Silva', 'Gerente', 'Vendas');

-- Inserir reunião de exemplo
INSERT INTO meetings (
    user_id, 
    title, 
    start_time, 
    end_time,
    duration_seconds,
    status,
    transcription_summary,
    key_points,
    decisions,
    participants
)
SELECT 
    id,
    'Reunião de Kickoff - Projeto Alpha',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days' + INTERVAL '90 minutes',
    5400,
    'completed',
    'Reunião inicial do Projeto Alpha com definição de escopo e responsabilidades.',
    ARRAY['Definir escopo do projeto', 'Estabelecer cronograma', 'Alocar recursos'],
    ARRAY['Aprovar orçamento de R$ 100.000', 'Prazo de entrega: 6 meses'],
    ARRAY['João Silva', 'Maria Santos', 'Pedro Costa']
FROM users 
WHERE username = 'joao.silva'
LIMIT 1;

-- Inserir documento na base de conhecimento
INSERT INTO knowledge_base (
    doc_type,
    title,
    content_full,
    content_summary,
    tags,
    department,
    created_by
)
SELECT 
    'policy',
    'Política de Trabalho Remoto',
    'A empresa permite trabalho remoto híbrido...',
    'Política define regras para trabalho remoto com modelo híbrido.',
    ARRAY['trabalho-remoto', 'rh', 'benefícios'],
    'Recursos Humanos',
    id
FROM users 
WHERE username = 'admin'
LIMIT 1;
```

## 🔍 VERIFICAÇÃO DA IMPLEMENTAÇÃO

### Teste 1: Verificar Tabelas Criadas

```sql
-- Listar todas as tabelas criadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'meetings', 'knowledge_base', 'ai_interactions');
```

### Teste 2: Verificar Índices

```sql
-- Listar índices criados
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('users', 'meetings', 'knowledge_base', 'ai_interactions')
ORDER BY tablename, indexname;
```

### Teste 3: Testar Busca Textual

```sql
-- Testar busca em reuniões
SELECT * FROM search_meetings_text('projeto alpha', NULL, 5);
```

## 🔧 CONFIGURAÇÃO DO RLS (Row Level Security)

Para maior segurança, habilite RLS:

```sql
-- Habilitar RLS em todas as tabelas
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_interactions ENABLE ROW LEVEL SECURITY;

-- Política para users: usuários podem ver apenas seus próprios dados
CREATE POLICY users_policy ON users
    FOR ALL
    USING (auth.uid()::uuid = id);

-- Política para meetings: usuários veem suas próprias reuniões
CREATE POLICY meetings_policy ON meetings
    FOR ALL
    USING (auth.uid()::uuid = user_id);

-- Política para knowledge_base: todos podem ler documentos atuais
CREATE POLICY knowledge_read_policy ON knowledge_base
    FOR SELECT
    USING (is_current = true);

-- Política para ai_interactions: usuários veem suas próprias interações
CREATE POLICY ai_interactions_policy ON ai_interactions
    FOR ALL
    USING (auth.uid()::uuid = user_id);
```

## 📊 MONITORAMENTO E MANUTENÇÃO

### Queries Úteis para Monitoramento

```sql
-- Estatísticas de uso
SELECT 
    'Total Usuários' as metrica,
    COUNT(*) as valor
FROM users
WHERE is_active = true
UNION ALL
SELECT 
    'Total Reuniões',
    COUNT(*)
FROM meetings
WHERE status = 'completed'
UNION ALL
SELECT 
    'Documentos na Base',
    COUNT(*)
FROM knowledge_base
WHERE is_current = true
UNION ALL
SELECT 
    'Interações com IA (últimos 30 dias)',
    COUNT(*)
FROM ai_interactions
WHERE created_at > NOW() - INTERVAL '30 days';

-- Usuários mais ativos
SELECT 
    u.full_name,
    COUNT(DISTINCT m.id) as reunioes,
    COUNT(DISTINCT ai.id) as interacoes_ia
FROM users u
LEFT JOIN meetings m ON u.id = m.user_id
LEFT JOIN ai_interactions ai ON u.id = ai.user_id
GROUP BY u.id, u.full_name
ORDER BY reunioes DESC, interacoes_ia DESC
LIMIT 10;
```

## ⚠️ CONSIDERAÇÕES IMPORTANTES

1. **Segurança**: 
   - Sempre use hashes seguros para senhas (bcrypt)
   - Configure RLS apropriadamente
   - Use service_role_key apenas quando necessário

2. **Performance**:
   - Monitore o tamanho dos embeddings
   - Considere particionar tabelas grandes
   - Use VACUUM regularmente

3. **Backups**:
   - Configure backups automáticos no Supabase
   - Exporte estrutura regularmente

4. **Limites**:
   - Texto máximo no Supabase: 1GB por campo
   - Embeddings vector: até 16000 dimensões
   - JSONB: até 1GB

## 🚀 PRÓXIMOS PASSOS

1. **Integração com Backend**:
   - Configurar cliente Supabase no Python
   - Implementar funções de CRUD
   - Integrar com sistema de agentes

2. **Implementar Embeddings**:
   - Configurar OpenAI para gerar embeddings
   - Criar job para processar transcrições
   - Implementar busca semântica

3. **Testes**:
   - Criar suite de testes
   - Validar performance com dados reais
   - Otimizar queries conforme necessário

## 📞 SUPORTE

Em caso de dúvidas ou problemas:
1. Consulte a [documentação do Supabase](https://supabase.com/docs)
2. Verifique os logs no Dashboard
3. Use o SQL Editor para debug

---

**Última atualização**: Janeiro 2025
**Versão**: 1.0
**Autor**: Sistema AURALIS - Implementação ULTRATHINKS