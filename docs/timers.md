# Timer Adapters

The LeadVille Impact Bridge uses a flexible timer adapter system to support multiple shooting timer brands and protocols. This document explains how adapters work and how to use them.

## Architecture

### Adapter Interface

All timer adapters implement the `ITimerAdapter` interface:

```python
class ITimerAdapter(ABC):
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to timer device"""
        
    @abstractmethod  
    async def disconnect(self) -> None:
        """Disconnect from timer device"""
        
    @abstractmethod
    async def start_shooting(self) -> None:
        """Send start command to timer"""
        
    @abstractmethod
    async def stop_shooting(self) -> None:
        """Send stop command to timer"""
        
    @property
    @abstractmethod
    def events(self) -> AsyncIterator[TimerEvent]:
        """Stream of timer events"""
```

### Event Types

Adapters emit standardized events:

- **Shot**: Individual shot detected
- **StringStart**: Beginning of a shooting string  
- **StringStop**: End of a shooting string
- **TimerConnected**: Timer device connected
- **TimerDisconnected**: Timer device disconnected
- **ClockSync**: Time synchronization event

## Supported Timers

### AMG Commander

The AMG Commander is a Bluetooth LE shooting timer with rich timing data.

**Connection**: Bluetooth LE only
**Protocol**: Custom binary protocol over Nordic UART service

```bash
# Connect to AMG Commander
python bin/bridge.py --timer amg --ble 60:09:C3:1F:DC:1A
```

**Features**:
- Shot timing with millisecond precision
- String start/stop detection
- Battery status monitoring
- Automatic reconnection
- Multi-round support

### SpecialPie Timer

The SpecialPie Timer supports multiple connection types and includes advanced features.

**Connection**: USB Serial, Bluetooth LE, or UDP Simulator
**Protocol**: 7-byte binary protocol via BLE characteristic `fff3`

**⚠️ STATUS**: *Protocol reverse engineering in progress*
- Device: `50:54:7B:AD:4F:03` ("SP M1A2 Timer 4F03")
- Manufacturer: `indesign`
- Active Characteristic: `0000fff3-0000-1000-8000-00805f9b34fb`
- Sample Data: `88000400031013`

```bash
# USB Serial connection
python bin/bridge.py --timer specialpie --serial /dev/ttyACM0

# Bluetooth LE connection  
python bin/bridge.py --timer specialpie --ble AA:BB:CC:DD:EE:FF

# UDP Simulator
python bin/bridge.py --timer specialpie --sim
```

**Features**:
- Multiple transport support
- Clock synchronization with host
- Watchdog monitoring
- Checksum validation
- Auto-device detection

## Usage

### Command Line

The `bin/bridge.py` script provides a complete CLI:

```bash
# Basic usage
python bin/bridge.py --timer <timer_type> <connection_options>

# Examples
python bin/bridge.py --timer amg --ble 60:09:C3:1F:DC:1A
python bin/bridge.py --timer specialpie --serial COM3
python bin/bridge.py --timer specialpie --sim

# Options
--timer {amg,specialpie}     Timer adapter to use
--ble MAC_ADDRESS           Bluetooth LE connection
--serial PORT               Serial port connection  
--sim                       UDP simulator connection
--log-level {DEBUG,INFO,WARN,ERROR}
--log-format {text,json}
--config CONFIG_FILE        Configuration file
```

### Configuration File

Use `config.example.yaml` as a template:

```yaml
timer:
  type: "specialpie"
  connection:
    serial:
      port: "/dev/ttyACM0"
      baud: 115200

specialpie:
  watchdog_timeout: 3.0
  clock_sync:
    enabled: true
    interval: 60.0
```

### Programmatic Usage

```python
from impact_bridge.timers.factory import create_timer_adapter
from impact_bridge.timers.types import TimerConfig

# Create adapter
config = TimerConfig(
    timer_type="specialpie",
    serial_port="/dev/ttyACM0"
)
adapter = await create_timer_adapter(config)

# Connect and listen for events
await adapter.connect()
async for event in adapter.events:
    print(f"Event: {event}")
```

## Troubleshooting

### AMG Commander

**Connection Issues**:
- Verify MAC address with `bluetoothctl` or device manager
- Check timer is powered on and in pairing mode
- Ensure no other applications are connected to timer

**Missing Events**:
- Check Bluetooth signal strength
- Verify timer is in shooting mode (not setup)
- Look for BLE disconnection messages in logs

