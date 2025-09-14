# LeadVille Impact Bridge - Installation & Deployment Guide

Complete installation guide for LeadVille Impact Bridge production deployment on Raspberry Pi.

## Quick Installation (One-Click)

For production deployment on Raspberry Pi:

```bash
# Download and run the automated installer
curl -fsSL https://raw.githubusercontent.com/J2WFFDev/LeadVille/main/install_pi.sh | sudo bash

# Or clone repository first and run locally
git clone https://github.com/J2WFFDev/LeadVille.git
cd LeadVille
sudo ./install_pi.sh
```

The installer will:
- ✅ Create system user and directories
- ✅ Install all dependencies
- ✅ Configure Bluetooth and permissions  
- ✅ Install systemd services
- ✅ Setup log rotation
- ✅ Validate installation

## Installation Modes

### Online Mode (Default)
- Requires internet connection
- Downloads dependencies automatically
- Updates system packages
- Recommended for production

### Offline Mode
- Pre-download requirements using `scripts/prepare_offline.sh`
- Transfer files to air-gapped Pi
- Run installer with offline flag

## Manual Installation

If you prefer step-by-step control:

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install base packages
sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    build-essential libffi-dev libssl-dev \
    bluez bluez-tools libbluetooth-dev libglib2.0-dev \
    git curl wget nginx supervisor
```

### 2. Create System User

```bash
# Create leadville user with required groups
sudo useradd --system --home-dir /opt/leadville --shell /bin/bash \
    --groups bluetooth,dialout,gpio,i2c,spi,video \
    --create-home leadville
```

### 3. Setup Directories

```bash
# Create directory structure
sudo mkdir -p /opt/leadville/{src,config,logs,scripts,data}
sudo mkdir -p /etc/leadville/{network,systemd}
sudo mkdir -p /var/log/leadville/{bridge,api,network}
sudo mkdir -p /opt/leadville/logs/{console,debug,main}

# Set ownership
sudo chown -R leadville:leadville /opt/leadville
sudo chown -R leadville:leadville /var/log/leadville
```

### 4. Install Application

```bash
# Clone repository
git clone https://github.com/J2WFFDev/LeadVille.git
cd LeadVille

# Copy files to system location
sudo cp -r {src,config,requirements*.txt,leadville_bridge.py} /opt/leadville/
sudo cp -r {*.py,*.html,*.js,*.css} /opt/leadville/ 2>/dev/null || true
sudo cp -r scripts /opt/leadville/ 2>/dev/null || true
sudo chown -R leadville:leadville /opt/leadville
```

### 5. Python Environment

```bash
# Create virtual environment
sudo -u leadville python3 -m venv /opt/leadville/venv

