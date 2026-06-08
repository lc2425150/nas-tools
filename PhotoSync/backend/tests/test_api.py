import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db, engine

@pytest.fixture
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await engine.dispose()

class TestAPI:
    async def test_health(self, client):
        r = await client.get("/api/v1/system/health")
        assert r.status_code == 200
        assert r.json()["status"] in ("healthy", "degraded")

    async def test_profiles_crud(self, client):
        r = await client.post("/api/v1/profiles", json={
            "name": "Test Profile", "match_type": "manual", "destination": "/photos/test",
        })
        assert r.status_code == 201
        pid = r.json()["id"]
        r = await client.get(f"/api/v1/profiles/{pid}")
        assert r.status_code == 200
        r = await client.put(f"/api/v1/profiles/{pid}", json={"name": "Updated"})
        assert r.status_code == 200 and r.json()["name"] == "Updated"
        r = await client.delete(f"/api/v1/profiles/{pid}")
        assert r.status_code == 200

    async def test_settings(self, client):
        r = await client.put("/api/v1/settings", json={"poll_interval": 10})
        assert r.status_code == 200
        r = await client.get("/api/v1/settings")
        assert r.status_code == 200
        assert r.json()["poll_interval"] == 10
