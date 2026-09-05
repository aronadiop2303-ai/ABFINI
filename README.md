# ABFINI

Backend Python/FastAPI modulaire : connaissance documentaire → embeddings →
recherche sémantique (Supabase/pgvector) → RAG → génération multi-fournisseur
→ agentisation (OMNI). Voir les README de chaque dossier pour le détail par
module (`documents/`, `embeddings/`, `search/`, `rag/`, `models/`,
`omni-agent/`, `observability/`).

## Structure du dépôt

| Dossier | Rôle |
|---|---|
| `api/` | API HTTP FastAPI (`/health`, `/health/dependencies`, `/v1/chat`) |
| `documents/`, `embeddings/`, `search/`, `rag/`, `models/`, `observability/` | Backend : ingestion, embeddings BGE 768D, recherche vectorielle, pipeline RAG, fournisseurs de génération (DeepSeek/OpenRouter/local), observabilité |
| `omni-agent/` | Agent OMNI (orchestration, permissions, planification), consomme le RAG ABFINI |
| `supabase/migrations/` | Schéma SQL (`document_chunks`, index HNSW, RPC de recherche sémantique) |
| `web/` | Client de test Web minimal, déployé sur Vercel — voir `web/README.md` |
| `mobile-test/` | Client de test mobile Expo Go minimal — voir `mobile-test/README.md` |
| `Dockerfile`, `render.yaml` | Configuration d'hébergement de l'API (préparée, déploiement réel non encore effectué) |

## Lancer les tests localement

```bash
pip install -r api/requirements.txt -r documents/requirements.txt
pip install pytest  # non listé en dépendance de prod, utilisé pour lancer les tests localement
pytest api/test_server.py omni-agent/tests/
python -m models.test_deepseek
python -m models.test_openrouter
python -m models.test_router
python -m observability.test_metrics
python -m rag.test_pipeline
python -m rag.retriever_test
python -m search.ranking_test
python -m documents.tests.test_pipeline
```

`embeddings/run_test.py`, `rag/e2e_supabase_test.py` et `rag/e2e_deepseek_test.py`
nécessitent respectivement un accès réseau à Hugging Face et de vrais secrets
Supabase/DeepSeek — ils tournent en CI (`.github/workflows/`), pas
nécessairement en local selon votre environnement.

## État de l'hébergement

- **API** : tourne en local (`uvicorn api.server:app --host 0.0.0.0 --port 8000`)
  pendant les tests actuels ; hébergement public (Render/Fly.io) préparé
  (`Dockerfile` + `render.yaml`) mais **pas encore déployé**.
- **Web** : déployé sur Vercel — https://abfini-web.vercel.app — en attente
  que `ABFINI_API_URL`/`ABFINI_API_KEY` soient configurés sur Vercel une fois
  l'API hébergée publiquement (voir `web/README.md`).
- **Mobile** : testé avec succès via Expo Go sur réseau Wi-Fi local (voir
  `mobile-test/README.md` pour les KNOWN ISSUES et la procédure).

## Known Issues (niveau dépôt)

- Le `Dockerfile` n'a pas pu être validé par un vrai `docker build` dans
  l'environnement Claude Code : le daemon Docker démarre, mais l'accès au
  registre Docker Hub (`production.cloudfront.docker.com`) y est bloqué par
  la politique réseau de l'environnement (403, confirmé volontaire — pas une
  erreur de configuration à contourner). Le Dockerfile a été relu
  manuellement pour la cohérence des chemins (`api/requirements.txt`
  référence `../embeddings/requirements.txt`, résolu correctement car les
  deux fichiers sont copiés dans la même arborescence relative) et le
  binding sur `$PORT`. À valider par un `docker build .` réel avant
  déploiement (Render/Fly le referont de toute façon lors du build).
- Le cycle mobile complet (question → réponse réelle) n'est pas encore
  confirmé — seul le chargement de l'écran d'accueil l'est (voir
  `mobile-test/README.md`).