# Install dependencies
cd /opt/leadville
sudo -u leadville ./venv/bin/pip install --upgrade pip
sudo -u leadville ./venv/bin/pip install -r requirements_pi.txt
```

### 6. Install Services

```bash
# Copy systemd service files
sudo cp systemd/*.service /etc/systemd/system/

# Reload and enable services
sudo systemctl daemon-reload
sudo systemctl enable leadville-bridge leadville-api

# Start services
sudo systemctl start leadville-bridge leadville-api
```

## Post-Installation Configuration

### 1. Device MAC Addresses

**Critical**: Update MAC addresses for your specific hardware:

```bash
sudo -u leadville nano /opt/leadville/leadville_bridge.py
```

Update these lines:
```python
# Device MACs - Update these for your hardware
AMG_TIMER_MAC = "60:09:C3:1F:DC:1A"    # Your AMG timer MAC
BT50_SENSOR_MAC = "F8:FE:92:31:12:E3"   # Your BT50 sensor MAC
```

### 2. Configuration Files

Main configuration file:
```bash
sudo -u leadville nano /opt/leadville/config/dev_config.json
```

Key settings to review:
```json
{
  "enhanced_impact": {
    "peak_threshold": 10.0,      // Adjust for your setup
    "onset_threshold": 3.0,      // Sensitivity tuning
    "lookback_samples": 10       // Detection window
  },
  "timing": {
    "expected_delay_ms": 526.0,  // Shot-to-impact delay
    "correlation_window_ms": 2000
  },
  "sensor": {
    "calibration_samples": 100,  // Reduce for Pi if needed
    "auto_calibrate_on_startup": true
  }
}
```

### 3. Bluetooth Permissions

Ensure Bluetooth is properly configured:
```bash
# Check Bluetooth adapter
sudo hciconfig hci0

# Test BLE scanning
sudo hcitool lescan

# If issues, restart Bluetooth
sudo systemctl restart bluetooth
```

## Service Management

### Starting/Stopping Services

```bash
# Start all services
sudo systemctl start leadville-bridge leadville-api leadville-network

# Stop services
sudo systemctl stop leadville-bridge leadville-api

# Restart services
sudo systemctl restart leadville-bridge

# Enable auto-start on boot
sudo systemctl enable leadville-bridge leadville-api
```

### Monitoring Services

```bash
# Check service status
systemctl status leadville-bridge
systemctl status leadville-api

# View real-time logs
journalctl -u leadville-bridge -f
journalctl -u leadville-api -f

# View recent logs
journalctl -u leadville-bridge --since "1 hour ago"
```

### Log Files

Application logs are stored in multiple locations:

```bash
# Systemd journal logs
journalctl -u leadville-bridge -f

# Application file logs
tail -f /var/log/leadville/bridge/bridge.log
tail -f /opt/leadville/logs/console/bridge_console_*.log

# Debug logs (if enabled)
tail -f /opt/leadville/logs/debug/debug_*.log
```

## API Access

### REST API Server

The API server runs on port 8000 by default:

```bash
# Test API access
curl http://localhost:8000/v1/health

# View API documentation
# Open: http://raspberrypi.local:8000/docs
```

### Generate OpenAPI Specification

```bash
# Generate OpenAPI spec
cd /opt/leadville
./venv/bin/python scripts/generate_openapi.py --output api-spec.json

# Generate YAML format
./venv/bin/python scripts/generate_openapi.py --format yaml --output api-spec.yaml
```

## Network Configuration

### Access Point Mode

For standalone operation without external network:

```bash
# Setup networking components
sudo ./scripts/network/setup_networking.sh

# Switch to AP mode
sudo /etc/leadville/network/switch-to-ap.sh
```

### Client Mode

For connection to existing WiFi network:

```bash
# Switch to client mode
sudo /etc/leadville/network/switch-to-client.sh

# Configure WiFi credentials
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

## Validation & Testing

### Installation Validation

```bash
# Run built-in validation
cd /opt/leadville
sudo -u leadville ./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
try:
    import impact_bridge
    print('✅ LeadVille modules available')
except ImportError as e:
    print(f'❌ Import failed: {e}')
"

# Test BLE functionality
sudo -u leadville ./venv/bin/python -c "
try:
    import bleak
    print('✅ BLE library available')
except ImportError as e:
    print(f'❌ BLE library failed: {e}')
"
```

### Hardware Testing

```bash
# Test Bluetooth adapter
sudo hciconfig hci0 up
sudo hcitool lescan | head -10

# Test device connectivity (replace MACs with your devices)
sudo -u leadville timeout 30 ./venv/bin/python -c "
import asyncio
import bleak

async def scan():
    devices = await bleak.BleakScanner.discover(timeout=10.0)
    target_macs = ['60:09:C3:1F:DC:1A', 'F8:FE:92:31:12:E3']
    found = [d for d in devices if d.address in target_macs]
    
    if found:
        print(f'✅ Found {len(found)} target devices')
        for d in found:
            print(f'   {d.address}: {d.name}')
    else:
        print('❌ Target devices not found')

asyncio.run(scan())
"
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied Errors
```bash
# Check user groups
groups leadville

# Add to bluetooth group if missing
sudo usermod -a -G bluetooth leadville

# Check directory permissions
ls -la /opt/leadville
ls -la /var/log/leadville
```

#### 2. BLE Connection Issues
```bash
# Reset Bluetooth adapter
sudo hciconfig hci0 down
sudo hciconfig hci0 up
sudo systemctl restart bluetooth

# Clear Bluetooth cache
sudo systemctl stop bluetooth
sudo rm -rf /var/lib/bluetooth/*
sudo systemctl start bluetooth
```

#### 3. Service Start Failures
```bash
# Check service logs
journalctl -u leadville-bridge --no-pager

# Check configuration file syntax
sudo -u leadville /opt/leadville/venv/bin/python -c "
import json
with open('/opt/leadville/config/dev_config.json') as f:
    json.load(f)
print('✅ Configuration file is valid JSON')
"

# Test manual startup
sudo -u leadville bash
cd /opt/leadville
source venv/bin/activate
PYTHONPATH=src python leadville_bridge.py
```

#### 4. Import Errors
```bash
# Check Python path
sudo -u leadville bash -c "
cd /opt/leadville
export PYTHONPATH=src
python -c 'import sys; print(sys.path)'
python -c 'import impact_bridge; print(impact_bridge.__file__)'
"

# Reinstall dependencies
cd /opt/leadville
sudo -u leadville ./venv/bin/pip install --force-reinstall -r requirements_pi.txt
```

### Performance Optimization

#### Pi 3/4 Specific Settings
```json
{
  "sensor": {
    "calibration_samples": 50,        // Reduced for Pi performance
    "calibration_timeout_seconds": 30 // Faster startup
  },
  "logging": {
    "console_level": "INFO",          // Reduce log verbosity
    "file_level": "INFO",
    "enable_raw_data_logging": false  // Disable for performance
  }
}
```

#### System Resource Monitoring
```bash
# Monitor system resources
htop

# Check CPU temperature
vcgencmd measure_temp

# Monitor disk space
df -h /opt/leadville
df -h /var/log/leadville
```

## Uninstallation

To completely remove LeadVille:

```bash
# Stop and disable services
sudo systemctl stop leadville-bridge leadville-api leadville-network
sudo systemctl disable leadville-bridge leadville-api leadville-network

# Remove service files
sudo rm /etc/systemd/system/leadville-*.service
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/leadville
sudo rm -rf /etc/leadville
sudo rm -rf /var/log/leadville

# Remove system user
sudo userdel -r leadville

# Remove log rotation config
sudo rm /etc/logrotate.d/leadville
```

## Support

### Getting Help

1. **Check logs**: `journalctl -u leadville-bridge -f`
2. **Review configuration**: `/opt/leadville/config/dev_config.json`
3. **Test hardware**: Use BLE scanning commands above
4. **Validate installation**: Run validation scripts
5. **Check GitHub issues**: https://github.com/J2WFFDev/LeadVille/issues

### Reporting Issues

When reporting issues, include:
- Pi model and OS version (`cat /etc/os-release`)
- Service logs (`journalctl -u leadville-bridge --no-pager`)
- Configuration file (`cat /opt/leadville/config/dev_config.json`)
- Hardware setup (AMG timer and BT50 sensor models)

### System Information Collection

```bash
# Collect system information for support
cd /opt/leadville
sudo -u leadville ./venv/bin/python -c "
import platform
import subprocess
import json

print('=== SYSTEM INFO ===')
print(f'OS: {platform.platform()}')
print(f'Python: {platform.python_version()}')

try:
    result = subprocess.run(['hciconfig', 'hci0'], 
                          capture_output=True, text=True)
    print(f'Bluetooth: {\"Available\" if result.returncode == 0 else \"Not found\"}')
except:
    print('Bluetooth: Command failed')

try:
    with open('config/dev_config.json') as f:
        config = json.load(f)
    print(f'Config: Valid JSON with {len(config)} sections')
except Exception as e:
    print(f'Config: Error - {e}')

print('=== END SYSTEM INFO ===')
"
```