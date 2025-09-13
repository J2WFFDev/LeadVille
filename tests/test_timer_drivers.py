"""Tests for pluggable timer driver architecture."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.impact_bridge.timer_drivers import registry, TimerDriverInterface
from src.impact_bridge.timer_drivers.amg_driver import AMGTimerDriver
from src.impact_bridge.timer_drivers.specialpie_driver import SpecialPieTimerDriver
from src.impact_bridge.pluggable_timer_manager import PluggableTimerManager


class TestTimerDriverRegistry:
    """Test timer driver registry functionality."""
    
    def test_registry_has_default_drivers(self):
        """Test that registry has default drivers registered."""
        available = registry.get_available_drivers()
        
        assert "amg_labs" in available
        assert "specialpie" in available
        assert available["amg_labs"]["vendor_name"] == "AMG Labs"
        assert available["specialpie"]["vendor_name"] == "SpecialPie"
    
    def test_create_amg_driver(self):
        """Test creating AMG timer driver."""
        config = {
            "device_id": "60:09:C3:1F:DC:1A",
            "uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
        }
        
        driver = registry.create_driver("amg_labs", config)
        
        assert isinstance(driver, AMGTimerDriver)
        assert driver.vendor_name == "AMG Labs"
        assert driver.device_type == "Commander"
        assert "bluetooth_le" in driver.supported_features
    
    def test_create_specialpie_driver(self):
        """Test creating SpecialPie timer driver."""
        config = {
            "device_id": "SP:00:00:00:00:00",
            "protocol_version": "1.0"
        }
        
        driver = registry.create_driver("specialpie", config)
        
        assert isinstance(driver, SpecialPieTimerDriver)
        assert driver.vendor_name == "SpecialPie"
        assert driver.device_type == "Pro Timer"
        assert "custom_protocols" in driver.supported_features
    
    def test_invalid_driver_raises_error(self):
        """Test that requesting invalid driver raises error."""
        with pytest.raises(KeyError):
            registry.create_driver("nonexistent", {})


class TestAMGTimerDriver:
    """Test AMG timer driver implementation."""
    
    def test_amg_driver_properties(self):
        """Test AMG driver basic properties."""
        config = {"device_id": "60:09:C3:1F:DC:1A"}
        driver = AMGTimerDriver(config)
        
        assert driver.vendor_name == "AMG Labs"
        assert driver.device_type == "Commander"
        assert not driver.is_running
        assert "shot_detection" in driver.supported_features
    
    @pytest.mark.asyncio
    async def test_amg_driver_status(self):
        """Test AMG driver status reporting."""
        config = {"device_id": "60:09:C3:1F:DC:1A"}
        driver = AMGTimerDriver(config)
        
        status = await driver.get_status()
        
        assert status["vendor"] == "AMG Labs"
        assert status["device_type"] == "Commander"
        assert status["running"] is False
        assert status["device_id"] == "60:09:C3:1F:DC:1A"
    
    @pytest.mark.asyncio
    async def test_amg_driver_device_info(self):
        """Test AMG driver device info."""
        config = {
            "device_id": "60:09:C3:1F:DC:1A",
            "uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
        }
        driver = AMGTimerDriver(config)
        
        info = await driver.get_device_info()
        
        assert info["vendor"] == "AMG Labs"
        assert info["device_id"] == "60:09:C3:1F:DC:1A"
        assert info["uuid"] == "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


class TestSpecialPieTimerDriver:
    """Test SpecialPie timer driver implementation."""
    
    def test_specialpie_driver_properties(self):
        """Test SpecialPie driver basic properties."""
        config = {"device_id": "SP:00:00:00:00:00"}
        driver = SpecialPieTimerDriver(config)
        
        assert driver.vendor_name == "SpecialPie"
        assert driver.device_type == "Pro Timer"
        assert not driver.is_running
        assert "multi_stage_timing" in driver.supported_features
    
    @pytest.mark.asyncio
    async def test_specialpie_driver_status(self):
        """Test SpecialPie driver status reporting."""
        config = {"device_id": "SP:00:00:00:00:00"}
        driver = SpecialPieTimerDriver(config)
        
        status = await driver.get_status()
        
        assert status["vendor"] == "SpecialPie"
        assert status["device_type"] == "Pro Timer"
        assert status["implementation_status"] == "placeholder"
        assert status["device_id"] == "SP:00:00:00:00:00"
    
    @pytest.mark.asyncio
    async def test_specialpie_start_stop(self):
        """Test SpecialPie driver start/stop functionality."""
        config = {"device_id": "SP:00:00:00:00:00"}
        driver = SpecialPieTimerDriver(config)
        
        # Test start
        await driver.start()
        assert driver.is_running
        
        # Test stop
        await driver.stop()
        assert not driver.is_running


class TestPluggableTimerManager:
    """Test pluggable timer manager."""
    
    def test_manager_initialization(self):
        """Test manager initializes with correct vendor."""
        config = {
            "timer": {
                "vendor": "amg_labs",
                "amg_labs": {"device_id": "60:09:C3:1F:DC:1A"}
            },
            "mqtt": {"enabled": False},
            "websocket": {"enabled": False},
            "database": {"enabled": False}
        }
        
        manager = PluggableTimerManager(config)
        
        assert manager.vendor == "amg_labs"
        assert manager.vendor_config["device_id"] == "60:09:C3:1F:DC:1A"
    
    def test_manager_status(self):
        """Test manager status reporting."""
        config = {
            "timer": {
                "vendor": "specialpie",
                "specialpie": {"device_id": "SP:00:00:00:00:00"}
            },
            "mqtt": {"enabled": False},
            "websocket": {"enabled": False},
            "database": {"enabled": False}
        }
        
        manager = PluggableTimerManager(config)
        status = manager.get_status()
        
        assert status["manager_running"] is False
        assert status["vendor"] == "specialpie"
        assert "amg_labs" in status["available_drivers"]
        assert "specialpie" in status["available_drivers"]
    
    @pytest.mark.asyncio
    async def test_manager_vendor_switching(self):
        """Test manager can switch between vendors.""" 
        config = {
            "timer": {
                "vendor": "amg_labs",
                "amg_labs": {"device_id": "60:09:C3:1F:DC:1A"},
                "specialpie": {"device_id": "SP:00:00:00:00:00"}
            },
            "mqtt": {"enabled": False},
            "websocket": {"enabled": False},
            "database": {"enabled": False}
        }
        
        manager = PluggableTimerManager(config)
        
        # Start with AMG driver
        assert manager.vendor == "amg_labs"
        
        # Switch to SpecialPie
        await manager.switch_vendor("specialpie")
        assert manager.vendor == "specialpie"
        
        # Verify driver was created
        assert isinstance(manager.timer_driver, SpecialPieTimerDriver)


if __name__ == "__main__":
    pytest.main([__file__])