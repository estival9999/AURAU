-- ============================================================================
-- 🚀 SCRIPT SQL DEFINITIVO PARA SUPABASE - SISTEMA AURALIS
-- ============================================================================
-- Autor: Sistema AURALIS - Implementação ULTRATHINKS
-- Data: Janeiro 2025
-- Versão: 2.0 - DEFINITIVO
-- ============================================================================

-- ============================================================================
-- IMPORTANTE: Execute este script em partes se necessário
-- Parte 1: Limpeza (linhas 15-30)
-- Parte 2: Extensões (linhas 35-40)
-- Parte 3: Tabelas e resto (linha 45 em diante)
-- ============================================================================

-- ============================================================================
-- PARTE 1: LIMPEZA SEGURA (Execute primeiro, ignore erros)
-- ============================================================================
-- Os comandos abaixo podem gerar erros se os objetos não existirem
-- Isso é normal e esperado - continue com a execução

DROP VIEW IF EXISTS user_stats CASCADE;
DROP VIEW IF EXISTS recent_meetings_summary CASCADE;
DROP FUNCTION IF EXISTS search_similar_meetings CASCADE;
DROP FUNCTION IF EXISTS search_meetings_text CASCADE;
DROP FUNCTION IF EXISTS search_knowledge_chunks CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
DROP TABLE IF EXISTS ai_interactions CASCADE;
DROP TABLE IF EXISTS knowledge_base CASCADE;
DROP TABLE IF EXISTS meetings CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- PARTE 2: HABILITAR EXTENSÕES NECESSÁRIAS
-- ============================================================================

-- Extensões necessárias para o sistema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- PARTE 3: CRIAR ESTRUTURA COMPLETA DO BANCO
-- ============================================================================

-- ----------------------------------------------------------------------------
-- TABELA 1: USERS (Usuários do Sistema)
-- ----------------------------------------------------------------------------
CREATE TABLE users (
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
    
    CONSTRAINT username_lowercase CHECK (username = LOWER(username))
);

COMMENT ON TABLE users IS 'Tabela de usuários do sistema AURALIS';
COMMENT ON COLUMN users.password_hash IS 'Senha criptografada usando bcrypt';
COMMENT ON COLUMN users.role IS 'Cargo/função do usuário na empresa';
COMMENT ON COLUMN users.department IS 'Departamento ou área de atuação';

-- ----------------------------------------------------------------------------
-- TABELA 2: MEETINGS (Reuniões)
-- ----------------------------------------------------------------------------
CREATE TABLE meetings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled',
    observations TEXT,
    transcription_full TEXT,
    transcription_summary TEXT,
    key_points TEXT[],
    decisions TEXT[],
    action_items JSONB,
    participants TEXT[],
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (status IN ('scheduled', 'recording', 'paused', 'completed', 'cancelled'))
);

COMMENT ON TABLE meetings IS 'Histórico de reuniões gravadas com transcrições e análises';
COMMENT ON COLUMN meetings.embedding IS 'Vetor de embeddings OpenAI para busca semântica';
COMMENT ON COLUMN meetings.action_items IS 'JSON com estrutura: [{action, responsible, deadline}]';
COMMENT ON COLUMN meetings.key_points IS 'Array com os principais pontos discutidos na reunião';
COMMENT ON COLUMN meetings.decisions IS 'Array com as decisões tomadas durante a reunião';

-- ----------------------------------------------------------------------------
-- TABELA 3: KNOWLEDGE_BASE (Base de Conhecimento)
-- ----------------------------------------------------------------------------
CREATE TABLE knowledge_base (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    doc_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content_full TEXT NOT NULL,
    content_summary TEXT,
    content_chunks JSONB,
    tags TEXT[],
    department VARCHAR(50),
    category VARCHAR(100),
    version VARCHAR(20) DEFAULT '1.0',
    is_current BOOLEAN DEFAULT true,
    chunk_embeddings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    CHECK (doc_type IN ('policy', 'procedure', 'manual', 'guideline', 'other'))
);

COMMENT ON TABLE knowledge_base IS 'Base de conhecimento corporativo para RAG';
COMMENT ON COLUMN knowledge_base.content_chunks IS 'Documento dividido em chunks: [{chunk_id, text, embedding}]';
COMMENT ON COLUMN knowledge_base.chunk_embeddings IS 'Embeddings para cada chunk do documento';

-- ----------------------------------------------------------------------------
-- TABELA 4: AI_INTERACTIONS (Interações com IA)
-- ----------------------------------------------------------------------------
CREATE TABLE ai_interactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES meetings(id) ON DELETE SET NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    context_used JSONB,
    response_time_ms INTEGER,
    tokens_used INTEGER,
    model_used VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE ai_interactions IS 'Histórico de conversas com AURALIS';
COMMENT ON COLUMN ai_interactions.context_used IS 'Contexto RAG: {meetings: [], knowledge: [], chunks: []}';

-- ============================================================================
-- PARTE 4: CRIAR TODOS OS ÍNDICES
-- ============================================================================

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

-- ============================================================================
-- PARTE 5: CRIAR FUNÇÕES E TRIGGERS
-- ============================================================================

-- Função para atualizar timestamp automaticamente
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

-- ============================================================================
-- PARTE 6: FUNÇÕES DE BUSCA RAG
-- ============================================================================

-- Buscar reuniões similares usando embeddings
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

-- Busca textual em reuniões
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

-- Buscar chunks de conhecimento
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

-- ============================================================================
-- PARTE 7: CRIAR VIEWS ÚTEIS
-- ============================================================================

-- View de estatísticas de usuários
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

-- View de reuniões recentes
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

-- ============================================================================
-- PARTE 8: DADOS DE TESTE INICIAIS
-- ============================================================================

-- Inserir usuário admin para testes
INSERT INTO users (username, password_hash, email, full_name, role, department)
VALUES 
    ('admin', '$2b$10$K.0HwpsoPDGaB/atFBmmXOGTw4ceeg33.WrxJx/FeC9.gCyYvIbs6', 'admin@auralis.com', 'Administrador', 'Admin', 'TI')
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- PARTE 9: VERIFICAÇÃO FINAL
-- ============================================================================

-- Verificar tabelas criadas
SELECT 
    table_name,
    CASE 
        WHEN table_name IN ('users', 'meetings', 'knowledge_base', 'ai_interactions') 
        THEN '✅ Criada com sucesso'
        ELSE '❌ Erro'
    END as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'meetings', 'knowledge_base', 'ai_interactions')
ORDER BY table_name;

-- Contar total de objetos criados
SELECT 
    'Resumo da instalação:' as info,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('users', 'meetings', 'knowledge_base', 'ai_interactions')) || ' tabelas, ' ||
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND tablename IN ('users', 'meetings', 'knowledge_base', 'ai_interactions')) || ' índices, ' ||
    (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public' AND routine_type = 'FUNCTION') || ' funções, ' ||
    (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public') || ' views' as total;

-- ============================================================================
-- FIM DO SCRIPT - SISTEMA AURALIS INSTALADO COM SUCESSO!
-- ============================================================================