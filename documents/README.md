# ABFINI V0.1 — Documents

Première brique d'ABFINI V0.1 : ingestion, extraction, normalisation, métadonnées et préparation des documents pour les embeddings et la recherche sémantique.

## Architecture

```text
Document
  ↓
Ingestion
  ↓
Extraction du texte
  ↓
Nettoyage / normalisation
  ↓
Chunking
  ↓
Métadonnées
  ↓
Embeddings (brique suivante)
  ↓
PostgreSQL + pgvector
  ↓
Recherche sémantique / RAG
  ↓
OMNI Agent V0.2
```

## Stack initiale

- Supabase Storage — stockage des fichiers
- PostgreSQL — métadonnées et contenu structuré
- Python — pipeline de traitement
- PyMuPDF — PDF
- python-docx — DOCX
- Markdown/TXT — traitement natif Python
- BeautifulSoup — HTML
- FastAPI — API du pipeline
- Docker — exécution reproductible

## Structure prévue

```text
documents/
├── ingestion/
├── parsers/
├── chunking/
├── metadata/
├── pipeline/
└── tests/
```

## Principe

Cette brique doit rester modulaire afin qu'ABFINI puisse ajouter progressivement OCR, Unstructured et d'autres parseurs sans modifier le cœur du système.

OMNI Agent V0.2 utilisera ultérieurement cette couche via des interfaces/API propres.
