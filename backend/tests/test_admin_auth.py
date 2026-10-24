"""Auth admin : lecture à l'appel, refus explicite si mal configurée.

Le point critique est la rotation : changer ADMIN_KEY doit prendre effet
sans redémarrer le process. C'est ce que la lecture à l'import rendait
impossible.
"""
import pytest

from tests.conftest import ADMIN_HEADERS


async def test_admin_ok(client):
    r = await client.get("/admin/missions", headers=ADMIN_HEADERS)
    assert r.status_code == 200


async def test_admin_wrong_key_is_403(client):
    r = await client.get("/admin/missions",
                         headers={"Authorization": "Bearer pas-la-bonne-cle"})
    assert r.status_code == 403


async def test_admin_missing_key_is_503(client, monkeypatch):
    """Sans ADMIN_KEY on refuse explicitement — pas de clé par défaut."""
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    r = await client.get("/admin/missions", headers=ADMIN_HEADERS)
    assert r.status_code == 503
    assert "non configurée" in r.json()["detail"]


async def test_admin_weak_key_is_503(client, monkeypatch):
    """Une valeur de démonstration publique ne doit pas ouvrir le panneau."""
    monkeypatch.setenv("ADMIN_KEY", "admin-secret-key")
    r = await client.get("/admin/missions",
                         headers={"Authorization": "Bearer admin-secret-key"})
    assert r.status_code == 503
    assert "démonstration" in r.json()["detail"]


async def test_admin_short_key_is_503(client, monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "abc")
    r = await client.get("/admin/missions", headers={"Authorization": "Bearer abc"})
    assert r.status_code == 503


async def test_admin_key_rotation_without_restart(client, monkeypatch):
    """Rotation à chaud : la nouvelle clé passe, l'ancienne tombe."""
    monkeypatch.setenv("ADMIN_KEY", "cle-de-rotation-2026")

    new = await client.get("/admin/missions",
                           headers={"Authorization": "Bearer cle-de-rotation-2026"})
    assert new.status_code == 200

    old = await client.get("/admin/missions", headers=ADMIN_HEADERS)
    assert old.status_code == 403


async def test_admin_writes_also_guarded(client, monkeypatch):
    """Le versement au monde passe par la même dépendance."""
    monkeypatch.setenv("ADMIN_KEY", "admin-secret-key")
    r = await client.post("/world/publish", json={"items": []},
                          headers={"Authorization": "Bearer admin-secret-key"})
    assert r.status_code == 503
