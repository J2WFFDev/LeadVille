# LeadVille MQTT Internal Message Bus

LeadVille Impact Bridge includes a comprehensive MQTT-based internal message bus for real-time communication between system components and external monitoring systems.

## Architecture

The MQTT message bus provides:
- **Real-time event streaming** - All system events are published to MQTT topics
- **System monitoring** - Status and health information is continuously published
- **Sensor telemetry** - Raw sensor data and processed results are streamed
- **Message persistence** - Important messages are retained for late-joining subscribers
- **Scalable integration** - Easy integration with external systems and dashboards

## Topic Structure

All LeadVille MQTT topics use the prefix `leadville/` to avoid conflicts with other systems.

### System Status Topics

- **`leadville/bridge/status`** - Bridge system status updates
  - Connection states (AMG, BT50 sensors)
  - Detector status and active plates
  - MQTT client statistics
  - Published every 30 seconds with retain flag

- **`leadville/system/health`** - System health metrics
  - Resource usage (CPU, memory)
  - Disk space and log file sizes
  - Error counts and performance metrics

### Timer Topics

- **`leadville/timer/events`** - Timer event notifications
  - T0 start signals
  - Shot detection events
  - Stop signals
  - Raw timing data

- **`leadville/timer/status`** - Timer connection status
  - AMG Commander connection state
  - Signal strength and battery level
  - Configuration and calibration status

### Sensor Topics

- **`leadville/sensor/{sensor_id}/telemetry`** - Real-time sensor data
  - Raw acceleration readings (x, y, z)
  - Battery level and temperature
  - Sample timestamps and sequence numbers
  - High-frequency data (not retained)

- **`leadville/sensor/{sensor_id}/status`** - Sensor connection status
  - Connection state and signal strength
  - Calibration status and baseline values
  - Error conditions and reconnection attempts

### Detection Topics

- **`leadville/detection/impacts`** - Impact detection events
  - Hit detection with timing correlation
  - Peak amplitude and duration measurements
  - Plate identification and coordinates
  - Statistical analysis results

- **`leadville/detection/shots`** - Shot detection events
  - Timer-based shot detection
  - Correlation with impact events
  - Timing accuracy and validation

### Run-Specific Topics

- **`leadville/run/{run_id}/events`** - Run-specific events
  - Run start and end events
  - Stage transitions and scoring
  - Shooter and match information

- **`leadville/run/{run_id}/status`** - Run progress tracking
  - Current stage and target status
  - Shot count and time remaining
  - Score calculations and penalties

## Setup and Deployment

### Development Setup

1. **Install Mosquitto**:
   ```bash
   sudo apt-get install mosquitto mosquitto-clients
   ```

2. **Configure and start broker**:
   ```bash
   ./scripts/setup_mqtt.sh
   ```

3. **Test the integration**:
   ```bash
   python scripts/test_mqtt_integration.py
   ```

### Monitoring Tools

Monitor all LeadVille messages:
```bash
./scripts/monitor_mqtt.py
```

Or use mosquitto clients directly:
```bash
mosquitto_sub -h localhost -t 'leadville/#' -v
```