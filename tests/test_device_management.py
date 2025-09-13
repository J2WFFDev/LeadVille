"""Tests for BLE device management functionality."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.impact_bridge.device_manager import DeviceManager, DiscoveredDevice, DeviceHealth
from src.impact_bridge.database.models import Sensor, Target, Stage, Match
from src.impact_bridge.database.engine import get_database_session
from src.impact_bridge.database.crud import SensorCRUD, TargetCRUD, StageCRUD, MatchCRUD


class TestDeviceManager:
    """Test the DeviceManager class."""
    
    @pytest.fixture
    def device_manager(self):
        """Create a DeviceManager instance for testing."""
        return DeviceManager()
    
    def test_device_manager_initialization(self, device_manager):
        """Test DeviceManager initializes correctly."""
        assert device_manager._discovered_devices == {}
        assert device_manager._device_health == {}
        assert device_manager._scanning is False
        assert device_manager._health_monitoring is False
    
    def test_identify_device_type_bt50(self, device_manager):
        """Test device type identification for BT50 sensors."""
        # Mock BLEDevice and advertisement data
        mock_device = Mock()
        mock_device.name = "WitMotion BT50"
        
        mock_advertisement = Mock()
        mock_advertisement.local_name = "WitMotion BT50"
        mock_advertisement.service_uuids = ["0000ffe0-0000-1000-8000-00805f9a34fb"]
        mock_advertisement.manufacturer_data = {0x0183: b"test_data"}
        
        device_type = device_manager._identify_device_type(mock_device, mock_advertisement)
        assert device_type == "bt50"
    
    def test_identify_device_type_amg(self, device_manager):
        """Test device type identification for AMG timers."""
        # Mock BLEDevice and advertisement data
        mock_device = Mock()
        mock_device.name = "AMG Commander"
        
        mock_advertisement = Mock()
        mock_advertisement.local_name = "AMG Commander"
        mock_advertisement.service_uuids = ["6e400001-b5a3-f393-e0a9-e50e24dcca9e"]
        mock_advertisement.manufacturer_data = {}
        
        device_type = device_manager._identify_device_type(mock_device, mock_advertisement)
        assert device_type == "amg"
    
    def test_identify_device_type_unknown(self, device_manager):
        """Test device type identification for unknown devices."""
        # Mock BLEDevice and advertisement data
        mock_device = Mock()
        mock_device.name = "Unknown Device"
        
        mock_advertisement = Mock()
        mock_advertisement.local_name = "Unknown Device"
        mock_advertisement.service_uuids = ["12345678-1234-1234-1234-123456789abc"]
        mock_advertisement.manufacturer_data = {}
        
        device_type = device_manager._identify_device_type(mock_device, mock_advertisement)
        assert device_type == "unknown"
    
    @pytest.mark.asyncio
    async def test_start_discovery_mock(self, device_manager):
        """Test device discovery with mocked BLE scanner."""
        mock_discovered_devices = {
            "AA:BB:CC:DD:EE:FF": DiscoveredDevice(
                address="AA:BB:CC:DD:EE:FF",
                name="Test BT50",
                rssi=-50,
                manufacturer_data={0x0183: b"test"},
                service_uuids=["0000ffe0-0000-1000-8000-00805f9a34fb"],
                local_name="Test BT50",
                advertisement_data={},
                device_type="bt50"
            )
        }
        
        with patch('src.impact_bridge.device_manager.BleakScanner') as mock_scanner:
            # Mock the async context manager
            mock_scanner_instance = AsyncMock()
            mock_scanner.return_value.__aenter__ = AsyncMock(return_value=mock_scanner_instance)
            mock_scanner.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Simulate discovery by setting discovered devices directly
            device_manager._discovered_devices = mock_discovered_devices
            
            discovered = await device_manager.start_discovery(duration=0.1)
            
            assert len(discovered) == 1
            assert discovered[0].address == "AA:BB:CC:DD:EE:FF"
            assert discovered[0].device_type == "bt50"
    
    @pytest.mark.asyncio
    async def test_pair_device_success(self, device_manager):
        """Test successful device pairing."""
        mock_address = "AA:BB:CC:DD:EE:FF"
        
        with patch('src.impact_bridge.device_manager.BleakClient') as mock_client:
            # Mock successful connection
            mock_client_instance = AsyncMock()
            mock_client_instance.is_connected = AsyncMock(return_value=True)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            success = await device_manager.pair_device(mock_address, "bt50")
            
            assert success is True
            assert mock_address in device_manager._device_health
            assert device_manager._device_health[mock_address].is_connected is True
    
    @pytest.mark.asyncio
    async def test_pair_device_failure(self, device_manager):
        """Test failed device pairing."""
        mock_address = "AA:BB:CC:DD:EE:FF"
        
        with patch('src.impact_bridge.device_manager.BleakClient') as mock_client:
            # Mock failed connection
            mock_client_instance = AsyncMock()
            mock_client_instance.is_connected = AsyncMock(return_value=False)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            success = await device_manager.pair_device(mock_address, "bt50")
            
            assert success is False


class TestDeviceDatabase:
    """Test device database operations."""
    
    @pytest.fixture
    def setup_test_data(self):
        """Set up test data in the database."""
        with get_database_session() as session:
            # Create a test match
            match = MatchCRUD.create(
                session=session,
                name="Test Match",
                date=datetime.utcnow(),
                location="Test Location"
            )
            
            # Create a test stage
            stage = StageCRUD.create(
                session=session,
                match_id=match.id,
                name="Test Stage",
                number=1
            )
            
            # Create a test target
            target = TargetCRUD.create(
                session=session,
                stage_id=stage.id,
                name="Test Target"
            )
            
            session.commit()
            return {"match": match, "stage": stage, "target": target}
    
    @pytest.mark.asyncio
    async def test_assign_device_to_target_new_sensor(self, setup_test_data):
        """Test assigning a new device to a target."""
        device_manager = DeviceManager()
        test_data = setup_test_data
        mock_address = "AA:BB:CC:DD:EE:FF"
        
        success = await device_manager.assign_device_to_target(
            mock_address, 
            test_data["target"].id
        )
        
        assert success is True
        
        # Verify sensor was created in database
        with get_database_session() as session:
            sensor = SensorCRUD.get_by_hw_addr(session, mock_address)
            assert sensor is not None
            assert sensor.hw_addr == mock_address
            assert sensor.target_id == test_data["target"].id
            assert sensor.label == f"Sensor-{mock_address[-4:]}"
    
    @pytest.mark.asyncio
    async def test_assign_device_to_target_existing_sensor(self, setup_test_data):
        """Test reassigning an existing device to a different target."""
        device_manager = DeviceManager()
        test_data = setup_test_data
        mock_address = "BB:CC:DD:EE:FF:AA"
        
        # First, create a sensor
        with get_database_session() as session:
            sensor = SensorCRUD.create(
                session=session,
                hw_addr=mock_address,
                label="Original Sensor",
                target_id=None
            )
            session.commit()
            original_sensor_id = sensor.id
        
        # Now assign it to a target
        success = await device_manager.assign_device_to_target(
            mock_address, 
            test_data["target"].id
        )
        
        assert success is True
        
        # Verify sensor was updated
        with get_database_session() as session:
            sensor = SensorCRUD.get_by_hw_addr(session, mock_address)
            assert sensor is not None
            assert sensor.id == original_sensor_id  # Same sensor
            assert sensor.target_id == test_data["target"].id  # Updated target
    
    @pytest.mark.asyncio
    async def test_unassign_device(self, setup_test_data):
        """Test unassigning a device from its target."""
        device_manager = DeviceManager()
        test_data = setup_test_data
        mock_address = "CC:DD:EE:FF:AA:BB"
        
        # First, create and assign a sensor
        with get_database_session() as session:
            sensor = SensorCRUD.create(
                session=session,
                hw_addr=mock_address,
                label="Test Sensor",
                target_id=test_data["target"].id
            )
            session.commit()
        
        # Now unassign it
        success = await device_manager.unassign_device(mock_address)
        
        assert success is True
        
        # Verify sensor was unassigned
        with get_database_session() as session:
            sensor = SensorCRUD.get_by_hw_addr(session, mock_address)
            assert sensor is not None
            assert sensor.target_id is None
    
    @pytest.mark.asyncio
    async def test_unassign_nonexistent_device(self):
        """Test unassigning a device that doesn't exist."""
        device_manager = DeviceManager()
        mock_address = "DD:EE:FF:AA:BB:CC"
        
        success = await device_manager.unassign_device(mock_address)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_device_list_empty(self):
        """Test getting device list when no devices exist."""
        device_manager = DeviceManager()
        
        devices = await device_manager.get_device_list()
        
        assert isinstance(devices, list)
        # May have devices from other tests, so just check it's a list
    
    @pytest.mark.asyncio
    async def test_get_device_list_with_devices(self, setup_test_data):
        """Test getting device list with existing devices."""
        device_manager = DeviceManager()
        test_data = setup_test_data
        mock_address = "EE:FF:AA:BB:CC:DD"
        
        # Create a sensor
        with get_database_session() as session:
            sensor = SensorCRUD.create(
                session=session,
                hw_addr=mock_address,
                label="List Test Sensor",
                target_id=test_data["target"].id,
                battery=85.5,
                rssi=-45
            )
            session.commit()
        
        devices = await device_manager.get_device_list()
        
        # Find our test device in the list
        test_device = None
        for device in devices:
            if device['address'] == mock_address:
                test_device = device
                break
        
        assert test_device is not None
        assert test_device['label'] == "List Test Sensor"
        assert test_device['target_id'] == test_data["target"].id
        assert test_device['battery'] == 85.5
        assert test_device['rssi'] == -45
        assert test_device['is_connected'] is False  # No health data


