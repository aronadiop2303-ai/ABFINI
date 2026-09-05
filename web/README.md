# ABFINI Web — client de test V0.1

Interface de test minimale, aucune réponse simulée : tout provient de l'API ABFINI réelle.

- `index.html` / `style.css` / `app.js` — page statique (aucun build, aucun framework).
- `api/config.js` — fonction Vercel qui expose uniquement `ABFINI_API_URL` (non secret) au navigateur.
- `api/chat.js` — fonction Vercel qui relaie `POST /v1/chat` vers l'API ABFINI en ajoutant `Authorization: Bearer ABFINI_API_KEY` côté serveur. La clé n'est **jamais** envoyée au navigateur.

## Déploiement Vercel

1. Créer un projet Vercel pointant sur ce dépôt avec **Root Directory = `web`**.
2. Configurer les variables d'environnement du projet Vercel (Production + Preview) :
   - `ABFINI_API_URL` — URL HTTPS de l'API ABFINI déployée (ex. `https://abfini-api.example.com`)
   - `ABFINI_API_KEY` — la clé configurée côté API (`ABFINI_API_KEY` sur le backend)
3. Sur le backend ABFINI, configurer `ABFINI_CORS_ORIGINS` avec le domaine Vercel exact (ex. `https://abfini-web.vercel.app`) pour autoriser les appels navigateur à `GET /health` et `GET /health/dependencies` (ces deux routes sont publiques et ne portent aucun secret).
4. Déployer. Aucun build n'est nécessaire (page statique + fonctions serverless Node).

## Ce que fait réellement la page

- Au chargement, appelle `GET {ABFINI_API_URL}/health` puis `GET {ABFINI_API_URL}/health/dependencies` directement depuis le navigateur pour afficher l'état réel de l'API, du Model Router, des Embeddings et de la recherche vectorielle Supabase.
- À l'envoi d'un message, appelle `POST /api/chat` (même origine, fonction Vercel) qui relaie vers `POST {ABFINI_API_URL}/v1/chat` avec la clé API côté serveur, et affiche la réponse réelle, les sources (document/chunk/similarité) et le modèle utilisé.
- Aucune valeur n'est jamais simulée : une panne réelle du backend s'affiche comme une erreur, jamais comme un faux succès.
