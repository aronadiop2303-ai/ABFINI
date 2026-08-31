# ABFINI V0.1 — Document Storage

Brique 1.3/1.4 : stockage séparé du fichier original et des données normalisées.

## Architecture

```text
Document uploadé
      ↓
Supabase Storage
      │
      └── storage_path
             ↓
       PostgreSQL
       ├── documents
       └── document_chunks
```

## Règles

- Le fichier original est conservé dans Supabase Storage.
- PostgreSQL conserve les métadonnées, le texte normalisé et les chunks.
- `storage_path` relie l'enregistrement PostgreSQL au fichier original.
- Aucun secret, token ou clé API ne doit être commité dans GitHub.
- L'accès aux documents doit rester contrôlé par RLS et les permissions ABFINI.

## Bucket recommandé

`documents`

Organisation recommandée :

`documents/<document_id>/original/<filename>`

Cette couche sera utilisée ensuite par le pipeline d'embeddings et pgvector.
