-- ABFINI: unambiguous REST-facing semantic search RPC.
-- Avoid overloaded PostgREST function signatures by exposing one dedicated name.

create or replace function public.semantic_search_document_chunks(
  query_embedding vector(768),
  match_threshold double precision default 0.0,
  match_count integer default 5
)
returns table (
  id uuid,
  document_id uuid,
  chunk_index integer,
  content text,
  metadata jsonb,
  similarity double precision
)
language sql
stable
security invoker
set search_path = public
as $$
  select
    dc.id,
    dc.document_id,
    dc.chunk_index,
    dc.content,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) as similarity
  from public.document_chunks as dc
  where dc.embedding is not null
    and 1 - (dc.embedding <=> query_embedding) >= match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;

revoke all on function public.semantic_search_document_chunks(vector(768), double precision, integer) from public, anon, authenticated;
grant execute on function public.semantic_search_document_chunks(vector(768), double precision, integer) to service_role;
