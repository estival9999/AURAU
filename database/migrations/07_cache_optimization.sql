-- =====================================================
-- Cache and Optimization Tables
-- Version: 1.0.0
-- Description: Performance optimization through intelligent caching
-- =====================================================

-- Drop existing tables if needed (for clean migration)
DROP TABLE IF EXISTS public.token_usage CASCADE;
DROP TABLE IF EXISTS public.system_metrics CASCADE;
DROP TABLE IF EXISTS public.query_cache CASCADE;

-- =====================================================
-- 1. QUERY CACHE TABLE
-- =====================================================
CREATE TABLE public.query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key TEXT UNIQUE NOT NULL,
    cache_hash TEXT GENERATED ALWAYS AS (md5(cache_key)) STORED,
    query_text TEXT NOT NULL,
    query_type TEXT CHECK (query_type IN ('search', 'analysis', 'summary', 'embedding', 'other')),
    result JSONB NOT NULL,
    result_size INTEGER GENERATED ALWAYS AS (pg_column_size(result)) STORED,
    agent_id UUID REFERENCES public.ai_agents(id),
    user_id UUID REFERENCES public.users(id),
    hit_count INTEGER DEFAULT 0,
    ttl_seconds INTEGER DEFAULT 3600,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ GENERATED ALWAYS AS (created_at + (ttl_seconds * INTERVAL '1 second')) STORED,
    last_accessed TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT cache_key_not_empty CHECK (trim(cache_key) != ''),
    CONSTRAINT query_text_not_empty CHECK (trim(query_text) != ''),
    CONSTRAINT valid_result CHECK (jsonb_typeof(result) = 'object'),
    CONSTRAINT valid_ttl CHECK (ttl_seconds > 0)
);

-- Create indexes
CREATE INDEX idx_query_cache_key ON public.query_cache(cache_key);
CREATE INDEX idx_query_cache_hash ON public.query_cache(cache_hash);
CREATE INDEX idx_query_cache_expires ON public.query_cache(expires_at);
CREATE INDEX idx_query_cache_agent ON public.query_cache(agent_id);
CREATE INDEX idx_query_cache_user ON public.query_cache(user_id);
CREATE INDEX idx_query_cache_type ON public.query_cache(query_type);
CREATE INDEX idx_query_cache_created ON public.query_cache(created_at DESC);

-- Partial index for active cache entries
CREATE INDEX idx_query_cache_active ON public.query_cache(cache_key) 
    WHERE expires_at > CURRENT_TIMESTAMP;

-- Add comments
COMMENT ON TABLE public.query_cache IS 'Intelligent query result caching';
COMMENT ON COLUMN public.query_cache.cache_key IS 'Unique key for cache lookup';
COMMENT ON COLUMN public.query_cache.result_size IS 'Size of cached result in bytes';

-- =====================================================
-- 2. TOKEN USAGE TABLE
-- =====================================================
CREATE TABLE public.token_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id),
    agent_id UUID REFERENCES public.ai_agents(id),
    interaction_id UUID REFERENCES public.agent_interactions(id),
    model TEXT NOT NULL,
    tokens_input INTEGER CHECK (tokens_input >= 0),
    tokens_output INTEGER CHECK (tokens_output >= 0),
    tokens_total INTEGER GENERATED ALWAYS AS (COALESCE(tokens_input, 0) + COALESCE(tokens_output, 0)) STORED,
    cost_input DECIMAL(10,6),
    cost_output DECIMAL(10,6),
    cost_total DECIMAL(10,6) GENERATED ALWAYS AS (COALESCE(cost_input, 0) + COALESCE(cost_output, 0)) STORED,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT model_not_empty CHECK (trim(model) != '')
);

-- Create indexes
CREATE INDEX idx_token_usage_user ON public.token_usage(user_id);
CREATE INDEX idx_token_usage_agent ON public.token_usage(agent_id);
CREATE INDEX idx_token_usage_interaction ON public.token_usage(interaction_id);
CREATE INDEX idx_token_usage_model ON public.token_usage(model);
CREATE INDEX idx_token_usage_created ON public.token_usage(created_at DESC);

-- Partial index for high-cost operations
CREATE INDEX idx_token_usage_high_cost ON public.token_usage(cost_total DESC) 
    WHERE cost_total > 0.01;

