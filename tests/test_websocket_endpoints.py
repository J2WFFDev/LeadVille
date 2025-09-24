#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_logs_ws():
    try:
        uri = 'ws://localhost:8001/ws/logs'
        print(f'🔌 Connecting to {uri}...')
        async with websockets.connect(uri) as ws:
            print('✅ Connected! Requesting logs...')
            await ws.send(json.dumps({'type': 'request_logs', 'limit': 5}))
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(response)
            print(f'📋 Received: {data.get("type", "unknown")} with {len(data.get("logs", []))} logs')
            
            if data.get("logs"):
                print("Sample log entries:")
                for i, log in enumerate(data.get("logs", [])[:3]):
                    print(f"  {i+1}. {log}")
            
            print('🎉 WebSocket /ws/logs is working!')
            
    except Exception as e:
        print(f'❌ Error: {e}')

async def test_live_ws():
    try:
        uri = 'ws://localhost:8001/ws/live'
        print(f'🔌 Connecting to {uri}...')
        async with websockets.connect(uri) as ws:
            print('✅ Connected to live endpoint!')
            
            # Send subscription
            await ws.send(json.dumps({'type': 'subscribe', 'channels': ['status']}))
            print('📡 Subscribed to status channel')
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            print(f'📋 Received: {data}')
            print('🎉 WebSocket /ws/live is working!')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    print("=== Testing WebSocket Endpoints ===")
    asyncio.run(test_logs_ws())
    print()
    asyncio.run(test_live_ws())