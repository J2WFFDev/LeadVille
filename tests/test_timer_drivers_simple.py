"""Simple tests for pluggable timer driver architecture (without dependencies)."""

import pytest
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.impact_bridge.timer_drivers.base import TimerDriverInterface, TimerDriverRegistry
from src.impact_bridge.timer_drivers.amg_driver import AMGTimerDriver
from src.impact_bridge.timer_drivers.specialpie_driver import SpecialPieTimerDriver


class TestTimerDriverRegistry:
    """Test timer driver registry functionality."""
    
    def test_registry_creation(self):
        """Test creating a new registry."""
        registry = TimerDriverRegistry()
        assert len(registry.get_available_drivers()) == 0
    
    def test_register_and_create_driver(self):
        """Test registering and creating drivers."""
        registry = TimerDriverRegistry()
        registry.register_driver("amg_labs", AMGTimerDriver)
        
        config = {"device_id": "60:09:C3:1F:DC:1A"}
        driver = registry.create_driver("amg_labs", config)
        
        assert isinstance(driver, AMGTimerDriver)
        assert driver.vendor_name == "AMG Labs"
    
    def test_available_drivers_info(self):
        """Test getting driver information."""
        registry = TimerDriverRegistry()
        registry.register_driver("amg_labs", AMGTimerDriver)
        registry.register_driver("specialpie", SpecialPieTimerDriver)
        
        available = registry.get_available_drivers()
        
        assert "amg_labs" in available
        assert "specialpie" in available
        assert available["amg_labs"]["vendor_name"] == "AMG Labs"
        assert available["specialpie"]["vendor_name"] == "SpecialPie"
    
    def test_invalid_driver_raises_error(self):
        """Test that requesting invalid driver raises error."""
        registry = TimerDriverRegistry()
        
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
        assert "bluetooth_le" in driver.supported_features
    
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
        assert status["connected"] is False
    
    @pytest.mark.asyncio
    async def test_amg_driver_device_info(self):
        """Test AMG driver device info."""
        config = {
            "device_id": "60:09:C3:1F:DC:1A",
            "uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
            "frame_validation": True
        }
        driver = AMGTimerDriver(config)
        
        info = await driver.get_device_info()
        
        assert info["vendor"] == "AMG Labs"
        assert info["device_id"] == "60:09:C3:1F:DC:1A"
        assert info["uuid"] == "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
        assert info["frame_validation"] is True
    
    def test_amg_driver_callback_setup(self):
        """Test callback setup functionality."""
        config = {"device_id": "60:09:C3:1F:DC:1A"}
        driver = AMGTimerDriver(config)
        
        callback_called = False
        def test_callback(data):
            nonlocal callback_called
            callback_called = True
        
        driver.set_callback("on_timer_event", test_callback)
        assert driver._callbacks["on_timer_event"] == test_callback


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
        assert "custom_protocols" in driver.supported_features
    
    @pytest.mark.asyncio
    async def test_specialpie_driver_status(self):
        """Test SpecialPie driver status reporting."""
        config = {
            "device_id": "SP:00:00:00:00:00",
            "protocol_version": "2.0"
        }
        driver = SpecialPieTimerDriver(config)
        
        status = await driver.get_status()
        
        assert status["vendor"] == "SpecialPie"
        assert status["device_type"] == "Pro Timer"
        assert status["implementation_status"] == "placeholder"
        assert status["device_id"] == "SP:00:00:00:00:00"
        assert status["protocol_version"] == "2.0"
    
    @pytest.mark.asyncio
    async def test_specialpie_start_stop(self):
        """Test SpecialPie driver start/stop functionality."""
        config = {"device_id": "SP:00:00:00:00:00"}
        driver = SpecialPieTimerDriver(config)
        
        # Test initial state
        assert not driver.is_running
        
        # Test start
        await driver.start()
        assert driver.is_running
        
        # Test stop
        await driver.stop()
        assert not driver.is_running
    
    @pytest.mark.asyncio
    async def test_specialpie_device_info(self):
        """Test SpecialPie device information."""
        config = {"device_id": "SP:12:34:56:78:90"}
        driver = SpecialPieTimerDriver(config)
        
        info = await driver.get_device_info()
        
        assert info["vendor"] == "SpecialPie"
        assert info["device_id"] == "SP:12:34:56:78:90"
        assert info["firmware_version"] == "1.0.0-placeholder"
        assert "implementation_notes" in info


class TestTimerDriverInterface:
    """Test abstract timer driver interface."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TimerDriverInterface({})
    
    def test_callback_notification_sync(self):
        """Test callback notification with synchronous callback."""
        # Create a concrete implementation for testing
        class TestDriver(TimerDriverInterface):
            @property
            def vendor_name(self) -> str:
                return "Test"
            
            @property 
            def device_type(self) -> str:
                return "Test Device"
            
            @property
            def supported_features(self):
                return ["test"]
            
            async def start(self):
                pass
            
            async def stop(self):
                pass
            
            async def get_status(self):
                return {}
            
            async def get_device_info(self):
                return {}
        
        driver = TestDriver({})
        
        callback_data = []
        def test_callback(data):
            callback_data.append(data)
        
        driver.set_callback("on_timer_event", test_callback)
        
        # Test notification
        asyncio.run(driver._notify_callback("on_timer_event", "test_data"))
        
        assert len(callback_data) == 1
        assert callback_data[0] == "test_data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])