class TestDeviceHealthMonitoring:
    """Test device health monitoring functionality."""
    
    @pytest.mark.asyncio
    async def test_health_monitoring_start_stop(self):
        """Test starting and stopping health monitoring."""
        device_manager = DeviceManager()
        
        # Start monitoring
        await device_manager.start_health_monitoring(interval=0.1)
        assert device_manager._health_monitoring is True
        assert device_manager._health_task is not None
        
        # Stop monitoring
        await device_manager.stop_health_monitoring()
        assert device_manager._health_monitoring is False
    
    def test_update_device_error(self):
        """Test updating device error status."""
        device_manager = DeviceManager()
        mock_address = "FF:AA:BB:CC:DD:EE"
        error_message = "Connection timeout"
        
        device_manager._update_device_error(mock_address, error_message)
        
        assert mock_address in device_manager._device_health
        health = device_manager._device_health[mock_address]
        assert health.last_error == error_message
        assert health.is_connected is False
        assert health.connection_attempts == 1
    
    def test_get_health_status(self):
        """Test getting health status for a specific device."""
        device_manager = DeviceManager()
        mock_address = "AA:BB:CC:DD:EE:FF"
        
        # Initially no health data
        health = device_manager.get_health_status(mock_address)
        assert health is None
        
        # Add some health data
        device_manager._update_device_error(mock_address, "Test error")
        health = device_manager.get_health_status(mock_address)
        assert health is not None
        assert health.address == mock_address
        assert health.last_error == "Test error"
    
    def test_get_all_health_status(self):
        """Test getting health status for all devices."""
        device_manager = DeviceManager()
        
        # Add health data for multiple devices
        addresses = ["AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02"]
        for addr in addresses:
            device_manager._update_device_error(addr, f"Error for {addr}")
        
        all_health = device_manager.get_all_health_status()
        assert len(all_health) >= 2  # May have health data from other tests
        
        for addr in addresses:
            assert addr in all_health
            assert all_health[addr].address == addr
    
    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test device manager shutdown."""
        device_manager = DeviceManager()
        
        # Start monitoring to have something to shut down
        await device_manager.start_health_monitoring(interval=0.1)
        
        # Add some data
        device_manager._discovered_devices["test"] = Mock()
        device_manager._device_health["test"] = Mock()
        
        # Shutdown
        await device_manager.shutdown()
        
        # Verify cleanup
        assert device_manager._health_monitoring is False
        assert len(device_manager._discovered_devices) == 0
        assert len(device_manager._device_health) == 0


if __name__ == "__main__":
    # Simple test runner for development
    import asyncio
    
    def run_async_test(coro):
        """Helper to run async tests."""
        return asyncio.run(coro)
    
    # Test basic functionality
    manager = DeviceManager()
    assert manager._discovered_devices == {}
    print("✓ DeviceManager initialization test passed")
    
    # Test device type identification
    mock_device = Mock()
    mock_device.name = "WitMotion BT50"
    mock_advertisement = Mock()
    mock_advertisement.local_name = "WitMotion BT50"
    mock_advertisement.service_uuids = ["0000ffe0-0000-1000-8000-00805f9a34fb"]
    mock_advertisement.manufacturer_data = {0x0183: b"test_data"}
    
    device_type = manager._identify_device_type(mock_device, mock_advertisement)
    assert device_type == "bt50"
    print("✓ Device type identification test passed")
    
    print("Basic tests completed successfully!")