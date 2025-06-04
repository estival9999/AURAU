-- =====================================================
-- Knowledge Base Tables
-- Version: 1.0.0
-- Description: Document management and version control
-- =====================================================

-- Drop existing tables if needed (for clean migration)
DROP TABLE IF EXISTS public.document_revisions CASCADE;
DROP TABLE IF EXISTS public.knowledge_documents CASCADE;

-- =====================================================
-- 1. KNOWLEDGE DOCUMENTS TABLE
-- =====================================================
CREATE TABLE public.knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    document_type document_type NOT NULL,
    source_type source_type NOT NULL,
    source_meeting_id UUID REFERENCES public.meetings(id) ON DELETE SET NULL,
    author_id UUID REFERENCES public.users(id),
    version INTEGER DEFAULT 1,
    tags TEXT[] DEFAULT '{}',
    category TEXT,
    is_published BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT title_not_empty CHECK (trim(title) != ''),
    CONSTRAINT content_not_empty CHECK (trim(content) != ''),
    CONSTRAINT valid_version CHECK (version > 0),
    CONSTRAINT valid_metadata CHECK (jsonb_typeof(metadata) = 'object')
);

-- Create indexes
CREATE INDEX idx_documents_title ON public.knowledge_documents(title);
CREATE INDEX idx_documents_type ON public.knowledge_documents(document_type);
CREATE INDEX idx_documents_source_type ON public.knowledge_documents(source_type);
CREATE INDEX idx_documents_author ON public.knowledge_documents(author_id);
CREATE INDEX idx_documents_source_meeting ON public.knowledge_documents(source_meeting_id);
CREATE INDEX idx_documents_published ON public.knowledge_documents(is_published);
CREATE INDEX idx_documents_archived ON public.knowledge_documents(is_archived);
CREATE INDEX idx_documents_category ON public.knowledge_documents(category);
CREATE INDEX idx_documents_created ON public.knowledge_documents(created_at DESC);
CREATE INDEX idx_documents_tags ON public.knowledge_documents USING GIN(tags);

-- Full-text search indexes
CREATE INDEX idx_documents_title_fts ON public.knowledge_documents 
    USING GIN(to_tsvector('portuguese', title));
CREATE INDEX idx_documents_content_fts ON public.knowledge_documents 
    USING GIN(to_tsvector('portuguese', content));
CREATE INDEX idx_documents_combined_fts ON public.knowledge_documents 
    USING GIN(to_tsvector('portuguese', title || ' ' || content));

-- Add comments
COMMENT ON TABLE public.knowledge_documents IS 'Knowledge base documents and articles';
COMMENT ON COLUMN public.knowledge_documents.source_meeting_id IS 'Link to meeting if document was generated from it';
COMMENT ON COLUMN public.knowledge_documents.version IS 'Current version number';
COMMENT ON COLUMN public.knowledge_documents.metadata IS 'Additional metadata in JSON format';

-- =====================================================
-- 2. DOCUMENT REVISIONS TABLE
-- =====================================================
CREATE TABLE public.document_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.knowledge_documents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    changed_by UUID REFERENCES public.users(id),
    change_summary TEXT,
    diff_content JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT title_not_empty CHECK (trim(title) != ''),
    CONSTRAINT content_not_empty CHECK (trim(content) != ''),
    CONSTRAINT valid_version CHECK (version > 0),
    CONSTRAINT unique_document_version UNIQUE (document_id, version)
);

-- Create indexes
CREATE INDEX idx_revisions_document ON public.document_revisions(document_id);
CREATE INDEX idx_revisions_version ON public.document_revisions(document_id, version DESC);
CREATE INDEX idx_revisions_changed_by ON public.document_revisions(changed_by);
CREATE INDEX idx_revisions_created ON public.document_revisions(created_at DESC);

