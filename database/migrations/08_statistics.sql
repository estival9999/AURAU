-- =====================================================
-- Statistics and Analytics Tables
-- Version: 1.0.0
-- Description: Aggregated statistics for users and agents
-- =====================================================

-- Drop existing tables if needed (for clean migration)
DROP TABLE IF EXISTS public.agent_statistics CASCADE;
DROP TABLE IF EXISTS public.user_statistics CASCADE;

-- =====================================================
-- 1. USER STATISTICS TABLE
-- =====================================================
CREATE TABLE public.user_statistics (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    total_meetings_organized INTEGER DEFAULT 0,
    total_meetings_attended INTEGER DEFAULT 0,
    total_recording_minutes INTEGER DEFAULT 0,
    total_transcription_words INTEGER DEFAULT 0,
    total_action_items_assigned INTEGER DEFAULT 0,
    total_action_items_completed INTEGER DEFAULT 0,
    total_ai_interactions INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0,
    last_activity TIMESTAMPTZ,
    last_meeting_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Computed fields
    action_completion_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN total_action_items_assigned = 0 THEN 0
            ELSE (total_action_items_completed::DECIMAL / total_action_items_assigned * 100)
        END
    ) STORED,
    avg_meeting_duration_minutes DECIMAL(10,2) GENERATED ALWAYS AS (
        CASE 
            WHEN total_meetings_attended = 0 THEN 0
            ELSE (total_recording_minutes::DECIMAL / total_meetings_attended)
        END
    ) STORED
);

-- Create indexes
CREATE INDEX idx_user_stats_activity ON public.user_statistics(last_activity DESC);
CREATE INDEX idx_user_stats_meetings ON public.user_statistics(total_meetings_organized DESC);
CREATE INDEX idx_user_stats_tokens ON public.user_statistics(total_tokens_used DESC);

-- Add comments
COMMENT ON TABLE public.user_statistics IS 'Aggregated statistics per user';
COMMENT ON COLUMN public.user_statistics.action_completion_rate IS 'Percentage of completed action items';

-- =====================================================
-- 2. AGENT STATISTICS TABLE
-- =====================================================
CREATE TABLE public.agent_statistics (
    agent_id UUID PRIMARY KEY REFERENCES public.ai_agents(id) ON DELETE CASCADE,
    total_interactions INTEGER DEFAULT 0,
    successful_interactions INTEGER DEFAULT 0,
    failed_interactions INTEGER DEFAULT 0,
    total_response_time_ms BIGINT DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    total_satisfaction_score INTEGER DEFAULT 0,
    satisfaction_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error_at TIMESTAMPTZ,
    last_interaction_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Computed fields
    success_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN total_interactions = 0 THEN 0
            ELSE (successful_interactions::DECIMAL / total_interactions * 100)
        END
    ) STORED,
    average_response_time_ms DECIMAL(10,2) GENERATED ALWAYS AS (
        CASE 
            WHEN successful_interactions = 0 THEN 0
            ELSE (total_response_time_ms::DECIMAL / successful_interactions)
        END
    ) STORED,
    cache_hit_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN (cache_hits + cache_misses) = 0 THEN 0
            ELSE (cache_hits::DECIMAL / (cache_hits + cache_misses) * 100)
        END
    ) STORED,
    average_satisfaction DECIMAL(3,2) GENERATED ALWAYS AS (
        CASE 
            WHEN satisfaction_count = 0 THEN 0
            ELSE (total_satisfaction_score::DECIMAL / satisfaction_count)
        END
    ) STORED
);

-- Create indexes
CREATE INDEX idx_agent_stats_interactions ON public.agent_statistics(total_interactions DESC);
CREATE INDEX idx_agent_stats_success_rate ON public.agent_statistics(success_rate DESC);
CREATE INDEX idx_agent_stats_response_time ON public.agent_statistics(average_response_time_ms);
CREATE INDEX idx_agent_stats_last_interaction ON public.agent_statistics(last_interaction_at DESC);

