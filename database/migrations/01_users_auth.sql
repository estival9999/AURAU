-- =====================================================
-- User Management Tables
-- Version: 1.0.0
-- Description: User authentication and session management
-- =====================================================

-- Drop existing tables if needed (for clean migration)
DROP TABLE IF EXISTS public.user_sessions CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- =====================================================
-- 1. USERS TABLE
-- =====================================================
-- Extends Supabase auth.users with additional profile information
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT,
    area TEXT DEFAULT 'geral',
    role user_role DEFAULT 'user',
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT username_length CHECK (char_length(username) >= 3 AND char_length(username) <= 50),
    CONSTRAINT username_format CHECK (username ~ '^[a-zA-Z0-9_-]+$'),
    CONSTRAINT valid_preferences CHECK (jsonb_typeof(preferences) = 'object')
);

-- Create indexes for users
CREATE INDEX idx_users_username ON public.users(username);
CREATE INDEX idx_users_area ON public.users(area);
CREATE INDEX idx_users_role ON public.users(role);
CREATE INDEX idx_users_is_active ON public.users(is_active);
CREATE INDEX idx_users_created_at ON public.users(created_at DESC);

-- Add comments
COMMENT ON TABLE public.users IS 'Extended user profile information';
COMMENT ON COLUMN public.users.id IS 'User ID from auth.users';
COMMENT ON COLUMN public.users.username IS 'Unique username for the system';
COMMENT ON COLUMN public.users.area IS 'Department or area of the user';
COMMENT ON COLUMN public.users.role IS 'System role (user, admin, manager)';
COMMENT ON COLUMN public.users.preferences IS 'User preferences in JSON format';

-- =====================================================
-- 2. USER SESSIONS TABLE
-- =====================================================
-- Track user sessions for security and analytics
CREATE TABLE public.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL DEFAULT generate_token(64),
    ip_address INET,
    user_agent TEXT,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT valid_session_duration CHECK (
        ended_at IS NULL OR ended_at >= started_at
    )
);

-- Create indexes for sessions
CREATE INDEX idx_user_sessions_user_id ON public.user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON public.user_sessions(session_token);
CREATE INDEX idx_user_sessions_active ON public.user_sessions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_user_sessions_started_at ON public.user_sessions(started_at DESC);

-- Add comments
COMMENT ON TABLE public.user_sessions IS 'User session tracking for security and analytics';
COMMENT ON COLUMN public.user_sessions.session_token IS 'Unique session identifier';
COMMENT ON COLUMN public.user_sessions.ip_address IS 'IP address of the session';
COMMENT ON COLUMN public.user_sessions.user_agent IS 'Browser/device information';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Auto-update updated_at timestamp for users
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-update last_activity for sessions
CREATE TRIGGER update_session_activity
    BEFORE UPDATE ON public.user_sessions
    FOR EACH ROW
    WHEN (OLD.is_active = TRUE AND NEW.is_active = TRUE)
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to create a new user profile
CREATE OR REPLACE FUNCTION public.create_user_profile(
    user_id UUID,
    username TEXT,
    full_name TEXT DEFAULT NULL,
    area TEXT DEFAULT 'geral'
)
RETURNS public.users AS $$
DECLARE
    new_user public.users;
BEGIN
    INSERT INTO public.users (id, username, full_name, area)
    VALUES (user_id, username, full_name, area)
    RETURNING * INTO new_user;
    
    RETURN new_user;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update last login
CREATE OR REPLACE FUNCTION public.update_last_login(user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users 
    SET last_login = CURRENT_TIMESTAMP 
    WHERE id = user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to end user session
CREATE OR REPLACE FUNCTION public.end_user_session(session_token TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE public.user_sessions
    SET 
        is_active = FALSE,
        ended_at = CURRENT_TIMESTAMP
    WHERE 
        user_sessions.session_token = end_user_session.session_token
        AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clean old sessions
CREATE OR REPLACE FUNCTION public.cleanup_old_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.user_sessions
    WHERE 
        is_active = FALSE 
        AND ended_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_sessions ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view own profile" 
    ON public.users FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.users FOR UPDATE 
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id AND role = 'user'); -- Prevent self-promotion

CREATE POLICY "Admins can view all users" 
    ON public.users FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Sessions policies
CREATE POLICY "Users can view own sessions" 
    ON public.user_sessions FOR SELECT 
    USING (user_id = auth.uid());

CREATE POLICY "Users can create own sessions" 
    ON public.user_sessions FOR INSERT 
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own sessions" 
    ON public.user_sessions FOR UPDATE 
    USING (user_id = auth.uid());

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Create trigger to auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, username, full_name)
    VALUES (
        NEW.id, 
        COALESCE(NEW.raw_user_meta_data->>'username', NEW.email),
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new signups
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW 
    EXECUTE FUNCTION public.handle_new_user();