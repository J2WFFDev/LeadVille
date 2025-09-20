# LeadVille Impact Bridge

A production-ready Bluetooth Low Energy (BLE) based impact sensor system for shooting sports applications. The LeadVille Bridge provides real-time shot detection, impact correlation, and comprehensive data logging through integration with AMG timers and BT50 acceleration sensors.

## Features

- 🎯 **Real-time Impact Detection**: Advanced algorithms for precise shot and impact detection
- 📡 **BLE Integration**: Seamless connection with AMG timers and BT50 sensors
- ⏱️ **Timing Correlation**: Automatic correlation between timer shots and sensor impacts
- 📊 **Statistical Calibration**: Self-learning timing calibration with statistical analysis
- 🔧 **Auto-Calibration**: Dynamic baseline establishment on startup
- 📝 **Comprehensive Logging**: Multi-level logging with console and file output
- ⚙️ **Configurable Parameters**: JSON-based configuration system
- 🧪 **Enhanced Detection**: Onset timing detection with dual-threshold analysis

## System Requirements

- Python 3.8+
- Windows 10/11 with Bluetooth support
- AMG Timer (MAC: 60:09:C3:1F:DC:1A)
- BT50 Acceleration Sensor (MAC: F8:FE:92:31:12:E3)

## Installation

### Windows Development Setup

```bash
# Navigate to project directory
cd LeadVille

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Raspberry Pi Deployment

```bash
# Transfer project to Pi (see PI_DEPLOYMENT.md for methods)
# Then run the automated setup script:
cd /home/pi/LeadVille
chmod +x setup_pi.sh
./setup_pi.sh

# Or manual installation:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_pi.txt
```

### 2. Configuration

The system uses JSON-based configuration in `config/dev_config.json`:

```json
{
  "enhanced_impact": {
    "enabled": true,
    "peak_threshold": 150.0,
    "onset_threshold": 30.0
  },
  "shot_detection": {
    "threshold": 150.0,
    "min_duration": 6,
    "max_duration": 11
  },
  "timing": {
    "expected_delay_ms": 526.0,
    "correlation_window_ms": 2000
  }
}
```

## Usage

### Basic Operation

**Windows:**
```bash
# Run the LeadVille Bridge
python leadville_bridge.py
```

**Raspberry Pi:**
```bash
# Activate virtual environment and run
source venv/bin/activate
python leadville_bridge.py

# Or as systemd service (if installed):
sudo systemctl start leadville-bridge
```

### System Operation Flow

1. **Startup**: Bridge initializes and connects to BLE devices
2. **Calibration**: Automatic sensor baseline calibration (100+ samples)
3. **Detection**: Real-time monitoring for shots and impacts
4. **Correlation**: Automatic timing correlation between events
5. **Logging**: Comprehensive event logging to multiple formats

### Output Logs

The system generates multiple log files:

- `logs/console/bridge_console_YYYYMMDD_HHMMSS.log` - Complete console output
- `logs/debug/bridge_debug_YYYYMMDD_HHMMSS.log` - Detailed debug information  
- `logs/main/bridge_main_YYYYMMDD.csv` - Structured event data (CSV)
- `logs/main/bridge_main_YYYYMMDD.ndjson` - Structured event data (JSON)

## Architecture

### Core Components

- **`impact_bridge/`** - Core library package
  - **`wtvb_parse.py`** - BT50 sensor data parser (corrected 1mg scale)
  - **`shot_detector.py`** - Advanced shot detection with validation
  - **`timing_calibration.py`** - Real-time timing correlation
  - **`enhanced_impact_detection.py`** - Onset timing detection
  - **`statistical_timing_calibration.py`** - Statistical analysis
  - **`dev_config.py`** - Configuration management

- **`leadville_bridge.py`** - Main application entry point

### Key Algorithms

#### Shot Detection
- **Threshold-based detection**: Configurable raw count threshold
- **Duration validation**: 6-11 sample duration requirement  
- **Interval enforcement**: Minimum 1-second between shots
- **Baseline calibration**: Dynamic zero-point establishment

#### Enhanced Impact Detection
- **Dual threshold system**: Peak detection + onset identification
- **Lookback analysis**: Precise onset timing detection
- **Buffer management**: Sliding window sample analysis

#### Timing Correlation
- **Real-time correlation**: Shot-impact event pairing
- **Statistical calibration**: Self-learning delay optimization
- **Correlation window**: 2-second maximum correlation time

## Device Configuration

### AMG Timer
- **MAC Address**: `60:09:C3:1F:DC:1A`
- **Service UUID**: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- **Frame Types**: START (0x0105), SHOT (0x0103), STOP (0x0108)

### BT50 Sensor  
- **MAC Address**: `F8:FE:92:31:12:E3`
- **Service UUID**: `0000ffe4-0000-1000-8000-00805f9a34fb`
- **Protocol**: WitMotion 5561 (corrected 1mg scale factor)
- **Sample Rate**: ~100Hz continuous acceleration data

## Development

### Project Structure
```
LeadVille/
├── src/impact_bridge/          # Core library
├── config/                     # Configuration files
├── logs/                       # Output logs
│   ├── console/               # Console logs
│   ├── debug/                 # Debug logs  
│   └── main/                  # Event logs
├── leadville_bridge.py         # Main application
├── pyproject.toml             # Python package config
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests (when available)
pytest tests/

