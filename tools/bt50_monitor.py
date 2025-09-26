#!/usr/bin/env python3
"""
BT50 Notification Monitor
Simple tool to connect to BT50 and monitor all notifications to understand the protocol
"""

import asyncio
import logging
import sys
from datetime import datetime

try:
    from bleak import BleakClient
except ImportError:
    print("Error: bleak library not found. Install with: pip install bleak")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BT50Monitor:
    def __init__(self, address: str):
        self.address = address
        self.notification_count = 0
        
    async def monitor(self, duration: int = 30):
        """Monitor BT50 notifications for specified duration"""
        logger.info(f"Connecting to BT50 at {self.address}...")
        
        try:
            async with BleakClient(self.address, timeout=10.0) as client:
                logger.info(f"✅ Connected to {self.address}")
                
                # List all services and characteristics (handle different bleak versions)
                try:
                    if hasattr(client, 'get_services'):
                        services = await client.get_services()
                    elif hasattr(client, 'services'):
                        services = client.services
                    else:
                        # Fallback - just connect and access services
                        services = client.services
                    
                    logger.info(f"Found {len(services)} services:")
                    
                    for service in services:
                        logger.info(f"  Service: {service.uuid}")
                        for char in service.characteristics:
                            props = [p for p in char.properties]
                            logger.info(f"    Char: {char.uuid} - Properties: {props}")
                except Exception as e:
                    logger.warning(f"Service enumeration failed: {e}")
                
                # Set up notification handler
                def notification_handler(sender, data):
                    self.notification_count += 1
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    logger.info(f"[{timestamp}] Notification #{self.notification_count} from {sender}:")
                    logger.info(f"  Raw data: {data.hex()}")
                    logger.info(f"  Length: {len(data)} bytes")
                    
                    # Parse potential multi-frame notifications
                    offset = 0
                    frame_count = 0
                    while offset < len(data) - 1:
                        if data[offset] == 0x55:
                            frame_count += 1
                            frame_type = data[offset + 1] if offset + 1 < len(data) else 0
                            logger.info(f"  Frame {frame_count}: Header 0x{data[offset]:02x} 0x{frame_type:02x}")
                            
                            if frame_type == 0x61:
                                logger.info("    -> Acceleration data frame")
                                # Acceleration frames are typically 20 bytes
                                offset += 20 if offset + 20 <= len(data) else len(data) - offset
                            elif frame_type == 0x64:
                                logger.info("    -> Battery voltage frame (Type 1)")
                                if offset + 4 < len(data):
                                    voltage_raw = int.from_bytes(data[offset+2:offset+4], byteorder='little')
                                    voltage_v = voltage_raw / 100.0
                                    logger.info(f"    -> Voltage: {voltage_v:.2f}V")
                                offset += 20 if offset + 20 <= len(data) else len(data) - offset
                            elif frame_type == 0x71:
                                logger.info("    -> Battery/Status frame (Type 2)")
                                if offset + 8 < len(data):
                                    # Look for voltage data in next few bytes
                                    for i in range(2, min(10, len(data) - offset - 1)):
                                        if offset + i + 1 < len(data):
                                            voltage_raw = int.from_bytes(data[offset+i:offset+i+2], byteorder='little')
                                            voltage_v = voltage_raw / 100.0
                                            if 3.0 <= voltage_v <= 5.0:  # Reasonable battery voltage range
                                                logger.info(f"    -> Potential voltage at offset {i}: {voltage_v:.2f}V")
                                # Search for next frame or end
                                next_frame = -1
                                for i in range(offset + 2, len(data)):
                                    if data[i] == 0x55:
                                        next_frame = i
                                        break
                                if next_frame > 0:
                                    offset = next_frame
                                else:
                                    offset = len(data)
                            else:
                                logger.info(f"    -> Unknown frame type: 0x{frame_type:02x}")
                                # Skip to next 0x55 or end
                                next_frame = -1
                                for i in range(offset + 1, len(data)):
                                    if data[i] == 0x55:
                                        next_frame = i
                                        break
                                if next_frame > 0:
                                    offset = next_frame
                                else:
                                    offset = len(data)
                        else:
                            offset += 1
                    
                    logger.info("")
                
                # Enable notifications on data characteristic
                data_uuid = "0000ffe4-0000-1000-8000-00805f9a34fb"
                config_uuid = "0000ffe9-0000-1000-8000-00805f9a34fb"
                
                await client.start_notify(data_uuid, notification_handler)
                logger.info(f"✅ Notifications enabled on {data_uuid}")
                
                # Send battery query command
                battery_cmd = bytes([0xFF, 0xAA, 0x27, 0x64, 0x00])
                logger.info(f"Sending battery command: {battery_cmd.hex()}")
                await client.write_gatt_char(config_uuid, battery_cmd)
                
                # Monitor for specified duration
                logger.info(f"Monitoring notifications for {duration} seconds...")
                logger.info("Press Ctrl+C to stop early")
                
                try:
                    await asyncio.sleep(duration)
                except KeyboardInterrupt:
                    logger.info("Monitoring stopped by user")
                
                await client.stop_notify(data_uuid)
                
                logger.info(f"✅ Monitoring complete. Received {self.notification_count} notifications")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bt50_monitor.py <BT50_ADDRESS> [DURATION_SECONDS]")
        print("Example: python3 bt50_monitor.py EA:18:3D:6D:BA:E5 30")
        sys.exit(1)
    
    address = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    monitor = BT50Monitor(address)
    await monitor.monitor(duration)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")