-- Add comments
COMMENT ON TABLE public.agent_statistics IS 'Aggregated performance statistics per agent';
COMMENT ON COLUMN public.agent_statistics.cache_hit_rate IS 'Percentage of requests served from cache';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Auto-update updated_at
CREATE TRIGGER update_user_statistics_updated_at 
    BEFORE UPDATE ON public.user_statistics
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_statistics_updated_at 
    BEFORE UPDATE ON public.agent_statistics
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to update user statistics
CREATE OR REPLACE FUNCTION public.update_user_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle different table updates
    CASE TG_TABLE_NAME
        WHEN 'meetings' THEN
            IF TG_OP = 'INSERT' THEN
                INSERT INTO public.user_statistics (user_id, total_meetings_organized, last_meeting_date)
                VALUES (NEW.organizer_id, 1, NEW.actual_start)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_meetings_organized = user_statistics.total_meetings_organized + 1,
                    last_meeting_date = GREATEST(user_statistics.last_meeting_date, EXCLUDED.last_meeting_date),
                    last_activity = CURRENT_TIMESTAMP;
            END IF;
            
        WHEN 'meeting_participants' THEN
            IF TG_OP = 'INSERT' AND NEW.user_id IS NOT NULL THEN
                INSERT INTO public.user_statistics (user_id, total_meetings_attended)
                VALUES (NEW.user_id, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_meetings_attended = user_statistics.total_meetings_attended + 1,
                    last_activity = CURRENT_TIMESTAMP;
            END IF;
            
        WHEN 'action_items' THEN
            IF TG_OP = 'INSERT' AND NEW.assigned_to IS NOT NULL THEN
                INSERT INTO public.user_statistics (user_id, total_action_items_assigned)
                VALUES (NEW.assigned_to, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_action_items_assigned = user_statistics.total_action_items_assigned + 1,
                    last_activity = CURRENT_TIMESTAMP;
            ELSIF TG_OP = 'UPDATE' AND NEW.status = 'completed' AND OLD.status != 'completed' THEN
                UPDATE public.user_statistics
                SET 
                    total_action_items_completed = total_action_items_completed + 1,
                    last_activity = CURRENT_TIMESTAMP
                WHERE user_id = NEW.assigned_to;
            END IF;
            
        WHEN 'agent_interactions' THEN
            IF TG_OP = 'INSERT' THEN
                INSERT INTO public.user_statistics (user_id, total_ai_interactions)
                VALUES (NEW.user_id, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_ai_interactions = user_statistics.total_ai_interactions + 1,
                    last_activity = CURRENT_TIMESTAMP;
            END IF;
            
        WHEN 'token_usage' THEN
            IF TG_OP = 'INSERT' AND NEW.user_id IS NOT NULL THEN
                INSERT INTO public.user_statistics (user_id, total_tokens_used, total_cost_usd)
                VALUES (NEW.user_id, NEW.tokens_total, NEW.cost_total)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_tokens_used = user_statistics.total_tokens_used + EXCLUDED.total_tokens_used,
                    total_cost_usd = user_statistics.total_cost_usd + EXCLUDED.total_cost_usd,
                    last_activity = CURRENT_TIMESTAMP;
            END IF;
    END CASE;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update agent statistics
CREATE OR REPLACE FUNCTION public.update_agent_statistics()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'agent_interactions' THEN
        IF TG_OP = 'UPDATE' AND OLD.output_text IS NULL AND NEW.output_text IS NOT NULL THEN
            -- Successful interaction completed
            INSERT INTO public.agent_statistics (
                agent_id, 
                total_interactions,
                successful_interactions,
                total_response_time_ms,
                last_interaction_at
            ) VALUES (
                NEW.agent_id, 
                1,
                1,
                COALESCE(NEW.response_time_ms, 0),
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (agent_id) DO UPDATE SET
                total_interactions = agent_statistics.total_interactions + 1,
                successful_interactions = agent_statistics.successful_interactions + 1,
                total_response_time_ms = agent_statistics.total_response_time_ms + COALESCE(EXCLUDED.total_response_time_ms, 0),
                last_interaction_at = CURRENT_TIMESTAMP;
                
            -- Update satisfaction if provided
            IF NEW.satisfaction_rating IS NOT NULL THEN
                UPDATE public.agent_statistics
                SET 
                    total_satisfaction_score = total_satisfaction_score + NEW.satisfaction_rating,
                    satisfaction_count = satisfaction_count + 1
                WHERE agent_id = NEW.agent_id;
            END IF;
            
        ELSIF TG_OP = 'UPDATE' AND NEW.error_message IS NOT NULL THEN
            -- Failed interaction
            INSERT INTO public.agent_statistics (
                agent_id,
                total_interactions,
                failed_interactions,
                error_count,
                last_error_at
            ) VALUES (
                NEW.agent_id,
                1,
                1,
                1,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (agent_id) DO UPDATE SET
                total_interactions = agent_statistics.total_interactions + 1,
                failed_interactions = agent_statistics.failed_interactions + 1,
                error_count = agent_statistics.error_count + 1,
                last_error_at = CURRENT_TIMESTAMP;
        END IF;
        
    ELSIF TG_TABLE_NAME = 'token_usage' AND NEW.agent_id IS NOT NULL THEN
        -- Update token usage
        INSERT INTO public.agent_statistics (
            agent_id,
            total_tokens_used,
            total_cost_usd
        ) VALUES (
            NEW.agent_id,
            NEW.tokens_total,
            NEW.cost_total
        )
        ON CONFLICT (agent_id) DO UPDATE SET
            total_tokens_used = agent_statistics.total_tokens_used + EXCLUDED.total_tokens_used,
            total_cost_usd = agent_statistics.total_cost_usd + EXCLUDED.total_cost_usd;
            
    ELSIF TG_TABLE_NAME = 'query_cache' AND NEW.agent_id IS NOT NULL THEN
        -- Update cache statistics
        IF TG_OP = 'UPDATE' AND NEW.hit_count > OLD.hit_count THEN
            UPDATE public.agent_statistics
            SET cache_hits = cache_hits + 1
            WHERE agent_id = NEW.agent_id;
        ELSIF TG_OP = 'INSERT' THEN
            UPDATE public.agent_statistics
            SET cache_misses = cache_misses + 1
            WHERE agent_id = NEW.agent_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic statistics updates
CREATE TRIGGER update_user_stats_on_meeting
    AFTER INSERT ON public.meetings
    FOR EACH ROW
    EXECUTE FUNCTION public.update_user_statistics();

CREATE TRIGGER update_user_stats_on_participant
    AFTER INSERT ON public.meeting_participants
    FOR EACH ROW
    EXECUTE FUNCTION public.update_user_statistics();

CREATE TRIGGER update_user_stats_on_action_item
    AFTER INSERT OR UPDATE ON public.action_items
    FOR EACH ROW
    EXECUTE FUNCTION public.update_user_statistics();

CREATE TRIGGER update_user_stats_on_interaction
    AFTER INSERT ON public.agent_interactions
    FOR EACH ROW
    EXECUTE FUNCTION public.update_user_statistics();

CREATE TRIGGER update_user_stats_on_token_usage
    AFTER INSERT ON public.token_usage
    FOR EACH ROW
    EXECUTE FUNCTION public.update_user_statistics();

CREATE TRIGGER update_agent_stats_on_interaction
    AFTER UPDATE ON public.agent_interactions
    FOR EACH ROW
    EXECUTE FUNCTION public.update_agent_statistics();

CREATE TRIGGER update_agent_stats_on_token_usage
    AFTER INSERT ON public.token_usage
    FOR EACH ROW
    EXECUTE FUNCTION public.update_agent_statistics();

CREATE TRIGGER update_agent_stats_on_cache
    AFTER INSERT OR UPDATE ON public.query_cache
    FOR EACH ROW
    EXECUTE FUNCTION public.update_agent_statistics();

-- Function to get user activity summary
CREATE OR REPLACE FUNCTION public.get_user_activity_summary(
    p_user_id UUID,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    meetings_organized INTEGER,
    meetings_attended INTEGER,
    action_items_pending INTEGER,
    action_items_completed INTEGER,
    ai_interactions INTEGER,
    recent_meetings JSONB,
    recent_actions JSONB,
    activity_trend JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH user_stats AS (
        SELECT * FROM public.user_statistics WHERE user_id = p_user_id
    ),
    recent_meetings AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'id', m.id,
                'title', m.title,
                'date', m.actual_start,
                'duration_minutes', m.duration_seconds / 60
            ) ORDER BY m.actual_start DESC
        ) AS meetings
        FROM public.meetings m
        WHERE 
            (m.organizer_id = p_user_id OR EXISTS (
                SELECT 1 FROM public.meeting_participants mp
                WHERE mp.meeting_id = m.id AND mp.user_id = p_user_id
            ))
            AND m.actual_start >= CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days
        LIMIT 10
    ),
    recent_actions AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'id', a.id,
                'description', a.description,
                'status', a.status,
                'due_date', a.due_date,
                'priority', a.priority
            ) ORDER BY a.created_at DESC
        ) AS actions
        FROM public.action_items a
        WHERE 
            a.assigned_to = p_user_id
            AND a.created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days
        LIMIT 10
    ),
    activity_trend AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'date', activity_date,
                'meetings', meeting_count,
                'interactions', interaction_count
            ) ORDER BY activity_date
        ) AS trend
        FROM (
            SELECT 
                DATE(created_at) AS activity_date,
                COUNT(DISTINCT m.id) AS meeting_count,
                COUNT(DISTINCT ai.id) AS interaction_count
            FROM generate_series(
                CURRENT_DATE - INTERVAL '1 day' * (p_days - 1),
                CURRENT_DATE,
                INTERVAL '1 day'
            ) AS d(date)
            LEFT JOIN public.meetings m ON DATE(m.created_at) = d.date AND m.organizer_id = p_user_id
            LEFT JOIN public.agent_interactions ai ON DATE(ai.created_at) = d.date AND ai.user_id = p_user_id
            GROUP BY DATE(created_at)
        ) t
    )
    SELECT 
        COALESCE(us.total_meetings_organized, 0) AS meetings_organized,
        COALESCE(us.total_meetings_attended, 0) AS meetings_attended,
        (SELECT COUNT(*) FROM public.action_items WHERE assigned_to = p_user_id AND status = 'pending')::INTEGER AS action_items_pending,
        COALESCE(us.total_action_items_completed, 0) AS action_items_completed,
        COALESCE(us.total_ai_interactions, 0) AS ai_interactions,
        rm.meetings AS recent_meetings,
        ra.actions AS recent_actions,
        at.trend AS activity_trend
    FROM user_stats us, recent_meetings rm, recent_actions ra, activity_trend at;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get agent performance summary
