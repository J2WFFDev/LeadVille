# LeadVille Networking Modes

This document describes the networking modes feature that enables dual network operation with AP mode (offline) and client mode (online) switching capabilities.

## Overview

The LeadVille Impact Bridge now supports two networking modes:

- **AP Mode (Access Point)**: Creates a WiFi hotspot for offline operation
- **Client Mode**: Connects to existing WiFi networks for online operation

The system provides automatic fallback to AP mode when internet connectivity is lost, ensuring continuous operation.

## Features

### 🌐 Network Mode Switching
- Seamless switching between AP and Client modes
- Web-based configuration interface
- API endpoints for programmatic control
- Automatic service management (hostapd, dnsmasq, wpa_supplicant)

### 📡 Access Point Mode
- **SSID**: LeadVille-Bridge
- **Password**: leadville2024 (configurable)
- **IP Range**: 192.168.4.1-200
- **Captive Portal**: Redirects to bridge.local
- **DNS**: Local DNS server with bridge.local resolution

### 🔗 Client Mode
- WiFi network scanning and selection
- WPA/WPA2 security support
- DHCP client configuration
- Internet connectivity monitoring

### 🔍 Network Monitoring
- Automatic connectivity checking
- Configurable failure thresholds
- Auto-fallback to AP mode on connection loss
- Real-time status monitoring

### 🌍 Web Interface
- User-friendly network management
- Real-time status display
- WiFi network scanning
- Mode switching controls

## Installation

### Prerequisites
```bash
# Install required system packages
sudo apt update
sudo apt install -y hostapd dnsmasq nginx wireless-tools wpasupplicant dhcpcd5
```

### Python Dependencies
```bash
pip install flask flask-cors
```

### Setup on Raspberry Pi
```bash
# Run the Pi setup script with networking option
./setup_pi.sh
# When prompted, choose "y" for networking setup

# Or run networking setup separately
sudo ./scripts/network/setup_networking.sh
```

## Configuration

### Main Configuration
Edit `config/dev_config.json`:

```json
{
  "networking": {
    "enabled": true,
    "default_mode": "ap",
    "web_server_port": 5000,
    "captive_portal_port": 8080,
    "monitoring": {
      "check_interval_seconds": 30,
      "failure_threshold": 3,
      "auto_fallback": true
    },
    "ap_mode": {
      "ssid": "LeadVille-Bridge",
      "password": "leadville2024",
      "ip_address": "192.168.4.1",
      "dhcp_range": "192.168.4.10,192.168.4.200"
    }
  }
}
```

### Network Configuration Files
- `config/network/hostapd.conf` - AP mode configuration
- `config/network/dnsmasq.conf` - DHCP and DNS configuration
- `config/network/nginx.conf` - Reverse proxy configuration

## Usage

### Starting the Network Service
```bash
# Start the network management service
python -m impact_bridge.networking.network_service

# Or using systemd (after setup)
sudo systemctl start leadville-network
```

### Web Interface
Access the web interface at:
- **AP Mode**: http://192.168.4.1 or http://bridge.local
- **Client Mode**: http://[device-ip]:5000

### API Endpoints

#### Get Network Status
```bash
GET /api/network/status
```

Response:
```json
{
  "network": {
    "mode": "ap",
    "connected": true,
    "ip_address": "192.168.4.1",
    "ssid": "LeadVille-Bridge"
  },
  "monitor": {
    "is_monitoring": true,
    "failure_count": 0
  },
  "success": true
}
```

#### Switch Network Mode
```bash
POST /api/network/mode
Content-Type: application/json

# Switch to AP mode
{"mode": "ap"}

# Switch to Client mode
{"mode": "client", "ssid": "MyWiFi", "password": "password123"}
```

#### Scan WiFi Networks
```bash
GET /api/network/scan
```

#### Check Internet Connectivity
```bash
GET /api/network/connectivity
```

### Manual Mode Switching
```bash
# Switch to AP mode
sudo /etc/leadville/network/switch-to-ap.sh

# Switch to Client mode
sudo /etc/leadville/network/switch-to-client.sh
```

## Architecture

### Components

1. **NetworkManager**: Core network mode switching logic
2. **NetworkMonitor**: Connectivity monitoring and auto-fallback
3. **NetworkWebServer**: Web interface and API endpoints
4. **CaptivePortal**: Redirects clients to bridge interface in AP mode

### Service Architecture
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│    nginx     │◄──►│ NetworkWebServer│
└─────────────────┘    │ (Port 80)    │    │   (Port 5000)   │
                       └──────────────┘    └─────────────────┘
                              │                       │
                       ┌──────────────┐              │
                       │CaptivePortal │              │
                       │ (Port 8080)  │              │
                       └──────────────┘              │
                                                     │
                       ┌─────────────────────────────┴─┐
                       │     NetworkService            │
                       │  ┌─────────────────────────┐  │
                       │  │   NetworkManager        │  │
                       │  │   - Mode switching      │  │
                       │  │   - Status monitoring   │  │
                       │  └─────────────────────────┘  │
                       │  ┌─────────────────────────┐  │
                       │  │   NetworkMonitor        │  │
                       │  │   - Connectivity check  │  │
                       │  │   - Auto-fallback       │  │
                       │  └─────────────────────────┘  │
                       └───────────────────────────────┘
```

### System Services Integration
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   hostapd   │  │   dnsmasq   │  │    nginx    │
│ (AP mode)   │  │ (DHCP/DNS)  │  │(Reverse Proxy)│
└─────────────┘  └─────────────┘  └─────────────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
            ┌─────────────────────────┐
            │  leadville-network      │
            │      (systemd)          │
            └─────────────────────────┘
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Ensure proper permissions
   sudo chown -R pi:pi /etc/leadville
   sudo chmod +x /etc/leadville/network/*.sh
   ```

2. **Service Start Failures**
   ```bash
   # Check service status
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   sudo systemctl status leadville-network
   
   # View logs
   journalctl -u leadville-network -f
   ```

3. **WiFi Interface Issues**
   ```bash
   # Check interface status
   ip addr show wlan0
   sudo iwconfig wlan0
   
   # Restart networking
   sudo systemctl restart networking
   ```

### Logs
- **Network Service**: `journalctl -u leadville-network`
- **System Services**: `journalctl -u hostapd`, `journalctl -u dnsmasq`
- **LeadVille Logs**: `logs/console/` directory

## Security Considerations

- Default AP password should be changed in production
- Web interface runs on HTTP (consider HTTPS for production)
- Firewall rules are configured for basic security
- SSH access is maintained during mode switches

## Demo

Run the networking demo to test functionality:

```bash
python demo_networking.py
```

This will demonstrate the networking components without requiring actual hardware.

## Future Enhancements

- WPA3 security support
- Multiple WiFi network profiles
- VPN client integration  
- Advanced firewall rules
- HTTPS support for web interface
- Mobile app integration