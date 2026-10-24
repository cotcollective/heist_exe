from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

DB_PATH = os.getenv("DB_PATH", "/app/data/heist.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Crée le schéma manquant, puis applique les migrations en attente.

    L'ordre compte : `create_all` ne CRÉE que les tables absentes, il ne
    touche jamais aux colonnes d'une table existante. Une base 1.0.0 garde
    donc son ancien `waypoints` et c'est la migration qui le reconstruit.
    Sur une base neuve, le schéma sort déjà complet de `create_all` et on
    baseline les migrations au lieu de les rejouer.
    """
    from sqlalchemy import inspect

    from app import models  # noqa: F401 — importer pour enregistrer les modèles
    from app.migrations import apply_migrations

    async with engine.begin() as conn:
        had_waypoints = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table("waypoints")
        )
        await conn.run_sync(Base.metadata.create_all)
        await apply_migrations(conn, baseline_fresh=not had_waypoints)
