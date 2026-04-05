import pytest
from tests.conftest import ADMIN_HEADERS, MISSION_PAYLOAD


async def _create_mission(client):
    r = await client.post("/admin/missions", json=MISSION_PAYLOAD, headers=ADMIN_HEADERS)
    return r.json()


@pytest.mark.asyncio
async def test_list_active_missions(client):
    await _create_mission(client)
    r = await client.get("/missions/active")
    assert r.status_code == 200
    assert len(r.json()) == 1
    # Ne pas retourner le pin_hash dans la liste publique
    mission = r.json()[0]
    assert "pin_hash" not in mission


@pytest.mark.asyncio
async def test_auth_bon_pin(client):
    mission = await _create_mission(client)
    r = await client.post("/missions/auth", json={
        "mission_id": mission["id"],
        "pin": "2077",
        "player_name": "Agent_Dave",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["mission"]["id"] == mission["id"]


@pytest.mark.asyncio
async def test_auth_mauvais_pin(client):
    mission = await _create_mission(client)
    r = await client.post("/missions/auth", json={
        "mission_id": mission["id"],
        "pin": "9999",
        "player_name": "Agent_X",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_mission_inexistante(client):
    r = await client.post("/missions/auth", json={
        "mission_id": 9999,
        "pin": "2077",
        "player_name": "Agent_X",
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_me_avec_token_valide(client):
    mission = await _create_mission(client)
    auth = await client.post("/missions/auth", json={
        "mission_id": mission["id"], "pin": "2077", "player_name": "Dave"
    })
    token = auth.json()["access_token"]
    r = await client.get("/missions/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["title"] == "Opération Tétreaultville"


@pytest.mark.asyncio
async def test_me_sans_token(client):
    r = await client.get("/missions/me")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_me_token_invalide(client):
    r = await client.get("/missions/me", headers={"Authorization": "Bearer token-bidon"})
    assert r.status_code == 401
