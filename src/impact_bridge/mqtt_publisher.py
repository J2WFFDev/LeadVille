"""
MQTT Publisher for Timer Events
Publishes AMG timer events to MQTT broker for real-time integration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from asyncio_mqtt import Client as MQTTClient
from asyncio_mqtt.error import MqttError

logger = logging.getLogger(__name__)


class TimerEventMQTTPublisher:
    """MQTT publisher for AMG timer events"""
    
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        topic_prefix: str = "timer/events",
        client_id: str = "leadville-timer",
        username: Optional[str] = None,
        password: Optional[str] = None,
        enabled: bool = True
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic_prefix = topic_prefix
        self.client_id = client_id
        self.username = username
        self.password = password
        self.enabled = enabled
        
        self._client: Optional[MQTTClient] = None
        self._connected = False
        self._publish_task: Optional[asyncio.Task] = None
        self._publish_queue = asyncio.Queue()
        
    async def start(self):
        """Start MQTT publisher"""
        if not self.enabled:
            logger.info("MQTT publisher disabled")
            return
            
        try:
            self._client = MQTTClient(
                hostname=self.broker_host,
                port=self.broker_port,
                client_id=self.client_id,
                username=self.username,
                password=self.password
            )
            
            await self._client.__aenter__()
            self._connected = True
            
            # Start publish worker
            self._publish_task = asyncio.create_task(self._publish_worker())
            
            logger.info(f"MQTT publisher started: {self.broker_host}:{self.broker_port}")
            
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            self._connected = False
    
    async def stop(self):
        """Stop MQTT publisher"""
        if not self.enabled:
            return
            
        if self._publish_task:
            self._publish_task.cancel()
            try:
                await self._publish_task
            except asyncio.CancelledError:
                pass
                
        if self._client and self._connected:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"MQTT disconnect error: {e}")
            finally:
                self._connected = False
                
        logger.info("MQTT publisher stopped")
    
    async def publish_timer_event(self, event_type: str, event_data: Dict[str, Any]):
        """Publish timer event to MQTT"""
        if not self.enabled or not self._connected:
            return
            
        try:
            # Create event message
            message = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "device_id": "60:09:C3:1F:DC:1A",  # AMG MAC address
                "data": event_data
            }
            
            # Queue for async publishing
            await self._publish_queue.put((event_type, message))
            
        except Exception as e:
            logger.error(f"Error queuing MQTT message: {e}")
    
    async def _publish_worker(self):
        """Background worker to publish queued messages"""
        while True:
            try:
                # Wait for message to publish
                event_type, message = await self._publish_queue.get()
                
                if not self._connected or not self._client:
                    continue
                
                # Publish to specific topic
                topic = f"{self.topic_prefix}/{event_type.lower()}"
                payload = json.dumps(message)
                
                await self._client.publish(topic, payload, qos=1)
                logger.debug(f"Published to {topic}: {event_type}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"MQTT publish error: {e}")
                await asyncio.sleep(1.0)  # Brief pause before retry

    def is_connected(self) -> bool:
        """Check if MQTT client is connected"""
        return self._connected


class AMGEventMQTTIntegration:
    """Integration class to connect AMG events with MQTT publishing"""
    
    def __init__(self, mqtt_publisher: TimerEventMQTTPublisher):
        self.mqtt_publisher = mqtt_publisher
        
    async def handle_amg_event(self, parsed_data: Dict[str, Any]):
        """Handle AMG timer event and publish to MQTT"""
        event_type = self._determine_event_type(parsed_data)
        
        if event_type:
            await self.mqtt_publisher.publish_timer_event(event_type, {
                "shot_state": parsed_data.get("shot_state"),
                "current_shot": parsed_data.get("current_shot"),
                "total_shots": parsed_data.get("total_shots"),
                "current_time": parsed_data.get("current_time"),
                "split_time": parsed_data.get("split_time"),
                "event_detail": parsed_data.get("event_detail"),
                "raw_hex": parsed_data.get("raw_hex")
            })
    
    def _determine_event_type(self, parsed_data: Dict[str, Any]) -> Optional[str]:
        """Determine MQTT event type from parsed AMG data"""
        shot_state = parsed_data.get("shot_state", "")
        
        if shot_state == "START":
            return "start"
        elif shot_state == "STOPPED":
            return "stop"  
        elif shot_state == "ACTIVE":
            current_shot = parsed_data.get("current_shot", 0)
            if current_shot > 0:
                return "shot"
            else:
                return "active"
        
        return None