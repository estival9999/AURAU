-- =====================================================
-- Transcriptions and Analysis Tables
-- Version: 1.0.0
-- Description: Meeting transcriptions, segments, and insights
-- =====================================================

-- Drop existing tables if needed (for clean migration)
DROP TABLE IF EXISTS public.meeting_decisions CASCADE;
DROP TABLE IF EXISTS public.action_items CASCADE;
DROP TABLE IF EXISTS public.meeting_summaries CASCADE;
DROP TABLE IF EXISTS public.transcription_segments CASCADE;
DROP TABLE IF EXISTS public.meeting_transcriptions CASCADE;

-- =====================================================
-- 1. MEETING TRANSCRIPTIONS TABLE
-- =====================================================
CREATE TABLE public.meeting_transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    full_text TEXT NOT NULL,
    language TEXT DEFAULT 'pt-BR',
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    word_count INTEGER GENERATED ALWAYS AS (
        array_length(string_to_array(full_text, ' '), 1)
    ) STORED,
    processing_time_ms INTEGER,
    provider TEXT DEFAULT 'openai',
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT full_text_not_empty CHECK (trim(full_text) != ''),
    CONSTRAINT valid_processing_time CHECK (processing_time_ms IS NULL OR processing_time_ms > 0)
);

-- Create indexes
CREATE INDEX idx_transcriptions_meeting ON public.meeting_transcriptions(meeting_id);
CREATE INDEX idx_transcriptions_created ON public.meeting_transcriptions(created_at DESC);
CREATE INDEX idx_transcriptions_language ON public.meeting_transcriptions(language);

-- Full-text search index
CREATE INDEX idx_transcriptions_text_fts ON public.meeting_transcriptions 
    USING GIN(to_tsvector('portuguese', full_text));

-- Add comments
COMMENT ON TABLE public.meeting_transcriptions IS 'Complete meeting transcriptions';
COMMENT ON COLUMN public.meeting_transcriptions.confidence_score IS 'Overall transcription confidence (0-1)';
COMMENT ON COLUMN public.meeting_transcriptions.word_count IS 'Auto-calculated word count';

-- =====================================================
-- 2. TRANSCRIPTION SEGMENTS TABLE
-- =====================================================
CREATE TABLE public.transcription_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcription_id UUID NOT NULL REFERENCES public.meeting_transcriptions(id) ON DELETE CASCADE,
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL,
    speaker_name TEXT,
    speaker_id UUID REFERENCES public.users(id),
    text TEXT NOT NULL,
    start_time_seconds DECIMAL(10,3),
    end_time_seconds DECIMAL(10,3),
    duration_seconds DECIMAL(10,3) GENERATED ALWAYS AS (
        end_time_seconds - start_time_seconds
    ) STORED,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    sentiment sentiment_type DEFAULT 'neutral',
    key_points TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT text_not_empty CHECK (trim(text) != ''),
    CONSTRAINT valid_times CHECK (end_time_seconds >= start_time_seconds),
    CONSTRAINT valid_segment_index CHECK (segment_index >= 0)
);

-- Create indexes
CREATE INDEX idx_segments_transcription ON public.transcription_segments(transcription_id);
CREATE INDEX idx_segments_meeting ON public.transcription_segments(meeting_id);
CREATE INDEX idx_segments_speaker ON public.transcription_segments(speaker_id);
CREATE INDEX idx_segments_speaker_name ON public.transcription_segments(speaker_name);
CREATE INDEX idx_segments_sentiment ON public.transcription_segments(sentiment);
CREATE INDEX idx_segments_index ON public.transcription_segments(transcription_id, segment_index);

-- Full-text search on segments
CREATE INDEX idx_segments_text_fts ON public.transcription_segments 
    USING GIN(to_tsvector('portuguese', text));

-- Add comments
COMMENT ON TABLE public.transcription_segments IS 'Individual speech segments with speaker identification';
COMMENT ON COLUMN public.transcription_segments.key_points IS 'Key points extracted from this segment';

