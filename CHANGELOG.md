# Changelog

All notable changes to HEIST.EXE are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

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
