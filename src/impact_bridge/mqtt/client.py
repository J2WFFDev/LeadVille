"""MQTT client wrapper for LeadVille Impact Bridge internal message bus."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union

import aiomqtt
from aiomqtt import Client as AioMqttClient

from .topics import MqttTopics

logger = logging.getLogger(__name__)


class MqttClient:
    """MQTT client wrapper with automatic reconnection and message publishing."""
    
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        keepalive: int = 60,
        retry_interval: float = 5.0,
        max_retry_interval: float = 60.0,
        enabled: bool = True,
    ) -> None:
        """Initialize MQTT client.
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            username: Optional username for authentication
            password: Optional password for authentication
            client_id: Optional client ID (defaults to leadville-bridge-{timestamp})
            keepalive: Keep-alive interval in seconds
            retry_interval: Initial retry interval for reconnection
            max_retry_interval: Maximum retry interval for reconnection
            enabled: Whether MQTT publishing is enabled
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.client_id = client_id or f"leadville-bridge-{int(time.time())}"
        self.keepalive = keepalive
        self.retry_interval = retry_interval
        self.max_retry_interval = max_retry_interval
        self.enabled = enabled
        
        # Internal state
        self._client: Optional[AioMqttClient] = None
        self._connected = False
        self._stop_requested = False
        self._connection_task: Optional[asyncio.Task] = None
        self._current_retry_interval = retry_interval
        
        # Message counters for monitoring
        self._messages_published = 0
        self._messages_failed = 0
        self._last_publish_time: Optional[float] = None
        self._connection_attempts = 0
        self._last_connection_time: Optional[float] = None
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to broker."""
        return self._connected and self._client is not None
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "connected": self.is_connected,
            "enabled": self.enabled,
            "messages_published": self._messages_published,
            "messages_failed": self._messages_failed,
            "connection_attempts": self._connection_attempts,
            "last_publish_time": self._last_publish_time,
            "last_connection_time": self._last_connection_time,
            "broker": f"{self.broker_host}:{self.broker_port}",
            "client_id": self.client_id,
        }
    
    async def start(self) -> None:
        """Start the MQTT client with automatic reconnection."""
        if not self.enabled:
            logger.info("MQTT client disabled, skipping start")
            return
        
        logger.info(f"Starting MQTT client (broker: {self.broker_host}:{self.broker_port})")
        self._stop_requested = False
        self._connection_task = asyncio.create_task(self._connection_loop())
    
    async def stop(self) -> None:
        """Stop the MQTT client."""
        logger.info("Stopping MQTT client")
        self._stop_requested = True
        
        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass
        
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting MQTT client: {e}")
        
        self._connected = False
        self._client = None
    
    async def publish(
        self,
        topic: str,
        payload: Union[str, Dict[str, Any]],
        qos: int = 1,
        retain: bool = False,
    ) -> bool:
        """Publish a message to MQTT broker.
        
        Args:
            topic: MQTT topic to publish to
            payload: Message payload (string or dict to be JSON-encoded)
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether message should be retained by broker
            
        Returns:
            True if message was published successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        if not self.is_connected:
            logger.debug(f"MQTT not connected, dropping message to {topic}")
            self._messages_failed += 1
            return False
        
        try:
            # Convert dict payload to JSON
            if isinstance(payload, dict):
                # Add timestamp if not present
                if "timestamp" not in payload:
                    payload["timestamp"] = datetime.utcnow().isoformat() + "Z"
                payload_str = json.dumps(payload, separators=(",", ":"))
            else:
                payload_str = str(payload)
            
            # Publish message
            await self._client.publish(topic, payload_str, qos=qos, retain=retain)
            
            self._messages_published += 1
            self._last_publish_time = time.time()
            
            logger.debug(f"Published to {topic}: {payload_str[:100]}{'...' if len(payload_str) > 100 else ''}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            self._messages_failed += 1
            return False
    
    async def publish_status(self, component: str, status_data: Dict[str, Any]) -> bool:
        """Publish a status message.
        
        Args:
            component: Component name generating the status
            status_data: Status data dictionary
            
        Returns:
            True if published successfully
        """
        topic = {
            "bridge": MqttTopics.BRIDGE_STATUS,
            "timer": MqttTopics.TIMER_STATUS,
            "system": MqttTopics.SYSTEM_HEALTH,
        }.get(component, f"{MqttTopics.BASE}/{component}/status")
        
        payload = {
            "component": component,
            "status": status_data,
            "client_stats": self.stats,
        }
        
        return await self.publish(topic, payload, retain=True)
    
    async def publish_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        sensor_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> bool:
        """Publish an event message.
        
        Args:
            event_type: Type of event (HIT, T0, SHOT, etc.)
            event_data: Event data dictionary
            sensor_id: Optional sensor ID for sensor-specific events
            run_id: Optional run ID for run-specific events
            
        Returns:
            True if published successfully
        """
        # Determine topic based on event type and context
        if event_type in ("HIT", "IMPACT"):
            topic = MqttTopics.IMPACT_EVENTS
        elif event_type in ("SHOT", "T0"):
            topic = MqttTopics.SHOT_EVENTS
        elif event_type == "TIMER_EVENT":
            topic = MqttTopics.TIMER_EVENTS
        elif sensor_id:
            topic = MqttTopics.sensor_telemetry(sensor_id)
        elif run_id:
            topic = MqttTopics.run_events(run_id)
        else:
            topic = f"{MqttTopics.BASE}/events/{event_type.lower()}"
        
        payload = {
            "event_type": event_type,
            "data": event_data,
        }
        
        if sensor_id:
            payload["sensor_id"] = sensor_id
        if run_id:
            payload["run_id"] = run_id
        
        return await self.publish(topic, payload)
    
    async def publish_telemetry(self, sensor_id: str, telemetry_data: Dict[str, Any]) -> bool:
        """Publish sensor telemetry data.
        
        Args:
            sensor_id: Sensor identifier
            telemetry_data: Telemetry data dictionary
            
        Returns:
            True if published successfully
        """
        topic = MqttTopics.sensor_telemetry(sensor_id)
        
        payload = {
            "sensor_id": sensor_id,
            "telemetry": telemetry_data,
        }
        
        return await self.publish(topic, payload)
    
    async def _connection_loop(self) -> None:
        """Main connection loop with automatic reconnection."""
        while not self._stop_requested:
            try:
                await self._connect_and_maintain()
                
            except asyncio.CancelledError:
                logger.info("MQTT connection loop cancelled")
                break
                
            except Exception as e:
                logger.error(f"MQTT connection error: {e}")
                
            # Wait before retry
            if not self._stop_requested:
                logger.info(f"MQTT reconnecting in {self._current_retry_interval}s")
                await asyncio.sleep(self._current_retry_interval)
                
                # Exponential backoff
                self._current_retry_interval = min(
                    self._current_retry_interval * 1.5,
                    self.max_retry_interval
                )
    
    async def _connect_and_maintain(self) -> None:
        """Connect to broker and maintain connection."""
        self._connection_attempts += 1
        
        # Connect to broker
        async with AioMqttClient(
            hostname=self.broker_host,
            port=self.broker_port,
            identifier=self.client_id,
            keepalive=self.keepalive,
            username=self.username,
            password=self.password,
        ) as client:
            self._client = client
            self._connected = True
            self._current_retry_interval = self.retry_interval  # Reset retry interval
            self._last_connection_time = time.time()
            
            logger.info(f"MQTT connected to {self.broker_host}:{self.broker_port}")
            
            # Publish connection status
            await self.publish_status("mqtt", {"connected": True, "broker": f"{self.broker_host}:{self.broker_port}"})
            
            # Maintain connection until stopped or disconnected
            try:
                while not self._stop_requested:
                    await asyncio.sleep(1.0)
                    
            except aiomqtt.MqttError as e:
                logger.error(f"MQTT connection lost: {e}")
                self._connected = False
                raise
            
            finally:
                self._connected = False
                self._client = None
                logger.info("MQTT disconnected")