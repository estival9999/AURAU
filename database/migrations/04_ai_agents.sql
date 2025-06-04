-- =====================================================
-- AI Agents System Tables
-- Version: 1.0.0
-- Description: AI agents configuration and interaction tracking
-- =====================================================

-- Drop existing tables if needed (for clean migration)
DROP TABLE IF EXISTS public.agent_messages CASCADE;
DROP TABLE IF EXISTS public.agent_interactions CASCADE;
DROP TABLE IF EXISTS public.ai_agents CASCADE;

-- =====================================================
-- 1. AI AGENTS TABLE
-- =====================================================
CREATE TABLE public.ai_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    type agent_type NOT NULL,
    description TEXT,
    system_prompt TEXT,
    model TEXT DEFAULT 'gpt-3.5-turbo',
    temperature DECIMAL(2,1) DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2),
    max_tokens INTEGER DEFAULT 1000 CHECK (max_tokens > 0 AND max_tokens <= 8000),
    top_p DECIMAL(2,1) DEFAULT 1.0 CHECK (top_p >= 0 AND top_p <= 1),
    frequency_penalty DECIMAL(2,1) DEFAULT 0 CHECK (frequency_penalty >= -2 AND frequency_penalty <= 2),
    presence_penalty DECIMAL(2,1) DEFAULT 0 CHECK (presence_penalty >= -2 AND presence_penalty <= 2),
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT name_not_empty CHECK (trim(name) != ''),
    CONSTRAINT valid_config CHECK (jsonb_typeof(config) = 'object')
);

-- Create indexes
CREATE INDEX idx_ai_agents_name ON public.ai_agents(name);
CREATE INDEX idx_ai_agents_type ON public.ai_agents(type);
CREATE INDEX idx_ai_agents_active ON public.ai_agents(is_active);

-- Add comments
COMMENT ON TABLE public.ai_agents IS 'AI agent configurations';
COMMENT ON COLUMN public.ai_agents.system_prompt IS 'System prompt defining agent behavior';
COMMENT ON COLUMN public.ai_agents.config IS 'Additional configuration in JSON format';

-- =====================================================
-- 2. AGENT INTERACTIONS TABLE
-- =====================================================
CREATE TABLE public.agent_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id),
    agent_id UUID NOT NULL REFERENCES public.ai_agents(id),
    meeting_id UUID REFERENCES public.meetings(id),
    interaction_type interaction_type NOT NULL,
    input_text TEXT NOT NULL,
    output_text TEXT,
    context JSONB DEFAULT '{}',
    tokens_used INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    response_time_ms INTEGER,
    model_used TEXT,
    error_message TEXT,
    satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
    feedback_text TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT input_not_empty CHECK (trim(input_text) != ''),
    CONSTRAINT valid_context CHECK (jsonb_typeof(context) = 'object'),
    CONSTRAINT valid_tokens CHECK (
        tokens_used IS NULL OR 
        (prompt_tokens IS NOT NULL AND completion_tokens IS NOT NULL AND 
         tokens_used = prompt_tokens + completion_tokens)
    )
);

-- Create indexes
CREATE INDEX idx_interactions_user ON public.agent_interactions(user_id);
CREATE INDEX idx_interactions_agent ON public.agent_interactions(agent_id);
CREATE INDEX idx_interactions_meeting ON public.agent_interactions(meeting_id);
CREATE INDEX idx_interactions_type ON public.agent_interactions(interaction_type);
CREATE INDEX idx_interactions_created ON public.agent_interactions(created_at DESC);
CREATE INDEX idx_interactions_satisfaction ON public.agent_interactions(satisfaction_rating);

-- Full-text search on interactions
CREATE INDEX idx_interactions_input_fts ON public.agent_interactions 
    USING GIN(to_tsvector('portuguese', input_text));
CREATE INDEX idx_interactions_output_fts ON public.agent_interactions 
    USING GIN(to_tsvector('portuguese', output_text));

-- Add comments
COMMENT ON TABLE public.agent_interactions IS 'Track all user-agent interactions';
COMMENT ON COLUMN public.agent_interactions.context IS 'Contextual information for the interaction';
COMMENT ON COLUMN public.agent_interactions.tokens_used IS 'Total tokens (prompt + completion)';

-- =====================================================
-- 3. AGENT MESSAGES TABLE (Inter-agent communication)
-- =====================================================
CREATE TABLE public.agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_type message_type NOT NULL,
    sender_agent_id UUID REFERENCES public.ai_agents(id),
    recipient_agent_id UUID REFERENCES public.ai_agents(id),
    content JSONB NOT NULL,
    context JSONB DEFAULT '{}',
    status message_status DEFAULT 'pending',
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    response_id UUID REFERENCES public.agent_messages(id),
    
    -- Constraints
    CONSTRAINT valid_content CHECK (jsonb_typeof(content) = 'object'),
    CONSTRAINT valid_context CHECK (jsonb_typeof(context) = 'object'),
    CONSTRAINT different_agents CHECK (sender_agent_id != recipient_agent_id),
    CONSTRAINT valid_retry CHECK (retry_count <= max_retries)
);