-- Add comments
COMMENT ON TABLE public.document_revisions IS 'Version history for knowledge documents';
COMMENT ON COLUMN public.document_revisions.change_summary IS 'Summary of what changed in this revision';
COMMENT ON COLUMN public.document_revisions.diff_content IS 'JSON diff of changes from previous version';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Auto-update updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON public.knowledge_documents
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create revision on document update
CREATE OR REPLACE FUNCTION create_document_revision()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create revision if content or title changed
    IF OLD.content != NEW.content OR OLD.title != NEW.title THEN
        -- Save current version as revision before update
        INSERT INTO public.document_revisions (
            document_id, version, title, content, summary,
            changed_by, change_summary
        ) VALUES (
            OLD.id, OLD.version, OLD.title, OLD.content, OLD.summary,
            auth.uid(), 'Document updated'
        );
        
        -- Increment version
        NEW.version = OLD.version + 1;
        NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER document_version_control
    BEFORE UPDATE ON public.knowledge_documents
    FOR EACH ROW
    WHEN (OLD.content IS DISTINCT FROM NEW.content OR OLD.title IS DISTINCT FROM NEW.title)
    EXECUTE FUNCTION create_document_revision();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to create document from meeting
CREATE OR REPLACE FUNCTION public.create_document_from_meeting(
    p_meeting_id UUID,
    p_document_type document_type,
    p_title TEXT,
    p_content TEXT,
    p_tags TEXT[] DEFAULT '{}'
)
RETURNS public.knowledge_documents AS $$
DECLARE
    new_document public.knowledge_documents;
    v_author_id UUID;
BEGIN
    -- Get meeting organizer as document author
    SELECT organizer_id INTO v_author_id
    FROM public.meetings
    WHERE id = p_meeting_id;
    
    -- Create document
    INSERT INTO public.knowledge_documents (
        title, content, document_type, source_type,
        source_meeting_id, author_id, tags
    ) VALUES (
        p_title, p_content, p_document_type, 'meeting',
        p_meeting_id, v_author_id, p_tags
    )
    RETURNING * INTO new_document;
    
    RETURN new_document;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to search documents
