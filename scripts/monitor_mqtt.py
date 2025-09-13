#!/usr/bin/env python3
"""MQTT message monitor for LeadVille Impact Bridge."""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiomqtt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MqttMonitor:
    """Monitor all LeadVille MQTT messages."""
    
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.stop_requested = False
        self.message_count = 0
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, stopping monitor...")
        self.stop_requested = True
    
    def _format_message(self, topic: str, payload: str) -> str:
        """Format an MQTT message for display."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Try to parse JSON payload for pretty printing
        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                # Format common fields nicely
                formatted_data = {}
                for key, value in data.items():
                    if key == "timestamp" and isinstance(value, str):
                        # Convert ISO timestamp to readable format
                        try:
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            formatted_data[key] = dt.strftime("%H:%M:%S.%f")[:-3]
                        except:
                            formatted_data[key] = value
                    else:
                        formatted_data[key] = value
                
                payload_str = json.dumps(formatted_data, indent=2)
            else:
                payload_str = json.dumps(data, indent=2)
        except json.JSONDecodeError:
            payload_str = payload
        
        return f"[{timestamp}] {topic}\n{payload_str}\n"
    
    def _categorize_topic(self, topic: str) -> str:
        """Categorize topic for color coding."""
        if "/status" in topic:
            return "STATUS"
        elif "/events" in topic:
            return "EVENT"
        elif "/telemetry" in topic:
            return "TELEMETRY"
        elif "/detection/" in topic:
            return "DETECTION"
        else:
            return "OTHER"
    
    async def monitor(self):
        """Monitor all LeadVille MQTT messages."""
        logger.info(f"Starting MQTT monitor for LeadVille Impact Bridge")
        logger.info(f"Connecting to broker: {self.broker_host}:{self.broker_port}")
        logger.info("Monitoring topics: leadville/#")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 80)
        
        try:
            async with aiomqtt.Client(hostname=self.broker_host, port=self.broker_port) as client:
                await client.subscribe("leadville/#")
                
                logger.info("✅ Connected and subscribed to leadville/#")
                logger.info("Waiting for messages...\n")
                
                async for message in client.messages:
                    if self.stop_requested:
                        break
                    
                    self.message_count += 1
                    topic = str(message.topic)
                    payload = message.payload.decode()
                    category = self._categorize_topic(topic)
                    
                    # Format and display message
                    formatted_msg = self._format_message(topic, payload)
                    
                    # Add visual separator for different message types
                    if category == "STATUS":
                        print(f"📊 {formatted_msg}")
                    elif category == "EVENT":
                        print(f"⚡ {formatted_msg}")
                    elif category == "TELEMETRY":
                        print(f"📡 {formatted_msg}")
                    elif category == "DETECTION":
                        print(f"🎯 {formatted_msg}")
                    else:
                        print(f"📨 {formatted_msg}")
                    
                    print("-" * 80)
                
        except KeyboardInterrupt:
            logger.info("Monitor interrupted by user")
        except Exception as e:
            logger.error(f"Monitor error: {e}")
        finally:
            logger.info(f"Monitor stopped. Total messages received: {self.message_count}")


async def main():
    """Main monitor function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor LeadVille MQTT messages")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--quiet", action="store_true", help="Reduce logging output")
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    monitor = MqttMonitor(args.host, args.port)
    await monitor.monitor()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor stopped by user")
        sys.exit(0)