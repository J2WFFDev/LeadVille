"""Enhanced bridge with BT50 integration, MQTT, and database persistence."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from .ble.witmotion_bt50 import Bt50Client, Bt50Sample, Bt50Calibration
from .enhanced_impact_detection import EnhancedImpactDetector, ImpactEvent
from .mqtt_client import SensorEventPublisher
from .database import SensorDatabase

logger = logging.getLogger(__name__)


class EnhancedSensorBridge:
    """Enhanced sensor bridge with complete BT50 integration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # BT50 sensor configuration
        self.bt50_config = config.get("bt50", {})
        self.mqtt_config = config.get("mqtt", {})
        self.database_config = config.get("database", {})
        
        # Core components
        self.bt50_client: Optional[Bt50Client] = None
        self.impact_detector: Optional[EnhancedImpactDetector] = None
        self.mqtt_publisher: Optional[SensorEventPublisher] = None
        self.database: Optional[SensorDatabase] = None
        
        # State tracking
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._impact_events: List[ImpactEvent] = []
        
        # Statistics
        self._stats = {
            "start_time": None,
            "total_samples": 0,
            "total_impacts": 0,
            "calibration_completions": 0,
        }
        
        self._init_components()
    
    def _init_components(self) -> None:
        """Initialize all bridge components."""
        
        # Initialize BT50 client
        if self.bt50_config:
            self.bt50_client = Bt50Client(
                sensor_id=self.bt50_config.get("sensor_id", "BT50_01"),
                mac_address=self.bt50_config.get("mac_address", "F8:FE:92:31:12:E3"),
                notify_uuid=self.bt50_config.get("notify_uuid", "0000ffe4-0000-1000-8000-00805f9a34fb"),
                auto_calibrate=self.bt50_config.get("auto_calibrate", True),
                calibration_samples=self.bt50_config.get("calibration_samples", 100),
                simulation_mode=self.bt50_config.get("simulation_mode", False),
                idle_reconnect_sec=self.bt50_config.get("idle_reconnect_sec", 300.0),
                keepalive_batt_sec=self.bt50_config.get("keepalive_batt_sec", 30.0),
            )
            
            # Set up callbacks
            self.bt50_client.set_sample_callback(self._on_sensor_sample)
            self.bt50_client.set_connect_callback(self._on_sensor_connect)
            self.bt50_client.set_disconnect_callback(self._on_sensor_disconnect)
            self.bt50_client.set_calibration_callback(self._on_calibration_complete)
        
        # Initialize impact detector
        enhanced_config = self.config.get("enhanced_impact", {})
        if enhanced_config.get("enabled", True):
            self.impact_detector = EnhancedImpactDetector(
                threshold=enhanced_config.get("peak_threshold", 10.0),
                onset_threshold=enhanced_config.get("onset_threshold", 3.0),
                lookback_samples=enhanced_config.get("lookback_samples", 10),
            )
        
        # Initialize MQTT publisher
        if self.mqtt_config.get("enabled", False):
            self.mqtt_publisher = SensorEventPublisher(
                broker_host=self.mqtt_config.get("broker_host", "localhost"),
                broker_port=self.mqtt_config.get("broker_port", 1883),
                username=self.mqtt_config.get("username"),
                password=self.mqtt_config.get("password"),
                base_topic=self.mqtt_config.get("base_topic", "leadville/sensors"),
                qos=self.mqtt_config.get("qos", 1),
                retain=self.mqtt_config.get("retain", False),
                enabled=self.mqtt_config.get("enabled", False),
            )
        
        # Initialize database
        if self.database_config.get("enabled", False):
            self.database = SensorDatabase(
                db_path=self.database_config.get("db_path", "leadville_sensors.db"),
                batch_size=self.database_config.get("batch_size", 100),
                flush_interval=self.database_config.get("flush_interval", 5.0),
                enabled=self.database_config.get("enabled", False),
            )
        
        logger.info("Enhanced sensor bridge components initialized")
    
    async def start(self) -> None:
        """Start the enhanced sensor bridge."""
        if self._running:
            logger.warning("Bridge already running")
            return
        
        self._running = True
        self._stats["start_time"] = time.monotonic()
        
        logger.info("Starting enhanced sensor bridge")
        
        # Start MQTT publisher
        if self.mqtt_publisher:
            await self.mqtt_publisher.start()
            logger.info("MQTT publisher started")
        
        # Start database
        if self.database:
            await self.database.start()
            logger.info("Database persistence started")
        
        # Start BT50 sensor
        if self.bt50_client:
            await self.bt50_client.start()
            logger.info("BT50 sensor client started")
        
        # Start monitoring task
        self._tasks.append(asyncio.create_task(self._monitoring_loop()))
        
        # Publish system start event
        await self._publish_system_event("bridge_started", {
            "bt50_enabled": self.bt50_client is not None,
            "mqtt_enabled": self.mqtt_publisher is not None,
            "database_enabled": self.database is not None,
            "impact_detection_enabled": self.impact_detector is not None,
        })
        
        logger.info("Enhanced sensor bridge started successfully")
    
    async def stop(self) -> None:
        """Stop the enhanced sensor bridge."""
        if not self._running:
            return
        
        self._running = False
        
        logger.info("Stopping enhanced sensor bridge")
        
        # Cancel monitoring tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._tasks.clear()
        
        # Stop components
        if self.bt50_client:
            await self.bt50_client.stop()
            logger.info("BT50 sensor client stopped")
        
        if self.database:
            await self.database.stop()
            logger.info("Database persistence stopped")
        
        if self.mqtt_publisher:
            await self.mqtt_publisher.stop()
            logger.info("MQTT publisher stopped")
        
        # Publish system stop event
        await self._publish_system_event("bridge_stopped", {
            "uptime_seconds": time.monotonic() - self._stats["start_time"] if self._stats["start_time"] else 0,
            "total_samples": self._stats["total_samples"],
            "total_impacts": self._stats["total_impacts"],
        })
        
        logger.info("Enhanced sensor bridge stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive bridge status."""
        status = {
            "bridge": {
                "running": self._running,
                "uptime_seconds": time.monotonic() - self._stats["start_time"] if self._stats["start_time"] else 0,
                "total_samples": self._stats["total_samples"],
                "total_impacts": self._stats["total_impacts"],
                "calibration_completions": self._stats["calibration_completions"],
            }
        }
        
        if self.bt50_client:
            status["bt50"] = self.bt50_client.get_status()
        
        if self.mqtt_publisher:
            status["mqtt"] = {
                "enabled": self.mqtt_publisher.enabled,
                "connected": self.mqtt_publisher._connected,
            }
        
        if self.database:
            status["database"] = {
                "enabled": self.database.enabled,
                "queue_size": self.database._write_queue.qsize() if hasattr(self.database._write_queue, 'qsize') else 0,
            }
        
        return status
    
    async def _on_sensor_sample(self, sample: Bt50Sample) -> None:
        """Handle incoming sensor sample."""
        self._stats["total_samples"] += 1
        
        # Process with impact detector
        if self.impact_detector and self.bt50_client and self.bt50_client.is_calibrated():
            # Create sample point for impact detection
            from .enhanced_impact_detection import SamplePoint
            from datetime import datetime, timedelta
            
            sample_point = SamplePoint(
                timestamp=datetime.now(),
                raw_values=[int(sample.vx * 1000), int(sample.vy * 1000), int(sample.vz * 1000)],
                corrected_values=[sample.vx, sample.vy, sample.vz],
                magnitude=sample.amplitude
            )
            
            # Check for impact
            impact_event = self.impact_detector.process_sample(sample_point)
            if impact_event:
                await self._on_impact_detected(impact_event)
        
        # Store sample in database
        if self.database:
            await self.database.store_sensor_sample(
                self.bt50_config.get("sensor_id", "BT50_01"),
                sample.to_dict()
            )
        
        # Publish sample via MQTT (only occasionally to avoid spam)
        if self.mqtt_publisher and self._stats["total_samples"] % 100 == 0:
            await self.mqtt_publisher.publish_sensor_sample(
                self.bt50_config.get("sensor_id", "BT50_01"),
                sample.to_dict()
            )
    
    async def _on_sensor_connect(self) -> None:
        """Handle sensor connection."""
        logger.info("BT50 sensor connected")
        
        await self._publish_sensor_event("connection", {"status": "connected"})
    
    async def _on_sensor_disconnect(self) -> None:
        """Handle sensor disconnection."""
        logger.warning("BT50 sensor disconnected")
        
        await self._publish_sensor_event("connection", {"status": "disconnected"})
    
    async def _on_calibration_complete(self, calibration: Bt50Calibration) -> None:
        """Handle calibration completion."""
        self._stats["calibration_completions"] += 1
        
        logger.info("BT50 sensor calibration completed")
        
        calibration_data = {
            "baseline_vx": calibration.baseline_vx,
            "baseline_vy": calibration.baseline_vy,
            "baseline_vz": calibration.baseline_vz,
            "samples_collected": calibration.samples_collected,
            "timestamp": datetime.now().isoformat(),
        }
        
        await self._publish_sensor_event("calibration_complete", calibration_data)
    
    async def _on_impact_detected(self, impact_event: ImpactEvent) -> None:
        """Handle impact detection."""
        self._stats["total_impacts"] += 1
        self._impact_events.append(impact_event)
        
        logger.info(f"Impact detected: magnitude={impact_event.peak_magnitude:.2f}, confidence={impact_event.confidence:.2f}")
        
        impact_data = {
            "onset_timestamp": impact_event.onset_timestamp.isoformat(),
            "peak_timestamp": impact_event.peak_timestamp.isoformat(),
            "onset_magnitude": impact_event.onset_magnitude,
            "peak_magnitude": impact_event.peak_magnitude,
            "duration_ms": impact_event.duration_ms,
            "confidence": impact_event.confidence,
            "sample_count": impact_event.sample_count,
        }
        
        # Store in database
        if self.database:
            await self.database.store_impact_detection(
                self.bt50_config.get("sensor_id", "BT50_01"),
                impact_data
            )
        
        # Publish via MQTT
        if self.mqtt_publisher:
            await self.mqtt_publisher.publish_impact_detection(
                self.bt50_config.get("sensor_id", "BT50_01"),
                impact_data
            )
    
    async def _publish_sensor_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish sensor event to MQTT and database."""
        sensor_id = self.bt50_config.get("sensor_id", "BT50_01")
        
        if self.mqtt_publisher:
            await self.mqtt_publisher.publish_sensor_event(sensor_id, event_type, event_data)
        
        if self.database:
            await self.database.store_sensor_event(sensor_id, event_type, event_data)
    
    async def _publish_system_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish system event."""
        if self.database:
            await self.database.store_system_event(event_type, event_data)
        
        if self.mqtt_publisher:
            await self.mqtt_publisher.publish_system_status(event_data)
    
    async def _monitoring_loop(self) -> None:
        """Periodic monitoring and status updates."""
        while self._running:
            try:
                await asyncio.sleep(30.0)  # Update every 30 seconds
                
                if self.bt50_client:
                    # Update sensor status in database
                    if self.database:
                        status = self.bt50_client.get_status()
                        health = self.bt50_client.get_health_status()
                        
                        combined_status = {**status, **health}
                        await self.database.update_sensor_status(
                            self.bt50_config.get("sensor_id", "BT50_01"),
                            combined_status
                        )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5.0)


async def create_enhanced_bridge(config_path: str = "config/dev_config.json") -> EnhancedSensorBridge:
    """Factory function to create enhanced bridge from configuration."""
    import json
    from pathlib import Path
    
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    else:
        logger.warning(f"Config file not found: {config_path}, using defaults")
        config = {}
    
    return EnhancedSensorBridge(config)