#!/bin/bash
# Setup script for MQTT broker and monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up MQTT broker for LeadVille Impact Bridge${NC}"

# Check if running as root for system setup
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}Running as root - configuring system-wide MQTT broker${NC}"
    
    # Create mosquitto directories
    mkdir -p /var/lib/mosquitto/
    mkdir -p /var/log/mosquitto/
    mkdir -p /etc/mosquitto/conf.d/
    
    # Set permissions
    chown -R mosquitto:mosquitto /var/lib/mosquitto/
    chown -R mosquitto:mosquitto /var/log/mosquitto/
    
    # Copy configuration
    cp config/mosquitto.conf /etc/mosquitto/conf.d/leadville.conf
    
    # Enable and start mosquitto service
    systemctl enable mosquitto
    systemctl restart mosquitto
    
    echo -e "${GREEN}System MQTT broker configured successfully${NC}"
    
else
    echo -e "${YELLOW}Running as user - starting local MQTT broker${NC}"
    
    # Check if mosquitto is installed
    if ! command -v mosquitto &> /dev/null; then
        echo -e "${RED}mosquitto is not installed. Please install it first:${NC}"
        echo "sudo apt-get install mosquitto mosquitto-clients"
        exit 1
    fi
    
    # Create local directories
    mkdir -p ./mqtt_data/persistence
    mkdir -p ./mqtt_data/logs
    
    # Start mosquitto in background with local config
    echo "Starting local MQTT broker..."
    mosquitto -c config/mosquitto.conf -d
    
    echo -e "${GREEN}Local MQTT broker started${NC}"
fi

# Test MQTT broker connection
echo -e "${YELLOW}Testing MQTT broker connection...${NC}"
sleep 2

# Test publish/subscribe
if command -v mosquitto_pub &> /dev/null && command -v mosquitto_sub &> /dev/null; then
    # Start subscriber in background
    timeout 5 mosquitto_sub -h localhost -t "leadville/test" > /tmp/mqtt_test.txt &
    sleep 1
    
    # Publish test message
    mosquitto_pub -h localhost -t "leadville/test" -m "MQTT broker test successful"
    sleep 1
    
    # Check if message was received
    if grep -q "MQTT broker test successful" /tmp/mqtt_test.txt 2>/dev/null; then
        echo -e "${GREEN}✓ MQTT broker is working correctly${NC}"
    else
        echo -e "${RED}✗ MQTT broker test failed${NC}"
        exit 1
    fi
    
    # Cleanup
    rm -f /tmp/mqtt_test.txt
else
    echo -e "${YELLOW}mosquitto-clients not available for testing${NC}"
fi

echo -e "${GREEN}MQTT setup complete!${NC}"
echo ""
echo "MQTT Topics configured for LeadVille:"
echo "  • leadville/bridge/status - Bridge system status"
echo "  • leadville/sensor/{id}/telemetry - Sensor data streams"
echo "  • leadville/timer/events - Timer event notifications"
echo "  • leadville/run/{id}/events - Run-specific events"
echo "  • leadville/detection/impacts - Impact detection events"
echo "  • leadville/detection/shots - Shot detection events"
echo ""
echo "To monitor all LeadVille messages:"
echo "  mosquitto_sub -h localhost -t 'leadville/#' -v"