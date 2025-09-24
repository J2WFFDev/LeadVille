#!/usr/bin/env python3
"""
Simple WebSocket test client for FastAPI WebSocket endpoint
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8001/ws/logs"
    try:
        print(f"🔌 Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Wait for initial message
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            print(f"📦 Received: {data.get('type', 'unknown')} with {len(data.get('logs', []))} logs")
            
            # Request more logs
            request = {"type": "request_logs", "limit": 3}
            await websocket.send(json.dumps(request))
            print("📤 Sent log request")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            print(f"📦 Received: {data.get('type', 'unknown')} with {len(data.get('logs', []))} logs")
            
            print("✅ WebSocket test completed successfully!")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())