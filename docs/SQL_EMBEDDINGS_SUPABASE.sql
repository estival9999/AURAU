-- ============================================================================
-- SQL PARA IMPLEMENTAÇÃO DE EMBEDDINGS E BUSCA SEMÂNTICA NO SUPABASE
-- Sistema AURALIS - RAG (Retrieval Augmented Generation)
-- ============================================================================

-- Habilitar extensão vector para trabalhar com embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- TABELAS PARA ARMAZENAMENTO DE EMBEDDINGS
-- ============================================================================

-- Embeddings de reuniões
CREATE TABLE IF NOT EXISTS meeting_embeddings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL, -- -1 para embedding principal, 0+ para chunks
    chunk_text TEXT NOT NULL, -- Texto do chunk (primeiros 500 chars)
    embedding vector(1536), -- Vetor de embedding (OpenAI usa 1536 dimensões)
    metadata JSONB DEFAULT '{}', -- Metadados adicionais
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Índice único para evitar duplicatas
    UNIQUE(meeting_id, chunk_index)
);

-- Embeddings da base de conhecimento
CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    doc_id UUID NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(doc_id, chunk_index)
);

-- ============================================================================
-- ÍNDICES PARA OTIMIZAÇÃO DE BUSCA
-- ============================================================================

-- Índice para busca vetorial rápida em reuniões
CREATE INDEX idx_meeting_embeddings_vector ON meeting_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Índice para busca vetorial rápida em documentos
CREATE INDEX idx_knowledge_embeddings_vector ON knowledge_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Índices para filtros comuns
CREATE INDEX idx_meeting_embeddings_meeting_id ON meeting_embeddings(meeting_id);
CREATE INDEX idx_knowledge_embeddings_doc_id ON knowledge_embeddings(doc_id);

-- ============================================================================
-- FUNÇÕES PARA BUSCA SEMÂNTICA
-- ============================================================================

