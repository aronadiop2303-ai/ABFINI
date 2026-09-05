-- ABFINI: core content schema for the document + RAG pipeline.
--
-- Introduces `documents` and `document_chunks`, consumed by:
--   - semantic_search_document_chunks (20260902_semantic_search_rpc.sql),
--     which reads dc.id/document_id/chunk_index/content/metadata/embedding;
--   - embeddings/index_supabase.py, which lists chunks pending embedding
--     and writes vectors back via set_document_chunk_embedding.
--
-- Timestamped before 20260902_semantic_search_rpc.sql so a fresh database
-- creates document_chunks before the RPC that references it.

create extension if not exists pgcrypto;
create extension if not exists vector;

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  mime_type text,
  size_bytes bigint,
  content_sha256 text,
  source text,
  storage_path text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  chunk_index integer not null,
  content text not null,
  embedding vector(768),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create index if not exists document_chunks_document_id_idx
  on public.document_chunks (document_id);

-- Cosine distance HNSW index: semantic_search_document_chunks orders by
-- `dc.embedding <=> query_embedding` (cosine distance).
create index if not exists document_chunks_embedding_hnsw_idx
  on public.document_chunks
  using hnsw (embedding vector_cosine_ops);

-- Deny-by-default: RLS on, no policies for anon/authenticated. All access
-- goes through service_role (which bypasses RLS), matching the
-- allowlisted, confirmation-gated access model used elsewhere in ABFINI/OMNI.
alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;

revoke all on public.documents from public, anon, authenticated;
revoke all on public.document_chunks from public, anon, authenticated;
grant select, insert, update, delete on public.documents to service_role;
grant select, insert, update, delete on public.document_chunks to service_role;

-- Consumed by embeddings/index_supabase.py to write a computed embedding
-- back onto a pending chunk without exposing raw vector writes over REST.
create or replace function public.set_document_chunk_embedding(
  chunk_id uuid,
  embedding_text text
)
returns void
language sql
security invoker
set search_path = public
as $$
  update public.document_chunks
  set embedding = embedding_text::vector(768),
      updated_at = now()
  where id = chunk_id;
$$;

revoke all on function public.set_document_chunk_embedding(uuid, text) from public, anon, authenticated;
grant execute on function public.set_document_chunk_embedding(uuid, text) to service_role;
