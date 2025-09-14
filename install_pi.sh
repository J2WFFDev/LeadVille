#!/bin/bash
# LeadVille Impact Bridge - One-Click Pi Installation Script
# Automated deployment system for production Raspberry Pi setup
# Version: 2.0.0

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LEADVILLE_DIR="/opt/leadville"
VENV_DIR="$LEADVILLE_DIR/venv"
CONFIG_DIR="/etc/leadville"
LOG_DIR="/var/log/leadville"
SERVICE_USER="leadville"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check if running on Raspberry Pi
check_pi() {
    if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        log_warning "This doesn't appear to be a Raspberry Pi"
        read -p "Continue anyway? (y/N): " confirm
        if [[ $confirm != [yY] ]]; then
            exit 1
        fi
    fi
}

# Create system user for LeadVille
create_system_user() {
    log_info "Creating system user for LeadVille..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --home-dir "$LEADVILLE_DIR" --shell /bin/bash \
                --groups bluetooth,dialout,gpio,i2c,spi,video \
                --create-home "$SERVICE_USER"
        log_success "Created system user: $SERVICE_USER"
    else
        log_info "System user $SERVICE_USER already exists"
        usermod -a -G bluetooth,dialout,gpio,i2c,spi,video "$SERVICE_USER"
    fi
}

# Install system packages
install_system_packages() {
    log_info "Updating system packages..."
    apt update && apt upgrade -y
    
    log_info "Installing core dependencies..."
    apt install -y \
        python3 python3-pip python3-venv python3-dev \
        build-essential libffi-dev libssl-dev \
        bluez bluez-tools libbluetooth-dev libglib2.0-dev \
        git curl wget \
        nginx supervisor \
        systemd-timesyncd ntp \
        htop iotop \
        logrotate rsyslog
    
    log_success "System packages installed"
}

# Setup directories and permissions
setup_directories() {
    log_info "Setting up directory structure..."
    
    # Create main directories
    mkdir -p "$LEADVILLE_DIR"/{src,config,logs,scripts,data}
    mkdir -p "$CONFIG_DIR"/{network,systemd}
    mkdir -p "$LOG_DIR"/{bridge,api,network}
    
    # Create logs subdirectories
    mkdir -p "$LEADVILLE_DIR/logs"/{console,debug,main}
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LEADVILLE_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    
    # Set permissions
    chmod -R 755 "$LEADVILLE_DIR"
    chmod -R 755 "$LOG_DIR"
    
    log_success "Directory structure created"
}

# Install Python environment
setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    
    # Create virtual environment as service user
    sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR"
    
    # Upgrade pip
    sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --upgrade pip
    
    log_success "Python environment ready"
}

