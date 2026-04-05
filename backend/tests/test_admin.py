import pytest
from tests.conftest import ADMIN_HEADERS, MISSION_PAYLOAD


@pytest.mark.asyncio
async def test_create_mission_success(client):
    r = await client.post("/admin/missions", json=MISSION_PAYLOAD, headers=ADMIN_HEADERS)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Opération Tétreaultville"
    assert len(data["waypoints"]) == 3
    # Vérifie l'ordre des waypoints
    orders = [w["order"] for w in data["waypoints"]]
    assert orders == [0, 1, 2]
    # Vérifie que les énigmes sont créées
    wp0 = next(w for w in data["waypoints"] if w["order"] == 0)
    assert wp0["enigma"] is not None
    assert wp0["enigma"]["question"] == "Lattes × numéro civique de la bâtisse rouge."
    # Pas de hash dans la réponse
    assert "answer_hash" not in wp0["enigma"]


@pytest.mark.asyncio
async def test_create_mission_without_admin_key(client):
    r = await client.post("/admin/missions", json=MISSION_PAYLOAD,
                          headers={"Authorization": "Bearer mauvaise-cle"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_mission_pin_trop_court(client):
    payload = {**MISSION_PAYLOAD, "pin": "12"}
    r = await client.post("/admin/missions", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_missions(client):
    await client.post("/admin/missions", json=MISSION_PAYLOAD, headers=ADMIN_HEADERS)
    r = await client.get("/admin/missions", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_delete_mission(client):
    r = await client.post("/admin/missions", json=MISSION_PAYLOAD, headers=ADMIN_HEADERS)
    mission_id = r.json()["id"]
    r = await client.delete(f"/admin/missions/{mission_id}", headers=ADMIN_HEADERS)
    assert r.status_code == 204
    r = await client.get("/admin/missions", headers=ADMIN_HEADERS)
    assert r.json() == []


@pytest.mark.asyncio
async def test_delete_mission_inexistante(client):
    r = await client.delete("/admin/missions/999", headers=ADMIN_HEADERS)
    assert r.status_code == 404
