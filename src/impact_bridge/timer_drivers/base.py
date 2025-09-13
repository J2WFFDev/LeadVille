"""Abstract timer driver interface and registry system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, Type
import asyncio
import logging

logger = logging.getLogger(__name__)


class TimerDriverInterface(ABC):
    """Abstract interface for timer drivers.
    
    All timer drivers must implement this interface to be compatible
    with the LeadVille impact bridge system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the timer driver with configuration.
        
        Args:
            config: Driver-specific configuration dictionary
        """
        self.config = config
        self._running = False
        self._callbacks = {
            'on_timer_event': None,
            'on_shot_detected': None, 
            'on_t0_signal': None,
            'on_connect': None,
            'on_disconnect': None,
            'on_health_update': None
        }
    
    @property
    @abstractmethod
    def vendor_name(self) -> str:
        """Return the vendor name for this timer driver."""
        pass
    
    @property
    @abstractmethod
    def device_type(self) -> str:
        """Return the device type/model for this timer driver."""
        pass
    
    @property
    @abstractmethod
    def supported_features(self) -> List[str]:
        """Return list of supported features."""
        pass
    
    @property
    def is_running(self) -> bool:
        """Check if the timer driver is currently running."""
        return self._running
    
    @abstractmethod
    async def start(self) -> None:
        """Start the timer driver and establish connection."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the timer driver and close connections."""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current status of the timer driver."""
        pass
    
    @abstractmethod
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        pass
    
    def set_callback(self, event_type: str, callback: Optional[Callable]) -> None:
        """Set callback for specific event type.
        
        Args:
            event_type: Type of event ('on_timer_event', 'on_shot_detected', etc.)
            callback: Callback function to set
        """
        if event_type in self._callbacks:
            self._callbacks[event_type] = callback
        else:
            logger.warning(f"Unknown callback type: {event_type}")
    
    async def _notify_callback(self, event_type: str, *args, **kwargs) -> None:
        """Safely notify a callback if it exists."""
        callback = self._callbacks.get(event_type)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {event_type} callback: {e}")


class TimerDriverRegistry:
    """Registry for discovering and creating timer drivers."""
    
    def __init__(self):
        self._drivers: Dict[str, Type[TimerDriverInterface]] = {}
    
    def register_driver(self, vendor_id: str, driver_class: Type[TimerDriverInterface]) -> None:
        """Register a timer driver class.
        
        Args:
            vendor_id: Unique identifier for the vendor/driver
            driver_class: Timer driver class that implements TimerDriverInterface
        """
        if not issubclass(driver_class, TimerDriverInterface):
            raise ValueError(f"Driver class {driver_class} must implement TimerDriverInterface")
        
        self._drivers[vendor_id] = driver_class
        logger.info(f"Registered timer driver: {vendor_id} -> {driver_class.__name__}")
    
    def get_available_drivers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available drivers.
        
        Returns:
            Dictionary mapping vendor_id to driver info
        """
        drivers_info = {}
        for vendor_id, driver_class in self._drivers.items():
            # Create a temporary instance to get metadata
            temp_instance = driver_class({})
            drivers_info[vendor_id] = {
                'vendor_name': temp_instance.vendor_name,
                'device_type': temp_instance.device_type,
                'supported_features': temp_instance.supported_features,
                'class_name': driver_class.__name__
            }
        return drivers_info
    
    def create_driver(self, vendor_id: str, config: Dict[str, Any]) -> TimerDriverInterface:
        """Create a timer driver instance.
        
        Args:
            vendor_id: Identifier of the driver to create
            config: Configuration for the driver
            
        Returns:
            Timer driver instance
            
        Raises:
            KeyError: If vendor_id is not registered
        """
        if vendor_id not in self._drivers:
            available = list(self._drivers.keys())
            raise KeyError(f"Driver '{vendor_id}' not found. Available drivers: {available}")
        
        driver_class = self._drivers[vendor_id]
        return driver_class(config)
    
    def is_driver_available(self, vendor_id: str) -> bool:
        """Check if a driver is available.
        
        Args:
            vendor_id: Identifier of the driver to check
            
        Returns:
            True if driver is available
        """
        return vendor_id in self._drivers