# Copy LeadVille application files
copy_application_files() {
    log_info "Copying LeadVille application files..."
    
    # Determine source directory (current directory or repository)
    if [[ -f "leadville_bridge.py" && -d "src" ]]; then
        SOURCE_DIR="$(pwd)"
        log_info "Installing from local directory: $SOURCE_DIR"
    else
        log_error "LeadVille source files not found in current directory"
        log_info "Please run this script from the LeadVille repository root"
        exit 1
    fi
    
    # Copy application files
    cp -r "$SOURCE_DIR"/{src,config,requirements*.txt,leadville_bridge.py} "$LEADVILLE_DIR/"
    cp -r "$SOURCE_DIR"/{*.py,*.html,*.js,*.css} "$LEADVILLE_DIR/" 2>/dev/null || true
    cp -r "$SOURCE_DIR/scripts" "$LEADVILLE_DIR/" 2>/dev/null || true
    
    # Copy systemd files
    if [[ -d "$SOURCE_DIR/systemd" ]]; then
        cp "$SOURCE_DIR/systemd"/*.service "$CONFIG_DIR/systemd/"
    fi
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LEADVILLE_DIR"
    
    log_success "Application files copied"
}

# Install Python dependencies
install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    cd "$LEADVILLE_DIR"
    
    # Install from Pi requirements if available, otherwise main requirements
    if [[ -f requirements_pi.txt ]]; then
        sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install -r requirements_pi.txt
    else
        sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install -r requirements.txt
    fi
    
    log_success "Python dependencies installed"
}

# Configure Bluetooth
configure_bluetooth() {
    log_info "Configuring Bluetooth services..."
    
    # Enable and start Bluetooth
    systemctl enable bluetooth
    systemctl start bluetooth
    
    # Test Bluetooth adapter
    if hciconfig hci0 >/dev/null 2>&1; then
        hciconfig hci0 up
        log_success "Bluetooth adapter configured"
    else
        log_warning "No Bluetooth adapter detected"
    fi
}

# Install systemd services
install_systemd_services() {
    log_info "Installing systemd services..."
    
    # Create systemd service files directory if it doesn't exist
    mkdir -p systemd
    
    # LeadVille Bridge service
    cat > /etc/systemd/system/leadville-bridge.service <<EOF
[Unit]
Description=LeadVille Impact Bridge - BLE Sensor System
Documentation=https://github.com/J2WFFDev/LeadVille
After=network.target bluetooth.target
Requires=bluetooth.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$LEADVILLE_DIR
Environment=PATH=$VENV_DIR/bin
Environment=PYTHONPATH=$LEADVILLE_DIR/src
ExecStart=$VENV_DIR/bin/python leadville_bridge.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=leadville-bridge

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LEADVILLE_DIR/logs $LOG_DIR
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # LeadVille API service
    cat > /etc/systemd/system/leadville-api.service <<EOF
[Unit]
Description=LeadVille Impact Bridge - REST API Server
Documentation=https://github.com/J2WFFDev/LeadVille
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$LEADVILLE_DIR
Environment=PATH=$VENV_DIR/bin
Environment=PYTHONPATH=$LEADVILLE_DIR/src
ExecStart=$VENV_DIR/bin/python -m src.impact_bridge.api.main
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=leadville-api

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LEADVILLE_DIR/logs $LOG_DIR
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # LeadVille Network Management service
    cat > /etc/systemd/system/leadville-network.service <<EOF
[Unit]
Description=LeadVille Impact Bridge - Network Management
Documentation=https://github.com/J2WFFDev/LeadVille
After=network.target bluetooth.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$LEADVILLE_DIR
Environment=PATH=$VENV_DIR/bin
Environment=PYTHONPATH=$LEADVILLE_DIR/src
ExecStart=$VENV_DIR/bin/python -m impact_bridge.networking.network_service
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=leadville-network

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LEADVILLE_DIR/logs $LOG_DIR
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    
    log_success "Systemd services installed"
}

# Configure log rotation
setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/leadville <<EOF
$LOG_DIR/*/*.log $LEADVILLE_DIR/logs/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload-or-restart leadville-bridge leadville-api leadville-network 2>/dev/null || true
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

# Validate installation
validate_installation() {
    log_info "Validating installation..."
    
    # Check Python environment
    if sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" --version >/dev/null 2>&1; then
        PYTHON_VERSION=$(sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" --version)
        log_success "Python environment: $PYTHON_VERSION"
    else
        log_error "Python environment validation failed"
        return 1
    fi
    
    # Check key dependencies
    if sudo -u "$SERVICE_USER" "$VENV_DIR/bin/python" -c "import bleak" 2>/dev/null; then
        log_success "BLE library (bleak) available"
    else
        log_warning "BLE library (bleak) not available"
    fi
    
    # Check LeadVille imports
    if sudo -u "$SERVICE_USER" PYTHONPATH="$LEADVILLE_DIR/src" "$VENV_DIR/bin/python" -c "import impact_bridge" 2>/dev/null; then
        log_success "LeadVille modules importable"
    else
        log_warning "LeadVille module import failed"
    fi
    
    # Check Bluetooth
    if hciconfig hci0 >/dev/null 2>&1; then
        log_success "Bluetooth adapter detected"
    else
        log_warning "No Bluetooth adapter detected"
    fi
    
    # Check systemd services
    for service in leadville-bridge leadville-api leadville-network; do
        if systemctl is-enabled "$service" >/dev/null 2>&1; then
            log_success "Service $service is installed"
        else
            log_warning "Service $service is not enabled"
        fi
    done
}

# Main installation function
main() {
    echo "🎯 LeadVille Impact Bridge - Production Installation"
    echo "=================================================="
    echo ""
    
    log_info "Starting automated Pi installation..."
    
    check_root
    check_pi
    
    # Installation steps
    create_system_user
    install_system_packages
    setup_directories
    setup_python_environment
    copy_application_files
    install_python_dependencies
    configure_bluetooth
    install_systemd_services
    setup_log_rotation
    
    # Validation
    echo ""
    log_info "Running installation validation..."
    validate_installation
    
    echo ""
    log_success "🎯 LeadVille Installation Complete!"
    echo "================================="
    echo ""
    echo "Service Management:"
    echo "  Enable services:  systemctl enable leadville-bridge leadville-api"
    echo "  Start services:   systemctl start leadville-bridge leadville-api"
    echo "  Check status:     systemctl status leadville-bridge"
    echo "  View logs:        journalctl -u leadville-bridge -f"
    echo ""
    echo "Configuration:"
    echo "  Main config:      $LEADVILLE_DIR/config/dev_config.json"
    echo "  Systemd configs:  $CONFIG_DIR/systemd/"
    echo "  Log files:        $LOG_DIR/"
    echo ""
    echo "Next Steps:"
    echo "  1. Verify device MAC addresses in $LEADVILLE_DIR/leadville_bridge.py"
    echo "  2. Start services: systemctl start leadville-bridge"
    echo "  3. Test BLE scanning: hcitool lescan"
    echo ""
    echo "⚠️  IMPORTANT: Update MAC addresses for your specific devices!"
    echo "   AMG Timer: 60:09:C3:1F:DC:1A"
    echo "   BT50 Sensor: F8:FE:92:31:12:E3"
}

# Run installation if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi