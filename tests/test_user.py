import pytest
from fastapi.testclient import TestClient
import tempfile
import os

# Setup test database
@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TEST_DB_PATH", path)

    from database import init_db
    init_db(path)

    yield path
    os.unlink(path)

@pytest.fixture
def client(setup_test_db):
    # Import after setting up test db
    from server import app
    return TestClient(app)

def test_create_user(client):
    response = client.post("/api/user", json={
        "voice_preference": "male",
        "onboarding_mode": "full"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["voice_preference"] == "male"
    assert data["onboarding_mode"] == "full"
    assert "id" in data

def test_get_user(client):
    # Create user first
    create_resp = client.post("/api/user", json={"voice_preference": "female"})
    user_id = create_resp.json()["id"]

    # Get user
    response = client.get(f"/api/user/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id

def test_update_user(client):
    # Create user first
    create_resp = client.post("/api/user", json={"voice_preference": "female"})
    user_id = create_resp.json()["id"]

    # Update user
    response = client.put(f"/api/user/{user_id}", json={"voice_preference": "male"})
    assert response.status_code == 200
    assert response.json()["voice_preference"] == "male"