-- =====================================================
-- 3. MEETING SUMMARIES TABLE
-- =====================================================
CREATE TABLE public.meeting_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    summary_type TEXT NOT NULL CHECK (summary_type IN ('executive', 'technical', 'action_items', 'decisions', 'full')),
    content TEXT NOT NULL,
    key_topics TEXT[] DEFAULT '{}',
    generated_by TEXT DEFAULT 'ai' CHECK (generated_by IN ('ai', 'user', 'system')),
    ai_model TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT content_not_empty CHECK (trim(content) != ''),
    CONSTRAINT unique_summary_type UNIQUE (meeting_id, summary_type)
);

-- Create indexes
CREATE INDEX idx_summaries_meeting ON public.meeting_summaries(meeting_id);
CREATE INDEX idx_summaries_type ON public.meeting_summaries(summary_type);
CREATE INDEX idx_summaries_created ON public.meeting_summaries(created_at DESC);
CREATE INDEX idx_summaries_topics ON public.meeting_summaries USING GIN(key_topics);

-- Add comments
COMMENT ON TABLE public.meeting_summaries IS 'AI-generated meeting summaries';
COMMENT ON COLUMN public.meeting_summaries.key_topics IS 'Main topics discussed in the meeting';

-- =====================================================
-- 4. ACTION ITEMS TABLE
-- =====================================================
CREATE TABLE public.action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES public.users(id),
    assigned_to_name TEXT,
    description TEXT NOT NULL,
    due_date DATE,
    priority priority_level DEFAULT 'medium',
    status task_status DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT description_not_empty CHECK (trim(description) != ''),
    CONSTRAINT valid_completion CHECK (
        (status = 'completed' AND completed_at IS NOT NULL) OR
        (status != 'completed' AND completed_at IS NULL)
    ),
    CONSTRAINT assigned_name_or_id CHECK (
        assigned_to IS NOT NULL OR assigned_to_name IS NOT NULL
    )
);

-- Create indexes
CREATE INDEX idx_action_items_meeting ON public.action_items(meeting_id);
CREATE INDEX idx_action_items_assigned_to ON public.action_items(assigned_to);
CREATE INDEX idx_action_items_status ON public.action_items(status);
CREATE INDEX idx_action_items_priority ON public.action_items(priority);
CREATE INDEX idx_action_items_due_date ON public.action_items(due_date);
CREATE INDEX idx_action_items_created ON public.action_items(created_at DESC);

-- Add comments
COMMENT ON TABLE public.action_items IS 'Tasks and action items from meetings';
COMMENT ON COLUMN public.action_items.assigned_to_name IS 'For external assignees not in the system';

-- =====================================================
-- 5. MEETING DECISIONS TABLE
-- =====================================================
CREATE TABLE public.meeting_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    decision_text TEXT NOT NULL,
    decision_type TEXT,
    made_by UUID REFERENCES public.users(id),
    made_by_name TEXT,
    impact_level impact_level DEFAULT 'medium',
    rationale TEXT,
    related_action_items UUID[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT decision_text_not_empty CHECK (trim(decision_text) != ''),
    CONSTRAINT decision_maker CHECK (
        made_by IS NOT NULL OR made_by_name IS NOT NULL
    )
);

-- Create indexes
CREATE INDEX idx_decisions_meeting ON public.meeting_decisions(meeting_id);
CREATE INDEX idx_decisions_made_by ON public.meeting_decisions(made_by);
CREATE INDEX idx_decisions_impact ON public.meeting_decisions(impact_level);
CREATE INDEX idx_decisions_created ON public.meeting_decisions(created_at DESC);

-- Add comments
COMMENT ON TABLE public.meeting_decisions IS 'Important decisions made during meetings';
COMMENT ON COLUMN public.meeting_decisions.related_action_items IS 'Array of action item IDs related to this decision';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Auto-update updated_at
CREATE TRIGGER update_transcriptions_updated_at 
    BEFORE UPDATE ON public.meeting_transcriptions
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_summaries_updated_at 
    BEFORE UPDATE ON public.meeting_summaries
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_action_items_updated_at 
    BEFORE UPDATE ON public.action_items
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Update meeting transcription status when transcription is created
CREATE OR REPLACE FUNCTION update_meeting_transcription_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.meetings
    SET transcription_status = 'completed'
    WHERE id = NEW.meeting_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_meeting_status_on_transcription
    AFTER INSERT ON public.meeting_transcriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_meeting_transcription_status();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to extract action items from transcript
