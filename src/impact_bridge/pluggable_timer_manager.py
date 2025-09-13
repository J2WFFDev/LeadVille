"""Pluggable timer manager that works with any timer driver."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .timer_drivers import registry, TimerDriverInterface
from .mqtt_publisher import TimerEventMQTTPublisher, AMGEventMQTTIntegration
from .timer_persistence import TimerPersistenceManager
from .timer_health import TimerHealthMonitor, TimerHealthIntegration
from .time_sync import TimeSynchronizer, TimeSyncIntegration
from .websocket_integration import TimerWebSocketServer, TimerWebSocketIntegration

logger = logging.getLogger(__name__)


class PluggableTimerManager:
    """Pluggable timer manager that supports multiple timer vendors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timer_config = config.get("timer", {})
        
        # Determine which timer vendor to use
        self.vendor = self.timer_config.get("vendor", "amg_labs")
        
        # Get vendor-specific config
        self.vendor_config = self.timer_config.get(self.vendor, {})
        
        # Core timer driver
        self.timer_driver: Optional[TimerDriverInterface] = None
        
        # Feature components (same as original AMG manager for compatibility)
        self.mqtt_publisher = TimerEventMQTTPublisher(**config.get("mqtt", {}))
        self.mqtt_integration = AMGEventMQTTIntegration(self.mqtt_publisher)
        
        self.persistence_manager = TimerPersistenceManager(
            db_path=Path(config.get("database", {}).get("db_path", "timer_events.db")),
            json_backup_path=Path(config.get("database", {}).get("json_backup_path", "logs/timer_events_backup.jsonl"))
        )
        
        # Timer health monitoring (adapt based on vendor)
        device_id = self.vendor_config.get("device_id", "UNKNOWN")
        self.health_monitor = TimerHealthMonitor(
            device_id=device_id,
            **self.timer_config.get("health_monitoring", {})
        )
        self.health_integration = TimerHealthIntegration(self.health_monitor)
        
        self.time_synchronizer = TimeSynchronizer(
            **self.timer_config.get("time_synchronization", {})
        )
        self.time_sync_integration = TimeSyncIntegration(self.time_synchronizer)
        
        self.websocket_server = TimerWebSocketServer(**config.get("websocket", {}))
        self.websocket_integration = TimerWebSocketIntegration(self.websocket_server)
        
        # State
        self._running = False
    
    async def start(self) -> None:
        """Start the pluggable timer manager."""
        if self._running:
            logger.warning("Timer manager already running")
            return
        
        try:
            # Create timer driver instance
            self.timer_driver = registry.create_driver(self.vendor, self.vendor_config)
            
            # Setup callbacks
            self._setup_driver_callbacks()
            
            # Start supporting services
            await self._start_services()
            
            # Start the timer driver
            await self.timer_driver.start()
            
            self._running = True
            logger.info(f"🚀 Pluggable timer manager started with {self.vendor} driver")
            
        except Exception as e:
            logger.error(f"Failed to start timer manager: {e}")
            await self._cleanup()
            raise
    
    async def stop(self) -> None:
        """Stop the pluggable timer manager."""
        if not self._running:
            return
        
        try:
            # Stop timer driver
            if self.timer_driver:
                await self.timer_driver.stop()
            
            # Stop supporting services
            await self._stop_services()
            
            self._running = False
            logger.info("🔌 Pluggable timer manager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping timer manager: {e}")
        finally:
            await self._cleanup()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive manager status."""
        base_status = {
            'manager_running': self._running,
            'vendor': self.vendor,
            'available_drivers': registry.get_available_drivers()
        }
        
        if self.timer_driver:
            # Get driver status asynchronously - for now return sync info
            base_status['driver_status'] = {
                'vendor_name': self.timer_driver.vendor_name,
                'device_type': self.timer_driver.device_type,
                'running': self.timer_driver.is_running,
                'supported_features': self.timer_driver.supported_features
            }
        
        return base_status
    
    async def get_driver_status(self) -> Dict[str, Any]:
        """Get detailed driver status asynchronously."""
        if not self.timer_driver:
            return {'error': 'No timer driver loaded'}
        
        return await self.timer_driver.get_status()
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        if not self.timer_driver:
            return {'error': 'No timer driver loaded'}
        
        return await self.timer_driver.get_device_info()
    
    async def switch_vendor(self, new_vendor: str, new_config: Optional[Dict[str, Any]] = None) -> None:
        """Switch to a different timer vendor.
        
        Args:
            new_vendor: Vendor ID to switch to
            new_config: Optional new configuration for the vendor
        """
        if not registry.is_driver_available(new_vendor):
            available = list(registry.get_available_drivers().keys())
            raise ValueError(f"Vendor '{new_vendor}' not available. Available: {available}")
        
        # Stop current driver
        if self.timer_driver and self._running:
            await self.timer_driver.stop()
        
        # Update vendor and config
        self.vendor = new_vendor
        if new_config:
            self.vendor_config = new_config
        else:
            self.vendor_config = self.timer_config.get(new_vendor, {})
        
        # Create new driver
        self.timer_driver = registry.create_driver(self.vendor, self.vendor_config)
        self._setup_driver_callbacks()
        
        # Start new driver if manager was running
        if self._running:
            await self.timer_driver.start()
        
        logger.info(f"🔄 Switched to {new_vendor} timer driver")
    
    def _setup_driver_callbacks(self) -> None:
        """Setup callbacks for the timer driver."""
        if not self.timer_driver:
            return
        
        self.timer_driver.set_callback('on_timer_event', self._on_timer_event)
        self.timer_driver.set_callback('on_shot_detected', self._on_shot_detected)
        self.timer_driver.set_callback('on_t0_signal', self._on_t0_signal)
        self.timer_driver.set_callback('on_connect', self._on_connect)
        self.timer_driver.set_callback('on_disconnect', self._on_disconnect)
        self.timer_driver.set_callback('on_health_update', self._on_health_update)
    
    async def _start_services(self) -> None:
        """Start supporting services."""
        await self.mqtt_publisher.start()
        await self.health_monitor.start_monitoring()
        await self.time_synchronizer.start_sync_monitoring()
        await self.websocket_server.start()
        
        logger.info("📡 Supporting services started")
    
    async def _stop_services(self) -> None:
        """Stop supporting services."""
        await self.mqtt_publisher.stop()
        await self.health_monitor.stop_monitoring()
        await self.time_synchronizer.stop_sync_monitoring()
        await self.websocket_server.stop()
        
        logger.info("📡 Supporting services stopped")
    
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        self.timer_driver = None
        self._running = False
    
    # Event handlers - same interface as AMGTimerManager for compatibility
    async def _on_timer_event(self, parsed_data: Dict[str, Any]) -> None:
        """Handle timer events from any driver."""
        try:
            # Process through integrations
            await self.mqtt_integration.handle_amg_event(parsed_data)
            await self.persistence_manager.save_timer_event(parsed_data)
            await self.websocket_integration.handle_timer_event(parsed_data)
            
            # Update session statistics
            await self._update_session_stats(parsed_data)
            
        except Exception as e:
            logger.error(f"Error processing timer event: {e}")
    
    async def _on_shot_detected(self, shot_data: Dict[str, Any]) -> None:
        """Handle shot detection from any driver."""
        try:
            logger.info(f"🎯 Shot detected: {shot_data}")
            # Additional shot-specific processing could go here
            
        except Exception as e:
            logger.error(f"Error processing shot detection: {e}")
    
    async def _on_t0_signal(self, timestamp_ns: int) -> None:
        """Handle T0 timing signals from any driver."""
        try:
            logger.debug(f"⏰ T0 signal: {timestamp_ns}")
            # Could integrate with timing calibration here
            
        except Exception as e:
            logger.error(f"Error processing T0 event: {e}")
    
    async def _on_connect(self) -> None:
        """Handle connection events."""
        try:
            logger.info(f"🔗 Timer connected: {self.vendor}")
            await self.websocket_integration.handle_connection_event("connected")
            
        except Exception as e:
            logger.error(f"Error processing connect event: {e}")
    
    async def _on_disconnect(self) -> None:
        """Handle disconnection events."""
        try:
            logger.warning(f"🔌 Timer disconnected: {self.vendor}")
            await self.websocket_integration.handle_connection_event("disconnected")
            
        except Exception as e:
            logger.error(f"Error processing disconnect event: {e}")
    
    async def _on_health_update(self, health_status) -> None:
        """Handle health status updates."""
        try:
            await self.websocket_integration.handle_health_update(health_status)
            
            if hasattr(health_status, 'connection_status') and health_status.connection_status.value == "error":
                logger.warning(f"Timer health issue: {health_status.connection_status.value}")
                
        except Exception as e:
            logger.error(f"Error processing health update: {e}")
    
    async def _update_session_stats(self, parsed_data: Dict[str, Any]) -> None:
        """Update session statistics."""
        # Placeholder for session statistics tracking
        pass
    
    # Compatibility methods for existing integrations
    async def force_time_sync(self):
        """Force immediate time synchronization."""
        await self.time_synchronizer.force_sync()
    
    async def get_recent_events(self, limit: int = 50):
        """Get recent timer events."""
        return await self.persistence_manager.get_recent_events(limit)
    
    async def get_session_events(self):
        """Get events from current session."""
        return await self.persistence_manager.get_session_events()