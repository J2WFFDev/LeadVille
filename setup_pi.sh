#!/bin/bash
# LeadVille Pi Setup Script (Legacy)
# Run this script on your Raspberry Pi after transferring the LeadVille project
# 
# ⚠️  NOTICE: This is the legacy setup script. For production deployment,
#    use the new automated installer: ./install_pi.sh
#
# The new installer provides:
# - Automated system user creation
# - Enhanced security settings  
# - Professional systemd service management
# - Comprehensive validation
# - Better error handling

echo "🎯 LeadVille Impact Bridge - Pi Setup (Legacy)"
echo "=============================================="
echo ""
echo "⚠️  RECOMMENDATION: Use the new automated installer instead:"
echo "   sudo ./install_pi.sh"
echo ""
read -p "Continue with legacy setup? (y/N): " continue_legacy
if [[ $continue_legacy != [yY] ]]; then
    echo "Switching to new installer..."
    exec sudo ./install_pi.sh
fi
echo ""

# Check if we're on a Pi
if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python and development tools
echo "🐍 Installing Python development environment..."
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential libffi-dev libssl-dev

# Install Bluetooth dependencies
echo "📡 Installing Bluetooth support..."
sudo apt install -y bluez bluez-tools libbluetooth-dev
sudo apt install -y libglib2.0-dev

# Add pi user to bluetooth group
echo "👤 Configuring user permissions..."
sudo usermod -a -G bluetooth $USER

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip in virtual environment
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Pi-specific requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements_pi.txt

# Enable Bluetooth service
echo "🔵 Enabling Bluetooth services..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Test Bluetooth
echo "🧪 Testing Bluetooth functionality..."
if sudo hciconfig hci0 > /dev/null 2>&1; then
    echo "✅ Bluetooth adapter detected"
    sudo hciconfig hci0 up
else
    echo "❌ No Bluetooth adapter found"
fi

# Create logs directory structure
echo "📝 Setting up logging directories..."
mkdir -p logs/{console,debug,main}

# Set permissions for logs
chmod -R 755 logs/

# Create systemd service file (optional)
read -p "🚀 Create systemd service for auto-startup? (y/N): " create_service
if [[ $create_service == [yY] ]]; then
    echo "Creating systemd service..."
    
    sudo tee /etc/systemd/system/leadville-bridge.service > /dev/null <<EOF
[Unit]
Description=LeadVille Impact Bridge
After=network.target bluetooth.target
Requires=bluetooth.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
Environment=PYTHONPATH=$PWD/src
ExecStart=$PWD/venv/bin/python leadville_bridge.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable leadville-bridge.service
    
    echo "✅ Service created. Start with: sudo systemctl start leadville-bridge"
    echo "   View logs with: journalctl -u leadville-bridge -f"
fi

# Setup networking components
echo ""
read -p "🌐 Setup networking components (AP/Client mode switching)? (y/N): " setup_networking
if [[ $setup_networking == [yY] ]]; then
    echo "Setting up networking components..."
    
    # Make setup script executable and run it
    chmod +x scripts/network/setup_networking.sh
    sudo ./scripts/network/setup_networking.sh
    
    echo "✅ Networking setup complete!"
fi

# Final setup validation
echo ""
echo "🔍 Setup Validation"
echo "=================="

# Check Python installation
if python --version > /dev/null 2>&1; then
    echo "✅ Python: $(python --version)"
else
    echo "❌ Python not found in virtual environment"
fi

# Check key dependencies
echo -n "🔍 Testing bleak import... "
if python -c "import bleak" > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
fi

echo -n "🔍 Testing impact_bridge import... "
if PYTHONPATH=src python -c "import impact_bridge" > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
fi

# Check Bluetooth
echo -n "🔍 Testing Bluetooth adapter... "
if sudo hciconfig hci0 > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
fi

echo ""
echo "🎯 LeadVille Pi Setup Complete!"
echo "==============================="
echo ""
echo "Next Steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Test BLE scanning: sudo hcitool lescan"
echo "3. Run LeadVille: python leadville_bridge.py"
echo ""
echo "Troubleshooting:"
echo "- If BLE fails, try: sudo systemctl restart bluetooth"
echo "- Check logs in: logs/console/"
echo "- View service logs: journalctl -u leadville-bridge -f"
echo ""

# Reminder about device MAC addresses
echo "⚠️  IMPORTANT: Verify MAC addresses in leadville_bridge.py match your devices!"
echo "   AMG Timer: Update AMG_TIMER_MAC if needed"
echo "   BT50 Sensor: Update BT50_SENSOR_MAC if needed"