CREATE OR REPLACE FUNCTION public.extract_action_items(
    p_meeting_id UUID,
    p_transcript_text TEXT
)
RETURNS INTEGER AS $$
DECLARE
    action_count INTEGER := 0;
    action_patterns TEXT[] := ARRAY[
        'ação:',
        'tarefa:',
        'pendência:',
        'deve fazer',
        'vai fazer',
        'precisa fazer',
        'responsável por',
        'ficou de'
    ];
BEGIN
    -- This is a placeholder for AI-based extraction
    -- In production, this would call an AI service
    -- For now, return 0
    RETURN action_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get meeting transcript with segments
CREATE OR REPLACE FUNCTION public.get_meeting_transcript(
    p_meeting_id UUID
)
RETURNS TABLE (
    segment_index INTEGER,
    speaker_name TEXT,
    text TEXT,
    start_time_seconds DECIMAL,
    sentiment sentiment_type
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ts.segment_index,
        ts.speaker_name,
        ts.text,
        ts.start_time_seconds,
        ts.sentiment
    FROM public.transcription_segments ts
    JOIN public.meeting_transcriptions mt ON ts.transcription_id = mt.id
    WHERE mt.meeting_id = p_meeting_id
    ORDER BY ts.segment_index;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to complete action item
CREATE OR REPLACE FUNCTION public.complete_action_item(
    p_action_id UUID,
    p_user_id UUID DEFAULT NULL
)
RETURNS public.action_items AS $$
DECLARE
    updated_item public.action_items;
BEGIN
    UPDATE public.action_items
    SET 
        status = 'completed',
        completed_at = CURRENT_TIMESTAMP
    WHERE 
        id = p_action_id
        AND (p_user_id IS NULL OR assigned_to = p_user_id)
        AND status != 'completed'
    RETURNING * INTO updated_item;
    
    RETURN updated_item;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS
ALTER TABLE public.meeting_transcriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transcription_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.action_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_decisions ENABLE ROW LEVEL SECURITY;

-- Transcription policies (inherit from meeting permissions)
CREATE POLICY "Users can view transcriptions of accessible meetings" 
    ON public.meeting_transcriptions FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.meetings m
            WHERE m.id = meeting_transcriptions.meeting_id
            AND (
                m.organizer_id = auth.uid() 
                OR EXISTS (
                    SELECT 1 FROM public.meeting_participants mp
                    WHERE mp.meeting_id = m.id AND mp.user_id = auth.uid()
                )
            )
        )
    );

-- Same policy pattern for segments, summaries, decisions
CREATE POLICY "Users can view segments of accessible meetings" 
    ON public.transcription_segments FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.meetings m
            WHERE m.id = transcription_segments.meeting_id
            AND (
                m.organizer_id = auth.uid() 
                OR EXISTS (
                    SELECT 1 FROM public.meeting_participants mp
                    WHERE mp.meeting_id = m.id AND mp.user_id = auth.uid()
                )
            )
        )
    );

-- Action items policies
CREATE POLICY "Users can view action items assigned to them" 
    ON public.action_items FOR SELECT 
    USING (assigned_to = auth.uid());

CREATE POLICY "Users can view action items from their meetings" 
    ON public.action_items FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.meetings m
            WHERE m.id = action_items.meeting_id
            AND (
                m.organizer_id = auth.uid() 
                OR EXISTS (
                    SELECT 1 FROM public.meeting_participants mp
                    WHERE mp.meeting_id = m.id AND mp.user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY "Users can update their action items" 
    ON public.action_items FOR UPDATE 
    USING (assigned_to = auth.uid());