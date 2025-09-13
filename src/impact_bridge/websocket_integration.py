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


# WebSocket test client for development
async def test_websocket_client():
    """Test WebSocket client for development"""
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Send ping
            ping_msg = {"type": "ping"}
            await websocket.send(json.dumps(ping_msg))
            
            # Subscribe to channels
            subscribe_msg = {
                "type": "subscribe",
                "channels": ["timer_events", "health_status"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 {data['type']}: {data}")
                
    except Exception as e:
        print(f"WebSocket client error: {e}")


# Example usage
async def test_websocket_server():
    """Test WebSocket server"""
    server = TimerWebSocketServer()
    
    # Start server
    await server.start()
    
    # Simulate some events
    await asyncio.sleep(2)
    await server.broadcast_timer_event("timer_start", {"message": "Timer started"})
    
    await asyncio.sleep(3)
    await server.broadcast_timer_event("shot_detected", {
        "shot_number": 1,
        "time": 2.45,
        "message": "Shot 1 detected"
    })
    
    # Keep server running
    try:
        await asyncio.sleep(30)  # Run for 30 seconds
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()


if __name__ == "__main__":
    # Test WebSocket server
    asyncio.run(test_websocket_server())