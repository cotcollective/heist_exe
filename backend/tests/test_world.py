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

async def _agent(client, name):
    """Enregistre un agent et renvoie une fabrique de corps signé."""
    from tests.agentkit import make_agent, sign_claim

    priv, jwk = make_agent()
    r = await client.post("/world/agents",
                          json={"player_name": name, "public_jwk": jwk})
    assert r.status_code == 200, r.text

    def body(waypoint_id, proof=None, ts=None, signature=None):
        sig, stamp = sign_claim(priv, waypoint_id, name, ts)
        out = {
            "player_name": name,
            "ts": stamp,
            "signature": signature if signature is not None else sig,
        }
        if proof is not None:
            out["proof"] = proof
        return out

    return body


async def test_claim_requires_proof_when_qr(client):
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    b = await _agent(client, "Sam")
    r = await client.post(f"/world/caches/{wp['id']}/claim", json=b(wp["id"]))
    assert r.status_code == 400


async def test_claim_wrong_proof(client):
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    b = await _agent(client, "Sam")
    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json=b(wp["id"], proof="mauvaise-preuve"))
    assert r.status_code == 403


async def test_claim_ok(client):
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    b = await _agent(client, "Sam")
    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json=b(wp["id"], proof="HEIST-CACHE-001"))
    assert r.status_code == 200
    d = r.json()
    assert d["claimed"] is True
    assert d["proven"] is True
    assert d["claim_count"] == 1


async def test_claim_idempotent_per_player(client):
    """Mode find : un joueur ne réclame qu'une fois, mais la cache reste ouverte."""
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    b = await _agent(client, "Sam")

    await client.post(f"/world/caches/{wp['id']}/claim",
                      json=b(wp["id"], proof="HEIST-CACHE-001"))
    r2 = await client.post(f"/world/caches/{wp['id']}/claim",
                           json=b(wp["id"], proof="HEIST-CACHE-001"))
    assert r2.status_code == 200
    d = r2.json()
    assert d["claimed"] is False
    assert d["already_claimed"] is True
    assert d["claim_count"] == 1


async def test_claim_multiple_players(client):
    """La multiplicité est la différence avec le régime progress."""
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    sam = await _agent(client, "Sam")
    alex = await _agent(client, "Alex")
    url = f"/world/caches/{wp['id']}/claim"

    a = await client.post(url, json=sam(wp["id"], proof="HEIST-CACHE-001"))
    b = await client.post(url, json=alex(wp["id"], proof="HEIST-CACHE-001"))
    assert a.json()["claim_count"] == 1
    assert b.json()["claim_count"] == 2

    listing = await client.get("/world/caches")
    assert listing.json()[0]["claim_count"] == 2


async def test_claim_unknown_cache(client):
    b = await _agent(client, "Sam")
    r = await client.post("/world/caches/9999/claim", json=b(9999))
    assert r.status_code == 404


# ── Réclamant authentifié ────────────────────────────────────────────────────

async def test_claim_without_agent_is_refused(client):
    """Sans clé d'appareil, on ne peut pas réclamer — même sans signature."""
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json={"player_name": "Inconnu"})
    assert r.status_code == 403
    assert "non enregistré" in r.json()["detail"]


async def test_claim_without_signature_is_refused(client):
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    await _agent(client, "Sam")
    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json={"player_name": "Sam", "proof": "HEIST-CACHE-001"})
    assert r.status_code == 401


async def test_claim_with_forged_signature_is_refused(client):
    """Signature d'une autre clé : le nom est bon, la preuve non."""
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    b = await _agent(client, "Sam")
    from tests.agentkit import make_agent, sign_claim
    other_priv, _ = make_agent()
    forged, _ = sign_claim(other_priv, wp["id"], "Sam")

    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json=b(wp["id"], proof="HEIST-CACHE-001", signature=forged))
    assert r.status_code == 403
    assert "invalide" in r.json()["detail"]


async def test_claim_signature_is_bound_to_waypoint(client):
    """Une signature valide pour A ne vaut pas pour B."""
    wp_a = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                              headers=ADMIN_HEADERS)).json()
    wp_b = (await client.post("/world/caches", json={**CACHE_PAYLOAD,
                                                     "title": "Autre",
                                                     "qr_code": "HEIST-CACHE-002"},
                              headers=ADMIN_HEADERS)).json()
    b = await _agent(client, "Sam")

    body_for_a = b(wp_a["id"], proof="HEIST-CACHE-001")
    r = await client.post(f"/world/caches/{wp_b['id']}/claim",
                          json={**body_for_a, "proof": "HEIST-CACHE-002"})
    assert r.status_code == 403


async def test_claim_expired_signature_is_refused(client):
    import time as _t
    wp = (await client.post("/world/caches", json=CACHE_PAYLOAD,
                            headers=ADMIN_HEADERS)).json()
    b = await _agent(client, "Sam")
    r = await client.post(f"/world/caches/{wp['id']}/claim",
                          json=b(wp["id"], proof="HEIST-CACHE-001",
                                 ts=int(_t.time()) - 5000))
    assert r.status_code == 401
    assert "expirée" in r.json()["detail"]


async def test_agent_name_cannot_be_stolen(client):
    """Un nom déjà associé à une clé n'est pas récupérable par une autre."""
    from tests.agentkit import make_agent
    await _agent(client, "Sam")
    _, other_jwk = make_agent()
    r = await client.post("/world/agents",
                          json={"player_name": "Sam", "public_jwk": other_jwk})
    assert r.status_code == 409


async def test_agent_registration_is_idempotent(client):
    """Re-enregistrer la même clé ne casse rien (relance de l'app)."""
    from tests.agentkit import make_agent
    priv, jwk = make_agent()
    a = await client.post("/world/agents", json={"player_name": "Sam", "public_jwk": jwk})
    b = await client.post("/world/agents", json={"player_name": "Sam", "public_jwk": jwk})
    assert a.status_code == 200 and b.status_code == 200


async def test_agent_rejects_bad_key(client):
    r = await client.post("/world/agents",
                          json={"player_name": "Sam", "public_jwk": {"kty": "RSA"}})
    assert r.status_code == 400


# ── Ensemencement : une mission qui finit laisse une cache ────────────────────

async def test_publish_copies_and_mission_survives(client):
    """Le versement COPIE : la mission garde ses waypoints, le monde gagne une cache."""
    mission = (await client.post("/admin/missions", json=MISSION_PAYLOAD,
                                 headers=ADMIN_HEADERS)).json()
    wp = mission["waypoints"][0]

    r = await client.post("/world/publish", json={"items": [{
        "mission_id": mission["id"],
        "waypoint_id": wp["id"],
        "title": wp["title"],
        "lat": wp["lat"],
        "lng": wp["lng"],
        "radius_meters": 120,
        "owner_label": "Papa",
    }]}, headers=ADMIN_HEADERS)
    assert r.status_code == 200
    cache_id = r.json()["published"][0]["cache_id"]
    assert cache_id != wp["id"], "la cache doit être un objet distinct du waypoint"

    # La mission est intacte
    missions = (await client.get("/admin/missions", headers=ADMIN_HEADERS)).json()
    m = next(x for x in missions if x["id"] == mission["id"])
    assert any(w["id"] == wp["id"] for w in m["waypoints"])
    assert all(w["is_public"] is False for w in m["waypoints"])

    # Le monde a la copie
    listing = (await client.get("/world/caches")).json()
    assert any(c["id"] == cache_id for c in listing)
    cache = next(c for c in listing if c["id"] == cache_id)
    assert cache["claim_mode"] == "find"
    assert cache["radius_meters"] == 120


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
