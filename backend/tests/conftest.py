import os

# ADMIN_KEY est maintenant lue à chaque requête (app/auth.py). La poser ici
# reste la façon la plus simple de configurer les tests, mais l'ordre
# d'import n'a plus d'importance.
os.environ.setdefault("ADMIN_KEY", "heist123")

# Les tests hachent beaucoup (PIN + une réponse d'énigme par waypoint, et le
# semis crée 17 hachures à lui seul). Aux rounds de production, la suite passe
# de 25 s à 80 s. On baisse le coût ICI UNIQUEMENT : la production garde les
# rounds par défaut, et les tests vérifient toujours de vrais hachages bcrypt.
import app.auth as _auth_mod
from passlib.context import CryptContext as _CryptContext

_auth_mod.pwd_context = _CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db import Base, get_db

# DB in-memory pour les tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Recrée le schéma avant chaque test."""
    from app import models  # noqa: F401
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db():
    """Session directe sur la base de test, pour vérifier ce que l'API ne dit pas.

    Nécessaire dès qu'un test doit prouver une absence (« le jeton n'est pas
    stocké en clair ») ou une étanchéité (« la partie n'a pas créé de mission »).
    """
    async with TestSession() as session:
        yield session


ADMIN_KEY = "heist123"
ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_KEY}"}

MISSION_PAYLOAD = {
    "title": "Opération Tétreaultville",
    "lore": "L'agent X a été compromis. La clé est cachée près de l'eau.",
    "pin": "2077",
    "duration_minutes": 45,
    "reward_text": "15$ au comptoir du dépanneur Taillon. 8 minutes avant trace.",
    "waypoints": [
        {
            "order": 0,
            "title": "Parc L.-O.-Taillon",
            "hint": "Le banc face au sud-est, vers le pont.",
            "lat": 45.5680,
            "lng": -73.5500,
            "radius_meters": 30,
            "enigma": {
                "question": "Lattes × numéro civique de la bâtisse rouge.",
                "answer": "84",
                "hint": "Le numéro est sur la façade principale.",
            },
        },
        {
            "order": 1,
            "title": "Mural Hochelaga",
            "hint": "Le graffiti avec l'œil qui te regarde.",
            "lat": 45.5695,
            "lng": -73.5485,
            "radius_meters": 25,
            "enigma": {
                "question": "Combien de couleurs différentes dans le mural?",
                "answer": "7",
            },
        },
        {
            "order": 2,
            "title": "Dépanneur Taillon",
            "hint": "La planque finale. Tu mérites les chips.",
            "lat": 45.5702,
            "lng": -73.5470,
            "radius_meters": 20,
            "enigma": None,
        },
    ],
}
