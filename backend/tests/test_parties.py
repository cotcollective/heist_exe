"""Comptes et parties — la séparation des mécaniques.

Ce que ces tests protègent, dans l'ordre d'importance :

  1. Une partie naît SANS compte. Si un jour il faut un compte pour jouer,
     le produit a changé sans que personne ne l'ait décidé.
  2. Le jeton est une capacité : sans lui rien, avec un autre rien non plus.
  3. Un email seul ne rend jamais une partie — sinon l'étiquette devient
     une clé et n'importe qui lit l'avancement du voisin.
  4. Les comptes et les missions sont étanches.
"""

import pytest
from sqlalchemy import func, select

from app.models import Mission, Party

pytestmark = pytest.mark.asyncio


async def _new_party(client, kind="mission", ref_id=None, title="Chasse du samedi"):
    r = await client.post("/play/parties", json={"kind": kind, "ref_id": ref_id, "title": title})
    assert r.status_code == 201, r.text
    return r.json()


async def _new_account(client, email="famille@exemple.test", label="Famille"):
    r = await client.post("/play/accounts", json={"email": email, "label": label})
    assert r.status_code == 201, r.text
    return r.json()


# -- 1. Jouer sans compte ----------------------------------------------------


async def test_party_needs_no_account(client):
    data = await _new_party(client)
    assert data["party"]["account_id"] is None
    assert data["party"]["kind"] == "mission"
    assert len(data["token"]) >= 32


async def test_party_token_is_not_stored_in_clear(client, db):
    data = await _new_party(client)
    token = data["token"]

    party = await db.get(Party, data["party"]["id"])
    assert token not in party.token_hash
    assert len(party.token_hash) == 64


async def test_state_starts_empty_and_can_be_read_back(client):
    data = await _new_party(client)
    pid, token = data["party"]["id"], data["token"]

    r = await client.get(f"/play/parties/{pid}", headers={"X-Party-Token": token})
    assert r.status_code == 200
    assert r.json()["state"] == {}


# -- 2. Le jeton est une capacite --------------------------------------------


async def test_missing_token_is_refused(client):
    pid = (await _new_party(client))["party"]["id"]
    assert (await client.get(f"/play/parties/{pid}")).status_code == 401


async def test_wrong_token_is_refused(client):
    pid = (await _new_party(client))["party"]["id"]
    r = await client.get(f"/play/parties/{pid}", headers={"X-Party-Token": "mauvais"})
    assert r.status_code == 403


async def test_unknown_party_and_bad_token_look_identical(client):
    pid = (await _new_party(client))["party"]["id"]

    r_bad = await client.get(f"/play/parties/{pid}", headers={"X-Party-Token": "x"})
    r_missing = await client.get("/play/parties/999999", headers={"X-Party-Token": "x"})

    assert r_bad.status_code == r_missing.status_code == 403
    assert r_bad.json()["detail"] == r_missing.json()["detail"]


async def test_delete_needs_the_token(client):
    pid = (await _new_party(client))["party"]["id"]
    assert (await client.delete(f"/play/parties/{pid}")).status_code == 401


# -- 3. Points de controle ---------------------------------------------------


async def test_checkpoint_replaces_state(client):
    data = await _new_party(client)
    pid, h = data["party"]["id"], {"X-Party-Token": data["token"]}

    await client.patch(f"/play/parties/{pid}", headers=h, json={"state": {"etape": 2}})
    await client.patch(f"/play/parties/{pid}", headers=h, json={"state": {"etape": 3}})

    r = await client.get(f"/play/parties/{pid}", headers=h)
    assert r.json()["state"] == {"etape": 3}


async def test_merge_keeps_what_the_other_tab_wrote(client):
    data = await _new_party(client)
    pid, h = data["party"]["id"], {"X-Party-Token": data["token"]}

    await client.patch(f"/play/parties/{pid}", headers=h, json={"merge": {"balise_1": True}})
    await client.patch(f"/play/parties/{pid}", headers=h, json={"merge": {"balise_2": True}})

    r = await client.get(f"/play/parties/{pid}", headers=h)
    assert r.json()["state"] == {"balise_1": True, "balise_2": True}


async def test_empty_checkpoint_is_refused(client):
    data = await _new_party(client)
    r = await client.patch(
        f"/play/parties/{data['party']['id']}",
        headers={"X-Party-Token": data["token"]},
        json={},
    )
    assert r.status_code == 422


