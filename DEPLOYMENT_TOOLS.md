# LeadVille Deployment Tools Overview

Complete deployment system for LeadVille Impact Bridge with automated installation, service management, and comprehensive documentation.

## 🚀 One-Click Installation

### Primary Installer: `install_pi.sh`

Production-ready automated installer for Raspberry Pi:

```bash
# Remote installation
curl -fsSL https://raw.githubusercontent.com/J2WFFDev/LeadVille/main/install_pi.sh | sudo bash

# Local installation  
sudo ./install_pi.sh
```

**Features:**
- ✅ Complete system user setup (`leadville` user)
- ✅ Automated dependency installation
- ✅ Bluetooth configuration and permissions
- ✅ Professional systemd service installation
- ✅ Log rotation and security settings
- ✅ Installation validation and testing
- ✅ Enhanced error handling and logging

## 📋 Service Management

### SystemD Services

Four production-ready services in `/systemd/`:

- **`leadville-bridge.service`** - Main BLE sensor bridge
- **`leadville-api.service`** - REST API server
- **`leadville-network.service`** - Network management
- **`leadville-websocket.service`** - WebSocket server

**Service Operations:**
```bash
# Start services
sudo systemctl start leadville-bridge leadville-api

# Enable auto-start
sudo systemctl enable leadville-bridge leadville-api

# View logs
journalctl -u leadville-bridge -f

# Check status
systemctl status leadville-bridge
```

## 📚 Documentation Suite

### Installation Guides

- **`INSTALLATION.md`** - Comprehensive installation guide
  - One-click installation instructions
  - Manual step-by-step procedures
  - Online/Offline installation modes
  - Post-installation configuration
  - Troubleshooting and validation

- **`PI_DEPLOYMENT.md`** - Raspberry Pi specific deployment
  - Transfer methods (Git, archive, direct copy)
  - Pi-specific optimizations
  - Hardware troubleshooting

### API Documentation

- **`API_README.md`** - FastAPI backend documentation
- **OpenAPI Specification Generation** via `scripts/generate_openapi.py`

## 🛠️ Development & Maintenance Tools

### Installation Scripts

- **`install_pi.sh`** - Primary production installer
- **`setup_pi.sh`** - Legacy setup script (updated to recommend new installer)
- **`scripts/prepare_offline.sh`** - Offline installation preparation
- **`scripts/network/setup_networking.sh`** - Network configuration

### Validation & Testing

- **`scripts/validate_installation.py`** - Comprehensive installation validation
  - System requirements verification
  - Directory structure validation
  - Python environment testing
  - Dependency checking
  - Bluetooth functionality tests
  - Service status validation
  - Application startup tests

### API Tools

- **`scripts/generate_openapi.py`** - OpenAPI 3.0 specification generator
  - JSON and YAML output formats
  - Validation and testing
  - Client generation support

## 🌐 Deployment Modes

### 1. Online Installation (Default)

Full internet-connected installation:

```bash
sudo ./install_pi.sh
```

- Downloads all dependencies
- Updates system packages
- Real-time validation
- Complete feature set

### 2. Offline Installation

Air-gapped deployment support:

```bash
# Preparation (on internet-connected system)
./scripts/prepare_offline.sh

# Transfer offline_packages/ to target Pi
# On target Pi:
cd offline_packages
sudo ./install_offline.sh
```

- Pre-downloaded Python wheels
- System package bundles
- Self-contained installation
- No internet required during deployment

### 3. Development Installation

Development-friendly setup:

```bash
# Use existing setup_pi.sh for development
./setup_pi.sh

# Or manual virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_pi.txt
```

## 🔧 Configuration Management

### Primary Configuration

- **`config/dev_config.json`** - Main application configuration
- **Hardware MAC addresses** - Update in `leadville_bridge.py`
- **Service environment variables** - Set in systemd service files

### Network Configuration

- **AP/Client mode switching** - Via network management scripts
- **WiFi configuration** - Standard wpa_supplicant setup
- **Web interface** - Nginx configuration included

## 🚨 Validation & Monitoring

### Installation Validation

```bash
# Comprehensive validation
python scripts/validate_installation.py

# Quick validation
python scripts/validate_installation.py --quick

# Generate report
python scripts/validate_installation.py --report validation_report.json
```

### System Monitoring

```bash
# Service status
systemctl status leadville-bridge leadville-api

# Real-time logs
journalctl -u leadville-bridge -f

# System resources
htop

# Bluetooth status
hciconfig hci0
```

## 📊 API & Integration

### REST API Server

- **Base URL:** `http://raspberrypi.local:8000`
- **Documentation:** `/docs` (Swagger UI)
- **Health Check:** `/v1/health`
- **OpenAPI Spec:** Generated via `scripts/generate_openapi.py`

### WebSocket Integration

- **Real-time data streaming**
- **Frontend integration support**
- **Event-based architecture**

## 🔒 Security Features

### System Security

- Dedicated `leadville` system user
- Restricted file permissions
- systemd security hardening
- Process isolation

### API Security

- JWT authentication
- Role-based access control (RBAC)
- Rate limiting
- CORS protection
- Security headers

### Network Security

- Configurable CORS origins
- Optional AP mode isolation
- SSL/TLS ready (certificates not included)

## 🎯 Quick Reference

### Essential Commands

```bash
# Install LeadVille
sudo ./install_pi.sh

# Start services  
sudo systemctl start leadville-bridge leadville-api

# View logs
journalctl -u leadville-bridge -f

# Validate installation
python scripts/validate_installation.py

# Generate API docs
python scripts/generate_openapi.py --output api-spec.json

# Test Bluetooth
sudo hcitool lescan
```

### Key Files

```
LeadVille/
├── install_pi.sh                    # Primary installer
├── INSTALLATION.md                  # Installation guide  
├── systemd/                         # Service definitions
│   ├── leadville-bridge.service
│   ├── leadville-api.service
│   ├── leadville-network.service
│   └── leadville-websocket.service
├── scripts/
│   ├── generate_openapi.py          # API documentation
│   ├── validate_installation.py     # Installation testing
│   └── prepare_offline.sh           # Offline setup
└── config/
    └── dev_config.json              # Main configuration
```

### Support & Troubleshooting

1. **Check installation validation:** `python scripts/validate_installation.py`
2. **Review service logs:** `journalctl -u leadville-bridge --no-pager`
3. **Test Bluetooth:** `sudo hciconfig hci0 && sudo hcitool lescan`
4. **Verify configuration:** Validate JSON in `config/dev_config.json`
5. **Check permissions:** `ls -la /opt/leadville` (should be owned by `leadville`)

For detailed troubleshooting, see `INSTALLATION.md` and `PI_DEPLOYMENT.md`.