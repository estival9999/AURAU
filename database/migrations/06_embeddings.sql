-- =====================================================
-- Vector Embeddings Tables
-- Version: 1.0.0
-- Description: Semantic search using pgvector
-- =====================================================

-- Ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables if needed (for clean migration)
DROP TABLE IF EXISTS public.search_embeddings_cache CASCADE;
DROP TABLE IF EXISTS public.document_embeddings CASCADE;
DROP TABLE IF EXISTS public.meeting_embeddings CASCADE;

-- =====================================================
-- 1. MEETING EMBEDDINGS TABLE
-- =====================================================
CREATE TABLE public.meeting_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_tokens INTEGER,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chunk_text_not_empty CHECK (trim(chunk_text) != ''),
    CONSTRAINT valid_chunk_index CHECK (chunk_index >= 0),
    CONSTRAINT valid_metadata CHECK (jsonb_typeof(metadata) = 'object'),
    CONSTRAINT unique_meeting_chunk UNIQUE (meeting_id, chunk_index)
);

-- Create indexes
CREATE INDEX idx_meeting_embeddings_meeting ON public.meeting_embeddings(meeting_id);
CREATE INDEX idx_meeting_embeddings_chunk ON public.meeting_embeddings(meeting_id, chunk_index);

-- Vector similarity search index using IVFFlat
-- Lists = ~sqrt(number of vectors), for 1M vectors use 1000 lists
CREATE INDEX idx_meeting_embeddings_vector ON public.meeting_embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Add comments
COMMENT ON TABLE public.meeting_embeddings IS 'Vector embeddings for meeting content';
COMMENT ON COLUMN public.meeting_embeddings.chunk_tokens IS 'Number of tokens in this chunk';
COMMENT ON COLUMN public.meeting_embeddings.embedding IS 'OpenAI embedding vector (1536 dimensions)';

-- =====================================================
-- 2. DOCUMENT EMBEDDINGS TABLE
-- =====================================================
CREATE TABLE public.document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_tokens INTEGER,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chunk_text_not_empty CHECK (trim(chunk_text) != ''),
    CONSTRAINT valid_chunk_index CHECK (chunk_index >= 0),
    CONSTRAINT valid_metadata CHECK (jsonb_typeof(metadata) = 'object'),
    CONSTRAINT unique_document_chunk UNIQUE (document_id, chunk_index)
);

-- Create indexes
CREATE INDEX idx_document_embeddings_document ON public.document_embeddings(document_id);
CREATE INDEX idx_document_embeddings_chunk ON public.document_embeddings(document_id, chunk_index);

-- Vector similarity search index
CREATE INDEX idx_document_embeddings_vector ON public.document_embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Add comments
COMMENT ON TABLE public.document_embeddings IS 'Vector embeddings for knowledge documents';

-- =====================================================
-- 3. SEARCH EMBEDDINGS CACHE TABLE
-- =====================================================
CREATE TABLE public.search_embeddings_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT UNIQUE NOT NULL,
    query_hash TEXT GENERATED ALWAYS AS (md5(query_text)) STORED,
    embedding vector(1536),
    model TEXT DEFAULT 'text-embedding-ada-002',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 1,
    
    -- Constraints
    CONSTRAINT query_text_not_empty CHECK (trim(query_text) != '')
);

-- Create indexes
CREATE INDEX idx_search_cache_hash ON public.search_embeddings_cache(query_hash);
CREATE INDEX idx_search_cache_last_used ON public.search_embeddings_cache(last_used DESC);
CREATE INDEX idx_search_cache_created ON public.search_embeddings_cache(created_at DESC);

-- Add comments
COMMENT ON TABLE public.search_embeddings_cache IS 'Cache for search query embeddings';
COMMENT ON COLUMN public.search_embeddings_cache.query_hash IS 'MD5 hash of query for fast lookup';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Auto-update updated_at
CREATE TRIGGER update_meeting_embeddings_updated_at 
    BEFORE UPDATE ON public.meeting_embeddings
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_embeddings_updated_at 
    BEFORE UPDATE ON public.document_embeddings
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Update last_used and use_count for cache hits
CREATE OR REPLACE FUNCTION update_search_cache_usage()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_used = CURRENT_TIMESTAMP;
    NEW.use_count = OLD.use_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cache_on_use
    BEFORE UPDATE ON public.search_embeddings_cache
    FOR EACH ROW
    WHEN (OLD.embedding IS NOT DISTINCT FROM NEW.embedding)
    EXECUTE FUNCTION update_search_cache_usage();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to search meetings by semantic similarity
CREATE OR REPLACE FUNCTION public.search_meetings_semantic(
    p_query_embedding vector(1536),
    p_limit INTEGER DEFAULT 10,
    p_threshold REAL DEFAULT 0.7
)
RETURNS TABLE (
    meeting_id UUID,
    chunk_text TEXT,
    chunk_index INTEGER,
    similarity REAL,
    meeting_title TEXT,
    meeting_date TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        me.meeting_id,
        me.chunk_text,
        me.chunk_index,
        1 - (me.embedding <=> p_query_embedding) AS similarity,
        m.title AS meeting_title,
        m.actual_start AS meeting_date
    FROM public.meeting_embeddings me
    JOIN public.meetings m ON me.meeting_id = m.id
    WHERE 1 - (me.embedding <=> p_query_embedding) >= p_threshold
    ORDER BY me.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to search documents by semantic similarity
CREATE OR REPLACE FUNCTION public.search_documents_semantic(
    p_query_embedding vector(1536),
    p_limit INTEGER DEFAULT 10,
    p_threshold REAL DEFAULT 0.7,
    p_document_types document_type[] DEFAULT NULL
)
RETURNS TABLE (
    document_id UUID,
    chunk_text TEXT,
    chunk_index INTEGER,
    similarity REAL,
    document_title TEXT,
    document_type document_type
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.document_id,
        de.chunk_text,
        de.chunk_index,
        1 - (de.embedding <=> p_query_embedding) AS similarity,
        d.title AS document_title,
        d.document_type
    FROM public.document_embeddings de
    JOIN public.knowledge_documents d ON de.document_id = d.id
    WHERE 
        1 - (de.embedding <=> p_query_embedding) >= p_threshold
        AND d.is_published = TRUE
        AND d.is_archived = FALSE
        AND (p_document_types IS NULL OR d.document_type = ANY(p_document_types))
    ORDER BY de.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to find similar meetings
CREATE OR REPLACE FUNCTION public.find_similar_meetings(
    p_meeting_id UUID,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    similar_meeting_id UUID,
    title TEXT,
    similarity REAL,
    common_chunks INTEGER
) AS $$
DECLARE
    v_embeddings vector(1536)[];
BEGIN
    -- Get embeddings for the source meeting
    SELECT array_agg(embedding)
    INTO v_embeddings
    FROM public.meeting_embeddings
    WHERE meeting_id = p_meeting_id;
    
    IF v_embeddings IS NULL THEN
        RETURN;
    END IF;
    
    -- Find similar meetings
    RETURN QUERY
    WITH similarity_scores AS (
        SELECT 
            me2.meeting_id,
            AVG(1 - (me1.embedding <=> me2.embedding)) AS avg_similarity,
            COUNT(*) AS common_chunks
        FROM public.meeting_embeddings me1
        CROSS JOIN public.meeting_embeddings me2
        WHERE 
            me1.meeting_id = p_meeting_id
            AND me2.meeting_id != p_meeting_id
            AND 1 - (me1.embedding <=> me2.embedding) > 0.7
        GROUP BY me2.meeting_id
    )
    SELECT 
        ss.meeting_id AS similar_meeting_id,
        m.title,
        ss.avg_similarity AS similarity,
        ss.common_chunks::INTEGER
    FROM similarity_scores ss
    JOIN public.meetings m ON ss.meeting_id = m.id
    ORDER BY ss.avg_similarity DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to chunk text for embedding
CREATE OR REPLACE FUNCTION public.chunk_text_for_embedding(
    p_text TEXT,
    p_chunk_size INTEGER DEFAULT 1000,
    p_overlap INTEGER DEFAULT 200
)
RETURNS TABLE (
    chunk_index INTEGER,
    chunk_text TEXT,
    start_position INTEGER,
    end_position INTEGER
) AS $$
DECLARE
    v_text_length INTEGER;
    v_current_pos INTEGER := 1;
    v_chunk_index INTEGER := 0;
BEGIN
    v_text_length := length(p_text);
    
    WHILE v_current_pos <= v_text_length LOOP
        chunk_index := v_chunk_index;
        start_position := v_current_pos;
        end_position := LEAST(v_current_pos + p_chunk_size - 1, v_text_length);
        
        -- Extract chunk
        chunk_text := substring(p_text FROM v_current_pos FOR p_chunk_size);
        
        -- Try to break at sentence boundary
        IF end_position < v_text_length THEN
            -- Look for sentence end near chunk boundary
            FOR i IN REVERSE end_position..GREATEST(end_position - 100, v_current_pos) LOOP
                IF substring(p_text FROM i FOR 1) IN ('.', '!', '?') THEN
                    end_position := i;
                    chunk_text := substring(p_text FROM v_current_pos FOR end_position - v_current_pos + 1);
                    EXIT;
                END IF;
            END LOOP;
        END IF;
        
        RETURN NEXT;
        
        -- Move to next chunk with overlap
        v_current_pos := end_position - p_overlap + 1;
        v_chunk_index := v_chunk_index + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to cleanup old cache entries
CREATE OR REPLACE FUNCTION public.cleanup_embedding_cache(
    p_days_old INTEGER DEFAULT 30,
    p_min_use_count INTEGER DEFAULT 2
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.search_embeddings_cache
    WHERE 
        last_used < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_old
        AND use_count < p_min_use_count;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS
ALTER TABLE public.meeting_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_embeddings_cache ENABLE ROW LEVEL SECURITY;

-- Meeting embeddings policies (inherit from meeting permissions)
CREATE POLICY "Users can view embeddings of accessible meetings" 
    ON public.meeting_embeddings FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.meetings m
            WHERE m.id = meeting_embeddings.meeting_id
            AND (
                m.organizer_id = auth.uid() 
                OR EXISTS (
                    SELECT 1 FROM public.meeting_participants mp
                    WHERE mp.meeting_id = m.id AND mp.user_id = auth.uid()
                )
            )
        )
    );

-- Document embeddings policies (inherit from document permissions)
CREATE POLICY "Users can view embeddings of accessible documents" 
    ON public.document_embeddings FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.knowledge_documents d
            WHERE d.id = document_embeddings.document_id
            AND (d.is_published = TRUE OR d.author_id = auth.uid())
        )
    );

