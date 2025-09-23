# LeadVille Pi Deployment Guide

## Transfer to Raspberry Pi

### Method 1: Direct Copy (if you have file sharing set up)
```bash
# From Windows, copy entire LeadVille folder to Pi
# Replace PI_IP_ADDRESS with your Pi's IP
scp -r C:\sandbox\TargetSensor\LeadVille pi@PI_IP_ADDRESS:/home/pi/
```

### Method 2: Git Repository (Recommended)
```bash
# On Windows - Initialize git repo
cd C:\sandbox\TargetSensor\LeadVille
git init
git add .
git commit -m "Initial LeadVille production release"

# Push to your repository (GitHub/GitLab)
git remote add origin YOUR_REPO_URL
git push -u origin main

# On Pi - Clone the repository
cd /home/pi
git clone YOUR_REPO_URL
cd LeadVille
```

### Method 3: Archive Transfer
```bash
# On Windows - Create archive
cd C:\sandbox\TargetSensor
tar -czf leadville.tar.gz LeadVille/

# Transfer to Pi
scp leadville.tar.gz pi@PI_IP_ADDRESS:/home/pi/

# On Pi - Extract
cd /home/pi
tar -xzf leadville.tar.gz
```

## Pi Installation Steps

### 1. Install Python Dependencies
```bash
cd /home/pi/LeadVille

# Update system packages
sudo apt update
sudo apt install python3-pip python3-venv

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Additional Pi-specific Bluetooth Dependencies
```bash
# Install system Bluetooth libraries
sudo apt install bluez bluez-tools libbluetooth-dev

# Install Python Bluetooth support
pip install pybluez
```

### 3. Configure Bluetooth Permissions
```bash
# Add pi user to bluetooth group
sudo usermod -a -G bluetooth pi

# Enable Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 4. Test BLE Scanning
```bash
# Test if BLE devices are visible
sudo hcitool lescan

# Or using bluetoothctl
bluetoothctl
> scan on
> devices
> quit
```

## Pi-Specific Configuration

### Update Device MAC Addresses (if different on Pi)
Edit `leadville_bridge.py` if your Pi uses different MAC addresses:

```python
# Device MACs - Update these for your Pi setup
AMG_TIMER_MAC = "60:09:C3:1F:DC:1A"  # Verify this matches your Pi's pairing
BT50_SENSOR_MAC = "F8:FE:92:31:12:E3"  # Verify this matches your Pi's pairing
```

### Optimize for Pi Performance
Edit `config/dev_config.json`:

```json
{
  "sensor": {
    "calibration_samples": 50,
    "calibration_timeout_seconds": 45
  },
  "logging": {
    "console_level": "INFO",
    "file_level": "INFO",
    "enable_raw_data_logging": false
  }
}
```

## Running on Pi

### Manual Execution
```bash
cd /home/pi/LeadVille
source venv/bin/activate
python leadville_bridge.py
```

### Run as Service (Optional)
Create systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/leadville-bridge.service
```

Service file content:
```ini
[Unit]
Description=LeadVille Impact Bridge
After=network.target bluetooth.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/LeadVille
Environment=PATH=/home/pi/LeadVille/venv/bin
ExecStart=/home/pi/LeadVille/venv/bin/python leadville_bridge.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable leadville-bridge.service
sudo systemctl start leadville-bridge.service
```

## Troubleshooting Pi Issues

### Permission Issues
```bash
# Run with sudo if needed (not recommended for production)
sudo python leadville_bridge.py

# Or fix bluetooth permissions
sudo chmod 666 /dev/bluetooth/hci0
```

### BLE Connection Issues
```bash
# Reset Bluetooth adapter
sudo hciconfig hci0 down
sudo hciconfig hci0 up

# Clear Bluetooth cache
sudo systemctl restart bluetooth
```

### Performance Monitoring
```bash
# Monitor system resources
htop

# Check logs
tail -f /home/pi/LeadVille/logs/console/bridge_console_*.log
```

## Pi vs Windows Differences

| Aspect | Windows | Raspberry Pi |
|--------|---------|--------------|
| Python Command | `python` | `python3` |
| Virtual Env | `venv\Scripts\activate` | `source venv/bin/activate` |
| Bluetooth Stack | Windows BLE | BlueZ |
| Permissions | User-level | May need `sudo` or group membership |
| Performance | Higher | Limited (adjust calibration samples) |
| Startup | Manual/Task Scheduler | systemd service |

## Next Steps After Transfer

1. **Transfer files** to Pi using your preferred method
2. **Install dependencies** and test basic functionality  
3. **Verify BLE device detection** with your AMG timer and BT50
4. **Run calibration test** to ensure sensor baseline works
5. **Configure as service** for automatic startup (optional)

The clean LeadVille codebase should work identically on Pi with these setup steps!