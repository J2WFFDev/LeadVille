"""MQTT client for publishing sensor events and data."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import time

try:
    from asyncio_mqtt import Client as MqttClient
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    MqttClient = None

logger = logging.getLogger(__name__)


class SensorEventPublisher:
    """MQTT publisher for sensor events and data."""
    
    def __init__(
        self, 
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_topic: str = "leadville/sensors",
        qos: int = 1,
        retain: bool = False,
        enabled: bool = True,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.base_topic = base_topic
        self.qos = qos
        self.retain = retain
        self.enabled = enabled and MQTT_AVAILABLE
        
        self._client: Optional[MqttClient] = None
        self._connected = False
        self._publish_task: Optional[asyncio.Task] = None
        self._message_queue = asyncio.Queue()
        
        if not MQTT_AVAILABLE and enabled:
            logger.warning("MQTT requested but asyncio-mqtt not available. Install with: pip install asyncio-mqtt")
            self.enabled = False
    
    async def start(self) -> None:
        """Start MQTT client and publisher task."""
        if not self.enabled:
            logger.info("MQTT publisher disabled")
            return
            
        logger.info(f"Starting MQTT publisher: {self.broker_host}:{self.broker_port}")
        
        self._publish_task = asyncio.create_task(self._publish_loop())
    
    async def stop(self) -> None:
        """Stop MQTT client."""
        if self._publish_task:
            self._publish_task.cancel()
            try:
                await self._publish_task
            except asyncio.CancelledError:
                pass
        
        if self._client:
            await self._disconnect()
    
    async def publish_sensor_sample(self, sensor_id: str, sample: Dict[str, Any]) -> None:
        """Publish a sensor sample."""
        if not self.enabled:
            return
            
        topic = f"{self.base_topic}/{sensor_id}/samples"
        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "sensor_id": sensor_id,
            "type": "sample",
            "data": sample
        }
        
        await self._queue_message(topic, message)
    
    async def publish_sensor_event(self, sensor_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish a sensor event (calibration, connection, impact, etc.)."""
        if not self.enabled:
            return
            
        topic = f"{self.base_topic}/{sensor_id}/events"
        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "sensor_id": sensor_id,
            "type": event_type,
            "data": event_data
        }
        
        await self._queue_message(topic, message)
    
    async def publish_impact_detection(self, sensor_id: str, impact_data: Dict[str, Any]) -> None:
        """Publish impact detection event."""
        if not self.enabled:
            return
            
        topic = f"{self.base_topic}/{sensor_id}/impacts"
        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "sensor_id": sensor_id,
            "type": "impact_detected",
            "data": impact_data
        }
        
        await self._queue_message(topic, message)
    
    async def publish_system_status(self, status_data: Dict[str, Any]) -> None:
        """Publish system status."""
        if not self.enabled:
            return
            
        topic = f"{self.base_topic}/system/status"
        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "system_status",
            "data": status_data
        }
        
        await self._queue_message(topic, message)
    
    async def _queue_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Queue a message for publishing."""
        try:
            await self._message_queue.put((topic, json.dumps(message)))
        except Exception as e:
            logger.error(f"Failed to queue MQTT message: {e}")
    
    async def _publish_loop(self) -> None:
        """Main publishing loop with connection management."""
        while True:
            try:
                await self._connect()
                
                if self._connected:
                    # Process queued messages
                    while self._connected:
                        try:
                            # Wait for message with timeout
                            topic, payload = await asyncio.wait_for(
                                self._message_queue.get(),
                                timeout=30.0
                            )
                            await self._publish_message(topic, payload)
                            
                        except asyncio.TimeoutError:
                            # Send keepalive/heartbeat
                            await self._publish_heartbeat()
                            
            except Exception as e:
                logger.error(f"MQTT publish loop error: {e}")
                await self._disconnect()
                
                # Wait before retry
                await asyncio.sleep(5.0)
    
    async def _connect(self) -> None:
        """Connect to MQTT broker."""
        if self._connected:
            return
            
        try:
            self._client = MqttClient(
                hostname=self.broker_host,
                port=self.broker_port,
                username=self.username,
                password=self.password,
            )
            
            await self._client.__aenter__()
            self._connected = True
            
            logger.info(f"MQTT connected to {self.broker_host}:{self.broker_port}")
            
            # Publish connection event
            await self._publish_message(
                f"{self.base_topic}/bridge/events",
                json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "mqtt_connected",
                    "data": {"broker": f"{self.broker_host}:{self.broker_port}"}
                })
            )
            
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            self._connected = False
            if self._client:
                try:
                    await self._client.__aexit__(None, None, None)
                except:
                    pass
                self._client = None
    
    async def _disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if not self._connected:
            return
            
        self._connected = False
        
        if self._client:
            try:
                # Publish disconnection event
                await self._publish_message(
                    f"{self.base_topic}/bridge/events",
                    json.dumps({
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": "mqtt_disconnected",
                        "data": {}
                    })
                )
                
                await self._client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"MQTT disconnect error: {e}")
            finally:
                self._client = None
        
        logger.info("MQTT disconnected")
    
    async def _publish_message(self, topic: str, payload: str) -> None:
        """Publish message to MQTT broker."""
        if not self._connected or not self._client:
            return
            
        try:
            await self._client.publish(
                topic, 
                payload,
                qos=self.qos,
                retain=self.retain
            )
            logger.debug(f"MQTT published to {topic}: {len(payload)} bytes")
            
        except Exception as e:
            logger.error(f"MQTT publish failed: {e}")
            self._connected = False
    
    async def _publish_heartbeat(self) -> None:
        """Publish heartbeat message."""
        heartbeat = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "heartbeat",
            "data": {
                "uptime": time.monotonic(),
                "queue_size": self._message_queue.qsize()
            }
        }
        
        await self._publish_message(
            f"{self.base_topic}/bridge/heartbeat",
            json.dumps(heartbeat)
        )