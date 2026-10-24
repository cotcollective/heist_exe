# Changelog

All notable changes to HEIST.EXE are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [1.1.0] — 2026-10-24

### 🗺️ Le Monde — caches publiques et chasse au trésor

Une mission était une île. Elle est maintenant un calque sur un substrat partagé.

#### Added
- **`Waypoint.mission_id` nullable** — un waypoint peut vivre hors mission. Une cache du monde est un waypoint orphelin.
- **`is_public`, `claim_mode`, `owner_label`** sur `Waypoint` — visibilité, régime de réclamation, attribution.
- **Table `waypoint_claims`** avec `UNIQUE(waypoint_id, player_name)` — une seule contrainte sert les **deux régimes** : progression exclusive par joueur dans une mission, trouvaille multiple et permanente dans le monde.
- **Router `/world`** — `GET /world/caches` (bbox, ne renvoie jamais `qr_code`, seulement `requires_proof`), `GET /world/caches/{id}`, `POST /world/caches` (plantation), `POST /world/caches/{id}/claim`.
- **`POST /world/publish` idempotent** — clé `(origin_mission_id, origin_waypoint_id)`, colonnes `origin_*` + index unique. Rejouer un lot renvoie les caches existantes avec `created=false`. Le versement **copie** : le waypoint d'origine reste dans sa mission, intact — une mission en cours ne doit pas être amputée.
- **Migrations SQL versionnées** — `backend/migrations/*.sql` + `schema_version`, sans dépendance. `init_db` crée le schéma manquant puis applique les fichiers en attente ; une base neuve est baselinée au lieu de rejouer. La 001 reconstruit `waypoints` (SQLite ne sait pas relâcher un `NOT NULL`).
- **Page `/world`** — carte publique sans authentification, cercles de recherche pointillés, bandeau tactile, panneau de détail, réclamation directe ou par scan QR.
- **Bouton « verser au monde »** dans le builder admin — une mission terminée ensemence le monde.
- **Téléchargement de la zone hors ligne** — depuis le briefing, bornes calculées sur les waypoints + 400 m, zooms 14-17, **plafonné à 250 tuiles** (politique d'usage OSM), écrites dans le cache `osm-tiles` servi par le service worker en `CacheFirst`. Ré-exécutable sans re-télécharger.
- **Réclamant authentifié par clé d'appareil** — plus de `player_name` en clair dans le body. L'appareil génère une paire ECDSA P-256 (WebCrypto), enregistre la publique via `POST /world/agents`, et signe chaque réclamation sur la forme canonique `waypoint_id|player_name|ts`. Le serveur vérifie avec la clé publique, fenêtre de validité 600 s. Pas de compte, pas de mot de passe, pas de courriel.
- **Un nom d'agent appartient à sa clé** — premier arrivé, premier servi : re-enregistrer un nom avec une autre clé renvoie 409. C'est ce qui empêche de réclamer une identité existante.
- **Hôte de tuiles unique** — `{s}.tile.openstreetmap.org` remplacé par `tile.openstreetmap.org` partout. La clé de cache est l'URL exacte : avec des sous-domaines aléatoires, le prefetch ne pouvait jamais servir la carte.

#### Changed
- **Inversion du rayon** — le cercle n'est plus une cible mais une **zone de recherche**. Aucun marqueur au centre. Distance affichée au **bord**, arrondie à 10 m, et **supprimée entièrement** à l'entrée dans la zone. Un compteur au mètre près transformait le téléphone en détecteur de métaux.
- **`CachePlant`** défaut à 120 m contre 30 m pour un waypoint de mission : tolérance d'arrivée vs aire de recherche.
- **`.hx-screen`** passe de `min-height` à `height: 100dvh` + `overflow-y: auto` — la carte Leaflet s'effondrait à 0 px dans un conteneur flex sans hauteur définie.

#### Fixed
- **`tests/conftest.py`** — `ADMIN_KEY` était définie après l'import de `app.main`, alors que `app/auth.py` la lit au niveau module. Résultat : 16 tests sur 22 échouaient en 403 et `KeyError: 'id'` en cascade. Une seule cause, seize symptômes.
- **`MissionBuilder` ne chargeait jamais une mission existante** — la route déclare `/admin/builder/:missionId`, le composant lisait `useParams().id`. Le paramètre était toujours `undefined`, donc le builder restait en mode « nouvelle mission » et le bouton de versement n'apparaissait jamais sur une mission qu'on venait de créer.
- **`ADMIN_KEY` et `SECRET_KEY` lues à l'import, avec des valeurs par défaut publiques** — deux trous de sécurité et un défaut d'exploitation :
  - `ADMIN_KEY` retombait sur `admin-secret-key`, une valeur écrite dans le dépôt. Déployer sans `.env` ouvrait le panneau d'administration à quiconque lit le README. Elle est maintenant lue à chaque requête, et l'administration répond **503** si elle est absente, trop courte ou égale à une valeur de démonstration connue.
  - `SECRET_KEY` retombait sur `dev-secret-change-in-prod-minimum-32-chars`, ce qui permettait de **forger un jeton joueur** et de réclamer des caches au nom de n'importe qui. Sans `SECRET_KEY`, une clé éphémère est générée au démarrage : les jetons ne survivent pas à un redémarrage, mais ils ne sont pas forgeables.
  - Comparaison de la clé admin en temps constant (`secrets.compare_digest`) — la comparaison naïve était sensible au timing.
  - Bonus : la rotation d'`ADMIN_KEY` prend effet **sans redémarrer le process**.

#### Tests
- **59 pytest** (22 → 59) : plantation, bbox, fuite de `qr_code`, preuve QR absente/invalide/valide, idempotence par joueur, multiplicité multi-joueurs, versement idempotent, versement depuis payload, comptes mixtes, contrôle admin, migration d'une base 1.0.0 (données et énigmes préservées, `NOT NULL` relâché), rejeu idempotent de la migration, baseline d'une base neuve, auth admin (503 sans clé, 503 clé faible, 503 clé courte, 403 mauvaise clé, rotation à chaud), et réclamation signée (sans agent 403, sans signature 401, signature forgée 403, signature liée au waypoint, signature expirée 401, nom volé 409, ré-enregistrement idempotent, clé invalide 400).

---

## [1.0.0] — 2025-04-05

### 🎉 Initial Release

The first public release of **HEIST.EXE** — an urban mission platform that transforms any neighbourhood into a real-world spy game.

#### Added
- **FastAPI 0.115** async backend with JWT PIN-based authentication and bcrypt hashing
- **React 18 + Vite 5** PWA frontend — installable on iOS/Android with no App Store
- **Leaflet + OpenStreetMap** map engine — zero API key, offline-capable
- **SQLite + aiosqlite** persistence — single-file database, simple backup
- **WebSocket countdown** — real-time mission timer synchronized across sessions
- **Howler.js** audio briefing support — crypted mission audio playback
- **html5-qrcode** integrated QR scanner — no native dependencies
- **Admin dashboard** — 3-step mission builder (info → waypoints → review)
- **Player flow** — Boot → Briefing → WaypointHunt → Enigma → RewardUnlock
- **Docker Compose** one-command deployment (backend + frontend + nginx)
- **Tétreaultville demo mission** — 4 real GPS waypoints in Montréal, ready to seed
- **22 pytest-asyncio tests** — full coverage (health, admin, auth, gameplay loops)
- **4 Playwright E2E specs** — mobile Chrome + Safari (PWA, boot, gameplay, admin)
- **GitHub Pages landing** — `docs/index.html` dark/tech showcase page
- **MIT License**

#### Fixed
- `bcrypt 5.x` incompatibility with `passlib 1.7.4` → pinned to `bcrypt==4.0.1`
- SQLAlchemy `MissingGreenlet` on lazy-loaded relations in async context → `selectinload` applied on all routes
- Duplicate `data-testid` JSX attribute in `Boot.jsx` causing Vite build failure

---

## [Unreleased]

### Planned
- Multi-language support (EN/FR toggle)
- Admin real-time mission tracking dashboard
- QR code generation for waypoints (auto-print sheet)
- Push notifications for countdown warnings
- Leaderboard (optional, opt-in)
