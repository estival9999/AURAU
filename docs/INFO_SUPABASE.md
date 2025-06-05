# 📊 INFO_SUPABASE - ESTRUTURA DETALHADA DAS TABELAS

## 🎯 VISÃO GERAL
Este documento contém o detalhamento completo de todas as tabelas do banco de dados Supabase para o sistema AURALIS, incluindo tipos de dados, descrições e exemplos práticos.

──────────────────────────────────────────────────────────────────────────────────────────────────

## 1️⃣ TABELA `users` - Dados dos Usuários

### 📋 Descrição
Armazena informações de autenticação e perfil dos usuários do sistema.

### 📊 Estrutura de Campos

| Campo         | Tipo         | Descrição                      | Exemplo                              |
|:--------------|:-------------|:-------------------------------|:-------------------------------------|
| id            | UUID         | Identificador único do usuário | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 |
| username      | VARCHAR(50)  | Nome de usuário único (login)  | joao.silva                           |
| password_hash | TEXT         | Senha criptografada (hash)     | $2b$10$... (bcrypt hash)             |
| email         | VARCHAR(100) | Email único do usuário         | joao.silva@empresa.com               |
| full_name     | VARCHAR(100) | Nome completo                  | João Carlos Silva                    |
| role          | VARCHAR(50)  | Cargo/função na empresa        | Gerente de Projetos                  |
| department    | VARCHAR(50)  | Departamento/área              | Tecnologia                           |
| created_at    | TIMESTAMP    | Data/hora de criação           | 2024-01-15 10:30:00                  |
| last_login    | TIMESTAMP    | Último acesso ao sistema       | 2024-01-20 14:45:00                  |
| is_active     | BOOLEAN      | Se usuário está ativo          | true                                 |

### 🔧 Funções SQL Relacionadas
```sql
-- Exemplo de inserção
INSERT INTO users (username, password_hash, email, full_name, role, department)
VALUES ('joao.silva', '$2b$10$...', 'joao.silva@empresa.com', 'João Carlos Silva', 'Gerente de Projetos', 'Tecnologia');

-- Exemplo de consulta
SELECT * FROM users WHERE username = 'joao.silva' AND is_active = true;
```

──────────────────────────────────────────────────────────────────────────────────────────────────

## 2️⃣ TABELA `meetings` - Histórico de Reuniões

### 📋 Descrição
Armazena todas as reuniões gravadas, suas transcrições, análises e metadados.

### 📊 Estrutura de Campos

| Campo                 | Tipo         | Descrição                         | Exemplo                                                        |
|:----------------------|:-------------|:----------------------------------|:---------------------------------------------------------------|
| id                    | UUID         | Identificador único da reunião    | b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22                          |
| user_id               | UUID         | ID do organizador (FK → users)    | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11                          |
| title                 | VARCHAR(200) | Título da reunião                 | Planejamento Sprint Q1 2024                                    |
| start_time            | TIMESTAMP    | Início da reunião                 | 2024-01-20 14:00:00                                            |
| end_time              | TIMESTAMP    | Fim da reunião                    | 2024-01-20 15:30:00                                            |
| duration_seconds      | INTEGER      | Duração em segundos               | 5400 (1h30min)                                                 |
| status                | VARCHAR(20)  | Estado da reunião                 | completed                                                      |
| observations          | TEXT         | Observações/notas                 | Reunião com foco em OKRs                                       |
| transcription_full    | TEXT         | Transcrição completa              | [João]: Vamos começar revisando...                             |
| transcription_summary | TEXT         | Resumo executivo                  | Reunião focou em definir OKRs para Q1...                       |
| key_points            | TEXT[]       | Principais pontos (array)         | ["Definir 3 OKRs principais", "Aumentar receita em 20%"]       |
| decisions             | TEXT[]       | Decisões tomadas (array)          | ["Aprovar orçamento de R$50k", "Contratar 2 devs"]             |
| action_items          | JSONB        | Ações com responsáveis            | [{"action": "Criar roadmap", "responsible": "Maria", "deadline": "2024-01-25"}] |
| participants          | TEXT[]       | Lista de participantes            | ["João Silva", "Maria Santos", "Pedro Costa"]                  |
| embedding             | vector(1536) | Vetor para busca semântica        | [0.1, -0.2, 0.3, ...] (1536 dimensões)                          |
| created_at            | TIMESTAMP    | Data de criação do registro       | 2024-01-20 15:35:00                                             |
| updated_at            | TIMESTAMP    | Última atualização                | 2024-01-20 16:00:00                                             |

