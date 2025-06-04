-- =====================================================
-- AURALIS Database Setup
-- Version: 1.0.0
-- Description: Initial database setup and extensions
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "unaccent"; -- For accent-insensitive search
CREATE EXTENSION IF NOT EXISTS "vector"; -- For embeddings (pgvector)

-- Create custom types
CREATE TYPE user_role AS ENUM ('user', 'admin', 'manager');
CREATE TYPE meeting_status AS ENUM ('scheduled', 'recording', 'paused', 'completed', 'cancelled', 'processing');
CREATE TYPE transcription_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE meeting_type AS ENUM ('general', 'standup', 'planning', 'review', 'brainstorm', 'one-on-one');
CREATE TYPE participant_role AS ENUM ('organizer', 'presenter', 'participant', 'observer');
CREATE TYPE sentiment_type AS ENUM ('positive', 'neutral', 'negative', 'mixed');
CREATE TYPE priority_level AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');
CREATE TYPE agent_type AS ENUM ('orchestrator', 'query', 'brainstorm', 'optimizer', 'context');
CREATE TYPE interaction_type AS ENUM ('query', 'analysis', 'brainstorm', 'summary', 'search');
CREATE TYPE message_type AS ENUM ('request', 'response', 'notification', 'broadcast', 'error');
CREATE TYPE message_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE document_type AS ENUM ('policy', 'procedure', 'guide', 'faq', 'reference', 'meeting_notes');
CREATE TYPE source_type AS ENUM ('manual', 'meeting', 'external', 'generated');
CREATE TYPE metric_type AS ENUM ('api_call', 'cache_hit', 'query_time', 'token_usage', 'error');
CREATE TYPE impact_level AS ENUM ('low', 'medium', 'high');

-- Set timezone
SET timezone = 'America/Sao_Paulo';

-- Create schemas if needed
CREATE SCHEMA IF NOT EXISTS public;

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

-- Create updated_at function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create function to generate random tokens
CREATE OR REPLACE FUNCTION generate_token(length INTEGER DEFAULT 32)
RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..length LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create function to calculate duration
CREATE OR REPLACE FUNCTION calculate_duration(start_time TIMESTAMPTZ, end_time TIMESTAMPTZ)
RETURNS INTEGER AS $$
BEGIN
    IF start_time IS NULL OR end_time IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN EXTRACT(EPOCH FROM (end_time - start_time))::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- Notify that setup is complete
DO $$
BEGIN
    RAISE NOTICE 'Database setup completed successfully';
END $$;