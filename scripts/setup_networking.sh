#!/bin/bash
# LeadVille Bridge Network Setup Script
# Configures AP mode, captive portal, and nginx reverse proxy

set -e

echo "🌐 Setting up LeadVille Bridge Networking..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Install required packages
echo "📦 Installing network packages..."
apt update
apt install -y hostapd dnsmasq nginx

# Create configuration directories
echo "📁 Creating configuration directories..."
mkdir -p /etc/leadville/network
mkdir -p /var/www/leadville

# Copy configuration files
echo "⚙️ Installing configuration files..."
cp config/network/hostapd.conf /etc/leadville/network/
cp config/network/dnsmasq.conf /etc/leadville/network/
cp config/network/nginx.conf /etc/nginx/sites-available/leadville

# Enable nginx site
echo "🔗 Enabling nginx site..."
ln -sf /etc/nginx/sites-available/leadville /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Configure hostapd service
echo "📡 Configuring hostapd service..."
systemctl unmask hostapd
systemctl disable hostapd  # Don't start by default
systemctl disable dnsmasq  # Don't start by default

# Configure iptables for NAT (if internet sharing needed)
echo "🔥 Configuring iptables..."
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

# Save iptables rules
iptables-save > /etc/iptables.ipv4.nat

# Create restore script
cat > /etc/rc.local << 'EOF'
#!/bin/bash
# Restore iptables rules
iptables-restore < /etc/iptables.ipv4.nat
exit 0
EOF
chmod +x /etc/rc.local

# Copy React frontend to nginx document root
echo "📱 Setting up frontend..."
if [ -d "frontend/dist" ]; then
    cp -r frontend/dist/* /var/www/leadville/
    chown -R www-data:www-data /var/www/leadville
else
    echo "⚠️ Frontend not built yet. Run 'cd frontend && npm run build' first."
fi

# Create network management service
echo "⚙️ Creating network management service..."
cat > /etc/systemd/system/leadville-network.service << 'EOF'
[Unit]
Description=LeadVille Bridge Network Manager
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/jrwest/projects/LeadVille
ExecStart=/usr/bin/python3 /home/jrwest/projects/LeadVille/src/impact_bridge/network_manager.py status
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable services
echo "🚀 Enabling services..."
systemctl daemon-reload
systemctl enable nginx
systemctl start nginx
systemctl enable leadville-network

# Create bridge.local hostname
echo "🏷️ Setting up bridge.local hostname..."
hostnamectl set-hostname bridge
echo "127.0.0.1 bridge.local" >> /etc/hosts

echo "✅ LeadVille Bridge networking setup complete!"
echo ""
echo "📋 Configuration Summary:"
echo "   📡 AP SSID: LeadVille-Bridge"
echo "   🔑 AP Password: leadville2024"
echo "   🌍 AP IP: 192.168.4.1"
echo "   🖥️ Captive Portal: http://bridge.local"
echo "   🔧 FastAPI Backend: http://bridge.local/api"
echo ""
echo "🔄 To switch modes:"
echo "   Online:  python3 src/impact_bridge/network_manager.py online --ssid WIFI_NAME --password WIFI_PASS"
echo "   Offline: python3 src/impact_bridge/network_manager.py offline"
echo "   Status:  python3 src/impact_bridge/network_manager.py status"