### 🔧 Funções SQL Relacionadas
```sql
-- Inserir nova reunião
INSERT INTO meetings (user_id, title, start_time, status, observations)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Daily Standup', NOW(), 'recording', 'Reunião diária da equipe');

-- Buscar reuniões recentes
SELECT id, title, start_time, duration_seconds 
FROM meetings 
WHERE user_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
ORDER BY start_time DESC 
LIMIT 10;

-- Busca semântica
SELECT * FROM search_similar_meetings('[0.1, -0.2, ...]'::vector(1536), 5);
```

──────────────────────────────────────────────────────────────────────────────────────────────────

## 3️⃣ TABELA `knowledge_base` - Base de Conhecimento Corporativo

### 📋 Descrição
Armazena documentos corporativos, políticas, procedimentos e manuais com suporte a busca semântica.

### 📊 Estrutura de Campos

| Campo            | Tipo         | Descrição                    | Exemplo                                                       |
|:-----------------|:-------------|:-----------------------------|:--------------------------------------------------------------|
| id               | UUID         | Identificador único          | c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33                         |
| doc_type         | VARCHAR(50)  | Tipo de documento            | policy                                                        |
| title            | VARCHAR(200) | Título do documento          | Política de Trabalho Remoto                                   |
| content_full     | TEXT         | Conteúdo completo            | A empresa permite trabalho remoto...                          |
| content_summary  | TEXT         | Resumo do conteúdo           | Política define regras para home office...                    |
| content_chunks   | JSONB        | Documento dividido em partes | [{"chunk_id": 1, "text": "Capítulo 1...", "embedding": [...]}] |
| tags             | TEXT[]       | Palavras-chave               | ["trabalho-remoto", "rh", "benefícios"]                       |
| department       | VARCHAR(50)  | Departamento relacionado     | Recursos Humanos                                              |
| category         | VARCHAR(100) | Categoria do documento       | Políticas Internas                                            |
| version          | VARCHAR(20)  | Versão do documento          | 2.5                                                           |
| is_current       | BOOLEAN      | Se é versão atual            | true                                                          |
| chunk_embeddings | JSONB        | Embeddings por chunk         | {"chunk_1": [0.1, -0.2...], "chunk_2": [...]}                |
| created_at       | TIMESTAMP    | Data de criação              | 2024-01-10 09:00:00                                           |
| updated_at       | TIMESTAMP    | Última atualização           | 2024-01-15 11:30:00                                           |
| created_by       | UUID         | Quem criou (FK → users)      | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11                         |

### 🔧 Funções SQL Relacionadas
```sql
-- Inserir novo documento
INSERT INTO knowledge_base (doc_type, title, content_full, tags, department, created_by)
VALUES ('policy', 'Política de Férias', 'Todos os funcionários têm direito...', 
        ARRAY['férias', 'rh', 'benefícios'], 'Recursos Humanos', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');

-- Buscar documentos por tag
SELECT id, title, content_summary 
FROM knowledge_base 
WHERE 'trabalho-remoto' = ANY(tags) AND is_current = true;

-- Busca textual em chunks
SELECT * FROM search_knowledge_chunks('home office', 'Recursos Humanos', 10);
```

──────────────────────────────────────────────────────────────────────────────────────────────────

## 4️⃣ TABELA `ai_interactions` - Histórico de Conversas com IA

### 📋 Descrição
Registra todas as interações dos usuários com o assistente AURALIS, incluindo contexto e métricas.

### 📊 Estrutura de Campos

| Campo            | Tipo        | Descrição                         | Exemplo                                                         |
|:-----------------|:------------|:----------------------------------|:----------------------------------------------------------------|
| id               | UUID        | Identificador único               | d3eebc99-9c0b-4ef8-bb6d-6bb9bd380a44                           |
| user_id          | UUID        | ID do usuário (FK → users)        | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11                           |
| meeting_id       | UUID        | ID reunião relacionada (opcional) | b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22                           |
| user_message     | TEXT        | Pergunta do usuário               | Quais foram as principais decisões da última reunião?           |
| ai_response      | TEXT        | Resposta da AURALIS               | As principais decisões foram: 1) Aprovar orçamento...          |
| context_used     | JSONB       | Contexto RAG utilizado            | {"meetings": ["b1ee..."], "knowledge": ["c2ee..."], "chunks": [...]} |
| response_time_ms | INTEGER     | Tempo de resposta (ms)            | 1250                                                            |
| tokens_used      | INTEGER     | Tokens consumidos                 | 485                                                             |
| model_used       | VARCHAR(50) | Modelo IA utilizado               | gpt-4-turbo                                                     |
| created_at       | TIMESTAMP   | Data/hora da interação            | 2024-01-20 16:15:30                                             |

