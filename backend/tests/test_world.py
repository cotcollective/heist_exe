"""Tests du monde : caches hors mission + double régime de réclamation."""
import pytest

from tests.conftest import ADMIN_HEADERS, MISSION_PAYLOAD

CACHE_PAYLOAD = {
    "title": "La boîte sous le banc",
    "lat": 45.5681,
    "lng": -73.5501,
    "radius_meters": 120,
    "hint": "Là où le métal rencontre le béton.",
    "qr_code": "HEIST-CACHE-001",
    "owner_label": "Papa",
}

FAR_CACHE = {
    "title": "Trop loin",
    "lat": 46.8139,
    "lng": -71.2080,
    "radius_meters": 80,
    "owner_label": "Quelqu'un",
}


# ── Plantation + catalogue ────────────────────────────────────────────────────

async def test_plant_cache(client):
    r = await client.post("/world/caches", json=CACHE_PAYLOAD, headers=ADMIN_HEADERS)
    assert r.status_code == 201
    d = r.json()
    assert d["is_public"] if "is_public" in d else True
    assert d["claim_mode"] == "find"
    assert d["requires_proof"] is True
    assert d["claim_count"] == 0


async def test_plant_cache_requires_admin(client):
    r = await client.post("/world/caches", json=CACHE_PAYLOAD,
                          headers={"Authorization": "Bearer pas-la-bonne-cle"})
    assert r.status_code == 403


async def test_list_caches_never_leaks_qr(client):
    await client.post("/world/caches", json=CACHE_PAYLOAD, headers=ADMIN_HEADERS)
    r = await client.get("/world/caches")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert "qr_code" not in body[0]
    assert body[0]["requires_proof"] is True


async def test_bbox_filters(client):
    await client.post("/world/caches", json=CACHE_PAYLOAD, headers=ADMIN_HEADERS)
    await client.post("/world/caches", json=FAR_CACHE, headers=ADMIN_HEADERS)

    near = await client.get("/world/caches", params={
        "lat_min": 45.50, "lat_max": 45.60, "lng_min": -73.60, "lng_max": -73.50,
    })
    assert len(near.json()) == 1
    assert near.json()[0]["title"] == CACHE_PAYLOAD["title"]

    tout = await client.get("/world/caches")
    assert len(tout.json()) == 2


async def test_mission_waypoints_not_in_world(client):
    """Un waypoint de mission n'est pas public : il ne doit pas fuiter."""
    await client.post("/admin/missions", json=MISSION_PAYLOAD, headers=ADMIN_HEADERS)
    r = await client.get("/world/caches")
    assert r.json() == []


# ── Réclamation : le cœur du double régime ────────────────────────────────────

async def test_claim_requires_proof_when_qr(client):
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json={"player_name": "Sam"})
    assert r.status_code == 400


async def test_claim_wrong_proof(client):
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json={"player_name": "Sam", "proof": "mauvaise-preuve"})
    assert r.status_code == 403


async def test_claim_ok(client):
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json={"player_name": "Sam", "proof": "HEIST-CACHE-001"})
    assert r.status_code == 200
    d = r.json()
    assert d["claimed"] is True
    assert d["proven"] is True
    assert d["claim_count"] == 1


async def test_claim_idempotent_per_player(client):
    """Mode find : un joueur ne réclame qu'une fois, mais la cache reste ouverte."""
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    url = f"/world/caches/{wp['id']}/claim"
    body = {"player_name": "Sam", "proof": "HEIST-CACHE-001"}

    await client.post(url, json=body)
    r2 = await client.post(url, json=body)
    assert r2.status_code == 200
    d = r2.json()
    assert d["claimed"] is False
    assert d["already_claimed"] is True
    assert d["claim_count"] == 1


async def test_claim_multiple_players(client):
    """La multiplicité est la différence avec le régime progress."""
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    url = f"/world/caches/{wp['id']}/claim"

    a = await client.post(url, json={"player_name": "Sam", "proof": "HEIST-CACHE-001"})
    b = await client.post(url, json={"player_name": "Alex", "proof": "HEIST-CACHE-001"})
    assert a.json()["claim_count"] == 1
    assert b.json()["claim_count"] == 2

    listing = await client.get("/world/caches")
    assert listing.json()[0]["claim_count"] == 2


