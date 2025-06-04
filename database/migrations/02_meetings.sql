-- =====================================================
-- Meetings and Recording Tables
-- Version: 1.0.0
-- Description: Core meeting management tables
-- =====================================================

-- Drop existing tables if needed (for clean migration)
DROP TABLE IF EXISTS public.meeting_recordings CASCADE;
DROP TABLE IF EXISTS public.meeting_participants CASCADE;
DROP TABLE IF EXISTS public.meetings CASCADE;

-- =====================================================
-- 1. MEETINGS TABLE
-- =====================================================
CREATE TABLE public.meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    organizer_id UUID NOT NULL REFERENCES public.users(id),
    status meeting_status DEFAULT 'scheduled',
    scheduled_start TIMESTAMPTZ,
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN actual_start IS NOT NULL AND actual_end IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (actual_end - actual_start))::INTEGER
            ELSE NULL
        END
    ) STORED,
    recording_url TEXT,
    transcription_status transcription_status DEFAULT 'pending',
    meeting_type meeting_type DEFAULT 'general',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT title_not_empty CHECK (trim(title) != ''),
    CONSTRAINT valid_duration CHECK (actual_end IS NULL OR actual_end >= actual_start),
    CONSTRAINT valid_metadata CHECK (jsonb_typeof(metadata) = 'object')
);

-- Create indexes
CREATE INDEX idx_meetings_organizer ON public.meetings(organizer_id);
CREATE INDEX idx_meetings_status ON public.meetings(status);
CREATE INDEX idx_meetings_scheduled_start ON public.meetings(scheduled_start);
CREATE INDEX idx_meetings_actual_start ON public.meetings(actual_start DESC);
CREATE INDEX idx_meetings_created_at ON public.meetings(created_at DESC);
CREATE INDEX idx_meetings_type ON public.meetings(meeting_type);
CREATE INDEX idx_meetings_tags ON public.meetings USING GIN(tags);
CREATE INDEX idx_meetings_title_trgm ON public.meetings USING gin(title gin_trgm_ops);
CREATE INDEX idx_meetings_transcription_status ON public.meetings(transcription_status);

-- Full-text search index
CREATE INDEX idx_meetings_title_fts ON public.meetings 
    USING GIN(to_tsvector('portuguese', title));

-- Add comments
COMMENT ON TABLE public.meetings IS 'Core meeting information and metadata';
COMMENT ON COLUMN public.meetings.duration_seconds IS 'Auto-calculated duration in seconds';
COMMENT ON COLUMN public.meetings.tags IS 'Array of tags for categorization';
COMMENT ON COLUMN public.meetings.metadata IS 'Flexible JSON metadata storage';

-- =====================================================
-- 2. MEETING PARTICIPANTS TABLE
-- =====================================================
CREATE TABLE public.meeting_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id),
    participant_name TEXT NOT NULL,
    role participant_role DEFAULT 'participant',
    joined_at TIMESTAMPTZ,
    left_at TIMESTAMPTZ,
    attendance_duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN joined_at IS NOT NULL AND left_at IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (left_at - joined_at))::INTEGER
            ELSE NULL
        END
    ) STORED,
    is_external BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT participant_name_not_empty CHECK (trim(participant_name) != ''),
    CONSTRAINT valid_attendance CHECK (left_at IS NULL OR left_at >= joined_at),
    CONSTRAINT user_or_external CHECK (
        (user_id IS NOT NULL AND is_external = FALSE) OR 
        (user_id IS NULL AND is_external = TRUE)
    )
);

-- Create indexes
CREATE INDEX idx_meeting_participants_meeting ON public.meeting_participants(meeting_id);
CREATE INDEX idx_meeting_participants_user ON public.meeting_participants(user_id);
CREATE INDEX idx_meeting_participants_role ON public.meeting_participants(role);
CREATE INDEX idx_meeting_participants_joined ON public.meeting_participants(joined_at);

-- Unique constraint to prevent duplicate participants
CREATE UNIQUE INDEX idx_unique_meeting_participant 
    ON public.meeting_participants(meeting_id, user_id) 
    WHERE user_id IS NOT NULL;

-- Add comments
COMMENT ON TABLE public.meeting_participants IS 'Track all meeting participants';
COMMENT ON COLUMN public.meeting_participants.is_external IS 'True for non-system users';

-- =====================================================
-- 3. MEETING RECORDINGS TABLE
-- =====================================================
CREATE TABLE public.meeting_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES public.meetings(id) ON DELETE CASCADE,
    recording_url TEXT NOT NULL,
    backup_url TEXT,
    file_size_bytes BIGINT,
    format TEXT DEFAULT 'webm',
    duration_seconds INTEGER,
    resolution TEXT,
    bitrate INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT recording_url_not_empty CHECK (trim(recording_url) != ''),
    CONSTRAINT valid_file_size CHECK (file_size_bytes IS NULL OR file_size_bytes > 0),
    CONSTRAINT valid_duration CHECK (duration_seconds IS NULL OR duration_seconds > 0)
);