### 🔧 Funções SQL Relacionadas
```sql
-- Registrar nova interação
INSERT INTO ai_interactions (user_id, user_message, ai_response, response_time_ms, tokens_used, model_used)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 
        'Resumir última reunião', 
        'A última reunião focou em...', 
        1250, 485, 'gpt-4-turbo');

-- Buscar histórico de conversas
SELECT user_message, ai_response, created_at 
FROM ai_interactions 
WHERE user_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' 
ORDER BY created_at DESC 
LIMIT 20;

-- Análise de uso
SELECT 
    COUNT(*) as total_interactions,
    SUM(tokens_used) as total_tokens,
    AVG(response_time_ms) as avg_response_time
FROM ai_interactions 
WHERE user_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' 
AND created_at >= NOW() - INTERVAL '30 days';
```

──────────────────────────────────────────────────────────────────────────────────────────────────

## 🔍 FUNÇÕES AUXILIARES PARA BUSCA RAG

### search_similar_meetings
```sql
-- Busca reuniões similares usando embeddings
SELECT * FROM search_similar_meetings(
    query_embedding := '[0.1, -0.2, ...]'::vector(1536),
    limit_results := 5
);
```

### search_knowledge_chunks
```sql
-- Busca chunks de conhecimento relevantes
SELECT * FROM search_knowledge_chunks(
    query_text := 'política de férias',
    department_filter := 'Recursos Humanos',
    limit_results := 10
);
```

──────────────────────────────────────────────────────────────────────────────────────────────────

## 📈 ÍNDICES PARA OTIMIZAÇÃO

```sql
-- Índices de performance
CREATE INDEX idx_meetings_user_id ON meetings(user_id);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_created_at ON meetings(created_at DESC);
CREATE INDEX idx_meetings_key_points ON meetings USING GIN(key_points);
CREATE INDEX idx_meetings_participants ON meetings USING GIN(participants);

CREATE INDEX idx_knowledge_tags ON knowledge_base USING GIN(tags);
CREATE INDEX idx_knowledge_department ON knowledge_base(department);
CREATE INDEX idx_knowledge_current ON knowledge_base(is_current);

CREATE INDEX idx_ai_interactions_user ON ai_interactions(user_id);
CREATE INDEX idx_ai_interactions_meeting ON ai_interactions(meeting_id);
CREATE INDEX idx_ai_interactions_created ON ai_interactions(created_at DESC);
```

──────────────────────────────────────────────────────────────────────────────────────────────────

## 🛡️ SEGURANÇA - ROW LEVEL SECURITY (RLS)

```sql
-- Habilitar RLS em todas as tabelas
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_interactions ENABLE ROW LEVEL SECURITY;

-- Política exemplo: usuários só veem suas próprias reuniões
CREATE POLICY "Users can view own meetings" ON meetings
    FOR SELECT USING (auth.uid() = user_id);

-- Política exemplo: todos podem ler base de conhecimento
CREATE POLICY "Everyone can read knowledge base" ON knowledge_base
    FOR SELECT USING (is_current = true);
```

──────────────────────────────────────────────────────────────────────────────────────────────────

## 📝 NOTAS IMPORTANTES

1. **Extensões Necessárias**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "vector";
   ```

2. **Limites de Tamanho**:
   - Campos TEXT: até 1GB
   - Arrays: recomendado até 1000 elementos
   - JSONB: até 1GB, mas mantenha chunks pequenos

3. **Performance**:
   - Use índices GIN para arrays e JSONB
   - Embeddings: considere índice IVFFlat para grandes volumes
   - Particione tabelas grandes por data se necessário

4. **Backup**:
   - Configure backup automático no Supabase
   - Exporte estrutura e dados regularmente
   - Teste restauração periodicamente

──────────────────────────────────────────────────────────────────────────────────────────────────