CREATE OR REPLACE FUNCTION public.get_agent_performance_summary()
RETURNS TABLE (
    agent_name TEXT,
    agent_type agent_type,
    total_interactions INTEGER,
    success_rate DECIMAL,
    avg_response_time_ms DECIMAL,
    cache_hit_rate DECIMAL,
    avg_satisfaction DECIMAL,
    total_cost DECIMAL,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.name AS agent_name,
        a.type AS agent_type,
        COALESCE(s.total_interactions, 0) AS total_interactions,
        COALESCE(s.success_rate, 0) AS success_rate,
        COALESCE(s.average_response_time_ms, 0) AS avg_response_time_ms,
        COALESCE(s.cache_hit_rate, 0) AS cache_hit_rate,
        COALESCE(s.average_satisfaction, 0) AS avg_satisfaction,
        COALESCE(s.total_cost_usd, 0) AS total_cost,
        CASE 
            WHEN a.is_active = FALSE THEN 'inactive'
            WHEN s.last_error_at > CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN 'error'
            WHEN s.success_rate < 80 THEN 'degraded'
            ELSE 'healthy'
        END AS status
    FROM public.ai_agents a
    LEFT JOIN public.agent_statistics s ON a.id = s.agent_id
    ORDER BY a.type, a.name;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS
ALTER TABLE public.user_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_statistics ENABLE ROW LEVEL SECURITY;

-- User statistics policies
CREATE POLICY "Users can view own statistics" 
    ON public.user_statistics FOR SELECT 
    USING (user_id = auth.uid());

CREATE POLICY "Admins can view all user statistics" 
    ON public.user_statistics FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND role IN ('admin', 'manager')
        )
    );

