import pytest
from fastapi.testclient import TestClient


def test_user_registration(client: TestClient):
    """Test user registration endpoint."""
    user_data = {
        "email": "newuser@example.com",
        "password": "securepassword123"
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data


def test_user_login(client: TestClient):
    """Test user login endpoint."""
    # First register a user
    user_data = {
        "email": "loginuser@example.com",
        "password": "loginpassword123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Then try to login
    response = client.post("/api/v1/auth/login", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client: TestClient, auth_headers: dict):
    """Test getting current user information."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "id" in data


def test_invalid_login(client: TestClient):
    """Test login with invalid credentials."""
    user_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/v1/auth/login", json=user_data)
    assert response.status_code == 401


def test_duplicate_registration(client: TestClient):
    """Test registering with duplicate email."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "password123"
    }
    
    # First registration should succeed
    response1 = client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 201
    
    # Second registration should fail
    response2 = client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 400