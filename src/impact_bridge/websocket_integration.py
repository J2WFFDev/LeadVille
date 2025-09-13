"""
WebSocket Integration for Real-time Timer Events
Provides WebSocket server for real-time AMG timer event updates
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Dict, Any, Set, Optional, Callable
from websockets.server import WebSocketServerProtocol, serve
import signal
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class TimerWebSocketServer:
    """WebSocket server for real-time timer events"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        enabled: bool = True
    ):
        self.host = host
        self.port = port
        self.enabled = enabled
        
        self._server = None
        self._clients: Set[WebSocketServerProtocol] = set()
        self._running = False
        
    async def start(self):
        """Start WebSocket server"""
        if not self.enabled:
            logger.info("WebSocket server disabled")
            return
            
        try:
            # Start WebSocket server
            self._server = await serve(
                self._handle_client,
                self.host,
                self.port
            )
            
            self._running = True
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            
    async def stop(self):
        """Stop WebSocket server"""
        if not self.enabled or not self._server:
            return
            
        self._running = False
        
        # Close all client connections
        if self._clients:
            await asyncio.gather(
                *[client.close() for client in self._clients.copy()],
                return_exceptions=True
            )
            self._clients.clear()
            
        # Stop server
        self._server.close()
        await self._server.wait_closed()
        
        logger.info("WebSocket server stopped")
        
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connection"""
        client_addr = websocket.remote_address
        logger.info(f"WebSocket client connected: {client_addr}")
        
        # Add to client set
        self._clients.add(websocket)
        
        try:
            # Send welcome message
            welcome_msg = {
                "type": "welcome",
                "message": "Connected to LeadVille Timer WebSocket",
                "timestamp": datetime.now().isoformat(),
                "server_info": {
                    "version": "2.0.0",
                    "features": ["timer_events", "health_monitoring", "real_time_updates"]
                }
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    error_msg = {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(error_msg))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
        finally:
            # Remove from client set
            self._clients.discard(websocket)
            
    async def _handle_client_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle message from WebSocket client"""
        message_type = data.get("type")
        
        if message_type == "ping":
            # Respond to ping
            pong_msg = {
                "type": "pong", 
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(pong_msg))
            
        elif message_type == "subscribe":
            # Handle subscription requests
            channels = data.get("channels", [])
            response = {
                "type": "subscription_ack",
                "channels": channels,
                "message": f"Subscribed to {len(channels)} channels",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))
            
        else:
            # Unknown message type
            error_msg = {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(error_msg))
            
    async def broadcast_timer_event(self, event_type: str, event_data: Dict[str, Any]):
        """Broadcast timer event to all connected clients"""
        if not self.enabled or not self._clients:
            return
            
        message = {
            "type": "timer_event",
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "device_id": "60:09:C3:1F:DC:1A",
            "data": event_data
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self._clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")
                disconnected_clients.append(client)
                
        # Remove disconnected clients
        for client in disconnected_clients:
            self._clients.discard(client)
            
        if disconnected_clients:
            logger.debug(f"Removed {len(disconnected_clients)} disconnected WebSocket clients")
            
    async def broadcast_health_status(self, health_data: Dict[str, Any]):
        """Broadcast timer health status to all connected clients"""
        if not self.enabled or not self._clients:
            return
            
        message = {
            "type": "health_status",
            "timestamp": datetime.now().isoformat(),
            "device_id": health_data.get("device_id", "60:09:C3:1F:DC:1A"),
            "data": health_data
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self._clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                logger.error(f"Error sending health status to WebSocket client: {e}")
                disconnected_clients.append(client)
                
        # Remove disconnected clients
        for client in disconnected_clients:
            self._clients.discard(client)
            
    async def broadcast_session_update(self, session_data: Dict[str, Any]):
        """Broadcast session update to all connected clients"""
        if not self.enabled or not self._clients:
            return
            
        message = {
            "type": "session_update",
            "timestamp": datetime.now().isoformat(),
            "data": session_data
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self._clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                logger.error(f"Error sending session update to WebSocket client: {e}")
                disconnected_clients.append(client)
                
        # Remove disconnected clients
        for client in disconnected_clients:
            self._clients.discard(client)
            
    def get_client_count(self) -> int:
        """Get number of connected WebSocket clients"""
        return len(self._clients)
        
    def is_running(self) -> bool:
        """Check if WebSocket server is running"""
        return self._running
        
    async def broadcast_sensor_event(self, sensor_data: Dict[str, Any]):
        """Broadcast sensor event to all connected clients"""
        if not self.enabled or not self._clients:
            return
            
        message = {
            "type": "sensor_event",
            "event_type": sensor_data.get("event_type", "impact_detected"),
            "timestamp": datetime.now().isoformat(),
            "sensor_id": sensor_data.get("sensor_id", "BT50_01"),
            "data": sensor_data
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self._clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                logger.error(f"Error sending sensor event to WebSocket client: {e}")
                disconnected_clients.append(client)
                
        # Remove disconnected clients
        for client in disconnected_clients:
            self._clients.discard(client)

    async def broadcast_status_update(self, status_data: Dict[str, Any]):
        """Broadcast status update to all connected clients"""
        if not self.enabled or not self._clients:
            return
            
        message = {
            "type": "status",
            "event_type": status_data.get("event_type", "system_status"),
            "timestamp": datetime.now().isoformat(),
            "data": status_data
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self._clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                logger.error(f"Error sending status update to WebSocket client: {e}")
                disconnected_clients.append(client)
                
        # Remove disconnected clients
        for client in disconnected_clients:
            self._clients.discard(client)

    async def broadcast_run_update(self, run_data: Dict[str, Any]):
        """Broadcast run update to all connected clients"""
        if not self.enabled or not self._clients:
            return
            
        message = {
            "type": "run_update",
            "event_type": run_data.get("event_type", "run_status_change"),
            "timestamp": datetime.now().isoformat(),
            "run_id": run_data.get("run_id"),
            "data": run_data
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self._clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                logger.error(f"Error sending run update to WebSocket client: {e}")
                disconnected_clients.append(client)
                
        # Remove disconnected clients
        for client in disconnected_clients:
            self._clients.discard(client)


class TimerWebSocketIntegration:
    """Integration class to connect timer events with WebSocket broadcasting"""
    
    def __init__(self, websocket_server: TimerWebSocketServer):
        self.websocket_server = websocket_server
        
    async def handle_amg_event(self, parsed_data: Dict[str, Any]):
        """Handle AMG timer event and broadcast via WebSocket"""
        event_type = self._determine_event_type(parsed_data)
        
        if event_type:
            await self.websocket_server.broadcast_timer_event(event_type, {
                "shot_state": parsed_data.get("shot_state"),
                "current_shot": parsed_data.get("current_shot"),
                "total_shots": parsed_data.get("total_shots"),
                "current_time": parsed_data.get("current_time"),
                "split_time": parsed_data.get("split_time"),
                "event_detail": parsed_data.get("event_detail"),
                "raw_hex": parsed_data.get("raw_hex")
            })
            
    async def handle_health_update(self, health_status):
        """Handle timer health update and broadcast via WebSocket"""
        health_data = health_status.to_dict() if hasattr(health_status, 'to_dict') else health_status
        await self.websocket_server.broadcast_health_status(health_data)
        
    async def handle_session_update(self, session_data: Dict[str, Any]):
        """Handle session update and broadcast via WebSocket"""
        await self.websocket_server.broadcast_session_update(session_data)

    async def handle_sensor_event(self, sensor_data: Dict[str, Any]):
        """Handle sensor event and broadcast via WebSocket"""
        await self.websocket_server.broadcast_sensor_event(sensor_data)

    async def handle_status_update(self, status_data: Dict[str, Any]):
        """Handle status update and broadcast via WebSocket"""
        await self.websocket_server.broadcast_status_update(status_data)

    async def handle_run_update(self, run_data: Dict[str, Any]):
        """Handle run update and broadcast via WebSocket"""
        await self.websocket_server.broadcast_run_update(run_data)
        
    def _determine_event_type(self, parsed_data: Dict[str, Any]) -> Optional[str]:
        """Determine WebSocket event type from parsed AMG data"""
        shot_state = parsed_data.get("shot_state", "")
        
        if shot_state == "START":
            return "timer_start"
        elif shot_state == "STOPPED":
            return "timer_stop"
        elif shot_state == "ACTIVE":
            current_shot = parsed_data.get("current_shot", 0)
            if current_shot > 0:
                return "shot_detected"
            else:
                return "timer_active"
        
        return None


# WebSocket test client for development with reconnection handling
async def test_websocket_client_with_reconnection():
    """Test WebSocket client with automatic reconnection for development"""
    uri = "ws://localhost:8765"
    max_reconnect_attempts = 5
    reconnect_delay = 3.0
    
    async def connect_and_listen():
        """Connect to WebSocket and listen for messages"""
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to {uri}")
                
                # Send ping
                ping_msg = {"type": "ping"}
                await websocket.send(json.dumps(ping_msg))
                
                # Subscribe to all channels
                subscribe_msg = {
                    "type": "subscribe",
                    "channels": ["timer_events", "health_status", "sensor_events", "status", "run_updates"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                # Listen for messages
                async for message in websocket:
                    data = json.loads(message)
                    print(f"📨 {data['type']}: {data}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            raise
        except Exception as e:
            logger.error(f"WebSocket client error: {e}")
            raise
    
    # Reconnection logic
    for attempt in range(max_reconnect_attempts):
        try:
            await connect_and_listen()
            break  # If we reach here, connection was successful
            
        except (websockets.exceptions.ConnectionClosed, 
                websockets.exceptions.InvalidURI,
                ConnectionRefusedError, 
                OSError) as e:
            if attempt < max_reconnect_attempts - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}. Retrying in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay *= 1.5  # Exponential backoff
            else:
                logger.error(f"Failed to connect after {max_reconnect_attempts} attempts")
                raise


# Enhanced WebSocket test client with live monitoring capabilities
async def enhanced_websocket_client():
    """Enhanced WebSocket client for live monitoring with reconnection"""
    uri = "ws://localhost:8765"
    
    class ReconnectingWebSocketClient:
        def __init__(self, uri: str):
            self.uri = uri
            self.websocket = None
            self.running = False
            self.reconnect_delay = 2.0
            self.max_reconnect_delay = 30.0
            
        async def connect(self):
            """Establish WebSocket connection"""
            try:
                self.websocket = await websockets.connect(self.uri)
                logger.info(f"✅ Connected to {self.uri}")
                self.reconnect_delay = 2.0  # Reset delay on successful connection
                return True
            except Exception as e:
                logger.error(f"❌ Connection failed: {e}")
                return False
                
        async def disconnect(self):
            """Close WebSocket connection"""
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
                
        async def send_message(self, message: dict):
            """Send message to WebSocket server"""
            if self.websocket:
                try:
                    await self.websocket.send(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    
        async def listen(self):
            """Listen for WebSocket messages with reconnection"""
            self.running = True
            
            while self.running:
                try:
                    if not self.websocket:
                        if not await self.connect():
                            await asyncio.sleep(self.reconnect_delay)
                            self.reconnect_delay = min(self.reconnect_delay * 1.5, self.max_reconnect_delay)
                            continue
                            
                        # Send initial messages after connection
                        await self.send_message({"type": "ping"})
                        await self.send_message({
                            "type": "subscribe",
                            "channels": ["status", "sensor_event", "timer_event", "run_update"]
                        })
                    
                    # Listen for messages
                    async for message in self.websocket:
                        data = json.loads(message)
                        await self.handle_message(data)
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("🔄 Connection lost, attempting to reconnect...")
                    self.websocket = None
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 1.5, self.max_reconnect_delay)
                    
                except Exception as e:
                    logger.error(f"❌ WebSocket error: {e}")
                    await asyncio.sleep(self.reconnect_delay)
                    
        async def handle_message(self, data: dict):
            """Handle incoming WebSocket message"""
            message_type = data.get("type")
            event_type = data.get("event_type", "")
            timestamp = data.get("timestamp", "")
            
            if message_type == "status":
                print(f"🔵 STATUS [{timestamp}] {event_type}: {data.get('message', '')}")
                
            elif message_type == "sensor_event":
                sensor_id = data.get("sensor_id", "unknown")
                print(f"🟢 SENSOR [{timestamp}] {sensor_id} - {event_type}")
                if "data" in data:
                    magnitude = data["data"].get("magnitude", "N/A")
                    print(f"    📊 Magnitude: {magnitude}")
                    
            elif message_type == "timer_event":
                device_id = data.get("device_id", "unknown")
                print(f"🟡 TIMER [{timestamp}] {device_id} - {event_type}")
                if "data" in data:
                    shot_state = data["data"].get("shot_state", "N/A")
                    current_shot = data["data"].get("current_shot", "N/A")
                    print(f"    🎯 State: {shot_state}, Shot: {current_shot}")
                    
            elif message_type == "run_update":
                run_id = data.get("run_id", "unknown")
                print(f"🟠 RUN [{timestamp}] {run_id} - {event_type}")
                
            else:
                print(f"📨 {message_type}: {json.dumps(data, indent=2)}")
                
        def stop(self):
            """Stop the client"""
            self.running = False
    
    # Create and run client
    client = ReconnectingWebSocketClient(uri)
    
    try:
        await client.listen()
    except KeyboardInterrupt:
        print("\n🛑 Client stopped by user")
    finally:
        client.stop()
        await client.disconnect()


# Example usage and testing
async def test_websocket_server():
    """Test WebSocket server with new event types"""
    server = TimerWebSocketServer()
    
    # Start server
    await server.start()
    
    try:
        # Simulate various events with realistic delays
        await asyncio.sleep(2)
        
        # Status update
        await server.broadcast_status_update({
            "event_type": "system_startup",
            "system_status": "operational",
            "connected_devices": 2,
            "active_sessions": 0
        })
        
        await asyncio.sleep(1)
        
        # Timer start event
        await server.broadcast_timer_event("timer_start", {
            "shot_state": "START",
            "message": "Timer started - waiting for first shot"
        })
        
        await asyncio.sleep(2)
        
        # Sensor event (impact detected)
        await server.broadcast_sensor_event({
            "event_type": "impact_detected",
            "sensor_id": "BT50_01",
            "magnitude": 15.5,
            "timestamp_sensor": datetime.now().isoformat(),
            "location": {"x": 2.3, "y": 1.8}
        })
        
        await asyncio.sleep(1)
        
        # Timer shot detected
        await server.broadcast_timer_event("shot_detected", {
            "shot_state": "ACTIVE",
            "current_shot": 1,
            "current_time": 3.45,
            "split_time": 3.45,
            "event_detail": "Shot 1: 3.45s"
        })
        
        await asyncio.sleep(2)
        
        # Run update
        await server.broadcast_run_update({
            "event_type": "run_started",
            "run_id": "run_001",
            "shooter_name": "John Doe",
            "stage_name": "Stage 1",
            "start_time": datetime.now().isoformat()
        })
        
        await asyncio.sleep(3)
        
        # Another sensor event
        await server.broadcast_sensor_event({
            "event_type": "impact_detected",
            "sensor_id": "BT50_01", 
            "magnitude": 12.8,
            "timestamp_sensor": datetime.now().isoformat(),
            "location": {"x": 1.9, "y": 2.1}
        })
        
        # Timer shot detected
        await server.broadcast_timer_event("shot_detected", {
            "shot_state": "ACTIVE",
            "current_shot": 2,
            "current_time": 6.23,
            "split_time": 2.78,
            "event_detail": "Shot 2: 6.23s (Split: 2.78s)"
        })
        
        await asyncio.sleep(5)
        
        # Final run update
        await server.broadcast_run_update({
            "event_type": "run_completed",
            "run_id": "run_001",
            "total_shots": 2,
            "total_time": 6.23,
            "end_time": datetime.now().isoformat()
        })
        
        # Timer stop
        await server.broadcast_timer_event("timer_stop", {
            "shot_state": "STOPPED",
            "total_shots": 2,
            "final_time": 6.23,
            "message": "Run completed successfully"
        })
        
        # Keep server running for additional testing
        print(f"🚀 WebSocket server running on ws://{server.host}:{server.port}")
        print("📊 Broadcasting sample events - connect with a client to see live updates")
        print("⏱️  Server will continue running for 30 seconds...")
        
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    finally:
        await server.stop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--client":
        # Run enhanced WebSocket client with reconnection
        print("🚀 Starting enhanced WebSocket client with reconnection...")
        asyncio.run(enhanced_websocket_client())
    elif len(sys.argv) > 1 and sys.argv[1] == "--simple-client":
        # Run simple WebSocket client with reconnection
        print("🚀 Starting WebSocket client with reconnection...")
        asyncio.run(test_websocket_client_with_reconnection())
    else:
        # Run WebSocket server with sample events
        print("🚀 Starting WebSocket server with sample events...")
        asyncio.run(test_websocket_server())