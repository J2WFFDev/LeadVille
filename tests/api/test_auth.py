"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.impact_bridge.api.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture  
def auth_headers(client):
    """Get authentication headers for testing."""
    # Login with admin user
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = client.post("/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }


def test_login_success(client):
    """Test successful login."""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = client.post("/v1/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "user" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    login_data = {
        "username": "admin",
        "password": "wrongpassword"
    }
    
    response = client.post("/v1/auth/login", json=login_data)
    
    assert response.status_code == 401
    # Check that message exists and contains expected text
    response_data = response.json()
    message = response_data.get("message")
    assert message is not None
    assert "Incorrect username or password" in message


def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    login_data = {
        "username": "nonexistent",
        "password": "password"
    }
    
    response = client.post("/v1/auth/login", json=login_data)
    
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["username"] == "admin"
    assert data["role"] == "admin"
    assert data["is_active"] is True


def test_refresh_token(client):
    """Test token refresh."""
    # First login
    login_data = {
        "username": "admin", 
        "password": "admin123"
    }
    
    login_response = client.post("/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]
    
    # Refresh the token
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    response = client.post("/v1/auth/refresh", json=refresh_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_logout(client):
    """Test user logout."""
    # First login
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = client.post("/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]
    
    # Logout
    logout_data = {
        "refresh_token": refresh_token
    }
    
    response = client.post("/v1/auth/logout", 
                          headers={"Authorization": f"Bearer {tokens['access_token']}"},
                          json=logout_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data


def test_get_csrf_token(client, auth_headers):
    """Test CSRF token generation."""
    response = client.get("/v1/auth/csrf-token", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "token" in data
    assert "expires_at" in data


def test_verify_token(client, auth_headers):
    """Test token verification."""
    response = client.post("/v1/auth/verify", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valid"] is True
    assert "user" in data
    assert data["user"]["username"] == "admin"


def test_get_roles(client):
    """Test getting available roles."""
    response = client.get("/v1/auth/roles")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "roles" in data
    roles = data["roles"]
    
    assert "admin" in roles
    assert "ro" in roles
    assert "scorekeeper" in roles
    assert "viewer" in roles
    assert "coach" in roles


def test_unauthorized_access(client):
    """Test accessing protected endpoint without authentication."""
    response = client.get("/v1/auth/me")
    
    # FastAPI security might return 403 when no credentials provided
    assert response.status_code in [401, 403]


def test_invalid_token(client):
    """Test using invalid token."""
    headers = {
        "Authorization": "Bearer invalid_token"
    }
    
    response = client.get("/v1/auth/me", headers=headers)
    
    assert response.status_code == 401


def test_different_user_roles(client):
    """Test login with different user roles."""
    test_users = [
        ("ro1", "ro123456", "ro"),
        ("scorekeeper1", "score123", "scorekeeper"),  
        ("viewer1", "view123", "viewer"),
        ("coach1", "coach123", "coach")
    ]
    
    for username, password, expected_role in test_users:
        login_data = {
            "username": username,
            "password": password
        }
        
        response = client.post("/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user"]["username"] == username
        assert data["user"]["role"] == expected_role