-- Cache policies (global access for authenticated users)
CREATE POLICY "Authenticated users can use embedding cache" 
    ON public.search_embeddings_cache FOR ALL 
    USING (auth.uid() IS NOT NULL)
    WITH CHECK (auth.uid() IS NOT NULL);

-- =====================================================
-- PERFORMANCE VIEWS
-- =====================================================

-- View for embedding statistics
CREATE OR REPLACE VIEW public.embedding_statistics AS
SELECT 
    'meetings' AS content_type,
    COUNT(DISTINCT meeting_id) AS total_items,
    COUNT(*) AS total_chunks,
    AVG(chunk_tokens) AS avg_tokens_per_chunk,
    MAX(chunk_index) + 1 AS max_chunks_per_item,
    pg_size_pretty(pg_total_relation_size('public.meeting_embeddings')) AS table_size
FROM public.meeting_embeddings

UNION ALL

SELECT 
    'documents' AS content_type,
    COUNT(DISTINCT document_id) AS total_items,
    COUNT(*) AS total_chunks,
    AVG(chunk_tokens) AS avg_tokens_per_chunk,
    MAX(chunk_index) + 1 AS max_chunks_per_item,
    pg_size_pretty(pg_total_relation_size('public.document_embeddings')) AS table_size
FROM public.document_embeddings;

-- Grant permissions
GRANT SELECT ON public.embedding_statistics TO authenticated;