# AMG Labs Commander Timer Integration

Complete BLE integration for AMG Labs Commander shot timer with comprehensive event processing, real-time monitoring, and multi-backend persistence.

## Features

### 🔗 BLE Connectivity
- **Hardware Support**: AMG Labs Commander timer (`60:09:C3:1F:DC:1A`)
- **Protocol**: 14-byte frame processing with UUID `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- **Event Types**: START (0x0105), SHOT (0x0103), STOP (0x0108)
- **Auto-Reconnect**: Robust connection management with exponential backoff
- **Frame Validation**: Enhanced integrity checking with corruption detection

### 📊 Event Processing  
- **Real-time Ingestion**: BLE notification processing
- **Shot Sequence Tracking**: Automatic shot numbering and timing
- **Timestamp Correlation**: Precise event timing for shot-impact correlation
- **Event Classification**: START/SHOT/STOP event detection and processing

### 🏥 Health Monitoring
- **Connection Status**: Real-time BLE connection monitoring  
- **Signal Quality**: RSSI (signal strength) tracking
- **Battery Monitoring**: Battery level reporting (if available)
- **Drift Detection**: Clock synchronization and drift alerts
- **Statistics**: Connection uptime, disconnect counts, data rates

### 💾 Data Persistence
- **Multi-Backend**: SQLite database + JSON backup files
- **Session Management**: Event grouping by shooting sessions
- **Query Support**: Recent events, session filtering, statistics
- **Backup Protection**: Automatic JSON line backup for data recovery

### 🌐 Real-time Integration
- **MQTT Publishing**: Event broadcasting to `timer/events` topics
- **WebSocket Server**: Real-time browser updates on port 8765
- **Health Broadcasting**: Live connection and performance status
- **Session Updates**: Real-time shooting session progress

### 🎭 Testing & Simulation
- **Hardware Simulation**: Complete timer simulation without physical device
- **Simulation Modes**: Single shot, multi-shot, rapid fire, precision match
- **Configurable Timing**: Custom shot intervals and sequences
- **Realistic Variance**: Random timing simulation for testing

## Quick Start

### Basic Usage

```python
from impact_bridge.amg_timer_manager import AMGTimerManager

# Configuration
config = {
    "amg_timer": {
        "device_id": "60:09:C3:1F:DC:1A",
        "uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
        "simulation_mode": False,  # Set True for testing
        "health_monitoring": {"enabled": True},
        "time_synchronization": {"enabled": True}
    },
    "database": {"enabled": True},
    "websocket": {"enabled": True, "port": 8765},
    "mqtt": {"enabled": False}
}

# Start manager
manager = AMGTimerManager(config)
await manager.start()

# Get status and events
status = manager.get_status()
events = await manager.get_recent_events(10)

await manager.stop()
```

### Demo Application

Run the comprehensive demo:

```bash
cd LeadVille
python examples/amg_timer_demo.py
```

Monitor WebSocket events:
```bash
python examples/amg_timer_demo.py --client
```

## Configuration

### AMG Timer Settings

```json
{
  "amg_timer": {
    "device_id": "60:09:C3:1F:DC:1A",
    "uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
    "frame_validation": true,
    "simulation_mode": false,
    "health_monitoring": {
      "enabled": true,
      "rssi_check_interval_sec": 30.0,
      "health_report_interval_sec": 60.0
    },
    "time_synchronization": {
      "enabled": true,
      "sync_interval_minutes": 5,
      "drift_threshold_ms": 100
    }
  }
}
```

### MQTT Integration

```json
{
  "mqtt": {
    "enabled": true,
    "broker_host": "localhost",
    "broker_port": 1883,
    "topic_prefix": "timer/events",
    "client_id": "leadville-timer"
  }
}
```

### Database Configuration

```json
{
  "database": {
    "enabled": true,
    "db_path": "timer_events.db",
    "json_backup_path": "logs/timer_events_backup.jsonl"
  }
}
```

### Simulation Settings

```json
{
  "simulation": {
    "mode": "multi_shot",
    "num_shots": 5,
    "shot_interval_sec": 2.0,
    "start_delay_sec": 3.0,
    "random_timing": false,
    "timing_variance_sec": 0.5
  }
}
```

## Event Types

### Timer Events
- **`timer_start`**: Timer start button pressed or beep signal
- **`shot_detected`**: Shot detection with timing and sequence info
- **`timer_stop`**: Timer stop button pressed or timeout
- **`timer_active`**: Timer running but no shot detected

### Health Events  
- **`connection_established`**: BLE connection successful
- **`connection_lost`**: BLE disconnection detected
- **`sync_update`**: Time synchronization status change
- **`drift_alert`**: Clock drift exceeds threshold

## API Reference

### AMGTimerManager

```python
class AMGTimerManager:
    async def start()                    # Start all components
    async def stop()                     # Stop all components  
    def get_status() -> Dict             # Get manager status
    async def get_recent_events(limit)   # Get recent timer events
    async def get_session_events()       # Get current session events
    async def force_time_sync()          # Force time synchronization
