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
l'application se bundle réellement sans erreur (Metro, 589 modules) — cela
valide le code, mais un test avec Expo Go sur un téléphone réel reste
nécessaire pour confirmer l'expérience de bout en bout (E2E mobile réel,
Phase 9).

## KNOWN ISSUES

- **Corrigé (P0)** : le champ de saisie et le bouton Envoyer étaient rendus
  cachés sous la barre de navigation système sur Android. Cause confirmée :
  `App.js` utilisait `SafeAreaView` importé depuis `react-native` (API
  dépréciée, n'appliquait plus correctement l'inset bas sur certains
  appareils Android) au lieu de `react-native-safe-area-context`. Corrigé en
  passant à `react-native-safe-area-context` (version `~5.7.0`, résolue
  depuis le manifeste de compatibilité SDK 57 embarqué dans le paquet
  `expo` — la commande `expo install` elle-même échouait dans
  l'environnement Claude Code faute d'accès réseau à l'API Expo, d'où cette
  résolution manuelle mais équivalente), en enveloppant l'app dans
  `SafeAreaProvider`, et en ajustant `KeyboardAvoidingView` (`behavior:
  "height"` sur Android au lieu de `undefined`).
  **Vérification visuelle non faite depuis Claude Code** (pas d'appareil
  physique ni de simulateur disponibles ici) — seule la validation possible
  ici a été faite : le bundle Metro se construit toujours sans erreur
  (`expo export --platform ios`, 589 modules). **Arona doit confirmer sur
  son téléphone** que le champ de saisie et le bouton sont maintenant
  visibles et utilisables.
  Pour récupérer le correctif : un simple `git pull` dans le dossier du
  dépôt suffit — le serveur Metro déjà lancé (`npx expo start`) rechargera
  l'app automatiquement sur le téléphone, sans avoir besoin de rescanner le
  QR code (redémarrer `npm start` uniquement si le rechargement automatique
  ne se déclenche pas).
- Le cycle complet question → réponse réelle sur téléphone physique n'est
  pas encore confirmé (seul le chargement de l'écran d'accueil l'est).