**Debug Commands**:
```bash
# Scan for BLE devices
python -c "
import asyncio
from bleak import BleakScanner
async def scan():
    devices = await BleakScanner.discover()
    for d in devices:
        print(f'{d.address}: {d.name}')
asyncio.run(scan())
"

# Test connection
python bin/bridge.py --timer amg --ble 60:09:C3:1F:DC:1A --log-level DEBUG
```

### SpecialPie Timer

**Serial Connection Issues**:
- Check device permissions: `sudo usermod -a -G dialout $USER`
- Verify correct port: `ls /dev/tty*` (Linux) or Device Manager (Windows)
- Try different baud rates: 9600, 38400, 115200

**Protocol Issues**:
- Enable debug logging to see raw frames
- Check for checksum errors in logs
- Verify cable quality and connections

**Clock Sync Problems**:
- Check system clock accuracy: `timedatectl status`
- Adjust max_skew_ms in configuration
- Monitor sync events in logs

**Debug Commands**:
```bash
# List serial ports
python -c "
from serial.tools import list_ports
for port in list_ports.comports():
    print(f'{port.device}: {port.description}')
"

# Test UDP simulator
python tools/specialpie_sim.py &
python bin/bridge.py --timer specialpie --sim --log-level DEBUG

# Raw serial debugging
python -c "
import serial
ser = serial.Serial('/dev/ttyACM0', 115200)
while True:
    data = ser.readline()
    print(repr(data))
"
```

### General Issues

**No Events Received**:
- Check timer device battery
- Verify correct timer type selection
- Enable DEBUG logging to see raw data
- Test with UDP simulator first

**WebSocket Connection**:
- Check WebSocket server is running on port 8001
- Verify firewall allows connections
- Test with `wscat -c ws://localhost:8001/ws`

**Database Issues**:
- Check database file permissions
- Verify SQLite installation
- Look for database lock errors in logs

## Development

### Adding New Adapters

1. Create adapter class implementing `ITimerAdapter`:
```python
class MyTimerAdapter(BaseTimerAdapter):
    async def connect(self) -> bool:
        # Implementation
        pass
    
    async def _read_events(self) -> AsyncIterator[TimerEvent]:
        # Event parsing loop
        pass
```

2. Add to factory in `timers/factory.py`
3. Update CLI in `bin/bridge.py`
4. Add configuration section
5. Write tests and documentation

### Testing

Run adapter tests:
```bash
# All timer tests
python -m pytest tests/timers/ -v

# Specific adapter
python -m pytest tests/timers/test_specialpie.py -v

# With coverage
python -m pytest tests/timers/ --cov=src/impact_bridge/timers
```

Use simulators for development:
```bash
# SpecialPie simulator
python tools/specialpie_sim.py

# Connect to simulator
python bin/bridge.py --timer specialpie --sim
```

### Debugging

Enable debug logging:
```bash
python bin/bridge.py --log-level DEBUG --log-format json
```

Key log messages to look for:
- `adapter.connected`: Timer connection established
- `adapter.event`: Events received from timer
- `websocket.event`: Events sent to frontend
- `database.record`: Events persisted to database

## WebSocket Events

Adapters send events to the frontend via WebSocket in JSON format:

```json
{
  "type": "shot",
  "data": {
    "shot_time": 0.234,
    "string_time": 1.456,
    "shot_number": 3,
    "string_number": 1
  },
  "timestamp": "2024-01-15T10:30:45.123Z",
  "adapter": "specialpie"
}
```

Event types:
- `shot`: Individual shot detected
- `string_start`: Beginning of shooting string
- `string_stop`: End of shooting string  
- `timer_connected`: Timer device connected
- `timer_disconnected`: Timer device disconnected
- `clock_sync`: Time synchronization completed

## Metrics

Prometheus metrics are available at `http://localhost:8080/metrics`:

- `shots_total`: Total shots detected by adapter
- `strings_total`: Total strings completed by adapter  
- `timer_connected`: Connection status (1=connected, 0=disconnected)
- `timer_clock_skew_ms`: Clock skew in milliseconds (SpecialPie only)

Example Grafana queries:
```promql
# Shot rate over time
rate(shots_total[5m])

# Connection uptime percentage
avg_over_time(timer_connected[1h]) * 100

# Clock drift monitoring
abs(timer_clock_skew_ms) > 500
```