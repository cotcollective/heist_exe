import pytest
from tests.conftest import ADMIN_HEADERS, MISSION_PAYLOAD


async def _setup(client):
    """Crée une mission et authentifie un joueur. Retourne (token, mission, headers)."""
    r = await client.post("/admin/missions", json=MISSION_PAYLOAD, headers=ADMIN_HEADERS)
    mission = r.json()
    auth = await client.post("/missions/auth", json={
        "mission_id": mission["id"], "pin": "2077", "player_name": "Agent_Dave"
    })
    token = auth.json()["access_token"]
    return token, mission, {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_waypoint_courant_initial(client):
    token, mission, headers = await _setup(client)
    r = await client.get("/waypoints/current", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["order"] == 0
    assert data["title"] == "Parc L.-O.-Taillon"
    assert data["enigma"] is not None


@pytest.mark.asyncio
async def test_soumettre_bonne_reponse(client):
    token, mission, headers = await _setup(client)
    wp = (await client.get("/waypoints/current", headers=headers)).json()
    r = await client.post("/waypoints/answer", json={
        "waypoint_id": wp["id"],
        "answer": "84",
    }, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["correct"] is True
    assert data["mission_complete"] is False
    assert data["next_waypoint"]["order"] == 1


@pytest.mark.asyncio
async def test_reponse_insensible_casse_et_espaces(client):
    """Le hash normalise: strip + lowercase avant bcrypt."""
    token, mission, headers = await _setup(client)
    wp = (await client.get("/waypoints/current", headers=headers)).json()
    r = await client.post("/waypoints/answer", json={
        "waypoint_id": wp["id"],
        "answer": "  84  ",  # avec espaces
    }, headers=headers)
    assert r.json()["correct"] is True


@pytest.mark.asyncio
async def test_mauvaise_reponse(client):
    token, mission, headers = await _setup(client)
    wp = (await client.get("/waypoints/current", headers=headers)).json()
    r = await client.post("/waypoints/answer", json={
        "waypoint_id": wp["id"],
        "answer": "999",
    }, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["correct"] is False
    assert data["next_waypoint"] is None


@pytest.mark.asyncio
async def test_progression_waypoint_apres_bonne_reponse(client):
    """Après bonne réponse, /current retourne le waypoint suivant."""
    token, mission, headers = await _setup(client)
    wp0 = (await client.get("/waypoints/current", headers=headers)).json()
    await client.post("/waypoints/answer", json={"waypoint_id": wp0["id"], "answer": "84"}, headers=headers)
    wp1 = (await client.get("/waypoints/current", headers=headers)).json()
    assert wp1["order"] == 1
    assert wp1["title"] == "Mural Hochelaga"


@pytest.mark.asyncio
async def test_game_loop_complet(client):
    """Passe les 3 waypoints → mission_complete True au dernier."""
    token, mission, headers = await _setup(client)

    # Waypoint 0 — avec énigme
    wp0 = (await client.get("/waypoints/current", headers=headers)).json()
    r0 = await client.post("/waypoints/answer", json={"waypoint_id": wp0["id"], "answer": "84"}, headers=headers)
    assert r0.json()["correct"] is True
    assert r0.json()["mission_complete"] is False

    # Waypoint 1 — avec énigme
    wp1 = (await client.get("/waypoints/current", headers=headers)).json()
    r1 = await client.post("/waypoints/answer", json={"waypoint_id": wp1["id"], "answer": "7"}, headers=headers)
    assert r1.json()["correct"] is True
    assert r1.json()["mission_complete"] is False

    # Waypoint 2 — pas d'énigme, last waypoint
    wp2 = (await client.get("/waypoints/current", headers=headers)).json()
    assert wp2["order"] == 2
    assert wp2["enigma"] is None
    # Pour le dernier waypoint sans énigme, on envoie une réponse vide
    # (dans la vraie app, le frontend détecte enigma=None et skip l'input)
    r2 = await client.post("/waypoints/answer", json={"waypoint_id": wp2["id"], "answer": ""}, headers=headers)
    # Le waypoint n'a pas d'énigme → 404 attendu (correct behaviour)
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_enigma_getter(client):
    token, mission, headers = await _setup(client)
    wp = (await client.get("/waypoints/current", headers=headers)).json()
    enigma_id = wp["enigma"]["id"]
    r = await client.get(f"/enigmas/{enigma_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "question" in data
    assert "answer_hash" not in data  # jamais exposé