-- Buscar reuniões similares usando embeddings
CREATE OR REPLACE FUNCTION buscar_reunioes_similares(
    query_embedding vector(1536),
    match_count INT DEFAULT 5,
    user_filter UUID DEFAULT NULL,
    start_date DATE DEFAULT NULL,
    end_date DATE DEFAULT NULL
)
RETURNS TABLE (
    meeting_id UUID,
    chunk_text TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (me.meeting_id)
        me.meeting_id,
        me.chunk_text,
        1 - (me.embedding <=> query_embedding) as similarity,
        me.metadata
    FROM meeting_embeddings me
    INNER JOIN meetings m ON m.id = me.meeting_id
    WHERE 
        -- Filtro por usuário se fornecido
        (user_filter IS NULL OR m.user_id = user_filter)
        -- Filtro por data se fornecido
        AND (start_date IS NULL OR m.start_time::date >= start_date)
        AND (end_date IS NULL OR m.start_time::date <= end_date)
    ORDER BY me.meeting_id, me.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Buscar documentos similares na base de conhecimento
CREATE OR REPLACE FUNCTION buscar_documentos_similares(
    query_embedding vector(1536),
    match_count INT DEFAULT 5,
    department_filter VARCHAR DEFAULT NULL,
    doc_type_filter VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    doc_id UUID,
    chunk_text TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ke.doc_id,
        ke.chunk_text,
        1 - (ke.embedding <=> query_embedding) as similarity,
        ke.metadata
    FROM knowledge_embeddings ke
    INNER JOIN knowledge_base kb ON kb.id = ke.doc_id
    WHERE 
        kb.is_current = true
        AND (department_filter IS NULL OR kb.department = department_filter)
        AND (doc_type_filter IS NULL OR kb.doc_type = doc_type_filter)
    ORDER BY ke.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Busca híbrida: combina busca vetorial com busca textual
CREATE OR REPLACE FUNCTION busca_hibrida_reunioes(
    query_text TEXT,
    query_embedding vector(1536),
    match_count INT DEFAULT 10,
    user_filter UUID DEFAULT NULL,
    weight_semantic FLOAT DEFAULT 0.7,  -- Peso da busca semântica (0-1)
    weight_keyword FLOAT DEFAULT 0.3    -- Peso da busca por palavras-chave (0-1)
)
RETURNS TABLE (
    meeting_id UUID,
    title VARCHAR,
    similarity_score FLOAT,
    chunk_text TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_search AS (
        -- Busca semântica por embeddings
        SELECT 
            me.meeting_id,
            m.title,
            1 - (me.embedding <=> query_embedding) as semantic_similarity,
            me.chunk_text,
            me.metadata
        FROM meeting_embeddings me
        INNER JOIN meetings m ON m.id = me.meeting_id
        WHERE (user_filter IS NULL OR m.user_id = user_filter)
        ORDER BY me.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    keyword_search AS (
        -- Busca por palavras-chave
        SELECT 
            m.id as meeting_id,
            m.title,
            ts_rank(
                to_tsvector('portuguese', 
                    COALESCE(m.title, '') || ' ' || 
                    COALESCE(m.transcription_summary, '') || ' ' || 
                    COALESCE(array_to_string(m.key_points, ' '), '')
                ),
                plainto_tsquery('portuguese', query_text)
            ) as keyword_relevance
        FROM meetings m
        WHERE 
            (user_filter IS NULL OR m.user_id = user_filter)
            AND to_tsvector('portuguese', 
                COALESCE(m.title, '') || ' ' || 
                COALESCE(m.transcription_summary, '') || ' ' || 
                COALESCE(array_to_string(m.key_points, ' '), '')
            ) @@ plainto_tsquery('portuguese', query_text)
        LIMIT match_count * 2
    )
    -- Combinar resultados com pesos
    SELECT DISTINCT ON (COALESCE(s.meeting_id, k.meeting_id))
        COALESCE(s.meeting_id, k.meeting_id) as meeting_id,
        COALESCE(s.title, k.title) as title,
        (
            COALESCE(s.semantic_similarity * weight_semantic, 0) + 
            COALESCE(k.keyword_relevance * weight_keyword, 0)
        ) as similarity_score,
        s.chunk_text,
        s.metadata
    FROM semantic_search s
    FULL OUTER JOIN keyword_search k ON s.meeting_id = k.meeting_id
    ORDER BY COALESCE(s.meeting_id, k.meeting_id), similarity_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNÇÕES AUXILIARES
-- ============================================================================

-- Função para calcular similaridade entre dois textos (via embeddings)
CREATE OR REPLACE FUNCTION calcular_similaridade_textos(
    text1 TEXT,
    text2 TEXT,
    embedding1 vector(1536),
    embedding2 vector(1536)
)
RETURNS FLOAT AS $$
BEGIN
    -- Retorna similaridade coseno (1 = idêntico, 0 = ortogonal)
    RETURN 1 - (embedding1 <=> embedding2);
END;
$$ LANGUAGE plpgsql;

-- Função para agrupar resultados similares
CREATE OR REPLACE FUNCTION agrupar_resultados_similares(
    resultados JSONB[],
    threshold_similaridade FLOAT DEFAULT 0.85
)
RETURNS JSONB[] AS $$
DECLARE
    grupos JSONB[] := '{}';
    resultado JSONB;
    grupo_encontrado BOOLEAN;
    grupo JSONB;
    i INT;
BEGIN
    FOREACH resultado IN ARRAY resultados
    LOOP
        grupo_encontrado := FALSE;
        
        -- Verificar se resultado pertence a algum grupo existente
        FOR i IN 1..array_length(grupos, 1)
        LOOP
            grupo := grupos[i];
            
            -- Se similaridade alta, adicionar ao grupo
            IF (resultado->>'similarity')::FLOAT >= threshold_similaridade THEN
                grupos[i] := jsonb_set(
                    grupo,
                    '{items}',
                    (grupo->'items') || jsonb_build_array(resultado)
                );
                grupo_encontrado := TRUE;
                EXIT;
            END IF;
        END LOOP;
        
        -- Se não encontrou grupo, criar novo
        IF NOT grupo_encontrado THEN
            grupos := grupos || jsonb_build_object(
                'representante', resultado,
                'items', jsonb_build_array(resultado)
            );
        END IF;
    END LOOP;
    
    RETURN grupos;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS ÚTEIS
-- ============================================================================

-- View de estatísticas de embeddings
CREATE OR REPLACE VIEW v_estatisticas_embeddings AS
SELECT 
    'reunioes' as tipo,
    COUNT(DISTINCT meeting_id) as num_documentos,
    COUNT(*) as num_embeddings,
    AVG(LENGTH(chunk_text)) as tamanho_medio_chunk,
    MAX(chunk_index) as max_chunks_por_doc
FROM meeting_embeddings
UNION ALL
SELECT 
    'conhecimento' as tipo,
    COUNT(DISTINCT doc_id) as num_documentos,
    COUNT(*) as num_embeddings,
    AVG(LENGTH(chunk_text)) as tamanho_medio_chunk,
    MAX(chunk_index) as max_chunks_por_doc
FROM knowledge_embeddings;

-- View de documentos sem embeddings (para manutenção)
CREATE OR REPLACE VIEW v_documentos_sem_embeddings AS
SELECT 
    'reuniao' as tipo,
    id,
    title,
    created_at
FROM meetings m
WHERE NOT EXISTS (
    SELECT 1 FROM meeting_embeddings me WHERE me.meeting_id = m.id
)
UNION ALL
SELECT 
    'conhecimento' as tipo,
    id,
    title,
    created_at
FROM knowledge_base kb
WHERE kb.is_current = true
  AND NOT EXISTS (
    SELECT 1 FROM knowledge_embeddings ke WHERE ke.doc_id = kb.id
);

-- ============================================================================
-- POLÍTICAS DE SEGURANÇA (RLS)
-- ============================================================================

-- Habilitar RLS nas tabelas de embeddings
ALTER TABLE meeting_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_embeddings ENABLE ROW LEVEL SECURITY;

-- Política para meeting_embeddings - usuários veem apenas embeddings de suas reuniões
CREATE POLICY "meeting_embeddings_select_policy" ON meeting_embeddings
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM meetings m 
            WHERE m.id = meeting_embeddings.meeting_id 
            AND m.user_id = auth.uid()
        )
    );

-- Política para knowledge_embeddings - todos podem ver (base compartilhada)
CREATE POLICY "knowledge_embeddings_select_policy" ON knowledge_embeddings
    FOR SELECT
    USING (true);

-- Políticas de inserção/atualização - apenas sistema
CREATE POLICY "embeddings_system_only_insert" ON meeting_embeddings
    FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "embeddings_system_only_insert_kb" ON knowledge_embeddings
    FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- ============================================================================
-- GRANT PERMISSÕES
-- ============================================================================

-- Permissões para as funções
GRANT EXECUTE ON FUNCTION buscar_reunioes_similares TO authenticated;
GRANT EXECUTE ON FUNCTION buscar_documentos_similares TO authenticated;
GRANT EXECUTE ON FUNCTION busca_hibrida_reunioes TO authenticated;

-- Permissões para views
GRANT SELECT ON v_estatisticas_embeddings TO authenticated;
GRANT SELECT ON v_documentos_sem_embeddings TO authenticated;

-- ============================================================================
-- COMENTÁRIOS DE DOCUMENTAÇÃO
-- ============================================================================

COMMENT ON TABLE meeting_embeddings IS 'Armazena embeddings de reuniões para busca semântica';
COMMENT ON TABLE knowledge_embeddings IS 'Armazena embeddings da base de conhecimento';
COMMENT ON FUNCTION buscar_reunioes_similares IS 'Busca reuniões similares usando similaridade vetorial';
COMMENT ON FUNCTION buscar_documentos_similares IS 'Busca documentos similares na base de conhecimento';
COMMENT ON FUNCTION busca_hibrida_reunioes IS 'Combina busca semântica e textual com pesos configuráveis';