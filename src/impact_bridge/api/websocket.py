"""WebSocket endpoint for real-time live updates."""

import asyncio
import json
import logging
from typing import Dict, Any, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse

from ..websocket_integration import TimerWebSocketServer, TimerWebSocketIntegration

logger = logging.getLogger(__name__)

router = APIRouter()

# Global WebSocket server instance (singleton pattern for this module)
_websocket_server: TimerWebSocketServer = None
_websocket_integration: TimerWebSocketIntegration = None

def get_websocket_server() -> TimerWebSocketServer:
    """Get or create WebSocket server instance."""
    global _websocket_server, _websocket_integration
    
    if _websocket_server is None:
        _websocket_server = TimerWebSocketServer(
            host="0.0.0.0",
            port=8765,  # Keeping existing port for compatibility
            enabled=True
        )
        _websocket_integration = TimerWebSocketIntegration(_websocket_server)
        
        # Start server in background task
        asyncio.create_task(_websocket_server.start())
    
    return _websocket_server


class ConnectionManager:
    """Manages WebSocket connections for the /ws/live endpoint."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected to /ws/live: {websocket.client}")
        
        # Send welcome message
        welcome_msg = {
            "type": "status",
            "event_type": "connection_established", 
            "message": "Connected to LeadVille Live Updates",
            "timestamp": "2023-09-13T18:30:45.123Z",
            "capabilities": ["status", "sensor_event", "timer_event", "run_update"]
        }
        await websocket.send_text(json.dumps(welcome_msg))
        
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected from /ws/live: {websocket.client}")
        
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
            
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")
                disconnected.append(connection)
        
        # Remove failed connections
        for connection in disconnected:
            self.active_connections.discard(connection)
            
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time live updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Listen for client messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(websocket, message)
            except json.JSONDecodeError:
                error_msg = {
                    "type": "status",
                    "event_type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": "2023-09-13T18:30:45.123Z"
                }
                await manager.send_personal_message(json.dumps(error_msg), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        

async def handle_client_message(websocket: WebSocket, message: Dict[str, Any]):
    """Handle messages from WebSocket clients."""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping
        pong_msg = {
            "type": "status",
            "event_type": "pong",
            "timestamp": "2023-09-13T18:30:45.123Z"
        }
        await manager.send_personal_message(json.dumps(pong_msg), websocket)
        
    elif message_type == "subscribe":
        # Handle subscription requests
        channels = message.get("channels", [])
        response = {
            "type": "status",
            "event_type": "subscription_confirmed",
            "channels": channels,
            "message": f"Subscribed to {len(channels)} channels",
            "timestamp": "2023-09-13T18:30:45.123Z"
        }
        await manager.send_personal_message(json.dumps(response), websocket)
        
    else:
        # Unknown message type
        error_msg = {
            "type": "status",
            "event_type": "error", 
            "message": f"Unknown message type: {message_type}",
            "timestamp": "2023-09-13T18:30:45.123Z"
        }
        await manager.send_personal_message(json.dumps(error_msg), websocket)


# Broadcasting functions for integration with other components
async def broadcast_status_update(status_data: Dict[str, Any]):
    """Broadcast status update to all connected clients."""
    message = {
        "type": "status",
        "event_type": "system_status_update",
        "timestamp": "2023-09-13T18:30:45.123Z",
        "data": status_data
    }
    await manager.broadcast(message)


async def broadcast_sensor_event(sensor_data: Dict[str, Any]):
    """Broadcast sensor event to all connected clients."""
    message = {
        "type": "sensor_event", 
        "event_type": sensor_data.get("event_type", "impact_detected"),
        "timestamp": "2023-09-13T18:30:45.123Z",
        "sensor_id": sensor_data.get("sensor_id", "BT50_01"),
        "data": sensor_data
    }
    await manager.broadcast(message)


async def broadcast_timer_event(timer_data: Dict[str, Any]):
    """Broadcast timer event to all connected clients."""
    message = {
        "type": "timer_event",
        "event_type": timer_data.get("event_type", "shot_detected"),
        "timestamp": "2023-09-13T18:30:45.123Z", 
        "device_id": "60:09:C3:1F:DC:1A",
        "data": timer_data
    }
    await manager.broadcast(message)


async def broadcast_run_update(run_data: Dict[str, Any]):
    """Broadcast run update to all connected clients."""
    message = {
        "type": "run_update",
        "event_type": run_data.get("event_type", "run_status_change"),
        "timestamp": "2023-09-13T18:30:45.123Z",
        "run_id": run_data.get("run_id"),
        "data": run_data
    }
    await manager.broadcast(message)


@router.get("/ws/test")
async def websocket_test_page():
    """Test page for WebSocket connection."""
    html = """
<!DOCTYPE html>
<html>
    <head>
        <title>LeadVille WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { height: 400px; border: 1px solid #ccc; overflow-y: auto; padding: 10px; margin: 10px 0; }
            .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
            .status { background-color: #e3f2fd; }
            .sensor_event { background-color: #f3e5f5; }
            .timer_event { background-color: #e8f5e8; }
            .run_update { background-color: #fff3e0; }
            .error { background-color: #ffebee; }
            button { margin: 5px; padding: 10px; }
            input { margin: 5px; padding: 5px; width: 200px; }
        </style>
    </head>
    <body>
        <h1>🎯 LeadVille WebSocket Live Updates Test</h1>
        
        <div>
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
            <span id="status">Disconnected</span>
        </div>
        
        <div>
            <input type="text" id="messageInput" placeholder="Type message..." />
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <div>
            <button onclick="sendPing()">Send Ping</button>
            <button onclick="subscribe()">Subscribe to All</button>
        </div>
        
        <div id="messages"></div>

        <script>
            let ws = null;
            let reconnectInterval = null;
            
            function connect() {
                if (ws) {
                    ws.close();
                }
                
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/live`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').style.color = 'green';
                    addMessage('Connected to WebSocket', 'status');
                    
                    // Clear any reconnect attempts
                    if (reconnectInterval) {
                        clearInterval(reconnectInterval);
                        reconnectInterval = null;
                    }
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage(`${data.type}: ${JSON.stringify(data, null, 2)}`, data.type);
                };
                
                ws.onclose = function(event) {
                    document.getElementById('status').textContent = 'Disconnected';
                    document.getElementById('status').style.color = 'red';
                    addMessage('WebSocket connection closed', 'error');
                    
                    // Auto-reconnect after 3 seconds
                    if (!reconnectInterval) {
                        reconnectInterval = setInterval(() => {
                            addMessage('Attempting to reconnect...', 'status');
                            connect();
                        }, 3000);
                    }
                };
                
                ws.onerror = function(error) {
                    addMessage(`WebSocket error: ${error}`, 'error');
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                }
                if (reconnectInterval) {
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value;
                if (ws && message) {
                    ws.send(message);
                    input.value = '';
                }
            }
            
            function sendPing() {
                if (ws) {
                    ws.send(JSON.stringify({type: 'ping'}));
                }
            }
            
            function subscribe() {
                if (ws) {
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        channels: ['status', 'sensor_event', 'timer_event', 'run_update']
                    }));
                }
            }
            
            function addMessage(message, type = 'status') {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.innerHTML = `<small>${new Date().toLocaleTimeString()}</small><br/><pre>${message}</pre>`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            // Auto-connect on page load
            window.onload = function() {
                connect();
            };
            
            // Handle Enter key in message input
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
</html>
    """
    return HTMLResponse(content=html)