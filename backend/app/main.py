from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.db import init_db
from app.routes import missions, waypoints, enigmas, media, admin
from app.ws import router as ws_router


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

origins = os.getenv("CORS_ORIGINS", "http://localhost").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(ws_router,        prefix="/ws",        tags=["websocket"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "online", "service": "HEIST.EXE"}
