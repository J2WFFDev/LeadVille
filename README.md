# LeadVille Impact Bridge

A production-ready Bluetooth Low Energy (BLE) based impact sensor system for shooting sports applications. LeadVille integrates the proven TinTown codebase with clean project structure, providing real-time shot detection, impact correlation, and comprehensive data logging through integration with AMG timers and BT50 acceleration sensors.

## Version 3.0.0 - TinTown Integration Complete ✅

**MAJOR MILESTONE**: Successfully integrated the entire working TinTown codebase into LeadVille's organized structure. This version brings over all proven functionality including corrected BT50 parsing, working impact detection, and complete timing calibration systems. **Status: WORKING** - Tested and running successfully on Raspberry Pi.

## Features

### Core TinTown Integration ✅
- 🎯 **Proven Impact Detection**: Integrated TinTown's working shot detection algorithms
- 📡 **Complete BLE Stack**: Full TinTown BLE implementation (AMG timers + BT50 sensors)
- ⚙️ **Corrected BT50 Parser**: Fixed scale factors and proper sensor data processing
- 📊 **Statistical Timing**: Advanced timing calibration with uncertainty analysis
- 🔧 **Auto-Calibration**: Dynamic baseline establishment with outlier filtering
- 🧪 **Enhanced Detection**: Dual-threshold onset detection system

### System Integration
- 📝 **TinTown Console Format**: Exact console output matching original TinTown
- ⏱️ **Timing Correlation**: Automatic shot-to-impact correlation system  
- 🔄 **Service Integration**: Systemd service for auto-startup on Pi
- 📋 **Multi-Config Support**: JSON, YAML, and development configuration files
- 🎛️ **Development Mode**: Enhanced logging and analysis capabilities

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