# ABFINI V0.1 — Brique 2.3 : Recherche sémantique

La recherche transforme une question en embedding puis interroge PostgreSQL/pgvector via la fonction RPC `match_document_chunks`.

```text
Question
  ↓
EmbeddingProvider.embed_query()
  ↓
vector(1536)
  ↓
match_document_chunks()
  ↓
Top-K chunks
  ↓
Contexte RAG
```

Le moteur ne dépend pas d'un fournisseur LLM particulier. La couche d'embedding reste interchangeable.

## Paramètres

- `limit` : nombre maximal de chunks retournés (Top-K)
- `threshold` : similarité cosine minimale
- dimension attendue : 1536

La recherche ne génère pas encore de réponse : elle fournit uniquement le contexte pertinent au futur module RAG.
