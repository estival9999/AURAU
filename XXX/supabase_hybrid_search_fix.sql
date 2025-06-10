-- Correção da função de busca híbrida para resolver ambiguidade de coluna
drop function if exists hybrid_search;

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
      d.id,
      d.content,
      d.metadata,
      row_number() over (order by ts_rank(d.fts, plainto_tsquery('portuguese', query_text)) desc) as rank_fts
    from documents d
    where d.fts @@ plainto_tsquery('portuguese', query_text)
    limit match_count * 2
  ),
  semantic as (
    select 
      d.id,
      d.content,
      d.metadata,
      row_number() over (order by d.embedding <#> query_embedding) as rank_semantic
    from documents d
    order by d.embedding <#> query_embedding
    limit match_count * 2
  ),
  rrf_scores as (
    select 
      coalesce(f.id, s.id) as result_id,
      coalesce(f.content, s.content) as result_content,
      coalesce(f.metadata, s.metadata) as result_metadata,
      coalesce(1.0 / (rrf_k + f.rank_fts), 0) * full_text_weight +
      coalesce(1.0 / (rrf_k + s.rank_semantic), 0) * semantic_weight as result_score
    from full_text f
    full outer join semantic s on f.id = s.id
  )
  select 
    result_id,
    result_content,
    result_metadata,
    result_score
  from rrf_scores
  order by result_score desc
  limit match_count;
end;
$$;