-- Add comments
COMMENT ON TABLE public.token_usage IS 'Track token consumption and costs';
COMMENT ON COLUMN public.token_usage.cost_total IS 'Total cost in USD';

-- =====================================================
-- 3. SYSTEM METRICS TABLE
-- =====================================================
CREATE TABLE public.system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type metric_type NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DECIMAL NOT NULL,
    unit TEXT DEFAULT 'count',
    tags JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT metric_name_not_empty CHECK (trim(metric_name) != ''),
    CONSTRAINT valid_tags CHECK (jsonb_typeof(tags) = 'object'),
    CONSTRAINT valid_metadata CHECK (jsonb_typeof(metadata) = 'object')
);

-- Create indexes
CREATE INDEX idx_metrics_type ON public.system_metrics(metric_type);
CREATE INDEX idx_metrics_name ON public.system_metrics(metric_name);
CREATE INDEX idx_metrics_created ON public.system_metrics(created_at DESC);
CREATE INDEX idx_metrics_tags ON public.system_metrics USING GIN(tags);

-- Partial indexes for specific metric types
CREATE INDEX idx_metrics_errors ON public.system_metrics(created_at DESC) 
    WHERE metric_type = 'error';
CREATE INDEX idx_metrics_api_calls ON public.system_metrics(created_at DESC) 
    WHERE metric_type = 'api_call';

-- Add comments
COMMENT ON TABLE public.system_metrics IS 'System performance and usage metrics';
COMMENT ON COLUMN public.system_metrics.tags IS 'Additional categorization tags';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update last_accessed on cache hit
CREATE OR REPLACE FUNCTION update_cache_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = CURRENT_TIMESTAMP;
    NEW.hit_count = OLD.hit_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cache_on_access
    BEFORE UPDATE ON public.query_cache
    FOR EACH ROW
    WHEN (OLD.result IS NOT DISTINCT FROM NEW.result)
    EXECUTE FUNCTION update_cache_last_accessed();

-- Calculate token costs based on model
CREATE OR REPLACE FUNCTION calculate_token_costs()
RETURNS TRIGGER AS $$
DECLARE
    v_cost_per_1k_input DECIMAL(10,6);
    v_cost_per_1k_output DECIMAL(10,6);
BEGIN
    -- Set costs based on model (prices as of 2024)
    CASE NEW.model
        WHEN 'gpt-4' THEN
            v_cost_per_1k_input := 0.03;
            v_cost_per_1k_output := 0.06;
        WHEN 'gpt-4-turbo' THEN
            v_cost_per_1k_input := 0.01;
            v_cost_per_1k_output := 0.03;
        WHEN 'gpt-3.5-turbo' THEN
            v_cost_per_1k_input := 0.0005;
            v_cost_per_1k_output := 0.0015;
        WHEN 'text-embedding-ada-002' THEN
            v_cost_per_1k_input := 0.0001;
            v_cost_per_1k_output := 0;
        ELSE
            v_cost_per_1k_input := 0.001;
            v_cost_per_1k_output := 0.002;
    END CASE;
    
    -- Calculate costs
    NEW.cost_input := (NEW.tokens_input::DECIMAL / 1000) * v_cost_per_1k_input;
    NEW.cost_output := (NEW.tokens_output::DECIMAL / 1000) * v_cost_per_1k_output;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_costs_on_insert
    BEFORE INSERT ON public.token_usage
    FOR EACH ROW
    EXECUTE FUNCTION calculate_token_costs();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to get or create cache entry
CREATE OR REPLACE FUNCTION public.get_or_create_cache(
    p_cache_key TEXT,
    p_query_text TEXT,
    p_query_type TEXT DEFAULT 'other',
    p_ttl_seconds INTEGER DEFAULT 3600
)
RETURNS public.query_cache AS $$
DECLARE
    v_cache_entry public.query_cache;
BEGIN
    -- Try to get existing cache entry
    SELECT * INTO v_cache_entry
    FROM public.query_cache
    WHERE 
        cache_key = p_cache_key
        AND expires_at > CURRENT_TIMESTAMP
    FOR UPDATE SKIP LOCKED;
    
    -- Update hit count if found
    IF v_cache_entry IS NOT NULL THEN
        UPDATE public.query_cache
        SET hit_count = hit_count + 1,
            last_accessed = CURRENT_TIMESTAMP
        WHERE id = v_cache_entry.id;
    END IF;
    
    RETURN v_cache_entry;
