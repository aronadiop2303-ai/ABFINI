# ABFINI Test — client mobile Expo Go

Mini-application Expo minimale et jetable, dédiée uniquement au test d'ABFINI
depuis un téléphone. Un seul écran : champ de saisie, réponse, sources,
modèle utilisé — rien de plus. Ce n'est pas l'application BARDEC (projet
séparé) et ne remplace aucune app existante.

Aucune réponse n'est simulée : l'écran appelle directement l'API ABFINI réelle
(`POST /v1/chat`), jamais de données fictives.

## Prérequis

- Node.js 18+
- L'app [Expo Go](https://expo.dev/go) installée sur le téléphone
- Le téléphone et la machine qui lance `npm start` doivent pouvoir joindre
  l'URL de l'API ABFINI (réseau local si l'API tourne en local, ou une URL
  HTTPS publique si elle est déployée).

## Configuration

```bash
cd mobile-test
npm install
cp .env.example .env
# éditer .env : EXPO_PUBLIC_ABFINI_API_URL et EXPO_PUBLIC_ABFINI_API_KEY
```

`EXPO_PUBLIC_ABFINI_API_KEY` est la clé applicative `ABFINI_API_KEY` du
backend (celle qui protège `/v1/chat`) — **jamais**
`SUPABASE_SERVICE_ROLE_KEY` ni `DEEPSEEK_API_KEY`, qui ne doivent jamais
quitter le serveur.

## Lancer et tester

```bash
npm start
```

1. Un QR code s'affiche dans le terminal.
2. Scanner ce QR code avec l'app Expo Go (Android : scanner intégré à Expo
   Go ; iOS : appareil photo puis ouvrir dans Expo Go).
3. L'app ABFINI Test s'ouvre sur le téléphone.
4. Taper : « Qu'est-ce qu'ABFINI ? » puis Envoyer.
5. La réponse réelle, ses sources (document/chunk/similarité) et le modèle
   utilisé s'affichent — ou un message d'erreur explicite si le backend est
   injoignable ou mal configuré (jamais un faux succès).

## Validation effectuée sans appareil physique

`npx expo export --platform ios` a été exécuté pour confirmer que
l'application se bundle réellement sans erreur (Metro, 580 modules) — cela
valide le code, mais un test avec Expo Go sur un téléphone réel reste
nécessaire pour confirmer l'expérience de bout en bout (E2E mobile réel,
Phase 9).