CREATE OR REPLACE FUNCTION public.search_knowledge_documents(
    p_query TEXT,
    p_document_types document_type[] DEFAULT NULL,
    p_tags TEXT[] DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    document_id UUID,
    title TEXT,
    summary TEXT,
    document_type document_type,
    tags TEXT[],
    relevance REAL,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id AS document_id,
        d.title,
        d.summary,
        d.document_type,
        d.tags,
        ts_rank(
            to_tsvector('portuguese', d.title || ' ' || d.content),
            plainto_tsquery('portuguese', p_query)
        ) AS relevance,
        d.created_at
    FROM public.knowledge_documents d
    WHERE 
        d.is_published = TRUE
        AND d.is_archived = FALSE
        AND (
            p_query IS NULL OR
            to_tsvector('portuguese', d.title || ' ' || d.content) @@ 
            plainto_tsquery('portuguese', p_query)
        )
        AND (p_document_types IS NULL OR d.document_type = ANY(p_document_types))
        AND (p_tags IS NULL OR d.tags && p_tags)
    ORDER BY relevance DESC, d.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get document with revision history
CREATE OR REPLACE FUNCTION public.get_document_history(
    p_document_id UUID
)
RETURNS TABLE (
    version INTEGER,
    title TEXT,
    changed_by_name TEXT,
    change_summary TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dr.version,
        dr.title,
        u.full_name AS changed_by_name,
        dr.change_summary,
        dr.created_at
    FROM public.document_revisions dr
    LEFT JOIN public.users u ON dr.changed_by = u.id
    WHERE dr.document_id = p_document_id
    
    UNION ALL
    
    SELECT 
        d.version,
        d.title,
        u.full_name AS changed_by_name,
        'Current version' AS change_summary,
        d.updated_at AS created_at
    FROM public.knowledge_documents d
    LEFT JOIN public.users u ON d.author_id = u.id
    WHERE d.id = p_document_id
    
    ORDER BY version DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to restore document revision
CREATE OR REPLACE FUNCTION public.restore_document_revision(
    p_document_id UUID,
    p_version INTEGER
)
RETURNS public.knowledge_documents AS $$
DECLARE
    v_revision public.document_revisions;
    restored_document public.knowledge_documents;
BEGIN
    -- Get the revision
    SELECT * INTO v_revision
    FROM public.document_revisions
    WHERE document_id = p_document_id AND version = p_version;
    
    IF v_revision IS NULL THEN
        RAISE EXCEPTION 'Revision not found';
    END IF;
    
    -- Update document with revision content
    UPDATE public.knowledge_documents
    SET 
        title = v_revision.title,
        content = v_revision.content,
        summary = v_revision.summary
    WHERE id = p_document_id
    RETURNING * INTO restored_document;
    
    RETURN restored_document;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to generate document summary
CREATE OR REPLACE FUNCTION public.generate_document_summary(
    p_content TEXT,
    p_max_length INTEGER DEFAULT 200
)
RETURNS TEXT AS $$
DECLARE
    sentences TEXT[];
    summary TEXT := '';
    current_length INTEGER := 0;
    i INTEGER;
BEGIN
    -- Split content into sentences (simple approach)
    sentences := string_to_array(p_content, '. ');
    
    -- Build summary from first sentences
    FOR i IN 1..array_length(sentences, 1) LOOP
        EXIT WHEN current_length >= p_max_length;
        
        IF length(sentences[i]) + current_length <= p_max_length THEN
            summary := summary || sentences[i] || '. ';
            current_length := length(summary);
        ELSE
            -- Truncate and add ellipsis
            summary := left(summary || sentences[i], p_max_length - 3) || '...';
            EXIT;
        END IF;
    END LOOP;
    
    RETURN trim(summary);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS
ALTER TABLE public.knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_revisions ENABLE ROW LEVEL SECURITY;

-- Document policies
CREATE POLICY "Users can view published documents" 
    ON public.knowledge_documents FOR SELECT 
    USING (is_published = TRUE AND auth.uid() IS NOT NULL);

CREATE POLICY "Authors can view own unpublished documents" 
    ON public.knowledge_documents FOR SELECT 
    USING (author_id = auth.uid());

CREATE POLICY "Users can create documents" 
    ON public.knowledge_documents FOR INSERT 
    WITH CHECK (author_id = auth.uid());

CREATE POLICY "Authors can update own documents" 
    ON public.knowledge_documents FOR UPDATE 
    USING (author_id = auth.uid());

CREATE POLICY "Authors can delete own unpublished documents" 
    ON public.knowledge_documents FOR DELETE 
    USING (author_id = auth.uid() AND is_published = FALSE);

-- Revision policies
CREATE POLICY "Users can view revisions of accessible documents" 
    ON public.document_revisions FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.knowledge_documents d
            WHERE d.id = document_revisions.document_id
            AND (d.is_published = TRUE OR d.author_id = auth.uid())
        )
    );

-- =====================================================
-- VIEWS
-- =====================================================

-- View for popular documents
CREATE OR REPLACE VIEW public.popular_documents AS
SELECT 
    d.id,
    d.title,
    d.summary,
    d.document_type,
    d.tags,
    d.author_id,
    u.full_name AS author_name,
    d.created_at,
    COUNT(DISTINCT ai.user_id) AS unique_viewers,
    COUNT(ai.id) AS total_views
FROM public.knowledge_documents d
LEFT JOIN public.users u ON d.author_id = u.id
LEFT JOIN public.agent_interactions ai ON 
    ai.context->>'document_id' = d.id::TEXT
WHERE 
    d.is_published = TRUE 
    AND d.is_archived = FALSE
GROUP BY d.id, u.full_name
ORDER BY total_views DESC, unique_viewers DESC;

-- Grant permissions on view
GRANT SELECT ON public.popular_documents TO authenticated;