-- Agent statistics policies (viewable by all authenticated users)
CREATE POLICY "Authenticated users can view agent statistics" 
    ON public.agent_statistics FOR SELECT 
    USING (auth.uid() IS NOT NULL);

-- =====================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- =====================================================

-- Leaderboard view
CREATE MATERIALIZED VIEW public.user_leaderboard AS
SELECT 
    u.id,
    u.full_name,
    u.username,
    us.total_meetings_organized,
    us.total_meetings_attended,
    us.action_completion_rate,
    us.total_ai_interactions,
    RANK() OVER (ORDER BY us.total_meetings_organized DESC) AS meetings_rank,
    RANK() OVER (ORDER BY us.action_completion_rate DESC) AS completion_rank,
    RANK() OVER (ORDER BY us.total_ai_interactions DESC) AS ai_usage_rank
FROM public.users u
JOIN public.user_statistics us ON u.id = us.user_id
WHERE u.is_active = TRUE;

-- Create index on materialized view
CREATE INDEX idx_leaderboard_meetings ON public.user_leaderboard(total_meetings_organized DESC);

-- Grant permissions
GRANT SELECT ON public.user_leaderboard TO authenticated;

-- Refresh function
CREATE OR REPLACE FUNCTION public.refresh_statistics_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.user_leaderboard;
END;
$$ LANGUAGE plpgsql;