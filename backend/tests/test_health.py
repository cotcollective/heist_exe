import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "online"


@pytest.mark.asyncio
async def test_docs_accessible(client):
    r = await client.get("/docs")
    assert r.status_code == 200