END;
$$ LANGUAGE plpgsql;

-- Function to save to cache
CREATE OR REPLACE FUNCTION public.save_to_cache(
    p_cache_key TEXT,
    p_query_text TEXT,
    p_result JSONB,
    p_query_type TEXT DEFAULT 'other',
    p_agent_id UUID DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_ttl_seconds INTEGER DEFAULT 3600
)
RETURNS public.query_cache AS $$
DECLARE
    v_cache_entry public.query_cache;
BEGIN
    INSERT INTO public.query_cache (
        cache_key, query_text, query_type, result,
        agent_id, user_id, ttl_seconds
    ) VALUES (
        p_cache_key, p_query_text, p_query_type, p_result,
        p_agent_id, p_user_id, p_ttl_seconds
    )
    ON CONFLICT (cache_key) DO UPDATE SET
        result = EXCLUDED.result,
        query_text = EXCLUDED.query_text,
        query_type = EXCLUDED.query_type,
        ttl_seconds = EXCLUDED.ttl_seconds,
        created_at = CURRENT_TIMESTAMP,
        hit_count = 0
    RETURNING * INTO v_cache_entry;
    
    RETURN v_cache_entry;
END;
$$ LANGUAGE plpgsql;

-- Function to log metrics
CREATE OR REPLACE FUNCTION public.log_metric(
    p_metric_type metric_type,
    p_metric_name TEXT,
    p_metric_value DECIMAL,
    p_unit TEXT DEFAULT 'count',
    p_tags JSONB DEFAULT '{}',
    p_metadata JSONB DEFAULT '{}'
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO public.system_metrics (
        metric_type, metric_name, metric_value,
        unit, tags, metadata
    ) VALUES (
        p_metric_type, p_metric_name, p_metric_value,
        p_unit, p_tags, p_metadata
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get cache statistics
CREATE OR REPLACE FUNCTION public.get_cache_statistics(
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    total_entries BIGINT,
    active_entries BIGINT,
    expired_entries BIGINT,
    total_hits BIGINT,
    avg_hit_rate DECIMAL,
    total_size_mb DECIMAL,
    most_used_queries JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH cache_stats AS (
        SELECT 
            COUNT(*) AS total_entries,
            COUNT(*) FILTER (WHERE expires_at > CURRENT_TIMESTAMP) AS active_entries,
            COUNT(*) FILTER (WHERE expires_at <= CURRENT_TIMESTAMP) AS expired_entries,
            SUM(hit_count) AS total_hits,
            AVG(hit_count) AS avg_hit_rate,
            SUM(result_size) / (1024.0 * 1024.0) AS total_size_mb
        FROM public.query_cache
        WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days
    ),
    top_queries AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'query', query_text,
                'hits', hit_count,
                'type', query_type
            ) ORDER BY hit_count DESC
        ) AS most_used
        FROM (
            SELECT query_text, query_type, SUM(hit_count) AS hit_count
            FROM public.query_cache
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days
            GROUP BY query_text, query_type
            ORDER BY hit_count DESC
            LIMIT 10
        ) t
    )
    SELECT 
        cs.total_entries,
        cs.active_entries,
        cs.expired_entries,
        cs.total_hits,
        cs.avg_hit_rate,
        cs.total_size_mb,
        tq.most_used AS most_used_queries
    FROM cache_stats cs, top_queries tq;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to cleanup expired cache