# Code formatting
black src/ leadville_bridge.py

# Type checking
mypy src/
```

## Configuration Parameters

### Enhanced Impact Detection
- `peak_threshold`: Primary detection threshold (default: 150.0)
- `onset_threshold`: Onset detection threshold (default: 30.0)  
- `lookback_samples`: Samples to analyze for onset (default: 10)

### Shot Detection
- `threshold`: Raw count change threshold (default: 150.0)
- `min_duration`: Minimum valid shot duration (default: 6 samples)
- `max_duration`: Maximum valid shot duration (default: 11 samples)
- `min_interval_seconds`: Minimum time between shots (default: 1.0s)

### Timing Correlation
- `expected_delay_ms`: Expected shot-to-impact delay (default: 526ms)
- `correlation_window_ms`: Maximum correlation window (default: 2000ms)

## Troubleshooting

### Common Issues

**Connection Failures**
- Ensure Bluetooth is enabled and devices are powered on
- Check MAC addresses match your specific devices
- Try resetting Bluetooth adapter: `Device Manager > Bluetooth > Disable/Enable`

**Calibration Problems**
- Ensure sensor is completely stationary during calibration
- Check for 100+ samples collection within 30-second timeout
- Verify BLE connection stability

**Detection Sensitivity**
- Adjust `peak_threshold` in config for sensitivity
- Monitor noise levels in calibration output
- Verify baseline establishment in startup logs

### Debug Mode

Enable detailed debugging by modifying log levels in `dev_config.json`:

```json
{
  "logging": {
    "console_level": "DEBUG", 
    "file_level": "DEBUG",
    "enable_raw_data_logging": true
  }
}
```

## Performance

- **Connection Time**: ~2-3 seconds for both devices
- **Calibration Time**: ~10-15 seconds (100 samples)
- **Detection Latency**: <50ms from sensor to log
- **Memory Usage**: ~50MB typical operation
- **CPU Usage**: <5% on modern systems

## License

MIT License - see LICENSE file for details.

## Support

For technical support or questions:
- Review debug logs in `logs/debug/` directory
- Check configuration in `config/dev_config.json`
- Verify device MAC addresses and UUIDs
- Monitor BLE connection stability

---

**LeadVille Impact Bridge v2.0** - Professional shooting sports impact detection system

## BT50 capture (tools/bt50_capture_db.py)

The project includes a lightweight multi-sensor capture tool at `tools/bt50_capture_db.py` which discovers/connects to BT50/WTVB devices, parses raw frames using the project's parser, and persists records to a local SQLite database at `logs/bt50_samples.db`.

Basic usage:

```
python3 -u tools/bt50_capture_db.py --mac AA:BB:CC:DD:EE:FF --duration 30
```

Key CLI flags:

- `--mac` (repeatable): sensor MAC address to capture from
- `--char`: notify characteristic UUID (default the BT50 notify UUID)
- `--duration`: seconds to capture
- `--status-interval`: seconds between writing status history rows for a sensor
- `--reconnect-max-retries`, `--reconnect-base-delay`, `--reconnect-max-delay`: control per-sensor reconnect/backoff
- `--detect-enabled`: enable built-in impact detection (heuristic)
- `--detect-window-ms`, `--detect-pre-ms`, `--detect-threshold-start`, `--detect-threshold-spike`: control detection window and thresholds

Database schema (summary)

- `bt50_samples`: Raw motion samples with columns: `id, ts_ns, sensor_mac, frame_hex, parser, vx, vy, vz, angle_x, angle_y, angle_z, temp_raw, temperature_c, disp_x, disp_y, disp_z, freq_x, freq_y, freq_z`.
- `device_status`: Latest status per sensor (one row per MAC). New column: `last_history_ns` (persisted timestamp when a history snapshot was last written). Columns: `sensor_mac` (PK), `last_seen_ns`, `temperature_c`, `temp_raw`, `battery_pct`, `battery_mv`, `last_history_ns`.
- `device_status_history`: Occasional status snapshots inserted at most once per `--status-interval` (or when values change significantly). Columns: `id, sensor_mac, ts_ns, temperature_c, temp_raw, battery_pct, battery_mv`.
- `impacts`: Compact impact summary events produced by the optional detector. Columns: `id, sensor_mac, impact_ts_ns, detection_ts_ns, peak_mag, pre_mag, post_mag, duration_ms`.

Notes:

- The capture tool batches DB writes and uses `PRAGMA journal_mode=WAL` to reduce IO contention.
- `last_history_ns` allows the capture process to avoid duplicating history rows after restart by seeding in-memory timers from the DB.
- Impact detection included is a simple heuristic for prototyping; you may want to scale raw accelerometer values to 'g' or tune thresholds per sensor.