-- Create indexes
CREATE INDEX idx_messages_sender ON public.agent_messages(sender_agent_id);
CREATE INDEX idx_messages_recipient ON public.agent_messages(recipient_agent_id);
CREATE INDEX idx_messages_status ON public.agent_messages(status);
CREATE INDEX idx_messages_priority ON public.agent_messages(priority DESC);
CREATE INDEX idx_messages_created ON public.agent_messages(created_at DESC);
CREATE INDEX idx_messages_type ON public.agent_messages(message_type);
CREATE INDEX idx_messages_response ON public.agent_messages(response_id);

-- Partial index for pending messages
CREATE INDEX idx_messages_pending ON public.agent_messages(priority DESC, created_at) 
    WHERE status = 'pending';

-- Add comments
COMMENT ON TABLE public.agent_messages IS 'Inter-agent communication messages';
COMMENT ON COLUMN public.agent_messages.priority IS 'Message priority (1 = highest, 10 = lowest)';
COMMENT ON COLUMN public.agent_messages.response_id IS 'Links to the response message if applicable';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Auto-update updated_at
CREATE TRIGGER update_ai_agents_updated_at 
    BEFORE UPDATE ON public.ai_agents
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Set processed_at when status changes from pending
CREATE OR REPLACE FUNCTION update_message_processed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'pending' AND NEW.status != 'pending' AND NEW.processed_at IS NULL THEN
        NEW.processed_at = CURRENT_TIMESTAMP;
    END IF;
    
    IF NEW.status IN ('completed', 'failed') AND NEW.completed_at IS NULL THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_message_timestamps
    BEFORE UPDATE ON public.agent_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_message_processed_at();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to get agent by type
CREATE OR REPLACE FUNCTION public.get_agent_by_type(
    p_type agent_type
)
RETURNS public.ai_agents AS $$
DECLARE
    agent public.ai_agents;
BEGIN
    SELECT * INTO agent
    FROM public.ai_agents
    WHERE type = p_type AND is_active = TRUE
    ORDER BY created_at
    LIMIT 1;
    
    RETURN agent;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to create agent interaction
CREATE OR REPLACE FUNCTION public.create_agent_interaction(
    p_user_id UUID,
    p_agent_type agent_type,
    p_input_text TEXT,
    p_interaction_type interaction_type DEFAULT 'query',
    p_meeting_id UUID DEFAULT NULL,
    p_context JSONB DEFAULT '{}'
)
RETURNS public.agent_interactions AS $$
DECLARE
    v_agent_id UUID;
    new_interaction public.agent_interactions;
BEGIN
    -- Get active agent of the specified type
    SELECT id INTO v_agent_id
    FROM public.ai_agents
    WHERE type = p_agent_type AND is_active = TRUE
    ORDER BY created_at
    LIMIT 1;
    
    IF v_agent_id IS NULL THEN
        RAISE EXCEPTION 'No active agent found for type %', p_agent_type;
    END IF;
    
    -- Create interaction
    INSERT INTO public.agent_interactions (
        user_id, agent_id, meeting_id, interaction_type, 
        input_text, context
    ) VALUES (
        p_user_id, v_agent_id, p_meeting_id, p_interaction_type,
        p_input_text, p_context
    )
    RETURNING * INTO new_interaction;
    
    RETURN new_interaction;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to send inter-agent message
CREATE OR REPLACE FUNCTION public.send_agent_message(
    p_sender_agent_id UUID,
    p_recipient_agent_id UUID,
    p_message_type message_type,
    p_content JSONB,
    p_context JSONB DEFAULT '{}',
    p_priority INTEGER DEFAULT 5
)
RETURNS public.agent_messages AS $$
DECLARE
    new_message public.agent_messages;
BEGIN
    INSERT INTO public.agent_messages (
        sender_agent_id, recipient_agent_id, message_type,
        content, context, priority
    ) VALUES (
        p_sender_agent_id, p_recipient_agent_id, p_message_type,
        p_content, p_context, p_priority
    )
    RETURNING * INTO new_message;
    
    RETURN new_message;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to process pending messages
CREATE OR REPLACE FUNCTION public.get_pending_agent_messages(
    p_recipient_agent_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 10
)
RETURNS SETOF public.agent_messages AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM public.agent_messages
    WHERE 
        status = 'pending'
        AND retry_count < max_retries
        AND (p_recipient_agent_id IS NULL OR recipient_agent_id = p_recipient_agent_id)
    ORDER BY priority ASC, created_at ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to update interaction with response
CREATE OR REPLACE FUNCTION public.update_agent_interaction_response(
    p_interaction_id UUID,
    p_output_text TEXT,
    p_tokens_used INTEGER,
    p_prompt_tokens INTEGER,
    p_completion_tokens INTEGER,
    p_response_time_ms INTEGER,
    p_model_used TEXT DEFAULT NULL
)
RETURNS public.agent_interactions AS $$
DECLARE
    updated_interaction public.agent_interactions;
