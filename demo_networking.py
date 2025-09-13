#!/usr/bin/env python3
"""
Demo script for LeadVille networking modes functionality.
This script demonstrates the network mode switching capabilities without requiring BLE hardware.
"""

import asyncio
import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from impact_bridge.networking import NetworkManager, NetworkMonitor
from impact_bridge.networking.web_server import NetworkWebServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def demo_networking():
    """Demonstrate networking functionality."""
    logger.info("🎯 LeadVille Networking Demo")
    logger.info("=" * 40)
    
    # Initialize networking components
    logger.info("📡 Initializing networking components...")
    network_manager = NetworkManager()
    network_monitor = NetworkMonitor(network_manager, check_interval=5, failure_threshold=2)
    web_server = NetworkWebServer(network_manager, network_monitor)
    
    # Display current status
    logger.info("📊 Current network status:")
    status = network_manager.get_status()
    for key, value in status.items():
        if key != 'timestamp':
            logger.info(f"   {key}: {value}")
    
    # Show monitoring status
    logger.info("🔍 Network monitoring status:")
    monitor_status = network_monitor.get_monitoring_status()
    for key, value in monitor_status.items():
        if key != 'timestamp':
            logger.info(f"   {key}: {value}")
    
    # Start monitoring
    logger.info("🚀 Starting network monitoring...")
    await network_monitor.start_monitoring()
    
    # Simulate running for a short time
    logger.info("⏱️  Running for 10 seconds to demonstrate monitoring...")
    await asyncio.sleep(10)
    
    # Stop monitoring
    logger.info("🛑 Stopping network monitoring...")
    await network_monitor.stop_monitoring()
    
    logger.info("✅ Demo completed successfully!")
    logger.info("")
    logger.info("🌐 To access the web interface:")
    logger.info("   1. Run: python -m impact_bridge.networking.network_service")
    logger.info("   2. Open browser to: http://localhost:5000")
    logger.info("   3. Use the web interface to switch network modes")
    logger.info("")
    logger.info("📡 Available API endpoints:")
    logger.info("   GET  /api/network/status        - Get network status")
    logger.info("   POST /api/network/mode          - Switch network mode")
    logger.info("   GET  /api/network/scan          - Scan for WiFi networks")
    logger.info("   GET  /api/network/connectivity  - Check internet connectivity")


if __name__ == '__main__':
    try:
        asyncio.run(demo_networking())
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo error: {e}")
        sys.exit(1)