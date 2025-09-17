#!/bin/bash
# Quick deployment script for LeadVille Pi services
set -e

echo "=== Quick Pi Service Deployment ==="

# Test connectivity first
echo "Testing Pi connectivity..."
if ! ping -c 1 192.168.1.124 > /dev/null 2>&1; then
    echo "Error: Cannot reach Pi at 192.168.1.124"
    echo "Please check network connectivity and try again"
    exit 1
fi

# Copy files to Pi
echo "Copying service files to Pi..."
scp systemd/*.service systemd/*.target raspberrypi:/tmp/
scp scripts/setup_pi_services.sh raspberrypi:/tmp/

# Run setup script on Pi
echo "Running setup script on Pi..."
ssh raspberrypi "chmod +x /tmp/setup_pi_services.sh && /tmp/setup_pi_services.sh"

echo "Deployment complete!"
echo ""
echo "Services should now be available at:"
echo "  FastAPI: http://192.168.1.124:8001/api/health"
echo "  Frontend: http://192.168.1.124:5173"
echo "  WebSocket: ws://192.168.1.124:8001/ws/live"