-- Create indexes
CREATE INDEX idx_meeting_recordings_meeting ON public.meeting_recordings(meeting_id);
CREATE INDEX idx_meeting_recordings_created ON public.meeting_recordings(created_at DESC);

-- Add comments
COMMENT ON TABLE public.meeting_recordings IS 'Store recording file information';
COMMENT ON COLUMN public.meeting_recordings.backup_url IS 'Secondary storage location';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Auto-update updated_at
CREATE TRIGGER update_meetings_updated_at 
    BEFORE UPDATE ON public.meetings
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recordings_updated_at 
    BEFORE UPDATE ON public.meeting_recordings
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to start a meeting
CREATE OR REPLACE FUNCTION public.start_meeting(meeting_id UUID)
RETURNS public.meetings AS $$
DECLARE
    updated_meeting public.meetings;
BEGIN
    UPDATE public.meetings
    SET 
        status = 'recording',
        actual_start = CURRENT_TIMESTAMP
    WHERE 
        id = meeting_id 
        AND status IN ('scheduled', 'paused')
    RETURNING * INTO updated_meeting;
    
    RETURN updated_meeting;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to end a meeting
CREATE OR REPLACE FUNCTION public.end_meeting(meeting_id UUID)
RETURNS public.meetings AS $$
DECLARE
    updated_meeting public.meetings;
BEGIN
    UPDATE public.meetings
    SET 
        status = 'completed',
        actual_end = CURRENT_TIMESTAMP
    WHERE 
        id = meeting_id 
        AND status IN ('recording', 'paused')
    RETURNING * INTO updated_meeting;
    
    -- Update all active participants
    UPDATE public.meeting_participants
    SET left_at = CURRENT_TIMESTAMP
    WHERE 
        meeting_participants.meeting_id = end_meeting.meeting_id
        AND left_at IS NULL;
    
    RETURN updated_meeting;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to add participant
CREATE OR REPLACE FUNCTION public.add_meeting_participant(
    p_meeting_id UUID,
    p_user_id UUID DEFAULT NULL,
    p_participant_name TEXT DEFAULT NULL,
    p_role participant_role DEFAULT 'participant',
    p_is_external BOOLEAN DEFAULT FALSE
)
RETURNS public.meeting_participants AS $$
DECLARE
    new_participant public.meeting_participants;
    v_participant_name TEXT;
BEGIN
    -- Determine participant name
    IF p_user_id IS NOT NULL THEN
        SELECT username INTO v_participant_name 
        FROM public.users 
        WHERE id = p_user_id;
    ELSE
        v_participant_name := p_participant_name;
    END IF;
    
    -- Insert participant
    INSERT INTO public.meeting_participants (
        meeting_id, user_id, participant_name, role, is_external, joined_at
    ) VALUES (
        p_meeting_id, p_user_id, v_participant_name, p_role, p_is_external, CURRENT_TIMESTAMP
    )
    RETURNING * INTO new_participant;
    
    RETURN new_participant;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get active meetings
CREATE OR REPLACE FUNCTION public.get_active_meetings(
    user_id UUID DEFAULT NULL
)
RETURNS SETOF public.meetings AS $$
BEGIN
    RETURN QUERY
    SELECT m.*
    FROM public.meetings m
    WHERE 
        m.status IN ('recording', 'paused')
        AND (
            user_id IS NULL 
            OR m.organizer_id = user_id
            OR EXISTS (
                SELECT 1 
                FROM public.meeting_participants mp
                WHERE mp.meeting_id = m.id AND mp.user_id = get_active_meetings.user_id
            )
        )
    ORDER BY m.actual_start DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS
ALTER TABLE public.meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_recordings ENABLE ROW LEVEL SECURITY;

-- Meetings policies
CREATE POLICY "Users can view meetings they organize" 
    ON public.meetings FOR SELECT 
    USING (organizer_id = auth.uid());

CREATE POLICY "Users can view meetings they participate in" 
    ON public.meetings FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.meeting_participants
            WHERE meeting_id = meetings.id AND user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create meetings" 
    ON public.meetings FOR INSERT 
    WITH CHECK (organizer_id = auth.uid());

CREATE POLICY "Organizers can update their meetings" 
    ON public.meetings FOR UPDATE 
    USING (organizer_id = auth.uid());

-- Participants policies
CREATE POLICY "Users can view participants of their meetings" 
    ON public.meeting_participants FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.meetings
            WHERE id = meeting_participants.meeting_id 
            AND (
                organizer_id = auth.uid() 
                OR EXISTS (
                    SELECT 1 FROM public.meeting_participants mp2
                    WHERE mp2.meeting_id = meetings.id AND mp2.user_id = auth.uid()
                )
            )
        )
    );

-- Recordings policies
CREATE POLICY "Users can view recordings of their meetings" 
    ON public.meeting_recordings FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.meetings
            WHERE id = meeting_recordings.meeting_id 
            AND (
                organizer_id = auth.uid() 
                OR EXISTS (
                    SELECT 1 FROM public.meeting_participants
                    WHERE meeting_id = meetings.id AND user_id = auth.uid()
                )
            )
        )
    );