#!/usr/bin/env python3
"""
Simple WebSocket server to test frontend integration
Simulates the LeadVille Bridge WebSocket API
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockWebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.running = False
        
    async def register_client(self, websocket):
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
    async def unregister_client(self, websocket):
        self.clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def handle_message(self, websocket, message):
        try:
            data = json.loads(message)
            logger.info(f"Received: {data}")
            
            if data.get('type') == 'ping':
                await websocket.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif data.get('type') == 'subscribe':
                channels = data.get('channels', [])
                logger.info(f"Client subscribed to channels: {channels}")
                await websocket.send(json.dumps({
                    "type": "subscription_confirmed",
                    "channels": channels,
                    "timestamp": datetime.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message}")
            
    async def handle_client(self, websocket):
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
            
    async def broadcast_message(self, message):
        if not self.clients:
            return
            
        disconnected = []
        for client in self.clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(client)
                
        # Remove disconnected clients
        for client in disconnected:
            self.clients.discard(client)
            
    async def simulate_events(self):
        """Simulate timer and sensor events"""
        shot_number = 1
        session_time = 0.0
        
        while self.running:
            await asyncio.sleep(3)  # Send event every 3 seconds
            
            # Simulate timer event
            timer_event = {
                "type": "timer_event",
                "event_type": "shot_detected",
                "timestamp": datetime.now().isoformat(),
                "device_id": "60:09:C3:1F:DC:1A",
                "data": {
                    "shot_state": "ACTIVE",
                    "current_shot": shot_number,
                    "current_time": session_time,
                    "event_detail": f"Shot {shot_number}: {session_time:.2f}s"
                }
            }
            
            await self.broadcast_message(timer_event)
            
            # Simulate health status
            health_status = {
                "type": "health_status",
                "timestamp": datetime.now().isoformat(),
                "device_id": "60:09:C3:1F:DC:1A",
                "data": {
                    "connection_status": "connected",
                    "rssi_dbm": random.randint(-80, -50),
                    "uptime_seconds": session_time + 120,
                    "data_rate_events_per_sec": 0.33
                }
            }
            
            await self.broadcast_message(health_status)
            
            # Simulate session update
            session_update = {
                "type": "session_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "session_id": "test_session_001",
                    "state": "active",
                    "shots": shot_number,
                    "duration": session_time
                }
            }
            
            await self.broadcast_message(session_update)
            
            shot_number += 1
            session_time += 3.5
            
    async def start(self):
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        self.running = True
        
        # Start the server
        server = await websockets.serve(self.handle_client, self.host, self.port)
        
        # Start event simulation
        event_task = asyncio.create_task(self.simulate_events())
        
        logger.info("WebSocket server started. Simulating events...")
        
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.running = False
            event_task.cancel()
            server.close()
            await server.wait_closed()

if __name__ == "__main__":
    server = MockWebSocketServer()
    asyncio.run(server.start())