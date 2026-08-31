# Documents — V0.1.2

## Formats supportés

- TXT
- Markdown
- PDF via PyMuPDF
- DOCX via python-docx
- HTML via BeautifulSoup

Pipeline :

`fichier → parser → texte normalisé → métadonnées → chunks → stockage/embeddings`

Dépendances : voir `documents/requirements.txt`.

Cette étape prépare le stockage PostgreSQL/Supabase et les embeddings de la suite d'ABFINI V0.1.
