#!/usr/bin/env python3
"""
WebSocket test client for LeadVille FastAPI live event streaming
"""

import asyncio
import websockets
import json
import time

async def test_live_websocket():
    uri = "ws://localhost:8001/ws/live"
    try:
        print(f"🔌 Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Wait for welcome message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"📦 Welcome: {data.get('type', 'unknown')}")
                if 'available_channels' in data:
                    print(f"📋 Available channels: {data['available_channels']}")
                
                # Wait for subscription confirmation
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"📦 Subscription: {data.get('type', 'unknown')}")
                if 'subscriptions' in data:
                    print(f"📋 Subscribed to: {data['subscriptions']}")
                
                # Wait for initial status
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(message)
                print(f"📦 Status: {data.get('type', 'unknown')}")
                if data.get('type') == 'status':
                    system = data.get('system', {})
                    cpu = system.get('cpu', {})
                    memory = system.get('memory', {})
                    print(f"💻 CPU: {cpu.get('usage_percent', 'N/A')}%, Memory: {memory.get('percent', 'N/A')}%")
                
                # Send a ping
                ping_msg = {"type": "ping"}
                await websocket.send(json.dumps(ping_msg))
                print("📤 Sent ping")
                
                # Wait for pong
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"📦 Response: {data.get('type', 'unknown')}")
                
                print("✅ WebSocket live endpoint test completed successfully!")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for messages")
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_websocket())