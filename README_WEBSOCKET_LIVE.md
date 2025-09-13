# WebSocket Live Updates API

Real-time WebSocket endpoint for live match monitoring with <25ms latency.

## Quick Start

### 1. Start the FastAPI Server
```bash
python start_api.py --host 0.0.0.0 --port 8000
```

### 2. Connect to WebSocket Endpoint
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live');

ws.onopen = function() {
    console.log('Connected to LeadVille Live Updates');
    
    // Subscribe to all event types
    ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['status', 'sensor_event', 'timer_event', 'run_update']
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log(`${data.type}: ${data.event_type}`, data);
};
```

### 3. Test WebSocket Interface
Visit: `http://localhost:8000/ws/test` for an interactive test interface with:
- Real-time connection status
- Message sending/receiving
- Automatic reconnection demonstration
- Live event monitoring

## Event Types

### Status Events (`status`)
System status updates and connection events:
```json
{
  "type": "status",
  "event_type": "connection_established",
  "message": "Connected to LeadVille Live Updates",
  "timestamp": "2023-09-13T18:30:45.123Z",
  "capabilities": ["status", "sensor_event", "timer_event", "run_update"]
}
```

### Sensor Events (`sensor_event`)
BT50 impact sensor detection events:
```json
{
  "type": "sensor_event",
  "event_type": "impact_detected",
  "timestamp": "2023-09-13T18:30:45.123Z",
  "sensor_id": "BT50_01",
  "data": {
    "magnitude": 15.5,
    "location": {"x": 2.3, "y": 1.8},
    "timestamp_sensor": "2023-09-13T18:30:45.120Z"
  }
}
```

### Timer Events (`timer_event`)
AMG timer shot detection and timing:
```json
{
  "type": "timer_event",
  "event_type": "shot_detected",
  "timestamp": "2023-09-13T18:30:45.123Z",
  "device_id": "60:09:C3:1F:DC:1A",
  "data": {
    "shot_state": "ACTIVE",
    "current_shot": 3,
    "current_time": 15.67,
    "split_time": 5.23,
    "event_detail": "Shot 3: 15.67s (Split: 5.23s)"
  }
}
```

### Run Updates (`run_update`)
Shooting run lifecycle and progress:
```json
{
  "type": "run_update",
  "event_type": "run_started",
  "timestamp": "2023-09-13T18:30:45.123Z",
  "run_id": "run_001",
  "data": {
    "shooter_name": "John Doe",
    "stage_name": "Stage 1",
    "start_time": "2023-09-13T18:30:45.123Z"
  }
}
```

## Client Reconnection

The WebSocket client includes automatic reconnection with exponential backoff:

```javascript
class ReconnectingWebSocket {
    constructor(url) {
        this.url = url;
        this.reconnectDelay = 2000; // Start with 2 seconds
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.connect();
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectDelay = 2000; // Reset delay on success
        };
        
        this.ws.onclose = () => {
            console.log(`Reconnecting in ${this.reconnectDelay}ms...`);
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
    }
    
    handleMessage(data) {
        switch(data.type) {
            case 'status':
                console.log('📊 Status:', data.event_type, data.message);
                break;
            case 'sensor_event':
                console.log('🎯 Sensor:', data.sensor_id, data.event_type);
                break;
            case 'timer_event':
                console.log('⏱️ Timer:', data.event_type, data.data?.current_shot);
                break;
            case 'run_update':
                console.log('🏃 Run:', data.run_id, data.event_type);
                break;
        }
    }
}

// Usage
const reconnectingWS = new ReconnectingWebSocket('ws://localhost:8000/ws/live');
```

## Development and Testing

### Start Standalone WebSocket Server
```bash
# Start server with sample events
python src/impact_bridge/websocket_integration.py

# Start enhanced client with reconnection
python src/impact_bridge/websocket_integration.py --client

# Start simple client
python src/impact_bridge/websocket_integration.py --simple-client
```

### Run Tests
```bash
# Run WebSocket integration tests
python -m pytest tests/test_websocket_simple.py -v

# Run all WebSocket tests
python -m pytest tests/test_websocket*.py -v
```

## Performance Characteristics

- **Connection Establishment**: <2 seconds
- **Event Broadcast Latency**: <25ms end-to-end
- **Reconnection Time**: 2-30 seconds (exponential backoff)
- **Concurrent Clients**: Unlimited (memory permitting)
- **Event Throughput**: >1000 events/second per client

## Integration Points

### Broadcasting Events from Application Code

```python
from src.impact_bridge.api.websocket import (
    broadcast_status_update,
    broadcast_sensor_event, 
    broadcast_timer_event,
    broadcast_run_update
)

# Status update
await broadcast_status_update({
    "event_type": "system_startup",
    "system_status": "operational"
})

# Sensor event
await broadcast_sensor_event({
    "event_type": "impact_detected",
    "sensor_id": "BT50_01",
    "magnitude": 15.5
})

# Timer event
await broadcast_timer_event({
    "event_type": "shot_detected",
    "shot_state": "ACTIVE",
    "current_shot": 1
})

# Run update
await broadcast_run_update({
    "event_type": "run_completed",
    "run_id": "run_001",
    "total_time": 45.67
})
```

### Using with Enhanced Bridge

```python
from src.impact_bridge.websocket_integration import TimerWebSocketIntegration

# Create integration
websocket_server = TimerWebSocketServer(enabled=True)
integration = TimerWebSocketIntegration(websocket_server)

# Handle events
await integration.handle_sensor_event(sensor_data)
await integration.handle_status_update(status_data)
await integration.handle_run_update(run_data)
```

## Configuration

WebSocket settings in `config/dev_config.json`:

```json
{
  "websocket": {
    "enabled": true,
    "host": "localhost", 
    "port": 8765
  }
}
```

## Security Considerations

- WebSocket endpoint supports CORS for web browser clients
- No authentication required for development (add JWT/tokens for production)
- Rate limiting available through FastAPI middleware
- SSL/TLS support via uvicorn configuration

## Troubleshooting

### Connection Issues
1. Verify WebSocket server is running: `netstat -an | grep 8000`
2. Check firewall settings for port 8000
3. Ensure no proxy blocking WebSocket upgrades
4. Use browser developer tools to inspect WebSocket connection

### Event Not Broadcasting
1. Verify client subscription: `{"type": "subscribe", "channels": [...]}`
2. Check server logs for broadcast errors
3. Confirm event data format matches expected schema
4. Test with `/ws/test` interface to isolate issues

### Performance Issues
1. Monitor connection count: `server.get_client_count()`
2. Check event broadcast frequency
3. Verify JSON serialization performance
4. Consider event batching for high-frequency updates