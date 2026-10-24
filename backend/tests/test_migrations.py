"""Tests des migrations : une base 1.0.0 doit survivre au passage en 1.1.0.

Le scénario réel : quelqu'un a un `heist.db` créé par la v1.0.0, avec des
missions et des parties en cours. Il tire le commit, redémarre, et doit
retrouver ses données — avec `mission_id` devenu nullable et les colonnes
du monde ajoutées.

On construit une base à l'ancien schéma, on applique la migration, et on
vérifie trois choses : les données sont intactes, la contrainte NOT NULL
est tombée, et rejouer la migration ne casse rien.
"""
import aiosqlite
import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.migrations import apply_migrations, migration_files, split_statements

# Schéma exactement tel que la v1.0.0 le produisait.
OLD_SCHEMA = """
CREATE TABLE missions (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    lore TEXT,
    pin_hash VARCHAR(200) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL,
    audio_file VARCHAR(300),
    reward_text TEXT
);
CREATE TABLE waypoints (
    id INTEGER NOT NULL PRIMARY KEY,
    mission_id INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    hint TEXT,
    lat FLOAT NOT NULL,
    lng FLOAT NOT NULL,
    radius_meters INTEGER NOT NULL,
    qr_code VARCHAR(100),
    FOREIGN KEY(mission_id) REFERENCES missions (id)
);
CREATE INDEX ix_waypoints_id ON waypoints (id);
CREATE INDEX ix_waypoints_mission_id ON waypoints (mission_id);
CREATE TABLE enigmas (
    id INTEGER NOT NULL PRIMARY KEY,
    waypoint_id INTEGER NOT NULL UNIQUE,
    question TEXT NOT NULL,
    answer_hash VARCHAR(200) NOT NULL,
    hint TEXT,
    FOREIGN KEY(waypoint_id) REFERENCES waypoints (id)
);
CREATE TABLE player_sessions (
    id INTEGER NOT NULL PRIMARY KEY,
    mission_id INTEGER NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    current_waypoint INTEGER NOT NULL,
    token_jti VARCHAR(100) NOT NULL UNIQUE,
    FOREIGN KEY(mission_id) REFERENCES missions (id)
);
INSERT INTO missions (id, title, pin_hash, duration_minutes, is_active, created_at)
VALUES (1, 'Vieille mission', 'hash', 45, 1, '2025-04-05T12:00:00');
INSERT INTO waypoints (id, mission_id, "order", title, lat, lng, radius_meters)
VALUES (10, 1, 0, 'Parc', 45.568, -73.550, 30);
INSERT INTO waypoints (id, mission_id, "order", title, lat, lng, radius_meters)
VALUES (11, 1, 1, 'Depanneur', 45.570, -73.547, 30);
INSERT INTO enigmas (id, waypoint_id, question, answer_hash)
VALUES (5, 10, 'Combien ?', 'hash');
"""


@pytest.fixture
def old_db(tmp_path):
    path = tmp_path / "heist_v1.db"
    return path, OLD_SCHEMA


async def _columns(path):
    async with aiosqlite.connect(path) as db:
        cur = await db.execute("PRAGMA table_info(waypoints)")
        return {row[1]: row for row in await cur.fetchall()}


async def _scalar(path, sql, params=()):
    async with aiosqlite.connect(path) as db:
        cur = await db.execute(sql, params)
        return await cur.fetchone()


async def _build_old_db(path, schema):
    async with aiosqlite.connect(path) as db:
        await db.executescript(schema)
        await db.commit()


async def test_migration_files_exist():
    files = migration_files()
    assert files, "aucun fichier de migration trouvé"
    assert files[0].stem.startswith("001")


async def test_split_statements_strips_comments():
    stmts = split_statements("-- un commentaire\nSELECT 1;\n\n-- autre\nSELECT 2;")
    assert stmts == ["SELECT 1", "SELECT 2"]


async def test_v1_db_migrates_preserving_data(old_db):
    path, schema = old_db
    await _build_old_db(path, schema)

    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
    async with engine.begin() as conn:
        executed = await apply_migrations(conn, baseline_fresh=False)
    await engine.dispose()

    assert "001_world" in executed

    cols = await _columns(path)
    # Les colonnes du monde sont là
    for c in ("is_public", "claim_mode", "owner_label",
              "origin_mission_id", "origin_waypoint_id"):
        assert c in cols, f"colonne manquante : {c}"
    # La contrainte NOT NULL est tombée sur mission_id
    assert cols["mission_id"][3] == 0, "mission_id doit être nullable"

    # Les données sont intactes
    row = await _scalar(path, "SELECT COUNT(*) FROM waypoints")
    assert row[0] == 2
    row = await _scalar(path, "SELECT title FROM waypoints WHERE id = 11")
    assert row[0] == "Depanneur"
    row = await _scalar(path, "SELECT COUNT(*) FROM enigmas")
    assert row[0] == 1

    # Les défauts sont appliqués
    row = await _scalar(path, "SELECT is_public, claim_mode FROM waypoints WHERE id = 10")
    assert row[0] == 0 and row[1] == "progress"

    # La table des réclamations existe
    row = await _scalar(
        path, "SELECT name FROM sqlite_master WHERE type='table' AND name='waypoint_claims'"
    )
    assert row is not None


async def test_migration_is_idempotent(old_db):
    path, schema = old_db
    await _build_old_db(path, schema)

    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
    async with engine.begin() as conn:
        first = await apply_migrations(conn, baseline_fresh=False)
    async with engine.begin() as conn:
        second = await apply_migrations(conn, baseline_fresh=False)
    await engine.dispose()

    assert first == ["001_world"]
    assert second == [], "rejouer ne doit rien réexécuter"

    row = await _scalar(path, "SELECT COUNT(*) FROM waypoints")
    assert row[0] == 2


async def test_fresh_db_is_baselined(tmp_path):
    """Une base neuve a déjà le bon schéma : on marque sans rejouer."""
    path = tmp_path / "fresh.db"
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "CREATE TABLE waypoints (id INTEGER PRIMARY KEY, "
            "mission_id INTEGER, is_public BOOLEAN, claim_mode TEXT, "
            "owner_label TEXT, origin_mission_id INTEGER, origin_waypoint_id INTEGER)"
        )
        await db.commit()

    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
    async with engine.begin() as conn:
        executed = await apply_migrations(conn, baseline_fresh=True)
    await engine.dispose()

    assert executed == [], "une base neuve ne rejoue pas les migrations"
    row = await _scalar(path, "SELECT COUNT(*) FROM schema_version")
    assert row[0] == len(migration_files())


async def test_published_cache_can_outlive_its_mission(old_db):
    """Après migration, un waypoint peut exister sans mission."""
    path, schema = old_db
    await _build_old_db(path, schema)

    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
    async with engine.begin() as conn:
        await apply_migrations(conn, baseline_fresh=False)
    await engine.dispose()

    async with aiosqlite.connect(path) as db:
        await db.execute(
            "UPDATE waypoints SET mission_id = NULL, is_public = 1, claim_mode = 'find' "
            "WHERE id = 10"
        )
        await db.commit()

    row = await _scalar(path, "SELECT mission_id, is_public FROM waypoints WHERE id = 10")
    assert row[0] is None
    assert row[1] == 1
