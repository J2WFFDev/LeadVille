"""
Real-time event streaming integration for LeadVille Bridge
Connects WebSocket clients with MQTT message bus for real-time event distribution
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

class EventStreamer:
    """Manages real-time event streaming to WebSocket clients"""
    
    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        self.subscription_channels: Dict[str, Set[WebSocket]] = {
            'status': set(),
            'sensor_events': set(),
            'timer_events': set(),
            'run_updates': set(),
            'health_status': set(),
            'system_monitoring': set(),
        }
        self.mqtt_client = None
        
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """Add a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[websocket] = {
            'connected_at': datetime.now(),
            'client_info': client_info or {},
            'subscriptions': set(),
            'last_ping': time.time()
        }
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message with available channels
        await self.send_to_client(websocket, {
            'type': 'connection_established',
            'timestamp': datetime.now().isoformat(),
            'available_channels': list(self.subscription_channels.keys()),
            'client_id': id(websocket)
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            # Remove from all subscription channels
            for channel_connections in self.subscription_channels.values():
                channel_connections.discard(websocket)
            
            del self.active_connections[websocket]
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe_client(self, websocket: WebSocket, channels: List[str]):
        """Subscribe a client to specific channels"""
        if websocket not in self.active_connections:
            return
        
        client_info = self.active_connections[websocket]
        
        for channel in channels:
            if channel in self.subscription_channels:
                self.subscription_channels[channel].add(websocket)
                client_info['subscriptions'].add(channel)
        
        await self.send_to_client(websocket, {
            'type': 'subscription_confirmed',
            'timestamp': datetime.now().isoformat(),
            'channels': channels,
            'subscriptions': list(client_info['subscriptions'])
        })
    
    async def unsubscribe_client(self, websocket: WebSocket, channels: List[str]):
        """Unsubscribe a client from specific channels"""
        if websocket not in self.active_connections:
            return
        
        client_info = self.active_connections[websocket]
        
        for channel in channels:
            if channel in self.subscription_channels:
                self.subscription_channels[channel].discard(websocket)
                client_info['subscriptions'].discard(channel)
    
    async def broadcast_event(self, channel: str, event_data: Dict[str, Any]):
        """Broadcast an event to all subscribers of a channel"""
        if channel not in self.subscription_channels:
            logger.warning(f"Unknown channel: {channel}")
            return
        
        subscribers = self.subscription_channels[channel].copy()
        if not subscribers:
            return
        
        # Add metadata
        event_data.update({
            'channel': channel,
            'timestamp': event_data.get('timestamp', datetime.now().isoformat()),
            'event_id': f"{channel}_{int(time.time() * 1000000)}"
        })
        
        # Send to all subscribers
        disconnected_clients = []
        for websocket in subscribers:
            try:
                await self.send_to_client(websocket, event_data)
            except Exception as e:
                logger.error(f"Failed to send event to client: {e}")
                disconnected_clients.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected_clients:
            self.disconnect(websocket)
    
    async def send_to_client(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send data to a specific WebSocket client"""
        try:
            await websocket.send_text(json.dumps(data, default=str))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket client: {e}")
            raise
    
    async def handle_client_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming message from WebSocket client"""
        message_type = message.get('type')
        
        if message_type == 'subscribe':
            channels = message.get('channels', [])
            await self.subscribe_client(websocket, channels)
            
        elif message_type == 'unsubscribe':
            channels = message.get('channels', [])
            await self.unsubscribe_client(websocket, channels)
            
        elif message_type == 'ping':
            await self.send_to_client(websocket, {
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            })
            
        elif message_type == 'get_status':
            await self.send_status_update(websocket)
            
        else:
            logger.warning(f"Unknown message type from client: {message_type}")
    
    async def send_status_update(self, websocket: WebSocket = None):
        """Send current system status"""
        try:
            from src.impact_bridge.system_monitor import SystemMonitor
            monitor = SystemMonitor()
            
            status_data = {
                'type': 'status',
                'timestamp': datetime.now().isoformat(),
                'system': monitor.get_system_stats(),
                'services': monitor.get_service_health(),
                'ble': monitor.get_ble_quality(),
                'connections': {
                    'websocket_clients': len(self.active_connections),
                    'mqtt_connected': self.mqtt_client.is_connected if self.mqtt_client else False
                }
            }
            
            if websocket:
                await self.send_to_client(websocket, status_data)
            else:
                await self.broadcast_event('status', status_data)
                
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
    
    async def send_sensor_event(self, sensor_id: str, event_type: str, data: Dict[str, Any]):
        """Send sensor event to subscribers"""
        event_data = {
            'type': 'sensor_event',
            'sensor_id': sensor_id,
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        await self.broadcast_event('sensor_events', event_data)
    
    async def send_timer_event(self, event_type: str, data: Dict[str, Any]):
        """Send timer event to subscribers"""
        event_data = {
            'type': 'timer_event',
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        await self.broadcast_event('timer_events', event_data)
    
    async def send_run_update(self, run_id: int, event_type: str, data: Dict[str, Any]):
        """Send run update to subscribers"""
        event_data = {
            'type': 'run_update',
            'run_id': run_id,
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        await self.broadcast_event('run_updates', event_data)
    
    async def send_health_status(self, device_id: str, status_data: Dict[str, Any]):
        """Send health status update"""
        event_data = {
            'type': 'health_status',
            'device_id': device_id,
            'timestamp': datetime.now().isoformat(),
            'data': status_data
        }
        await self.broadcast_event('health_status', event_data)
    
    def setup_mqtt_integration(self, mqtt_client):
        """Setup MQTT integration for event streaming"""
        self.mqtt_client = mqtt_client
        
        # Subscribe to relevant MQTT topics and forward to WebSocket clients
        async def handle_mqtt_message(topic: str, payload: Any):
            try:
                if topic.startswith('sensor/'):
                    sensor_id = topic.split('/')[1]
                    await self.send_sensor_event(sensor_id, 'telemetry', payload)
                    
                elif topic == 'timer/events':
                    await self.send_timer_event(payload.get('event_type', 'unknown'), payload)
                    
                elif topic.startswith('run/'):
                    run_id = int(topic.split('/')[1])
                    await self.send_run_update(run_id, payload.get('event_type', 'update'), payload)
                    
                elif topic == 'bridge/status':
                    await self.broadcast_event('status', payload)
                    
            except Exception as e:
                logger.error(f"Error handling MQTT message {topic}: {e}")
        
        # Subscribe to MQTT topics
        if mqtt_client:
            mqtt_client.subscribe('sensor/+/telemetry', handle_mqtt_message)
            mqtt_client.subscribe('timer/events', handle_mqtt_message)
            mqtt_client.subscribe('run/+/events', handle_mqtt_message)
            mqtt_client.subscribe('bridge/status', handle_mqtt_message)
    
    async def start_periodic_tasks(self):
        """Start periodic tasks like status updates and client cleanup"""
        asyncio.create_task(self._periodic_status_updates())
        asyncio.create_task(self._cleanup_stale_connections())
    
    async def _periodic_status_updates(self):
        """Send periodic status updates to subscribers"""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                if self.subscription_channels['status']:
                    await self.send_status_update()
            except Exception as e:
                logger.error(f"Error in periodic status update: {e}")
    
    async def _cleanup_stale_connections(self):
        """Clean up stale WebSocket connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                current_time = time.time()
                stale_connections = []
                
                for websocket, info in self.active_connections.items():
                    # Check if connection is stale (no ping for 5 minutes)
                    if current_time - info['last_ping'] > 300:
                        stale_connections.append(websocket)
                
                for websocket in stale_connections:
                    logger.info("Cleaning up stale WebSocket connection")
                    self.disconnect(websocket)
                    
            except Exception as e:
                logger.error(f"Error in connection cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        return {
            'total_connections': len(self.active_connections),
            'channel_subscriptions': {
                channel: len(connections) 
                for channel, connections in self.subscription_channels.items()
            },
            'mqtt_connected': self.mqtt_client.is_connected if self.mqtt_client else False
        }

# Global event streamer instance
event_streamer = EventStreamer()