```

### Event Data Structure

```python
@dataclass
class TimerEvent:
    timestamp: str           # ISO timestamp
    device_id: str          # AMG device MAC address  
    event_type: str         # Event classification
    shot_state: str         # Timer state (START/ACTIVE/STOPPED)
    current_shot: int       # Shot number in sequence
    total_shots: int        # Total shots in string
    current_time: float     # Shot time in seconds
    split_time: float       # Split timing
    event_detail: str       # Human-readable description
    raw_hex: str           # Raw frame data
    session_id: str        # Session identifier
```

## WebSocket Protocol

### Connection
```
ws://localhost:8765
```

### Message Types

**Subscription Request:**
```json
{
  "type": "subscribe",
  "channels": ["timer_events", "health_status"]
}
```

**Timer Event:**
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
    "event_detail": "Shot 3: 15.67s"
  }
}
```

**Health Status:**
```json
{
  "type": "health_status",
  "timestamp": "2023-09-13T18:30:45.123Z", 
  "device_id": "60:09:C3:1F:DC:1A",
  "data": {
    "connection_status": "connected",
    "rssi_dbm": -65,
    "uptime_seconds": 1234.5,
    "data_rate_events_per_sec": 0.33
  }
}
```

## MQTT Topics

### Event Publishing
- **`timer/events/start`**: Timer start events
- **`timer/events/shot`**: Shot detection events  
- **`timer/events/stop`**: Timer stop events
- **`timer/events/active`**: Timer active events

### Message Format
```json
{
  "timestamp": "2023-09-13T18:30:45.123Z",
  "event_type": "shot_detected", 
  "device_id": "60:09:C3:1F:DC:1A",
  "data": {
    "shot_state": "ACTIVE",
    "current_shot": 3,
    "current_time": 15.67,
    "event_detail": "Shot 3: 15.67s"
  }
}
```

## Frame Validation

### Validation Features
- **Length Checking**: 14-byte frame requirement
- **Structure Validation**: Type ID and state validation
- **Data Range Checking**: Reasonable value limits
- **Corruption Detection**: Bit pattern analysis
- **Checksum Support**: Optional checksum verification

### Validation Results
```python
{
  "valid": True,
  "result": "valid", 
  "errors": [],
  "warnings": [],
  "frame_size": 14,
  "hex_data": "01030001050200400030002000100000"
}
```

## Time Synchronization

### Features
- **Periodic Sync**: Configurable sync intervals
- **Drift Detection**: Automatic drift monitoring
- **Quality Assessment**: Sync quality rating (good/fair/poor/critical)
- **Correction Support**: Manual drift correction
- **Statistics**: Sync history and performance metrics

### Drift Thresholds
- **Good**: < 25ms drift
- **Fair**: 25-75ms drift  
- **Poor**: 75-150ms drift
- **Critical**: > 150ms drift

## Troubleshooting

### Common Issues

**BLE Connection Failed:**
- Check device MAC address matches physical timer
- Verify Bluetooth adapter is working (`hci0`)
- Ensure timer is in pairing/connectable mode
- Check for interference from other BLE devices

**Frame Validation Errors:**
- Enable debug logging to see raw frames
- Check for electromagnetic interference
- Verify timer firmware compatibility
- Use frame validator to analyze corruption patterns

**Time Sync Issues:**
- Check system clock accuracy
- Verify timer clock synchronization
- Monitor drift patterns in logs
- Consider manual sync correction

**WebSocket Connection Issues:**
- Check port 8765 availability
- Verify firewall settings
- Test with WebSocket client tools
- Check server startup logs

### Debug Logging

Enable comprehensive logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Monitoring

Monitor connection health:
```python
health_status = manager.health_monitor.get_health_status()
print(f"Connection: {health_status.connection_status}")
print(f"RSSI: {health_status.rssi}dBm") 
print(f"Uptime: {health_status.uptime_seconds}s")
```

## Performance

### Typical Performance
- **Detection Latency**: < 50ms for shot events
- **Connection Time**: 2-3 seconds for BLE establishment
- **CPU Usage**: < 5% during normal operation
- **Memory Usage**: < 50MB including all components
- **Event Rate**: Up to 10 events/second processing capability

### Optimization Tips
- Use simulation mode for development to avoid BLE overhead
- Enable database only when needed for better performance
- Adjust health monitoring intervals based on requirements
- Use MQTT QoS 1 for reliable delivery without overwhelming broker

## Integration Examples

### With Existing Bridge
```python
# Integrate with existing leadville_bridge.py
from impact_bridge.amg_timer_manager import AMGTimerManager

# In FixedBridge class
async def start_amg_integration(self):
    self.amg_manager = AMGTimerManager(self.config)
    await self.amg_manager.start()
    
    # Connect timing events
    self.amg_manager.set_t0_callback(self.timing_calibrator.add_shot_event)
```

### Custom Event Processing
```python
# Custom event handler
async def my_event_handler(parsed_data):
    if parsed_data['shot_state'] == 'ACTIVE':
        shot_num = parsed_data['current_shot']
        shot_time = parsed_data['current_time']
        print(f"Shot {shot_num} detected at {shot_time:.2f}s")

# Register handler
manager.amg_client.set_parsed_data_callback(my_event_handler)
```

---

For complete implementation details, see the source code in `src/impact_bridge/` directory.