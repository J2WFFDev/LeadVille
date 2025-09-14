"""Tests for admin dashboard API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.impact_bridge.api.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_node_info(client):
    """Test node info endpoint."""
    response = client.get("/v1/admin/node/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "mode" in data
    assert "status" in data
    assert "versions" in data
    assert isinstance(data["versions"], dict)


def test_system_monitoring(client):
    """Test system monitoring endpoint."""
    response = client.get("/v1/admin/monitoring/system")
    assert response.status_code == 200
    
    data = response.json()
    assert "cpu_usage_percent" in data
    assert "memory_usage_mb" in data
    assert "disk_usage_gb" in data
    assert "uptime_seconds" in data
    assert isinstance(data["cpu_usage_percent"], (int, float))
    assert isinstance(data["memory_usage_mb"], (int, float))


def test_service_health(client):
    """Test service health endpoint."""
    response = client.get("/v1/admin/monitoring/services")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # BLE, MQTT, Database
    
    for service in data:
        assert "service_name" in service
        assert "status" in service
        assert "last_check" in service
        assert service["status"] in ["healthy", "degraded", "unhealthy"]


def test_network_status(client):
    """Test network status endpoint."""
    response = client.get("/v1/admin/network/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "mode" in data
    assert "connected" in data
    assert isinstance(data["connected"], bool)


def test_network_configure(client):
    """Test network configuration endpoint."""
    # Test offline mode
    response = client.post(
        "/v1/admin/network/configure",
        json={"mode": "offline"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "success" in data
    assert "mode" in data
    assert data["mode"] == "offline"


def test_logs_tail(client):
    """Test log tail endpoint."""
    response = client.get("/v1/admin/logs/tail")
    assert response.status_code == 200
    
    data = response.json()
    assert "logs" in data
    assert "total_lines" in data
    assert "has_more" in data
    assert isinstance(data["logs"], list)
    
    if data["logs"]:
        log_entry = data["logs"][0]
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "message" in log_entry


def test_node_update(client):
    """Test node update endpoint."""
    response = client.put(
        "/v1/admin/node/info",
        json={"name": "test-node"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert "name" in data


def test_invalid_network_mode(client):
    """Test invalid network mode."""
    response = client.post(
        "/v1/admin/network/configure",
        json={"mode": "invalid"}
    )
    assert response.status_code == 400