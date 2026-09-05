# ABFINI V0.1 — Embeddings + pgvector

## Brique 2 — fondation vectorielle

Les `document_chunks` disposent maintenant d'une colonne `embedding vector(768)` dans PostgreSQL grâce à l'extension `pgvector`.

### Brique 2.1 — contrat provider

ABFINI utilise une interface `EmbeddingProvider` indépendante du fournisseur. Le cœur du pipeline ne dépend donc d'aucun fournisseur LLM.

- `embed(texts)` : un vecteur par texte, dans le même ordre.
- `embed_query(text)` : vecteur d'une requête.
- `model` : identifiant du modèle utilisé.
- `dimensions` : dimension du vecteur, compatible avec pgvector.

### Pipeline

```text
Document
  ↓
Chunks
  ↓
EmbeddingProvider
  ↓
768 dimensions
  ↓
PostgreSQL / pgvector
  ↓
HNSW cosine index
  ↓
Recherche sémantique
```

## Important

Aucune clé API et aucun fournisseur n'est codé en dur dans le cœur d'ABFINI. Le provider concret sera ajouté après validation du modèle d'embeddings choisi.

Le modèle de production doit produire exactement 768 dimensions, ou une migration de schéma devra adapter la dimension.

## Prochaine étape

Implémenter un provider concret et un worker qui transforme les chunks sans embedding en vecteurs puis les enregistre dans `document_chunks`.
