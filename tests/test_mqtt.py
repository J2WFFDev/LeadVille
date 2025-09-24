#!/usr/bin/env python3
"""
MQTT Message Bus Test Script for LeadVille Impact Bridge

Tests MQTT broker connectivity and basic pub/sub functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from impact_bridge.mqtt_client import LeadVilleMQTT, MQTTConfig, init_mqtt


def message_handler(topic: str, data):
    """Handle incoming MQTT messages"""
    print(f"📨 Received: {topic} -> {data}")


async def test_mqtt():
    """Test MQTT functionality"""
    print("🚀 Testing LeadVille MQTT Message Bus")
    print("=" * 50)
    
    # Initialize MQTT client
    config = MQTTConfig(client_id="leadville-test")
    client = await init_mqtt(config)
    
    if not client.connected:
        print("❌ Failed to connect to MQTT broker")
        return False
    
    # Test subscriptions
    print("\n📡 Setting up subscriptions...")
    client.subscribe('bridge/status', message_handler)
    client.subscribe('timer/events', message_handler)
    client.subscribe('sensor/+/telemetry', message_handler)
    
    # Wait a moment for subscriptions to be established
    await asyncio.sleep(1)
    
    # Test publishing
    print("\n📤 Publishing test messages...")
    
    # Test bridge status
    client.publish_bridge_status({
        'status': 'online',
        'node_name': 'pi-leadville-test',
        'services': ['ble', 'database', 'mqtt'],
        'uptime': 3600
    })
    
    # Test timer events
    client.publish_timer_event('START', {
        'sequence': 1,
        'raw_data': 'AMG Timer Start'
    })
    
    client.publish_timer_event('SHOT', {
        'sequence': 2,
        'shot_number': 1,
        'raw_data': 'AMG Timer Shot #1'
    })
    
    # Test sensor telemetry
    client.publish_sensor_telemetry('BT50-001', {
        'magnitude': 194.9,
        'raw_value': 1900.0,
        'battery': 85,
        'rssi': -45
    })
    
    client.publish_sensor_telemetry('BT50-002', {
        'magnitude': 156.2,
        'raw_value': 1850.0,
        'battery': 78,
        'rssi': -52
    })
    
    # Test run events
    client.publish_run_event(1, 'RUN_STARTED', {
        'shooter': 'Test Shooter',
        'stage': 'Stage 1'
    })
    
    # Wait for messages to be processed
    print("\n⏳ Waiting for messages...")
    await asyncio.sleep(2)
    
    # Test health status
    print("\n🏥 MQTT Health Status:")
    health = client.get_health_status()
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    # Cleanup
    client.disconnect()
    print("\n✅ MQTT test completed successfully!")
    return True


async def monitor_mode():
    """Monitor MQTT messages continuously"""
    print("🔍 MQTT Monitor Mode - Press Ctrl+C to exit")
    print("=" * 50)
    
    config = MQTTConfig(client_id="leadville-monitor")
    client = await init_mqtt(config)
    
    if not client.connected:
        print("❌ Failed to connect to MQTT broker")
        return
    
    # Subscribe to all LeadVille topics
    topics = [
        'bridge/status',
        'timer/events',
        'sensor/+/telemetry',
        'run/+/events',
        'system/health',
        'device/+/status'
    ]
    
    for topic in topics:
        client.subscribe(topic, message_handler)
    
    try:
        print(f"📡 Monitoring {len(topics)} topic patterns...")
        print("Waiting for messages...\n")
        
        # Keep monitoring
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Stopping monitor...")
        client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        asyncio.run(monitor_mode())
    else:
        asyncio.run(test_mqtt())