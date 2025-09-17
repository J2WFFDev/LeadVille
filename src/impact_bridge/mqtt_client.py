"""
MQTT Message Bus for LeadVille Impact Bridge

Provides real-time pub/sub communication between system components.
Based on GitHub issue #33 implementation.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage

logger = logging.getLogger(__name__)


@dataclass 
class MQTTConfig:
    """MQTT broker configuration"""
    host: str = "localhost"
    port: int = 1883
    keepalive: int = 60
    client_id: str = "leadville-bridge"
    username: Optional[str] = None
    password: Optional[str] = None
    qos: int = 1  # At least once delivery


class LeadVilleMQTT:
    """
    MQTT client wrapper for LeadVille Impact Bridge
    
    Topic Structure:
    - bridge/status - System status updates
    - sensor/{id}/telemetry - Sensor data streams  
    - timer/events - Timer event notifications
    - run/{id}/events - Run-specific events
    """
    
    # Topic definitions
    TOPICS = {
        'bridge_status': 'bridge/status',
        'sensor_telemetry': 'sensor/{sensor_id}/telemetry',
        'timer_events': 'timer/events', 
        'run_events': 'run/{run_id}/events',
        'system_health': 'system/health',
        'device_status': 'device/{device_id}/status'
    }
    
    def __init__(self, config: MQTTConfig = None):
        self.config = config or MQTTConfig()
        self.client = mqtt.Client(client_id=self.config.client_id)
        self.connected = False
        self.message_handlers: Dict[str, List[Callable]] = {}
        
        # Set up MQTT client callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        
        # Configure authentication if provided
        if self.config.username and self.config.password:
            self.client.username_pw_set(self.config.username, self.config.password)
    
    async def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker at {self.config.host}:{self.config.port}")
            self.client.connect(self.config.host, self.config.port, self.config.keepalive)
            self.client.loop_start()
            
            # Wait for connection
            retry_count = 0
            while not self.connected and retry_count < 10:
                await asyncio.sleep(0.1)
                retry_count += 1
            
            if self.connected:
                logger.info("✓ Connected to MQTT broker")
                return True
            else:
                logger.error("✗ Failed to connect to MQTT broker")
                return False
                
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT client connected successfully")
        else:
            self.connected = False
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        if rc != 0:
            logger.warning("MQTT client disconnected unexpectedly")
        else:
            logger.info("MQTT client disconnected")
    
    def _on_message(self, client, userdata, msg: MQTTMessage):
        """Callback for incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Try to parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
            
            logger.debug(f"MQTT message received: {topic} -> {data}")
            
            # Call registered handlers
            if topic in self.message_handlers:
                for handler in self.message_handlers[topic]:
                    try:
                        handler(topic, data)
                    except Exception as e:
                        logger.error(f"Error in MQTT message handler: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for successful message publish"""
        logger.debug(f"MQTT message published: {mid}")
    
    def subscribe(self, topic: str, handler: Callable[[str, Any], None] = None) -> bool:
        """
        Subscribe to MQTT topic
        
        Args:
            topic: Topic to subscribe to
            handler: Optional message handler function
        """
        try:
            result = self.client.subscribe(topic, qos=self.config.qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✓ Subscribed to MQTT topic: {topic}")
                
                # Register handler if provided
                if handler:
                    if topic not in self.message_handlers:
                        self.message_handlers[topic] = []
                    self.message_handlers[topic].append(handler)
                
                return True
            else:
                logger.error(f"✗ Failed to subscribe to topic: {topic}")
                return False
                
        except Exception as e:
            logger.error(f"MQTT subscribe error: {e}")
            return False
    
    def publish(self, topic: str, payload: Any, retain: bool = False) -> bool:
        """
        Publish message to MQTT topic
        
        Args:
            topic: Topic to publish to
            payload: Message payload (will be JSON encoded if dict)
            retain: Whether to retain the message
        """
        try:
            if not self.connected:
                logger.warning("Cannot publish - MQTT not connected")
                return False
            
            # JSON encode if dict/object
            if isinstance(payload, (dict, list)):
                message = json.dumps(payload)
            else:
                message = str(payload)
            
            result = self.client.publish(topic, message, qos=self.config.qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"MQTT published: {topic} -> {message[:100]}...")
                return True
            else:
                logger.error(f"MQTT publish failed: {topic}")
                return False
                
        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return False
    
    # Convenience methods for LeadVille-specific topics
    
    def publish_bridge_status(self, status: Dict[str, Any]) -> bool:
        """Publish bridge status update"""
        status.update({
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'bridge'
        })
        return self.publish(self.TOPICS['bridge_status'], status, retain=True)
    
    def publish_sensor_telemetry(self, sensor_id: str, data: Dict[str, Any]) -> bool:
        """Publish sensor telemetry data"""
        topic = self.TOPICS['sensor_telemetry'].format(sensor_id=sensor_id)
        data.update({
            'timestamp': datetime.utcnow().isoformat(),
            'sensor_id': sensor_id
        })
        return self.publish(topic, data)
    
    def publish_timer_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Publish timer event"""
        event_data = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'timer',
            **data
        }
        return self.publish(self.TOPICS['timer_events'], event_data)
    
    def publish_run_event(self, run_id: int, event_type: str, data: Dict[str, Any]) -> bool:
        """Publish run-specific event"""
        topic = self.TOPICS['run_events'].format(run_id=run_id)
        event_data = {
            'run_id': run_id,
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            **data
        }
        return self.publish(topic, event_data)
    
    def publish_device_status(self, device_id: str, status: Dict[str, Any]) -> bool:
        """Publish device status update"""
        topic = self.TOPICS['device_status'].format(device_id=device_id)
        status.update({
            'device_id': device_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        return self.publish(topic, status, retain=True)
    
    def subscribe_all_sensors(self, handler: Callable[[str, Any], None]) -> bool:
        """Subscribe to all sensor telemetry"""
        return self.subscribe('sensor/+/telemetry', handler)
    
    def subscribe_all_runs(self, handler: Callable[[str, Any], None]) -> bool:
        """Subscribe to all run events"""
        return self.subscribe('run/+/events', handler)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get MQTT client health status"""
        return {
            'connected': self.connected,
            'broker_host': self.config.host,
            'broker_port': self.config.port,
            'client_id': self.config.client_id,
            'subscriptions': len(self.message_handlers)
        }


# Global MQTT client instance
_mqtt_client: Optional[LeadVilleMQTT] = None


def get_mqtt_client(config: MQTTConfig = None) -> LeadVilleMQTT:
    """Get global MQTT client instance"""
    global _mqtt_client
    if _mqtt_client is None:
        _mqtt_client = LeadVilleMQTT(config)
    return _mqtt_client


async def init_mqtt(config: MQTTConfig = None) -> LeadVilleMQTT:
    """Initialize and connect MQTT client"""
    client = get_mqtt_client(config)
    await client.connect()
    return client