async def test_claim_unknown_cache(client):
    r = await client.post("/world/caches/9999/claim", json={"player_name": "Sam"})
    assert r.status_code == 404


# ── Ensemencement : une mission qui finit laisse une cache ────────────────────

async def test_publish_waypoint_detaches_and_opens(client):
    mission = (await client.post("/admin/missions", json=MISSION_PAYLOAD,
                                 headers=ADMIN_HEADERS)).json()
    wp_id = mission["waypoints"][0]["id"]

    r = await client.post(f"/world/caches/{wp_id}/publish", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    d = r.json()
    assert d["mission_id"] is None
    assert d["is_public"] is True
    assert d["claim_mode"] == "find"

    listing = await client.get("/world/caches")
    assert any(c["id"] == wp_id for c in listing.json())


# ── Versement idempotent (batch) ─────────────────────────────────────────────

async def test_publish_batch_is_idempotent(client):
    """Le même lot rejoué ne crée pas de doublon — indispensable au retry."""
    mission = (await client.post("/admin/missions", json=MISSION_PAYLOAD,
                                 headers=ADMIN_HEADERS)).json()
    wp = mission["waypoints"][0]

    lot = {"items": [{
        "mission_id": mission["id"],
        "waypoint_id": wp["id"],
        "title": wp["title"],
        "lat": wp["lat"],
        "lng": wp["lng"],
        "radius_meters": 140,
        "owner_label": "Papa",
    }]}

    r1 = await client.post("/world/publish", json=lot, headers=ADMIN_HEADERS)
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["created_count"] == 1
    assert d1["existing_count"] == 0
    first_id = d1["published"][0]["cache_id"]

    # Rejeu exact (coupure réseau, avion, file de retry)
    r2 = await client.post("/world/publish", json=lot, headers=ADMIN_HEADERS)
    d2 = r2.json()
    assert d2["created_count"] == 0
    assert d2["existing_count"] == 1
    assert d2["published"][0]["cache_id"] == first_id
    assert d2["published"][0]["created"] is False

    # Une seule cache dans le monde
    listing = await client.get("/world/caches")
    assert len(listing.json()) == 1
    assert listing.json()[0]["radius_meters"] == 140


async def test_publish_batch_from_payload(client):
    """Chemin hors-ligne : la mission n'existe pas côté serveur."""
    lot = {"items": [{
        "mission_id": 999,
        "waypoint_id": 4242,
        "title": "Cache jouée en avion",
        "lat": 45.56,
        "lng": -73.54,
        "radius_meters": 100,
        "hint": "Sous la troisieme planche.",
        "owner_label": "Papa",
    }]}

    r1 = await client.post("/world/publish", json=lot, headers=ADMIN_HEADERS)
    d1 = r1.json()
    assert d1["created_count"] == 1
    cache_id = d1["published"][0]["cache_id"]
    assert cache_id > 0

    r2 = await client.post("/world/publish", json=lot, headers=ADMIN_HEADERS)
    d2 = r2.json()
    assert d2["created_count"] == 0
    assert d2["published"][0]["cache_id"] == cache_id


async def test_publish_batch_mixed_counts(client):
    mission = (await client.post("/admin/missions", json=MISSION_PAYLOAD,
                                 headers=ADMIN_HEADERS)).json()
    wp = mission["waypoints"][0]

    item_a = {"mission_id": mission["id"], "waypoint_id": wp["id"],
              "title": wp["title"], "lat": wp["lat"], "lng": wp["lng"]}
    item_b = {"mission_id": 777, "waypoint_id": 1,
              "title": "Autre", "lat": 45.5, "lng": -73.5}

    await client.post("/world/publish", json={"items": [item_a]},
                      headers=ADMIN_HEADERS)
    r = await client.post("/world/publish", json={"items": [item_a, item_b]},
                          headers=ADMIN_HEADERS)
    d = r.json()
    assert d["created_count"] == 1
    assert d["existing_count"] == 1


async def test_publish_requires_admin(client):
    r = await client.post("/world/publish", json={"items": []},
                          headers={"Authorization": "Bearer nope"})
    assert r.status_code == 403
