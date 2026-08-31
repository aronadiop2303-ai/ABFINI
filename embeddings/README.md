# ABFINI V0.1 — Embeddings + pgvector

## Brique 2 — fondation vectorielle

Les `document_chunks` disposent maintenant d'une colonne `embedding vector(1536)` dans PostgreSQL grâce à l'extension `pgvector`.

### Pipeline

```text
Document
  ↓
Chunks
  ↓
Embedding provider
  ↓
1536 dimensions
  ↓
PostgreSQL / pgvector
  ↓
HNSW cosine index
  ↓
Recherche sémantique
```

## Important

Le fournisseur d'embeddings reste abstrait. Aucun fournisseur LLM ni aucune clé API n'est codé en dur ici.

Le modèle d'embeddings choisi pour la production doit produire exactement 1536 dimensions, ou une migration de schéma devra adapter la dimension.

## Prochaine étape

Implémenter l'interface `EmbeddingProvider`, puis un worker qui transforme les chunks sans embedding en vecteurs et les enregistre dans `document_chunks`.
