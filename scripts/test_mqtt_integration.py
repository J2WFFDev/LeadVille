#!/usr/bin/env python3
"""Test script to demonstrate MQTT integration with LeadVille Impact Bridge."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from impact_bridge.mqtt import MqttClient, MqttTopics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_mqtt_functionality():
    """Test MQTT client functionality."""
    logger.info("Starting MQTT integration test")
    
    # Create MQTT client
    mqtt_client = MqttClient(
        broker_host="localhost",
        broker_port=1883,
        client_id="leadville-test-client",
        enabled=True,
    )
    
    try:
        # Start MQTT client
        await mqtt_client.start()
        
        # Wait for connection
        await asyncio.sleep(2)
        
        if not mqtt_client.is_connected:
            logger.error("MQTT client failed to connect")
            return False
        
        logger.info("MQTT client connected successfully")
        
        # Test 1: Publish bridge status
        logger.info("Test 1: Publishing bridge status")
        bridge_status = {
            "t0_set": False,
            "amg_connected": False,
            "bt50_connected": 0,
            "bt50_total": 1,
            "detector_status": {"active_plates": []},
        }
        
        success = await mqtt_client.publish_status("bridge", bridge_status)
        logger.info(f"Bridge status published: {success}")
        
        # Test 2: Publish sensor telemetry
        logger.info("Test 2: Publishing sensor telemetry")
        telemetry_data = {
            "acceleration": {"x": 1.2, "y": -0.5, "z": 9.8},
            "battery": 85,
            "temperature": 23.5,
            "timestamp_ns": 1234567890000,
        }
        
        success = await mqtt_client.publish_telemetry("BT50_01", telemetry_data)
        logger.info(f"Sensor telemetry published: {success}")
        
        # Test 3: Publish timer event (T0)
        logger.info("Test 3: Publishing timer event")
        timer_event_data = {
            "source": "AMG_Commander",
            "timestamp_ns": 1234567890000,
            "event_type": "START",
        }
        
        success = await mqtt_client.publish_event("T0", timer_event_data)
        logger.info(f"Timer event published: {success}")
        
        # Test 4: Publish impact event
        logger.info("Test 4: Publishing impact event")
        impact_data = {
            "sensor_id": "BT50_01",
            "plate_id": "P1",
            "peak_amplitude": 150.5,
            "duration_ms": 8.2,
            "rms_amplitude": 45.3,
            "timestamp_ns": 1234567890100,
            "t_rel_ms": 526.5,
        }
        
        success = await mqtt_client.publish_event("HIT", impact_data, sensor_id="BT50_01")
        logger.info(f"Impact event published: {success}")
        
        # Test 5: Publish sensor status
        logger.info("Test 5: Publishing sensor status")
        success = await mqtt_client.publish_status("sensor", {
            "sensor_id": "BT50_01",
            "connected": True,
            "calibrated": True,
            "battery": 85,
        })
        logger.info(f"Sensor status published: {success}")
        
        # Show client statistics
        stats = mqtt_client.stats
        logger.info(f"MQTT Client Statistics:")
        logger.info(f"  Messages published: {stats['messages_published']}")
        logger.info(f"  Messages failed: {stats['messages_failed']}")
        logger.info(f"  Connection attempts: {stats['connection_attempts']}")
        
        # Wait a bit to let messages propagate
        await asyncio.sleep(1)
        
        logger.info("All MQTT tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"MQTT test failed: {e}")
        return False
        
    finally:
        # Stop MQTT client
        await mqtt_client.stop()
        logger.info("MQTT client stopped")


async def show_topic_structure():
    """Show the MQTT topic structure."""
    logger.info("LeadVille MQTT Topic Structure:")
    logger.info("=" * 50)
    
    topic_info = MqttTopics.get_topic_info()
    for topic, description in topic_info.items():
        logger.info(f"  {topic}")
        logger.info(f"    {description}")
        logger.info("")
    
    logger.info("Dynamic Topics (examples):")
    logger.info(f"  {MqttTopics.sensor_telemetry('BT50_01')}")
    logger.info(f"  {MqttTopics.sensor_status('BT50_01')}")
    logger.info(f"  {MqttTopics.run_events('RUN_001')}")
    logger.info(f"  {MqttTopics.run_status('RUN_001')}")


async def main():
    """Main test function."""
    logger.info("LeadVille MQTT Integration Test")
    logger.info("=" * 40)
    
    # Show topic structure
    await show_topic_structure()
    
    logger.info("\nStarting functionality tests...")
    logger.info("=" * 40)
    
    # Test MQTT functionality
    success = await test_mqtt_functionality()
    
    if success:
        logger.info("\n✅ All MQTT integration tests passed!")
        logger.info("\nTo monitor messages in real-time, run:")
        logger.info("  mosquitto_sub -h localhost -t 'leadville/#' -v")
        return 0
    else:
        logger.error("\n❌ MQTT integration tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)