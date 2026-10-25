"""Le PIN — un espace qui traîne ne doit pas bloquer un enfant dans l'escalier.

Défaut trouvé en usage réel : un PIN créé « 4821 » refusait « 4821 » si un
espace s'était glissé autour. Sur un clavier de téléphone, c'est banal
(autocomplétion, copier-coller, retour de ligne). Le message affiché était
« PIN incorrect », sans la moindre piste.

La réponse d'énigme était déjà normalisée (`strip().lower()`) ; le PIN ne
l'était pas. Incohérence, et elle coûtait un blocage au pire moment.
"""

import pytest

pytestmark = pytest.mark.asyncio

ADMIN = {"Authorization": "Bearer heist123"}


async def _make_mission(client, pin="4821", title="Ma mission perso"):
    r = await client.post("/admin/missions", headers=ADMIN, json={
        "title": title,
        "lore": "test",
        "pin": pin,
        "duration_minutes": 25,
        "reward_text": "bravo",
        "waypoints": [{
            "order": 0, "title": "Étape 1", "hint": "ici",
            "lat": 45.5680, "lng": -73.5500, "radius_meters": 30,
            "enigma": {"question": "2+2 ?", "answer": "4"},
        }],
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _auth(client, mission_id, pin, name="Dave"):
    return await client.post("/missions/auth", json={
        "mission_id": mission_id, "pin": pin, "player_name": name,
    })


async def test_pin_with_surrounding_spaces_is_accepted(client):
    mid = await _make_mission(client)

    for variante in [" 4821", "4821 ", "  4821  ", "\t4821\n"]:
        r = await _auth(client, mid, variante)
        assert r.status_code == 200, f"{variante!r} refusé"


async def test_pin_without_spaces_still_works(client):
    mid = await _make_mission(client)
    r = await _auth(client, mid, "4821")
    assert r.status_code == 200


async def test_wrong_pin_is_still_rejected(client):
    """Normaliser ne doit pas transformer la vérification en passoire."""
    mid = await _make_mission(client)

    for mauvais in ["0000", "482", "48210", ""]:
        r = await _auth(client, mid, mauvais)
        assert r.status_code == 401, f"{mauvais!r} accepté à tort"


async def test_pin_created_with_spaces_is_usable_typed_clean(client):
    """Le constructeur peut recevoir un PIN avec un espace : il doit rester utilisable."""
    mid = await _make_mission(client, pin=" 9999 ")

    r = await _auth(client, mid, "9999")
    assert r.status_code == 200

    r2 = await _auth(client, mid, " 9999 ")
    assert r2.status_code == 200


async def test_enigma_answer_tolerates_case_and_spaces(client):
    """Cohérence : la réponse d'énigme se normalise déjà, on le vérifie ici."""
    mid = await _make_mission(client)
    r = await _auth(client, mid, "4821")
    tok = r.json()["access_token"]
    wp = r.json()["mission"]["waypoints"][0]

    a = await client.post("/waypoints/answer",
                          json={"waypoint_id": wp["id"], "answer": "  4  "},
                          headers={"Authorization": f"Bearer {tok}"})
    assert a.status_code == 200
    assert a.json()["correct"] is True
