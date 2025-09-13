"""
AMG Timer Manager
Integrated manager that combines all AMG timer features:
- BLE connectivity and event processing  
- MQTT publishing
- Database persistence
- Health monitoring
- Time synchronization
- WebSocket real-time updates
- Simulation mode support
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .ble.amg import AmgClient
from .timer_simulator import AMGTimerSimulator, SimulationConfig, SimulationMode
from .mqtt_publisher import TimerEventMQTTPublisher, AMGEventMQTTIntegration
from .timer_persistence import TimerPersistenceManager
from .timer_health import TimerHealthMonitor, TimerHealthIntegration
from .time_sync import TimeSynchronizer, TimeSyncIntegration
from .websocket_integration import TimerWebSocketServer, TimerWebSocketIntegration

logger = logging.getLogger(__name__)


class AMGTimerManager:
    """Comprehensive AMG timer manager with all features"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.amg_config = config.get("amg_timer", {})
        
        # Core components
        self.amg_client: Optional[AmgClient] = None
        self.simulator: Optional[AMGTimerSimulator] = None
        
        # Feature components
        self.mqtt_publisher = TimerEventMQTTPublisher(**config.get("mqtt", {}))
        self.mqtt_integration = AMGEventMQTTIntegration(self.mqtt_publisher)
        
        self.persistence_manager = TimerPersistenceManager(
            db_path=Path(config.get("database", {}).get("db_path", "timer_events.db")),
            json_backup_path=Path(config.get("database", {}).get("json_backup_path", "logs/timer_events_backup.jsonl"))
        )
        
        self.health_monitor = TimerHealthMonitor(
            device_id=self.amg_config.get("device_id", "60:09:C3:1F:DC:1A"),
            **self.amg_config.get("health_monitoring", {})
        )
        self.health_integration = TimerHealthIntegration(self.health_monitor)
        
        self.time_synchronizer = TimeSynchronizer(
            **self.amg_config.get("time_synchronization", {})
        )
        self.time_sync_integration = TimeSyncIntegration(self.time_synchronizer)
        
        self.websocket_server = TimerWebSocketServer(**config.get("websocket", {}))
        self.websocket_integration = TimerWebSocketIntegration(self.websocket_server)
        
        # State
        self._running = False
        self._simulation_mode = self.amg_config.get("simulation_mode", False)
        
    async def start(self):
        """Start AMG timer manager with all components"""
        if self._running:
            logger.warning("AMG timer manager already running")
            return
            
        logger.info("🚀 Starting AMG Timer Manager")
        self._running = True
        
        try:
            # Start supporting services
            await self._start_services()
            
            # Start timer (real or simulated)
            if self._simulation_mode:
                await self._start_simulator()
            else:
                await self._start_real_timer()
                
            logger.info("✅ AMG Timer Manager started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start AMG Timer Manager: {e}")
            await self.stop()
            raise
            
    async def stop(self):
        """Stop AMG timer manager and all components"""
        if not self._running:
            return
            
        logger.info("🛑 Stopping AMG Timer Manager")
        self._running = False
        
        # Stop timer components
        if self.amg_client:
            await self.amg_client.stop()
            
        if self.simulator:
            await self.simulator.stop()
            
        # Stop services
        await self._stop_services()
        
        logger.info("✅ AMG Timer Manager stopped")
        
    async def _start_services(self):
        """Start supporting services"""
        # Start MQTT publisher
        await self.mqtt_publisher.start()
        
        # Start health monitoring
        await self.health_monitor.start_monitoring()
        
        # Start time synchronization
        await self.time_synchronizer.start_sync_monitoring()
        
        # Start WebSocket server
        await self.websocket_server.start()
        
        # Setup health monitoring callbacks
        self.health_monitor.set_health_callback(self._on_health_update)
        
        # Setup time sync callbacks
        self.time_synchronizer.set_sync_callback(self._on_sync_update)
        self.time_synchronizer.set_drift_alert_callback(self._on_drift_alert)
        
        logger.info("📡 Supporting services started")
        
    async def _stop_services(self):
        """Stop supporting services"""
        await self.mqtt_publisher.stop()
        await self.health_monitor.stop_monitoring()
        await self.time_synchronizer.stop_sync_monitoring()
        await self.websocket_server.stop()
        
        logger.info("📡 Supporting services stopped")
        
    async def _start_real_timer(self):
        """Start real AMG timer"""
        device_id = self.amg_config.get("device_id", "60:09:C3:1F:DC:1A")
        uuid = self.amg_config.get("uuid", "6e400003-b5a3-f393-e0a9-e50e24dcca9e")
        
        self.amg_client = AmgClient(
            mac_address=device_id,
            start_uuid=uuid
        )
        
        # Setup callbacks
        self.amg_client.set_parsed_data_callback(self._on_amg_event)
        self.amg_client.set_t0_callback(self._on_t0_event)
        
        # Setup health monitoring integration
        self.health_integration.setup_amg_client_callbacks(self.amg_client)
        
        # Start AMG client
        await self.amg_client.start()
        
        logger.info(f"📻 Real AMG timer started: {device_id}")
        
    async def _start_simulator(self):
        """Start AMG timer simulator"""
        sim_config_data = self.config.get("simulation", {})
        sim_config = SimulationConfig(
            mode=SimulationMode(sim_config_data.get("mode", "multi_shot")),
            num_shots=sim_config_data.get("num_shots", 5),
            shot_interval_sec=sim_config_data.get("shot_interval_sec", 2.0),
            start_delay_sec=sim_config_data.get("start_delay_sec", 3.0),
            random_timing=sim_config_data.get("random_timing", False),
            timing_variance_sec=sim_config_data.get("timing_variance_sec", 0.5),
            custom_sequence=sim_config_data.get("custom_sequence")
        )
        
        self.simulator = AMGTimerSimulator(config=sim_config)
        
        # Setup callbacks
        self.simulator.set_parsed_data_callback(self._on_amg_event)
        self.simulator.set_t0_callback(self._on_t0_event)
        
        # Start simulator
        await self.simulator.start()
        
        logger.info(f"🎭 AMG timer simulator started: {sim_config.mode.value}")
        
    async def _on_amg_event(self, parsed_data: Dict[str, Any]):
        """Handle AMG timer events"""
        try:
            # Log the event
            event_detail = parsed_data.get("event_detail", "Unknown event")
            shot_state = parsed_data.get("shot_state", "")
            logger.info(f"⏱️  AMG Event: {event_detail}")
            
            # Process through all integrations
            await self.mqtt_integration.handle_amg_event(parsed_data)
            await self.persistence_manager.store_timer_event(parsed_data)
            await self.time_sync_integration.handle_amg_timer_event(parsed_data)
            await self.websocket_integration.handle_amg_event(parsed_data)
            
            # Update session stats
            await self._update_session_stats(parsed_data)
            
        except Exception as e:
            logger.error(f"Error processing AMG event: {e}")
            
    async def _on_t0_event(self, timestamp_ns: int):
        """Handle T0 timing events"""
        try:
            logger.debug(f"⏰ T0 signal: {timestamp_ns}")
            
            # Could integrate with timing calibration here
            # self.timing_calibrator.add_shot_event(...)
            
        except Exception as e:
            logger.error(f"Error processing T0 event: {e}")
            
    async def _on_health_update(self, health_status):
        """Handle health status updates"""
        try:
            # Broadcast via WebSocket
            await self.websocket_integration.handle_health_update(health_status)
            
            # Log significant changes
            if health_status.connection_status.value == "error":
                logger.warning(f"Timer health issue: {health_status.connection_status.value}")
                
        except Exception as e:
            logger.error(f"Error processing health update: {e}")
            
    async def _on_sync_update(self, sync_status):
        """Handle time sync updates"""
        try:
            logger.debug(f"Time sync update: drift={sync_status.clock_drift_ms:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error processing sync update: {e}")
            
    async def _on_drift_alert(self, drift_ms: float):
        """Handle drift alerts"""
        try:
            logger.warning(f"⚠️ Clock drift alert: {drift_ms:.2f}ms")
            
            # Could trigger automatic correction here
            
        except Exception as e:
            logger.error(f"Error processing drift alert: {e}")
            
    async def _update_session_stats(self, parsed_data: Dict[str, Any]):
        """Update session statistics"""
        try:
            shot_state = parsed_data.get("shot_state", "")
            
            if shot_state == "ACTIVE" and parsed_data.get("current_shot", 0) > 0:
                # Shot detected
                session_data = {
                    "total_shots": parsed_data.get("current_shot", 0),
                    "last_shot_time": parsed_data.get("current_time", 0.0),
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.websocket_integration.handle_session_update(session_data)
                
        except Exception as e:
            logger.error(f"Error updating session stats: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive manager status"""
        return {
            "running": self._running,
            "simulation_mode": self._simulation_mode,
            "amg_connected": (
                self.amg_client.is_connected if self.amg_client 
                else self.simulator.is_connected if self.simulator 
                else False
            ),
            "mqtt_connected": self.mqtt_publisher.is_connected(),
            "websocket_clients": self.websocket_server.get_client_count(),
            "database_enabled": self.config.get("database", {}).get("enabled", False),
            "health_monitoring": self.health_monitor.get_health_summary(),
            "time_sync": self.time_synchronizer.get_sync_summary()
        }
        
    async def force_time_sync(self):
        """Force immediate time synchronization"""
        await self.time_synchronizer.force_sync_check()
        
    async def get_recent_events(self, limit: int = 50):
        """Get recent timer events"""
        return await self.persistence_manager.get_recent_events(limit)
        
    async def get_session_events(self):
        """Get events from current session"""
        return await self.persistence_manager.get_current_session_events()


# Example usage and testing
async def test_amg_timer_manager():
    """Test AMG timer manager"""
    
    # Test configuration
    config = {
        "amg_timer": {
            "device_id": "60:09:C3:1F:DC:1A",
            "uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e", 
            "simulation_mode": True,
            "health_monitoring": {"enabled": True},
            "time_synchronization": {"enabled": True}
        },
        "mqtt": {"enabled": False},
        "websocket": {"enabled": True, "host": "localhost", "port": 8765},
        "database": {"enabled": True},
        "simulation": {
            "mode": "multi_shot",
            "num_shots": 3,
            "shot_interval_sec": 2.0,
            "start_delay_sec": 1.0
        }
    }
    
    # Create and start manager
    manager = AMGTimerManager(config)
    
    try:
        await manager.start()
        
        # Let it run for a while
        await asyncio.sleep(15)
        
        # Print status
        status = manager.get_status()
        print("📊 Manager Status:")
        import json
        print(json.dumps(status, indent=2, default=str))
        
        # Get recent events
        events = await manager.get_recent_events(5)
        print(f"📋 Recent Events ({len(events)}):")
        for event in events:
            print(f"  - {event.event_type}: {event.event_detail}")
            
    finally:
        await manager.stop()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    asyncio.run(test_amg_timer_manager())