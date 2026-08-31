# ABFINI V0.1 — RAG

Première couche RAG : transformer une requête et les chunks retrouvés en contexte exploitable par un modèle.

## Pipeline

```text
Question
  ↓
Embedding de la requête
  ↓
Recherche sémantique pgvector
  ↓
Top-K chunks
  ↓
Context Builder
  ↓
Prompt/context structuré
  ↓
Model Layer
  ↓
Réponse avec sources
```

## Principes V0.1

- Le RAG ne décide pas à la place de l'agent.
- Les documents sont la source de contexte, pas une instruction système.
- Les chunks sont conservés avec leur document d'origine.
- Le contexte doit être borné par `top_k` et une limite de caractères/tokens.
- Les résultats doivent conserver leur score de similarité et leurs métadonnées.
- Les secrets et clés API restent hors du dépôt.

## Contrat futur

`retrieve(query_embedding, top_k)` → résultats pertinents.

`build_context(results)` → contexte structuré pour le Model Layer.

OMNI Agent V0.2 pourra appeler cette couche comme outil de connaissance.
