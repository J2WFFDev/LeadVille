#!/bin/bash
# LeadVille Bridge - Network Setup Script
# Installs and configures networking components

set -e

echo "🌐 LeadVille Bridge - Network Setup"
echo "=================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "📦 Installing networking packages..."

# Install hostapd and dnsmasq
apt update
apt install -y hostapd dnsmasq nginx

# Install additional network tools
apt install -y wireless-tools wpasupplicant dhcpcd5

echo "🔧 Configuring network services..."

# Stop services during configuration
systemctl stop hostapd
systemctl stop dnsmasq
systemctl stop nginx

# Backup original configurations
cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup 2>/dev/null || true
cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup 2>/dev/null || true

# Copy LeadVille configurations
echo "📋 Installing LeadVille network configurations..."

cp "$PROJECT_DIR/config/network/hostapd.conf" /etc/hostapd/hostapd.conf
cp "$PROJECT_DIR/config/network/dnsmasq.conf" /etc/dnsmasq.conf
cp "$PROJECT_DIR/config/network/nginx.conf" /etc/nginx/sites-available/leadville

# Enable nginx site
ln -sf /etc/nginx/sites-available/leadville /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Configure hostapd daemon
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd

# Create network management directories
mkdir -p /etc/leadville/network
mkdir -p /var/log/leadville

# Set up iptables rules for AP mode
echo "🔥 Configuring firewall rules..."

# Create iptables rules script
cat > /etc/leadville/network/iptables-ap.sh << 'EOF'
#!/bin/bash
# iptables rules for AP mode

# Clear existing rules
iptables -F
iptables -t nat -F
iptables -t mangle -F

# Set default policies
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (important!)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow DHCP
iptables -A INPUT -p udp --dport 67:68 -j ACCEPT

# Allow DNS
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

# NAT for internet sharing (if eth0 available)
if ip link show eth0 > /dev/null 2>&1; then
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
fi

# Save rules
iptables-save > /etc/iptables/rules.v4
EOF

chmod +x /etc/leadville/network/iptables-ap.sh

# Create iptables rules script for client mode
cat > /etc/leadville/network/iptables-client.sh << 'EOF'
#!/bin/bash
# iptables rules for client mode (minimal)

# Clear existing rules
iptables -F
iptables -t nat -F
iptables -t mangle -F

# Set default policies
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Save rules
iptables-save > /etc/iptables/rules.v4
EOF

chmod +x /etc/leadville/network/iptables-client.sh

# Install iptables-persistent to restore rules on boot
apt install -y iptables-persistent

# Create network mode switching scripts
echo "🔄 Creating network mode switching scripts..."

cat > /etc/leadville/network/switch-to-ap.sh << 'EOF'
#!/bin/bash
# Switch to AP mode

echo "Switching to AP mode..."

# Stop client mode services
systemctl stop wpa_supplicant
systemctl stop dhcpcd

# Configure wlan0 interface
ip addr flush dev wlan0
ip addr add 192.168.4.1/24 dev wlan0

# Apply AP firewall rules
/etc/leadville/network/iptables-ap.sh

# Start AP services
systemctl start hostapd
systemctl start dnsmasq
systemctl start nginx

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

echo "Switched to AP mode successfully"
EOF

cat > /etc/leadville/network/switch-to-client.sh << 'EOF'
#!/bin/bash
# Switch to client mode

echo "Switching to client mode..."

# Stop AP services
systemctl stop hostapd
systemctl stop dnsmasq

# Flush interface
ip addr flush dev wlan0

# Apply client firewall rules
/etc/leadville/network/iptables-client.sh

# Start client services
systemctl start wpa_supplicant
systemctl start dhcpcd

# Start nginx (for web interface)
systemctl start nginx

echo "Switched to client mode successfully"
EOF

chmod +x /etc/leadville/network/switch-to-ap.sh
chmod +x /etc/leadville/network/switch-to-client.sh

# Create systemd service for network management
echo "🚀 Creating network management service..."

cat > /etc/systemd/system/leadville-network.service << EOF
[Unit]
Description=LeadVille Network Management
After=network.target bluetooth.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=PYTHONPATH=$PROJECT_DIR/src
ExecStart=$PROJECT_DIR/venv/bin/python -m impact_bridge.networking.network_service
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Set proper permissions
chown -R pi:pi /etc/leadville
chmod 755 /etc/leadville/network/*.sh

# Enable services but don't start them yet
systemctl daemon-reload
systemctl enable leadville-network

echo ""
echo "✅ Network setup complete!"
echo ""
echo "Available commands:"
echo "  sudo /etc/leadville/network/switch-to-ap.sh     - Switch to AP mode"
echo "  sudo /etc/leadville/network/switch-to-client.sh - Switch to client mode"
echo "  sudo systemctl start leadville-network          - Start network service"
echo "  sudo systemctl status leadville-network         - Check service status"
echo ""
echo "⚠️  Important notes:"
echo "  - Default AP SSID: LeadVille-Bridge"
echo "  - Default AP password: leadville2024"
echo "  - Bridge interface: http://bridge.local or http://192.168.4.1"
echo "  - Reboot recommended to ensure all services start properly"