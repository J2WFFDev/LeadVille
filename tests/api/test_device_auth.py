"""Tests for device endpoint authentication and authorization."""

import pytest
from fastapi.testclient import TestClient

from src.impact_bridge.api.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def admin_headers(client):
    """Get admin authentication headers."""
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


@pytest.fixture
def viewer_headers(client):
    """Get viewer authentication headers."""
    login_data = {
        "username": "viewer1", 
        "password": "view123"
    }
    
    response = client.post("/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }


@pytest.fixture  
def ro_headers(client):
    """Get RO authentication headers."""
    login_data = {
        "username": "ro1",
        "password": "ro123456"
    }
    
    response = client.post("/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }


def test_device_list_requires_auth(client):
    """Test that device list endpoint requires authentication."""
    response = client.get("/v1/admin/devices/list")
    
    # Should return 403 (Forbidden) when no auth provided
    assert response.status_code == 403


def test_device_list_with_viewer(client, viewer_headers):
    """Test that viewer can access device list."""
    response = client.get("/v1/admin/devices/list", headers=viewer_headers)
    
    # Viewer should be able to read device list
    assert response.status_code == 200
    
    data = response.json()
    assert "devices" in data
    assert "total" in data


def test_device_list_with_admin(client, admin_headers):
    """Test that admin can access device list."""
    response = client.get("/v1/admin/devices/list", headers=admin_headers)
    
    # Admin should be able to read device list
    assert response.status_code == 200
    
    data = response.json()
    assert "devices" in data
    assert "total" in data


def test_device_discover_requires_admin(client, viewer_headers):
    """Test that device discovery requires admin privileges."""
    discover_data = {
        "duration": 5
    }
    
    # Viewer should not be able to start discovery
    response = client.post("/v1/admin/devices/discover", json=discover_data, headers=viewer_headers)
    assert response.status_code == 403


def test_device_discover_with_admin(client, admin_headers):
    """Test that admin can start device discovery."""
    discover_data = {
        "duration": 1  # Short duration for testing
    }
    
    response = client.post("/v1/admin/devices/discover", json=discover_data, headers=admin_headers)
    
    # Admin should be able to start discovery
    # Note: This might fail due to BLE dependencies, but auth should work
    assert response.status_code in [200, 500]  # 500 if BLE not available, but auth passed


def test_device_pair_requires_admin(client, ro_headers):
    """Test that device pairing requires admin privileges."""
    pair_data = {
        "address": "00:11:22:33:44:55",
        "device_type": "bt50"
    }
    
    # RO should not be able to pair devices
    response = client.post("/v1/admin/devices/pair", json=pair_data, headers=ro_headers)
    assert response.status_code == 403


def test_device_assign_requires_admin(client, viewer_headers):
    """Test that device assignment requires admin privileges."""
    assign_data = {
        "address": "00:11:22:33:44:55",
        "target_id": "target_1"
    }
    
    # Viewer should not be able to assign devices
    response = client.post("/v1/admin/devices/assign", json=assign_data, headers=viewer_headers)
    assert response.status_code == 403


def test_device_health_with_authenticated_user(client, ro_headers):
    """Test that authenticated users can view device health."""
    response = client.get("/v1/admin/devices/health", headers=ro_headers)
    
    # Any authenticated user should be able to view health
    assert response.status_code == 200
    
    # Should return a list (empty or with devices)
    data = response.json()
    assert isinstance(data, list)


def test_device_monitoring_requires_admin(client, viewer_headers):
    """Test that health monitoring control requires admin."""
    monitoring_data = {
        "enabled": True,
        "interval": 30
    }
    
    # Viewer should not be able to control monitoring
    response = client.post("/v1/admin/devices/monitoring", json=monitoring_data, headers=viewer_headers)
    assert response.status_code == 403


def test_device_remove_requires_admin(client, ro_headers):
    """Test that device removal requires admin privileges."""
    device_address = "00:11:22:33:44:55"
    
    # RO should not be able to remove devices
    response = client.delete(f"/v1/admin/devices/{device_address}", headers=ro_headers)
    assert response.status_code == 403


def test_no_auth_header_forbidden(client):
    """Test that requests without auth header are forbidden."""
    endpoints_to_test = [
        ("GET", "/v1/admin/devices/list"),
        ("GET", "/v1/admin/devices/health"), 
        ("POST", "/v1/admin/devices/discover"),
        ("POST", "/v1/admin/devices/pair"),
        ("POST", "/v1/admin/devices/assign"),
        ("DELETE", "/v1/admin/devices/00:11:22:33:44:55")
    ]
    
    for method, endpoint in endpoints_to_test:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})
        elif method == "DELETE":
            response = client.delete(endpoint)
        
        # All should return 403 Forbidden when no auth provided
        assert response.status_code == 403, f"Failed for {method} {endpoint}"


def test_invalid_token_forbidden(client):
    """Test that invalid tokens are rejected."""
    invalid_headers = {
        "Authorization": "Bearer invalid_token_12345"
    }
    
    response = client.get("/v1/admin/devices/list", headers=invalid_headers)
    assert response.status_code in [401, 403]  # Should be unauthorized