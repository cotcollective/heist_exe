"""Intégrité de la progression — on ne finit pas une chasse assis sur un banc.

Le défaut trouvé en semant les missions par défaut : `/waypoints/answer`
incrémentait `current_waypoint` à chaque bonne réponse sans vérifier que la
réponse portait sur l'étape courante. Répondre trois fois la même énigme
terminait la mission. Une chasse au trésor qu'on gagne sans marcher ne vaut
rien.
"""

import pytest
import pytest_asyncio

from app.seed_defaults import seed_default_missions

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True)
async def seeded(db):
    """Le client de test ne déclenche pas le lifespan : on sème à la main."""
    await seed_default_missions(db)

PIN = "1111"


async def _start(client):
    r = await client.get("/missions/active")
    mission = next(m for m in r.json() if m["title"] == "Le Trésor du Parc")
    a = await client.post("/missions/auth", json={
        "mission_id": mission["id"], "pin": PIN, "player_name": "Test",
    })
    assert a.status_code == 200, a.text
    return a.json()["access_token"], a.json()["mission"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


async def test_repeating_the_same_answer_does_not_advance(client):
    tok, mission = await _start(client)
    wp0 = mission["waypoints"][0]

    first = await client.post("/waypoints/answer",
                              json={"waypoint_id": wp0["id"], "answer": "banc"},
                              headers=_h(tok))
    assert first.status_code == 200
    assert first.json()["correct"] is True
    assert first.json()["mission_complete"] is False

    # Deuxième et troisième fois sur la MÊME étape : plus aucune progression.
    for _ in range(2):
        again = await client.post("/waypoints/answer",
                                  json={"waypoint_id": wp0["id"], "answer": "banc"},
                                  headers=_h(tok))
        assert again.status_code == 200
        assert again.json()["mission_complete"] is False

    # La mission n'est pas terminée : il reste deux étapes à marcher.
    wp1 = mission["waypoints"][1]
    second = await client.post("/waypoints/answer",
                               json={"waypoint_id": wp1["id"], "answer": "cloture"},
                               headers=_h(tok))
    assert second.json()["mission_complete"] is False


async def test_cannot_skip_ahead(client):
    tok, mission = await _start(client)
    last = mission["waypoints"][-1]

    r = await client.post("/waypoints/answer",
                          json={"waypoint_id": last["id"], "answer": "boite aux lettres"},
                          headers=_h(tok))
    assert r.status_code == 409


async def test_full_walk_reaches_the_end(client):
    """Le parcours normal aboutit — le garde-fou ne casse pas le jeu."""
    tok, mission = await _start(client)

    answers = ["banc", "cloture", "boite aux lettres"]
    last = None
    for wp, reponse in zip(mission["waypoints"], answers):
        last = await client.post("/waypoints/answer",
                                 json={"waypoint_id": wp["id"], "answer": reponse},
                                 headers=_h(tok))
        assert last.status_code == 200, last.text
        assert last.json()["correct"] is True

    assert last.json()["mission_complete"] is True


async def test_wrong_answer_does_not_advance(client):
    tok, mission = await _start(client)
    wp0 = mission["waypoints"][0]

    r = await client.post("/waypoints/answer",
                          json={"waypoint_id": wp0["id"], "answer": "table"},
                          headers=_h(tok))
    assert r.json()["correct"] is False

    # On peut toujours répondre correctement ensuite.
    ok = await client.post("/waypoints/answer",
                           json={"waypoint_id": wp0["id"], "answer": "banc"},
                           headers=_h(tok))
    assert ok.json()["correct"] is True
    assert ok.json()["mission_complete"] is False


async def test_answer_is_case_and_space_insensitive(client):
    tok, mission = await _start(client)
    wp0 = mission["waypoints"][0]

    r = await client.post("/waypoints/answer",
                          json={"waypoint_id": wp0["id"], "answer": "  BANC  "},
                          headers=_h(tok))
    assert r.json()["correct"] is True
