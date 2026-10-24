"""Missions par défaut — ce que le papa paresseux trouve en ouvrant l'app.

Ce que ces tests protègent :

  1. Une base neuve a cinq missions jouables, tout de suite.
  2. Le semis ne se répète pas : effacer les missions ne les fait pas revenir.
  3. Chaque mission est réellement jouable — PIN valide, waypoints ordonnés,
     énigmes dont la réponse passe la vérification.
  4. Les missions par défaut n'empêchent pas les vraies de fonctionner.
"""

import pytest
from sqlalchemy import func, select

from app.auth import verify_answer, verify_secret
from app.models import AppSetting, Enigma, Mission, Waypoint
from app.seed_defaults import SEED_KEY, DEFAULT_MISSIONS, seed_default_missions

pytestmark = pytest.mark.asyncio


# ── 1. Une base neuve a de quoi jouer ───────────────────────────────────────


async def test_seeds_five_missions(db):
    created = await seed_default_missions(db)
    assert created == 5

    total = (await db.execute(select(func.count()).select_from(Mission))).scalar()
    assert total == 5


async def test_every_mission_has_waypoints_in_order(db):
    await seed_default_missions(db)

    missions = (await db.execute(select(Mission))).scalars().all()
    for m in missions:
        wps = (await db.execute(
            select(Waypoint).where(Waypoint.mission_id == m.id).order_by(Waypoint.order)
        )).scalars().all()
        assert len(wps) >= 3, f"{m.title} n'a que {len(wps)} waypoints"
        assert [w.order for w in wps] == list(range(len(wps)))


async def test_every_waypoint_has_a_solvable_enigma(db):
    """Une énigme dont la réponse ne passe pas la vérification rend le jeu injouable."""
    await seed_default_missions(db)

    specs = {s["title"]: s for s in DEFAULT_MISSIONS}

    for title, spec in specs.items():
        mission = (await db.execute(
            select(Mission).where(Mission.title == title)
        )).scalar_one()

        wps = (await db.execute(
            select(Waypoint).where(Waypoint.mission_id == mission.id).order_by(Waypoint.order)
        )).scalars().all()

        for wp, (_, _, _, _, _, (_, expected)) in zip(wps, spec["waypoints"]):
            enigma = (await db.execute(
                select(Enigma).where(Enigma.waypoint_id == wp.id)
            )).scalar_one_or_none()
            assert enigma is not None, f"{title} / {wp.title} n'a pas d'énigme"
            assert verify_answer(expected, enigma.answer_hash), \
                f"{title} / {wp.title} : la réponse attendue ne passe pas"


async def test_every_pin_works(db):
    await seed_default_missions(db)

    for spec in DEFAULT_MISSIONS:
        mission = (await db.execute(
            select(Mission).where(Mission.title == spec["title"])
        )).scalar_one()
        assert verify_secret(spec["pin"], mission.pin_hash), f"PIN invalide pour {spec['title']}"


async def test_a_wrong_pin_is_rejected(db):
    await seed_default_missions(db)
    mission = (await db.execute(select(Mission))).scalars().first()
    assert not verify_secret("0000", mission.pin_hash)


async def test_coordinates_are_in_the_neighbourhood(db):
    """Les cinq chasses doivent tenir dans un rayon marchable."""
    await seed_default_missions(db)

    points = (await db.execute(select(Waypoint.lat, Waypoint.lng))).all()
    lats = [p.lat for p in points]
    lngs = [p.lng for p in points]

    # Tétreaultville : environ 45.55–45.58 nord, -73.56 à -73.53 ouest.
    assert 45.55 <= min(lats) and max(lats) <= 45.58
    assert -73.56 <= min(lngs) and max(lngs) <= -73.53


async def test_radii_are_generous_enough_for_a_child(db):
    """Sous 20 m, un enfant cherche une aiguille dans un parc."""
    await seed_default_missions(db)
    too_tight = (await db.execute(
        select(Waypoint.title).where(Waypoint.radius_meters < 20)
    )).all()
    assert too_tight == []


# ── 2. Le semis ne se répète pas ────────────────────────────────────────────


async def test_second_call_is_a_noop(db):
    await seed_default_missions(db)
    again = await seed_default_missions(db)
    assert again == 0

    total = (await db.execute(select(func.count()).select_from(Mission))).scalar()
    assert total == 5


async def test_deleting_missions_does_not_bring_them_back(db):
    """Sinon un papa qui repart à zéro croirait que la suppression ne marche pas."""
    await seed_default_missions(db)

    for m in (await db.execute(select(Mission))).scalars().all():
        await db.delete(m)
    await db.commit()

    assert (await db.execute(select(func.count()).select_from(Mission))).scalar() == 0

    # Redémarrage simulé : le semis ne doit rien recréer.
    assert await seed_default_missions(db) == 0
    assert (await db.execute(select(func.count()).select_from(Mission))).scalar() == 0


async def test_flag_is_recorded(db):
    await seed_default_missions(db)
    flag = await db.get(AppSetting, SEED_KEY)
    assert flag is not None
    assert flag.value == "done"


# ── 3. Cohabitation avec de vraies missions ─────────────────────────────────


async def test_existing_missions_are_not_disturbed(db):
    """Un papa qui a déjà sa mission ne doit pas se la faire doubler."""
    mine = Mission(title="Ma vraie mission", pin_hash="x", duration_minutes=20)
    db.add(mine)
    await db.commit()

    await seed_default_missions(db)

    total = (await db.execute(select(func.count()).select_from(Mission))).scalar()
    assert total == 6

    still_there = (await db.execute(
        select(Mission).where(Mission.title == "Ma vraie mission")
    )).scalar_one()
    assert still_there.id == mine.id


async def test_default_missions_are_all_active(db):
    """Une mission inactive n'apparaît pas dans la liste du joueur."""
    await seed_default_missions(db)
    inactive = (await db.execute(
        select(func.count()).select_from(Mission).where(Mission.is_active.is_(False))
    )).scalar()
    assert inactive == 0
