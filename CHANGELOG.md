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

#### Changed
- **Inversion du rayon** — le cercle n'est plus une cible mais une **zone de recherche**. Aucun marqueur au centre. Distance affichée au **bord**, arrondie à 10 m, et **supprimée entièrement** à l'entrée dans la zone. Un compteur au mètre près transformait le téléphone en détecteur de métaux.
- **`CachePlant`** défaut à 120 m contre 30 m pour un waypoint de mission : tolérance d'arrivée vs aire de recherche.
- **`.hx-screen`** passe de `min-height` à `height: 100dvh` + `overflow-y: auto` — la carte Leaflet s'effondrait à 0 px dans un conteneur flex sans hauteur définie.

#### Fixed
- **`tests/conftest.py`** — `ADMIN_KEY` était définie après l'import de `app.main`, alors que `app/auth.py` la lit au niveau module. Résultat : 16 tests sur 22 échouaient en 403 et `KeyError: 'id'` en cascade. Une seule cause, seize symptômes.

#### Tests
- **38 pytest** (22 → 38) : plantation, bbox, fuite de `qr_code`, preuve QR absente/invalide/valide, idempotence par joueur, multiplicité multi-joueurs, versement idempotent, versement depuis payload, comptes mixtes, contrôle admin.

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
