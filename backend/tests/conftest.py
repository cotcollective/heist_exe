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