async def test_bad_kind_is_refused(client):
    r = await client.post("/play/parties", json={"kind": "donjon"})
    assert r.status_code == 422


async def test_title_can_be_set_at_checkpoint(client):
    data = await _new_party(client, title=None)
    pid, h = data["party"]["id"], {"X-Party-Token": data["token"]}

    r = await client.patch(f"/play/parties/{pid}", headers=h, json={"title": "Le parc"})
    assert r.status_code == 200
    assert r.json()["title"] == "Le parc"


# -- 4. Le compte est un conteneur -------------------------------------------


async def test_account_holds_many_parties(client):
    acc = await _new_account(client)
    aid, ah = acc["account"]["id"], {"X-Account-Token": acc["token"]}

    for i in range(3):
        p = await _new_party(client, title=f"Partie {i}")
        r = await client.post(
            f"/play/accounts/{aid}/parties",
            headers=ah,
            json={"party_id": p["party"]["id"], "party_token": p["token"]},
        )
        assert r.status_code == 200, r.text

    r = await client.get(f"/play/accounts/{aid}/parties", headers=ah)
    listed = r.json()
    assert len(listed) == 3
    assert all(p["account_id"] == aid for p in listed)


async def test_email_is_not_a_key(client):
    acc = await _new_account(client, email="unique@exemple.test")
    aid = acc["account"]["id"]

    assert (await client.get(f"/play/accounts/{aid}/parties")).status_code == 401
    r = await client.get(f"/play/accounts/{aid}/parties",
                         headers={"X-Account-Token": "devine"})
    assert r.status_code == 403


async def test_same_email_twice_is_two_containers(client):
    a = await _new_account(client, email="pareil@exemple.test")
    b = await _new_account(client, email="pareil@exemple.test")
    assert a["account"]["id"] != b["account"]["id"]
    assert a["token"] != b["token"]


async def test_attach_needs_both_tokens(client):
    acc = await _new_account(client)
    p = await _new_party(client)

    r = await client.post(
        f"/play/accounts/{acc['account']['id']}/parties",
        headers={"X-Account-Token": acc["token"]},
        json={"party_id": p["party"]["id"], "party_token": "mauvais-jeton"},
    )
    assert r.status_code == 403


async def test_detach_keeps_the_party_alive(client):
    acc = await _new_account(client)
    aid, ah = acc["account"]["id"], {"X-Account-Token": acc["token"]}
    p = await _new_party(client)
    pid, ph = p["party"]["id"], {"X-Party-Token": p["token"]}

    await client.post(f"/play/accounts/{aid}/parties", headers=ah,
                      json={"party_id": pid, "party_token": p["token"]})
    await client.patch(f"/play/parties/{pid}", headers=ph, json={"state": {"etape": 1}})

    r = await client.delete(f"/play/accounts/{aid}/parties/{pid}", headers=ah)
    assert r.status_code == 200
    assert r.json()["account_id"] is None

    after = await client.get(f"/play/parties/{pid}", headers=ph)
    assert after.status_code == 200
    assert after.json()["state"] == {"etape": 1}


async def test_cannot_detach_someone_elses_party(client):
    a = await _new_account(client, email="a@exemple.test")
    b = await _new_account(client, email="b@exemple.test")
    p = await _new_party(client)

    await client.post(f"/play/accounts/{a['account']['id']}/parties",
                      headers={"X-Account-Token": a["token"]},
                      json={"party_id": p["party"]["id"], "party_token": p["token"]})

    r = await client.delete(
        f"/play/accounts/{b['account']['id']}/parties/{p['party']['id']}",
        headers={"X-Account-Token": b["token"]},
    )
    assert r.status_code == 404


# -- 5. Etancheite avec les missions -----------------------------------------


async def _mission_count(db) -> int:
    return (await db.execute(select(func.count()).select_from(Mission))).scalar()


async def test_creating_a_party_never_touches_missions(client, db):
    before = await _mission_count(db)
    await _new_party(client, kind="mission", ref_id=None)
    assert await _mission_count(db) == before


async def test_party_can_reference_a_mission_without_owning_it(client, db):
    m = Mission(title="Mission temoin", pin_hash="x", duration_minutes=30)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    mid = m.id

    data = await _new_party(client, kind="mission", ref_id=mid)
    assert data["party"]["ref_id"] == mid

    assert not hasattr(await db.get(Mission, mid), "parties")