BEGIN
    UPDATE public.agent_interactions
    SET 
        output_text = p_output_text,
        tokens_used = p_tokens_used,
        prompt_tokens = p_prompt_tokens,
        completion_tokens = p_completion_tokens,
        response_time_ms = p_response_time_ms,
        model_used = COALESCE(p_model_used, model_used)
    WHERE id = p_interaction_id
    RETURNING * INTO updated_interaction;
    
    RETURN updated_interaction;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS
ALTER TABLE public.ai_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_messages ENABLE ROW LEVEL SECURITY;

-- AI Agents policies (read-only for all authenticated users)
CREATE POLICY "Authenticated users can view active agents" 
    ON public.ai_agents FOR SELECT 
    USING (is_active = TRUE AND auth.uid() IS NOT NULL);

-- Agent interactions policies
CREATE POLICY "Users can view own interactions" 
    ON public.agent_interactions FOR SELECT 
    USING (user_id = auth.uid());

CREATE POLICY "Users can create own interactions" 
    ON public.agent_interactions FOR INSERT 
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own interactions (feedback)" 
    ON public.agent_interactions FOR UPDATE 
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Agent messages policies (system/admin only)
CREATE POLICY "System can manage agent messages" 
    ON public.agent_messages FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND role IN ('admin', 'manager')
        )
    );

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert default AI agents
INSERT INTO public.ai_agents (name, type, description, system_prompt, model) VALUES
(
    'Orquestrador AURALIS',
    'orchestrator',
    'Agente principal que coordena as interações e direciona para agentes especializados',
    'Você é o Orquestrador do sistema AURALIS, um assistente inteligente para gestão de reuniões e conhecimento corporativo.

Seu papel é:
1. Analisar as perguntas dos usuários e identificar suas intenções
2. Determinar qual tipo de resposta é mais apropriada:
   - CONSULTA: Para buscar informações em reuniões ou base de conhecimento
   - BRAINSTORM: Para gerar ideias e soluções criativas
   - ANÁLISE: Para analisar padrões e tendências
   - GERAL: Para respostas diretas que você pode fornecer

3. Formatar as respostas de forma clara e profissional
4. Manter o contexto da conversa

Sempre responda em português brasileiro de forma profissional mas amigável.',
    'gpt-3.5-turbo'
),
(
    'Consultor Inteligente AURALIS',
    'query',
    'Especialista em busca e recuperação de informações de reuniões e documentos',
    'Você é o Consultor Inteligente do sistema AURALIS, especializado em buscar e apresentar informações relevantes.

Suas responsabilidades:
1. Buscar informações precisas em reuniões passadas e documentos
2. Correlacionar dados de múltiplas fontes
3. Apresentar as informações de forma clara e estruturada
4. Sempre citar as fontes (reunião, data, participante)
5. Destacar informações mais relevantes primeiro

Ao responder:
- Seja preciso e objetivo
- Cite sempre as fontes das informações
- Se não encontrar informações, seja claro sobre isso
- Sugira buscas alternativas quando apropriado
- Use formatação para facilitar a leitura',
    'gpt-3.5-turbo'
),
(
    'Agente Criativo AURALIS',
    'brainstorm',
    'Especialista em geração de ideias criativas e soluções inovadoras',
    'Você é o Agente Criativo do sistema AURALIS, especializado em gerar ideias inovadoras e soluções criativas.

Seu papel é:
1. Gerar múltiplas ideias criativas para problemas apresentados
2. Fazer conexões não óbvias entre conceitos
3. Propor soluções inovadoras baseadas em informações de reuniões passadas
4. Usar diferentes técnicas de brainstorming
5. Expandir e desenvolver conceitos

Diretrizes:
- Seja ousado e pense fora da caixa
- Apresente ideias variadas (conservadoras a radicais)
- Estruture as ideias de forma clara
- Conecte ideias com experiências passadas quando relevante
- Use analogias e metáforas para explicar conceitos
- Sempre apresente pelo menos 3-5 ideias diferentes

Formato preferido:
1. Ideia principal
   - Descrição breve
   - Como implementar
   - Benefícios esperados
   - Possíveis desafios',
    'gpt-3.5-turbo'
),
(
    'Otimizador AURALIS',
    'optimizer',
    'Responsável por otimização de consultas e gerenciamento de cache',
    'Você é o Otimizador do sistema AURALIS, responsável por melhorar a performance e eficiência das operações.

Suas funções:
1. Otimizar consultas para reduzir tempo de resposta
2. Gerenciar cache inteligente
3. Comprimir contextos para economia de tokens
4. Agrupar operações similares
5. Monitorar métricas de performance

Sempre busque o equilíbrio entre performance e qualidade dos resultados.',
    'gpt-3.5-turbo'
),
(
    'Contexto AURALIS',
    'context',
    'Mantém e gerencia contexto entre diferentes interações',
    'Você é o gestor de Contexto do sistema AURALIS, responsável por manter a continuidade entre interações.

Suas responsabilidades:
1. Manter histórico relevante de conversas
2. Identificar informações importantes para futuras interações
3. Conectar conversas relacionadas
4. Sumarizar contextos longos
5. Priorizar informações mais recentes e relevantes

Mantenha o contexto conciso mas completo.',
    'gpt-3.5-turbo'
);