"""Tests for BLE device management API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient
from datetime import datetime

from src.impact_bridge.api.main import create_app
from src.impact_bridge.device_manager import DiscoveredDevice, DeviceHealth


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    app = create_app()
    return TestClient(app)


class TestDeviceDiscoveryAPI:
    """Test device discovery API endpoints."""
    
    def test_discover_devices_success(self, client):
        """Test successful device discovery."""
        mock_discovered_devices = [
            DiscoveredDevice(
                address="AA:BB:CC:DD:EE:FF",
                name="Test BT50",
                rssi=-50,
                manufacturer_data={0x0183: b"test"},
                service_uuids=["0000ffe0-0000-1000-8000-00805f9a34fb"],
                local_name="Test BT50",
                advertisement_data={},
                device_type="bt50"
            ),
            DiscoveredDevice(
                address="11:22:33:44:55:66",
                name="Test AMG",
                rssi=-60,
                manufacturer_data={},
                service_uuids=["6e400001-b5a3-f393-e0a9-e50e24dcca9e"],
                local_name="Test AMG",
                advertisement_data={},
                device_type="amg"
            )
        ]
        
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.start_discovery = AsyncMock(return_value=mock_discovered_devices)
            
            response = client.post(
                "/v1/admin/devices/discover",
                json={"duration": 5.0}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_found"] == 2
            assert data["duration"] == 5.0
            assert len(data["devices"]) == 2
            
            # Check first device
            device1 = data["devices"][0]
            assert device1["address"] == "AA:BB:CC:DD:EE:FF"
            assert device1["name"] == "Test BT50"
            assert device1["rssi"] == -50
            assert device1["device_type"] == "bt50"
            assert device1["manufacturer_data"] == {"395": "74657374"}  # hex encoded
            
            # Check second device
            device2 = data["devices"][1]
            assert device2["address"] == "11:22:33:44:55:66"
            assert device2["name"] == "Test AMG"
            assert device2["device_type"] == "amg"
    
    def test_discover_devices_invalid_duration(self, client):
        """Test device discovery with invalid duration."""
        response = client.post(
            "/v1/admin/devices/discover",
            json={"duration": 0.5}  # Too short
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_discover_devices_exception(self, client):
        """Test device discovery with exception."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.start_discovery = AsyncMock(side_effect=Exception("BLE error"))
            
            response = client.post(
                "/v1/admin/devices/discover",
                json={"duration": 5.0}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "BLE error" in data["detail"]


class TestDevicePairingAPI:
    """Test device pairing API endpoints."""
    
    def test_pair_device_success(self, client):
        """Test successful device pairing."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.pair_device = AsyncMock(return_value=True)
            
            response = client.post(
                "/v1/admin/devices/pair",
                json={
                    "address": "AA:BB:CC:DD:EE:FF",
                    "device_type": "bt50"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["address"] == "AA:BB:CC:DD:EE:FF"
            assert "Successfully paired" in data["message"]
    
    def test_pair_device_failure(self, client):
        """Test failed device pairing."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.pair_device = AsyncMock(return_value=False)
            
            response = client.post(
                "/v1/admin/devices/pair",
                json={
                    "address": "AA:BB:CC:DD:EE:FF",
                    "device_type": "bt50"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert data["address"] == "AA:BB:CC:DD:EE:FF"
            assert "Failed to pair" in data["message"]
    
    def test_pair_device_exception(self, client):
        """Test device pairing with exception."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.pair_device = AsyncMock(side_effect=Exception("Connection error"))
            
            response = client.post(
                "/v1/admin/devices/pair",
                json={
                    "address": "AA:BB:CC:DD:EE:FF",
                    "device_type": "bt50"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Connection error" in data["detail"]


class TestDeviceAssignmentAPI:
    """Test device assignment API endpoints."""
    
    def test_assign_device_success(self, client):
        """Test successful device assignment."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.assign_device_to_target = AsyncMock(return_value=True)
            
            response = client.post(
                "/v1/admin/devices/assign",
                json={
                    "address": "AA:BB:CC:DD:EE:FF",
                    "target_id": 123
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["address"] == "AA:BB:CC:DD:EE:FF"
            assert data["target_id"] == 123
            assert "Successfully assigned" in data["message"]
    
    def test_assign_device_failure(self, client):
        """Test failed device assignment."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.assign_device_to_target = AsyncMock(return_value=False)
            
            response = client.post(
                "/v1/admin/devices/assign",
                json={
                    "address": "AA:BB:CC:DD:EE:FF",
                    "target_id": 123
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert data["target_id"] == 123
            assert "Failed to assign" in data["message"]
    
    def test_unassign_device_success(self, client):
        """Test successful device unassignment."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.unassign_device = AsyncMock(return_value=True)
            
            response = client.post(
                "/v1/admin/devices/unassign",
                json={"address": "AA:BB:CC:DD:EE:FF"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["address"] == "AA:BB:CC:DD:EE:FF"
            assert "Successfully unassigned" in data["message"]
    
    def test_unassign_device_failure(self, client):
        """Test failed device unassignment."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.unassign_device = AsyncMock(return_value=False)
            
            response = client.post(
                "/v1/admin/devices/unassign",
                json={"address": "AA:BB:CC:DD:EE:FF"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert "Failed to unassign" in data["message"]


class TestDeviceListAPI:
    """Test device listing API endpoints."""
    
    def test_list_devices_empty(self, client):
        """Test listing devices when none exist."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.get_device_list = AsyncMock(return_value=[])
            
            response = client.get("/v1/admin/devices/list")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total"] == 0
            assert data["devices"] == []
    
    def test_list_devices_with_data(self, client):
        """Test listing devices with existing data."""
        mock_devices = [
            {
                'address': 'AA:BB:CC:DD:EE:FF',
                'label': 'Test Sensor 1',
                'target_id': 123,
                'node_id': None,
                'last_seen': datetime.utcnow(),
                'battery': 85.5,
                'rssi': -45,
                'calibration': {'offset': 1.0},
                'is_connected': True,
                'last_error': None,
                'connection_attempts': 0
            },
            {
                'address': '11:22:33:44:55:66',
                'label': 'Test Sensor 2',
                'target_id': None,
                'node_id': 456,
                'last_seen': datetime.utcnow(),
                'battery': None,
                'rssi': -60,
                'calibration': None,
                'is_connected': False,
                'last_error': 'Connection timeout',
                'connection_attempts': 3
            }
        ]
        
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.get_device_list = AsyncMock(return_value=mock_devices)
            
            response = client.get("/v1/admin/devices/list")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total"] == 2
            assert len(data["devices"]) == 2
            
            # Check first device
            device1 = data["devices"][0]
            assert device1["address"] == "AA:BB:CC:DD:EE:FF"
            assert device1["label"] == "Test Sensor 1"
            assert device1["target_id"] == 123
            assert device1["battery"] == 85.5
            assert device1["is_connected"] is True
            
            # Check second device
            device2 = data["devices"][1]
            assert device2["address"] == "11:22:33:44:55:66"
            assert device2["node_id"] == 456
            assert device2["last_error"] == "Connection timeout"
            assert device2["connection_attempts"] == 3
    
    def test_list_devices_exception(self, client):
        """Test device listing with exception."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.get_device_list = AsyncMock(side_effect=Exception("Database error"))
            
            response = client.get("/v1/admin/devices/list")
            
            assert response.status_code == 500
            data = response.json()
            assert "Database error" in data["detail"]


class TestDeviceHealthAPI:
    """Test device health monitoring API endpoints."""
    
    def test_get_device_health_success(self, client):
        """Test getting health status for a specific device."""
        mock_health = DeviceHealth(
            address="AA:BB:CC:DD:EE:FF",
            is_connected=True,
            rssi=-45,
            battery_level=85.5,
            last_seen=datetime.utcnow(),
            connection_attempts=0,
            last_error=None
        )
        
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.get_health_status = Mock(return_value=mock_health)
            
            response = client.get("/v1/admin/devices/health/AA:BB:CC:DD:EE:FF")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["address"] == "AA:BB:CC:DD:EE:FF"
            assert data["is_connected"] is True
            assert data["rssi"] == -45
            assert data["battery_level"] == 85.5
            assert data["connection_attempts"] == 0
            assert data["last_error"] is None
    
    def test_get_device_health_not_found(self, client):
        """Test getting health status for non-existent device."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.get_health_status = Mock(return_value=None)
            
            response = client.get("/v1/admin/devices/health/AA:BB:CC:DD:EE:FF")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
    
    def test_get_all_device_health(self, client):
        """Test getting health status for all devices."""
        mock_health_dict = {
            "AA:BB:CC:DD:EE:FF": DeviceHealth(
                address="AA:BB:CC:DD:EE:FF",
                is_connected=True,
                rssi=-45,
                battery_level=85.5,
                last_seen=datetime.utcnow(),
                connection_attempts=0,
                last_error=None
            ),
            "11:22:33:44:55:66": DeviceHealth(
                address="11:22:33:44:55:66",
                is_connected=False,
                rssi=None,
                battery_level=None,
                last_seen=datetime.utcnow(),
                connection_attempts=3,
                last_error="Connection timeout"
            )
        }
        
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.get_all_health_status = Mock(return_value=mock_health_dict)
            
            response = client.get("/v1/admin/devices/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2
            
            # Find devices by address
            device1 = next(d for d in data if d["address"] == "AA:BB:CC:DD:EE:FF")
            device2 = next(d for d in data if d["address"] == "11:22:33:44:55:66")
            
            assert device1["is_connected"] is True
            assert device1["battery_level"] == 85.5
            
            assert device2["is_connected"] is False
            assert device2["last_error"] == "Connection timeout"
    
    def test_control_health_monitoring_start(self, client):
        """Test starting health monitoring."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.start_health_monitoring = AsyncMock()
            
            response = client.post(
                "/v1/admin/devices/monitoring",
                json={
                    "enabled": True,
                    "interval": 30.0
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["enabled"] is True
            assert data["interval"] == 30.0
            assert "monitoring started" in data["message"]
    
    def test_control_health_monitoring_stop(self, client):
        """Test stopping health monitoring."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.stop_health_monitoring = AsyncMock()
            
            response = client.post(
                "/v1/admin/devices/monitoring",
                json={"enabled": False}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["enabled"] is False
            assert data["interval"] is None
            assert "monitoring stopped" in data["message"]
    
    def test_control_health_monitoring_invalid_interval(self, client):
        """Test health monitoring with invalid interval."""
        response = client.post(
            "/v1/admin/devices/monitoring",
            json={
                "enabled": True,
                "interval": 1.0  # Too short
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestDeviceRemovalAPI:
    """Test device removal API endpoints."""
    
    def test_remove_device_success(self, client):
        """Test successful device removal."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.unassign_device = AsyncMock(return_value=True)
            
            response = client.delete("/v1/admin/devices/AA:BB:CC:DD:EE:FF")
            
            assert response.status_code == 200
            data = response.json()
            assert "removed successfully" in data["message"]
    
    def test_remove_device_not_found(self, client):
        """Test removing non-existent device."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.unassign_device = AsyncMock(return_value=False)
            
            response = client.delete("/v1/admin/devices/AA:BB:CC:DD:EE:FF")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
    
    def test_remove_device_exception(self, client):
        """Test device removal with exception."""
        with patch('src.impact_bridge.api.devices.device_manager') as mock_manager:
            mock_manager.unassign_device = AsyncMock(side_effect=Exception("Database error"))
            
            response = client.delete("/v1/admin/devices/AA:BB:CC:DD:EE:FF")
            
            assert response.status_code == 500
            data = response.json()
            assert "Database error" in data["detail"]


if __name__ == "__main__":
    # Simple test runner for development
    from fastapi.testclient import TestClient
    from src.impact_bridge.api.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    # Test basic endpoint access
    response = client.get("/v1/admin/devices/list")
    assert response.status_code == 200
    print("✓ Device list endpoint accessible")
    
    # Test validation
    response = client.post(
        "/v1/admin/devices/discover",
        json={"duration": 0.5}  # Invalid duration
    )
    assert response.status_code == 422
    print("✓ Request validation working")
    
    print("Basic API tests completed successfully!")