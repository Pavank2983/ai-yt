import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/auth/register", json={
        "name": "TestUser",
        "email": "testuser@example.com",
        "password": "12345"
    })
    assert response.status_code in [200, 400]  # 400 if already exists

def test_login_user():
    response = client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "12345"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_me_endpoint():
    # Login first
    login = client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "12345"
    })
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert "email" in response.json()
