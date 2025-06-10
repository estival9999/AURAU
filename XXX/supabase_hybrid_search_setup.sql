-- Configuração completa para Busca Híbrida no Supabase
-- Este script deve ser executado no SQL Editor do Supabase

-- 1. Habilitar extensões necessárias
create extension if not exists vector;

-- 2. Criar tabela de documentos com suporte para busca híbrida
create table if not exists documents (
  id bigint primary key generated always as identity,
  content text not null,
  metadata jsonb,
  created_at timestamp with time zone default now(),
  -- Campo para busca full-text (gerado automaticamente)
  fts tsvector generated always as (to_tsvector('portuguese', content)) stored,
  -- Campo para embeddings (vetores de 512 dimensões)
  embedding vector(512)
);

-- 3. Criar índices para otimizar as buscas
-- Índice para busca full-text
create index if not exists documents_fts_idx on documents using gin(fts);

-- Índice para busca semântica (usando HNSW para melhor performance)
create index if not exists documents_embedding_idx on documents 
  using hnsw (embedding vector_ip_ops)
  with (m = 16, ef_construction = 64);

-- 4. Criar função de busca híbrida
create or replace function hybrid_search(
  query_text text,
  query_embedding vector(512),
  match_count int default 10,
  full_text_weight float default 1.0,
  semantic_weight float default 1.0,
  rrf_k int default 50
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  score float
)
language plpgsql
as $$
begin
  return query
  with full_text as (
    select 
      id,
      content,
      metadata,
      row_number() over (order by ts_rank(fts, plainto_tsquery('portuguese', query_text)) desc) as rank_fts
    from documents
    where fts @@ plainto_tsquery('portuguese', query_text)
    limit match_count * 2
  ),
  semantic as (
    select 
      id,
      content,
      metadata,
      row_number() over (order by embedding <#> query_embedding) as rank_semantic
    from documents
    order by embedding <#> query_embedding
    limit match_count * 2
  ),
  rrf_scores as (
    select 
      coalesce(f.id, s.id) as id,
      coalesce(f.content, s.content) as content,
      coalesce(f.metadata, s.metadata) as metadata,
      coalesce(1.0 / (rrf_k + f.rank_fts), 0) * full_text_weight +
      coalesce(1.0 / (rrf_k + s.rank_semantic), 0) * semantic_weight as score
    from full_text f
    full outer join semantic s on f.id = s.id
  )
  select 
    id,
    content,
    metadata,
    score
  from rrf_scores
  order by score desc
  limit match_count;
end;
$$;

-- 5. Função auxiliar para inserir documentos com embeddings
create or replace function insert_document_with_embedding(
  doc_content text,
  doc_embedding vector(512),
  doc_metadata jsonb default null
)
returns bigint
language plpgsql
as $$
declare
  new_id bigint;
begin
  insert into documents (content, embedding, metadata)
  values (doc_content, doc_embedding, doc_metadata)
  returning id into new_id;
  
  return new_id;
end;
$$;

-- 6. Criar view para facilitar consultas
create or replace view documents_search_view as
select 
  id,
  content,
  metadata,
  created_at,
  octet_length(content) as content_size
from documents;

-- 7. Função para análise de performance da busca
create or replace function analyze_search_performance(
  query_text text,
  query_embedding vector(512)
)
returns table (
  search_type text,
  result_count int,
  execution_time interval
)
language plpgsql
as $$
declare
  start_time timestamp;
  end_time timestamp;
begin
  -- Testar busca full-text
  start_time := clock_timestamp();
  perform * from documents 
  where fts @@ plainto_tsquery('portuguese', query_text) 
  limit 10;
  end_time := clock_timestamp();
  
  return query select 
    'full-text'::text,
    (select count(*) from documents where fts @@ plainto_tsquery('portuguese', query_text))::int,
    end_time - start_time;
  
  -- Testar busca semântica
  start_time := clock_timestamp();
  perform * from documents 
  order by embedding <#> query_embedding 
  limit 10;
  end_time := clock_timestamp();
  
  return query select 
    'semantic'::text,
    (select count(*) from documents)::int,
    end_time - start_time;
  
  -- Testar busca híbrida
  start_time := clock_timestamp();
  perform * from hybrid_search(query_text, query_embedding, 10);
  end_time := clock_timestamp();
  
  return query select 
    'hybrid'::text,
    10::int,
    end_time - start_time;
end;
$$;

-- 8. Comentários e instruções
comment on table documents is 'Tabela principal para armazenar documentos com suporte a busca híbrida';
comment on column documents.fts is 'Campo de busca full-text gerado automaticamente';
comment on column documents.embedding is 'Vetor de embedding para busca semântica';
comment on function hybrid_search is 'Função principal para realizar busca híbrida combinando full-text e semântica';