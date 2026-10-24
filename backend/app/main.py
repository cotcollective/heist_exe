from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from app.db import init_db
from app.routes import missions, waypoints, enigmas, media, admin, world, parties
from app.ws import router as ws_router

# Sert le frontend bâti depuis le même process, pour qu'un tunnel n'ait
# qu'une seule cible : ce port. Désactivé par défaut en développement (Vite
# s'en charge), activé si le dossier dist existe.
_DEFAULT_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
STATIC_DIR = Path(os.getenv("STATIC_DIR") or _DEFAULT_DIST)
SERVE_STATIC = os.getenv("SERVE_STATIC", "1") != "0" and (STATIC_DIR / "index.html").is_file()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs(os.getenv("MEDIA_PATH", "/app/media"), exist_ok=True)
    yield


app = FastAPI(
    title="HEIST.EXE — Mission Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

# ── CORS ────────────────────────────────────────────────────────────────────
# En mono-port, le frontend et l'API partagent l'origine : rien à autoriser.
# Dès que le frontend est servi ailleurs (CDN statique, Surge), il faut une
# liste EXPLICITE — jamais « * », parce que les jetons de partie voyagent en
# en-tête et qu'un wildcard laisserait n'importe quelle page les utiliser
# depuis le navigateur d'un joueur.
#
#   CORS_ORIGINS="https://heist-exe.surge.sh,http://localhost:5173"
#
# Pas d'étoile : on refuse de démarrer avec, plutôt que de la traduire en
# wildcard silencieux.
_raw_origins = os.getenv("CORS_ORIGINS", "")
ORIGINS = [o.strip().rstrip("/") for o in _raw_origins.split(",") if o.strip()]
if "*" in ORIGINS:
    raise RuntimeError(
        "CORS_ORIGINS ne peut pas contenir '*' : les jetons de partie "
        "voyagent en en-tête. Lister les origines explicitement."
    )

if ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGINS,
        # Pas de cookies : l'identité passe par X-Party-Token et Authorization.
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Party-Token", "X-Account-Token"],
        max_age=600,
    )

# Serve media files directly (audio clips)
media_path = os.getenv("MEDIA_PATH", "/app/media")
if os.path.exists(media_path):
    app.mount("/media", StaticFiles(directory=media_path), name="media")

# Routers
app.include_router(admin.router,     prefix="/admin",     tags=["admin"])
app.include_router(missions.router,  prefix="/missions",  tags=["missions"])
app.include_router(waypoints.router, prefix="/waypoints", tags=["waypoints"])  # inclut /answer
app.include_router(enigmas.router,   prefix="/enigmas",   tags=["enigmas"])
app.include_router(media.router,     prefix="/upload",    tags=["media"])
app.include_router(world.router, prefix="/world", tags=["world"])
app.include_router(parties.router, prefix="/play", tags=["play"])
app.include_router(ws_router,        prefix="/ws",        tags=["websocket"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "online", "service": "HEIST.EXE"}


# ── Frontend servi par le même process ───────────────────────────────────────
# Le client appelle /api/... ; les routes sont montées sans ce préfixe. On le
# retire à l'entrée plutôt que de dupliquer tout le routeur.
if SERVE_STATIC:
    _MEDIA_TYPES = {
        ".js": "application/javascript",
        ".webmanifest": "application/manifest+json",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".css": "text/css",
        ".json": "application/json",
    }

    @app.middleware("http")
    async def _strip_api_prefix(request, call_next):
        path = request.url.path
        if path == "/api" or path.startswith("/api/"):
            request.scope["path"] = path[4:] or "/"
            request.scope["raw_path"] = request.scope["path"].encode("utf-8")
        return await call_next(request)

    def _static_response(rel: str) -> FileResponse | None:
        """Sert un fichier du build, en refusant toute sortie du dossier."""
        root = STATIC_DIR.resolve()
        candidate = (root / rel).resolve()
        if not candidate.is_file():
            return None
        if candidate != root and root not in candidate.parents:
            return None
        media = _MEDIA_TYPES.get(candidate.suffix)
        return FileResponse(candidate, media_type=media) if media else FileResponse(candidate)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa(full_path: str):
        """Sert un fichier du build s'il existe, sinon index.html.

        Les types MIME de sw.js et du manifeste sont forcés : Python ne
        connaît pas .webmanifest, et un manifeste servi en text/plain casse
        l'installation PWA.
        """
        if full_path:
            resp = _static_response(full_path)
            if resp is not None:
                return resp

        index = STATIC_DIR / "index.html"
        if index.is_file():
            return FileResponse(index, media_type="text/html")
        raise HTTPException(status_code=404)