CREATE OR REPLACE FUNCTION public.cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.query_cache
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log cleanup metric
    PERFORM public.log_metric(
        'cache_hit',
        'cache_cleanup',
        deleted_count,
        'entries',
        '{"action": "cleanup"}'::JSONB
    );
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get token usage summary
CREATE OR REPLACE FUNCTION public.get_token_usage_summary(
    p_user_id UUID DEFAULT NULL,
    p_start_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP - INTERVAL '30 days',
    p_end_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
)
RETURNS TABLE (
    total_tokens BIGINT,
    total_cost DECIMAL,
    by_model JSONB,
    by_agent JSONB,
    daily_usage JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH usage_summary AS (
        SELECT 
            SUM(tokens_total) AS total_tokens,
            SUM(cost_total) AS total_cost
        FROM public.token_usage
        WHERE 
            created_at BETWEEN p_start_date AND p_end_date
            AND (p_user_id IS NULL OR user_id = p_user_id)
    ),
    model_breakdown AS (
        SELECT jsonb_object_agg(
            model,
            jsonb_build_object(
                'tokens', total_tokens,
                'cost', total_cost,
                'requests', request_count
            )
        ) AS by_model
        FROM (
            SELECT 
                model,
                SUM(tokens_total) AS total_tokens,
                SUM(cost_total) AS total_cost,
                COUNT(*) AS request_count
            FROM public.token_usage
            WHERE 
                created_at BETWEEN p_start_date AND p_end_date
                AND (p_user_id IS NULL OR user_id = p_user_id)
            GROUP BY model
        ) t
    ),
    agent_breakdown AS (
        SELECT jsonb_object_agg(
            agent_name,
            jsonb_build_object(
                'tokens', total_tokens,
                'cost', total_cost,
                'interactions', interaction_count
            )
        ) AS by_agent
        FROM (
            SELECT 
                a.name AS agent_name,
                SUM(tu.tokens_total) AS total_tokens,
                SUM(tu.cost_total) AS total_cost,
                COUNT(DISTINCT tu.interaction_id) AS interaction_count
            FROM public.token_usage tu
            JOIN public.ai_agents a ON tu.agent_id = a.id
            WHERE 
                tu.created_at BETWEEN p_start_date AND p_end_date
                AND (p_user_id IS NULL OR tu.user_id = p_user_id)
            GROUP BY a.name
        ) t
    ),
    daily_breakdown AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'date', usage_date,
                'tokens', daily_tokens,
                'cost', daily_cost
            ) ORDER BY usage_date
        ) AS daily_usage
        FROM (
            SELECT 
                DATE(created_at) AS usage_date,
                SUM(tokens_total) AS daily_tokens,
                SUM(cost_total) AS daily_cost
            FROM public.token_usage
            WHERE 
                created_at BETWEEN p_start_date AND p_end_date
                AND (p_user_id IS NULL OR user_id = p_user_id)
            GROUP BY DATE(created_at)
        ) t
    )
    SELECT 
        us.total_tokens,
        us.total_cost,
        mb.by_model,
        ab.by_agent,
        db.daily_usage
    FROM usage_summary us, model_breakdown mb, agent_breakdown ab, daily_breakdown db;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS
ALTER TABLE public.query_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.token_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_metrics ENABLE ROW LEVEL SECURITY;

-- Query cache policies
CREATE POLICY "Users can view own cache entries" 
    ON public.query_cache FOR SELECT 
    USING (user_id = auth.uid() OR user_id IS NULL);

-- Token usage policies
CREATE POLICY "Users can view own token usage" 
    ON public.token_usage FOR SELECT 
    USING (user_id = auth.uid());

-- System metrics policies (admin only)
CREATE POLICY "Admins can view system metrics" 
    ON public.system_metrics FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND role IN ('admin', 'manager')
        )
    );

-- =====================================================
-- SCHEDULED JOBS (using pg_cron if available)
-- =====================================================

-- Note: These require pg_cron extension
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule cache cleanup every hour
-- SELECT cron.schedule('cleanup-cache', '0 * * * *', 'SELECT public.cleanup_expired_cache();');

-- Schedule old token usage cleanup monthly
-- SELECT cron.schedule('cleanup-token-usage', '0 0 1 * *', 
--     'DELETE FROM public.token_usage WHERE created_at < CURRENT_TIMESTAMP - INTERVAL ''90 days'';');

-- Schedule metrics aggregation daily
-- SELECT cron.schedule('aggregate-metrics', '0 2 * * *', 
--     'INSERT INTO public.system_metrics (metric_type, metric_name, metric_value, unit, tags)
--      SELECT ''cache_hit'', ''daily_hit_rate'', AVG(hit_count), ''percentage'', 
--             jsonb_build_object(''date'', CURRENT_DATE - 1)
--      FROM public.query_cache 
--      WHERE DATE(created_at) = CURRENT_DATE - 1;');