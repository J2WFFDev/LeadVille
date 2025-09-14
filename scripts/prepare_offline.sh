#!/bin/bash
# LeadVille Impact Bridge - Offline Installation Preparation Script
# Prepares packages and dependencies for air-gapped/offline Pi deployment

set -e

# Configuration
OFFLINE_DIR="offline_packages"
PYTHON_VERSION="3.9"  # Adjust based on target Pi

echo "🌐 LeadVille Offline Installation Preparation"
echo "============================================"

# Create offline package directory
echo "📦 Creating offline package directory..."
mkdir -p "$OFFLINE_DIR"/{python_wheels,system_packages,resources}

# Download Python wheels
echo "🐍 Downloading Python package wheels..."
pip download -r requirements_pi.txt -d "$OFFLINE_DIR/python_wheels/"

# Download additional API dependencies if present
if [[ -f requirements.txt ]]; then
    pip download -r requirements.txt -d "$OFFLINE_DIR/python_wheels/"
fi

# Create package list for system dependencies
echo "📋 Creating system package list..."
cat > "$OFFLINE_DIR/system_packages/package_list.txt" <<EOF
# Core system packages for LeadVille Pi installation
python3
python3-pip
python3-venv
python3-dev
build-essential
libffi-dev
libssl-dev
bluez
bluez-tools
libbluetooth-dev
libglib2.0-dev
git
curl
wget
nginx
supervisor
systemd-timesyncd
ntp
htop
iotop
logrotate
rsyslog
EOF

# Download system packages (requires apt-offline or similar)
echo "📥 Downloading system packages..."
if command -v apt-offline >/dev/null 2>&1; then
    apt-offline set "$OFFLINE_DIR/system_packages/offline.sig" --install-packages \
        python3 python3-pip python3-venv python3-dev build-essential \
        libffi-dev libssl-dev bluez bluez-tools libbluetooth-dev \
        libglib2.0-dev git curl wget nginx supervisor \
        systemd-timesyncd ntp htop iotop logrotate rsyslog
    
    apt-offline get "$OFFLINE_DIR/system_packages/offline.sig" \
        --bundle "$OFFLINE_DIR/system_packages/packages.zip"
    
    echo "✅ System packages downloaded to packages.zip"
else
    echo "⚠️  apt-offline not available. System packages not downloaded."
    echo "   Install with: sudo apt install apt-offline"
    echo "   Or manually download .deb files for target architecture"
fi

# Copy installation scripts and resources
echo "📋 Copying installation resources..."
cp install_pi.sh "$OFFLINE_DIR/resources/"
cp -r systemd "$OFFLINE_DIR/resources/"
cp -r scripts "$OFFLINE_DIR/resources/"
cp requirements*.txt "$OFFLINE_DIR/resources/"

# Create offline installation script
echo "🛠️  Creating offline installer..."
cat > "$OFFLINE_DIR/install_offline.sh" <<'EOF'
#!/bin/bash
# LeadVille Offline Installation Script
# Run this script on the target Pi with offline packages

set -e

OFFLINE_DIR="$(dirname "$0")"
INSTALL_SCRIPT="$OFFLINE_DIR/resources/install_pi.sh"

echo "🎯 LeadVille Offline Installation"
echo "================================"

# Check if we're on target system
if [[ ! -f /proc/cpuinfo ]] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        exit 1
    fi
fi

# Install system packages if available
if [[ -f "$OFFLINE_DIR/system_packages/packages.zip" ]]; then
    echo "📦 Installing system packages from offline bundle..."
    sudo apt-offline install "$OFFLINE_DIR/system_packages/packages.zip"
else
    echo "⚠️  System packages not available. Install manually:"
    echo "   sudo apt install $(cat $OFFLINE_DIR/system_packages/package_list.txt | grep -v '^#' | tr '\n' ' ')"
    read -p "Press Enter to continue after installing packages..."
fi

# Modify install script to use offline wheels
echo "🔧 Preparing offline Python installation..."
export PIP_FIND_LINKS="$OFFLINE_DIR/python_wheels"
export PIP_NO_INDEX=true

# Copy resources to current directory for installation
cp -r "$OFFLINE_DIR/resources"/* .

# Run the main installer with offline mode
echo "🚀 Running LeadVille installation..."
sudo -E ./install_pi.sh

echo "✅ Offline installation complete!"
EOF

chmod +x "$OFFLINE_DIR/install_offline.sh"

# Create package information
echo "📊 Creating package information..."
cat > "$OFFLINE_DIR/README.md" <<EOF
# LeadVille Offline Installation Package

This package contains all necessary files for offline installation of LeadVille Impact Bridge.

## Contents

- **python_wheels/** - Python package wheels for offline pip installation
- **system_packages/** - System .deb packages and package lists
- **resources/** - Installation scripts and configuration files
- **install_offline.sh** - Main offline installation script

## Installation

1. Transfer this entire directory to your Raspberry Pi
2. On the Pi, run: \`sudo ./install_offline.sh\`
3. Follow the installation prompts

## Requirements

- Raspberry Pi with Raspbian/Raspberry Pi OS
- Root access (sudo)
- At least 1GB free disk space

## Package Information

Generated: $(date)
Python wheels: $(ls -1 "$OFFLINE_DIR/python_wheels" | wc -l) packages
System packages: $(wc -l < "$OFFLINE_DIR/system_packages/package_list.txt") packages
EOF

# Display summary
echo ""
echo "✅ Offline preparation complete!"
echo "================================"
echo ""
echo "Package Summary:"
echo "  Python wheels: $(ls -1 "$OFFLINE_DIR/python_wheels" | wc -l) packages"
echo "  Total size: $(du -sh "$OFFLINE_DIR" | cut -f1)"
echo ""
echo "Transfer Instructions:"
echo "  1. Copy entire '$OFFLINE_DIR' directory to target Pi"
echo "  2. On Pi: cd $OFFLINE_DIR"
echo "  3. On Pi: sudo ./install_offline.sh"
echo ""
echo "Archive for transfer:"
echo "  tar -czf leadville_offline_$(date +%Y%m%d).tar.gz $OFFLINE_DIR"