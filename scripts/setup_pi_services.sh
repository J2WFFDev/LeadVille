#!/bin/bash
set -e

echo "=== LeadVille Pi System Setup Script ==="
echo "Upgrading Node.js and installing systemd services..."

# Check if we're running as the correct user
if [ "$USER" != "jrwest" ]; then
    echo "Error: This script should be run as user 'jrwest'"
    echo "Usage: ssh raspberrypi 'bash -s' < setup_pi_services.sh"
    exit 1
fi

# 1. Install/upgrade Node.js using nvm
echo "Step 1: Installing Node Version Manager (nvm)..."
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
else
    echo "nvm already installed"
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

echo "Step 2: Installing Node.js 20.18.0..."
nvm install 20.18.0
nvm use 20.18.0
nvm alias default 20.18.0

echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# 2. Install frontend dependencies
echo "Step 3: Installing frontend dependencies..."
cd /home/jrwest/projects/LeadVille/frontend
npm install

# 3. Install systemd services (requires sudo)
echo "Step 4: Installing systemd services..."
echo "Note: The following commands require sudo access:"

# Copy service files
sudo cp /home/jrwest/projects/LeadVille/systemd/leadville-fastapi.service /etc/systemd/system/
sudo cp /home/jrwest/projects/LeadVille/systemd/leadville-frontend.service /etc/systemd/system/
sudo cp /home/jrwest/projects/LeadVille/systemd/leadville.target /etc/systemd/system/

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable leadville-bridge.service
sudo systemctl enable leadville-fastapi.service
sudo systemctl enable leadville-frontend.service
sudo systemctl enable leadville.target

echo "Step 5: Testing service configuration..."
sudo systemctl --no-pager status leadville-bridge.service || true
sudo systemctl --no-pager status leadville-fastapi.service || true
sudo systemctl --no-pager status leadville-frontend.service || true

echo "Step 6: Starting services..."
sudo systemctl start leadville.target

# Wait a moment for services to start
sleep 5

echo "Step 7: Verifying services are running..."
echo "=== Service Status ==="
sudo systemctl --no-pager status leadville.target
echo ""
echo "=== Listening Ports ==="
ss -tlnp | grep -E ':(8001|5173|1883)' || echo "No services listening on expected ports yet"
echo ""
echo "=== Process List ==="
ps aux | grep -E '(fastapi|vite|leadville)' | grep -v grep || echo "No matching processes found"

echo ""
echo "=== Setup Complete ==="
echo "FastAPI Backend: http://192.168.1.124:8001/api/health"
echo "Frontend Dev Server: http://192.168.1.124:5173"
echo "WebSocket Logs: ws://192.168.1.124:8001/ws/logs"
echo "WebSocket Live: ws://192.168.1.124:8001/ws/live"
echo ""
echo "To check service logs:"
echo "  sudo journalctl -u leadville-fastapi -f"
echo "  sudo journalctl -u leadville-frontend -f"
echo "  sudo journalctl -u leadville-bridge -f"