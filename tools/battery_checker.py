#!/usr/bin/env python3
"""
Battery Status Checker Tool
Standalone tool to test BLE battery reading from BT50 devices
"""

import asyncio
import logging
import json
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    from bleak import BleakScanner, BleakClient
    from bleak.backends.device import BLEDevice
except ImportError:
    print("Error: bleak library not found. Install with: pip install bleak")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatteryChecker:
    """Tool for checking battery status of BLE devices"""
    
    def __init__(self):
        self.target_devices = [
            "EA:18:3D:6D:BA:E5",  # BT50 Device 1
            "DB:10:38:B6:13:6B",  # BT50 Device 2  
            "C2:1B:DB:F0:55:50",  # BT50 Device 3
        ]
    
    async def discover_all_devices(self, duration: int = 15) -> List[BLEDevice]:
        """Discover all BLE devices in range"""
        logger.info(f"🔍 Scanning for ALL BLE devices for {duration} seconds...")
        
        devices = await BleakScanner.discover(timeout=duration)
        logger.info(f"Found {len(devices)} total devices:")
        
        known_devices = ['EA:18:3D:6D:BA:E5', 'C2:1B:DB:F0:55:50', '60:09:C3:1F:DC:1A', 'DB:10:38:B6:13:6B']
        
        for device in devices:
            status = "⭐ KNOWN" if device.address in known_devices else "   "
            logger.info(f"  {status} {device.address}: {device.name or '(Unknown)'} [RSSI: {device.rssi}dBm]")
        
        # Check for your specific devices
        logger.info(f"\n🎯 Checking for your specific devices:")
        for addr in known_devices:
            found = any(d.address == addr for d in devices)
            logger.info(f"  {addr}: {'✅ FOUND' if found else '❌ NOT FOUND'}")
        
        return devices

    async def discover_bt50_devices(self, duration: int = 5) -> List[BLEDevice]:
        """Discover BT50 devices in range"""
        logger.info(f"Scanning for BT50 devices for {duration} seconds...")
        
        devices = await BleakScanner.discover(timeout=duration)
        bt50_devices = []
        
        for device in devices:
            if device.name and 'BT50' in device.name:
                bt50_devices.append(device)
                logger.info(f"Found BT50: {device.name} ({device.address})")
        
        return bt50_devices
    
    async def read_device_battery(self, address: str) -> Dict[str, Any]:
        """Read battery level from a specific device"""
        logger.info(f"Attempting to connect to {address}...")
        
        result = {
            'address': address,
            'timestamp': datetime.now().isoformat(),
            'connected': False,
            'battery_level': None,
            'services': [],
            'error': None
        }
        
        try:
            async with BleakClient(address, timeout=10.0) as client:
                logger.info(f"✅ Connected to {address}")
                result['connected'] = True
                
                # Get services (handle different bleak versions)
                try:
                    if hasattr(client, 'get_services'):
                        services = await client.get_services()
                    elif hasattr(client, 'services'):
                        services = client.services
                    else:
                        # Trigger service discovery
                        await client.connect()
                        services = client.services
                    
                    result['services'] = [str(service.uuid) for service in services] if services else []
                    logger.info(f"Found {len(result['services'])} services")
                except Exception as service_e:
                    logger.warning(f"Service discovery failed: {service_e}")
                    result['services'] = []
                
                # Try to read battery level
                battery_level = await self._read_battery_level(client)
                if battery_level is not None:
                    result['battery_level'] = battery_level
                    logger.info(f"🔋 Battery Level: {battery_level}%")
                else:
                    logger.warning("❌ No battery service found")
                
                # List all services for debugging
                logger.info("Available services:")
                try:
                    if hasattr(client, 'get_services'):
                        services = await client.get_services()
                    elif hasattr(client, 'services'):
                        services = client.services
                    else:
                        services = []
                        
                    for service in services:
                        logger.info(f"  - {service.uuid}: {service.description}")
                        for char in service.characteristics:
                            logger.info(f"    - {char.uuid}: {char.description}")
                except Exception as debug_e:
                    logger.warning(f"Service debugging failed: {debug_e}")
                
        except asyncio.TimeoutError:
            result['error'] = 'Connection timeout'
            logger.error(f"❌ Connection timeout for {address}")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Connection failed for {address}: {e}")
        
        return result
    
    async def _read_battery_level(self, client: BleakClient) -> Optional[int]:
        """Read battery level from BLE device using WitMotion BT50 protocol"""
        # Standard Battery Service UUID
        BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
        BATTERY_LEVEL_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
        
        # WitMotion BT50 specific UUIDs
        WITMOTION_SERVICE_UUID = "0000ffe5-0000-1000-8000-00805f9a34fb"
        WITMOTION_CONFIG_UUID = "0000ffe9-0000-1000-8000-00805f9a34fb"
        WITMOTION_DATA_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"
        
        try:
            # Method 1: Try standard battery service first
            try:
                battery_data = await client.read_gatt_char(BATTERY_LEVEL_CHAR_UUID)
                if battery_data and len(battery_data) > 0:
                    battery_level = int(battery_data[0])
                    logger.info(f"✅ Standard battery service: {battery_level}%")
                    return battery_level
            except Exception as e:
                logger.debug(f"Standard battery service failed: {e}")
            
            # Method 2: Use WitMotion protocol with notifications
            battery_response = None
            notification_received = asyncio.Event()
            
            def notification_handler(sender, data):
                nonlocal battery_response
                logger.debug(f"Notification from {sender}: {data.hex()}")
                
                # Parse multi-frame notifications to find battery data
                offset = 0
                while offset < len(data) - 3:
                    if data[offset] == 0x55:
                        frame_type = data[offset + 1]
                        if frame_type == 0x71 and offset + 5 < len(data):
                            # Found battery/status frame: 55 71 64 00 [voltage_low] [voltage_high] ...
                            if data[offset + 2] == 0x64 and data[offset + 3] == 0x00:
                                battery_response = data[offset:offset + 20]  # Extract this frame
                                notification_received.set()
                                logger.debug(f"✅ Battery frame found: {battery_response.hex()}")
                                return
                        elif frame_type == 0x64 and offset + 5 < len(data):
                            # Original format: 55 64 [voltage_low] [voltage_high]
                            battery_response = data[offset:offset + 20]
                            notification_received.set()
                            logger.debug(f"✅ Battery response received: {battery_response.hex()}")
                            return
                    offset += 1
            
            try:
                # Enable notifications on the data characteristic
                await client.start_notify(WITMOTION_DATA_UUID, notification_handler)
                logger.debug("✅ Notifications enabled")
                
                # Send battery voltage query command
                battery_cmd = bytes([0xFF, 0xAA, 0x27, 0x64, 0x00])  # Get battery voltage
                logger.debug(f"Sending battery command: {battery_cmd.hex()}")
                await client.write_gatt_char(WITMOTION_CONFIG_UUID, battery_cmd)
                
                # Wait for response (up to 3 seconds)
                try:
                    await asyncio.wait_for(notification_received.wait(), timeout=3.0)
                    
                    if battery_response and len(battery_response) >= 6:
                        # Parse WitMotion battery response
                        if battery_response[0] == 0x55 and battery_response[1] == 0x71:
                            # Format: 0x55 0x71 0x64 0x00 [voltage_low] [voltage_high] ...
                            voltage_raw = int.from_bytes(battery_response[4:6], byteorder='little', signed=False)
                            voltage_v = voltage_raw / 100.0  # Convert to volts
                            
                            # Convert voltage to battery percentage
                            # WitMotion BT50 typical range: 3.0V (0%) to 4.2V (100%)
                            min_voltage = 3.0
                            max_voltage = 4.2
                            battery_pct = int(((voltage_v - min_voltage) / (max_voltage - min_voltage)) * 100)
                            battery_pct = max(0, min(100, battery_pct))  # Clamp to 0-100%
                            
                            logger.info(f"✅ WitMotion battery: {battery_pct}% ({voltage_v:.2f}V)")
                            return battery_pct
                        elif battery_response[0] == 0x55 and battery_response[1] == 0x64:
                            # Original format: 0x55 0x64 [voltage_low] [voltage_high] [checksum]
                            voltage_raw = int.from_bytes(battery_response[2:4], byteorder='little', signed=False)
                            voltage_v = voltage_raw / 100.0  # Convert to volts
                            
                            min_voltage = 3.0
                            max_voltage = 4.2
                            battery_pct = int(((voltage_v - min_voltage) / (max_voltage - min_voltage)) * 100)
                            battery_pct = max(0, min(100, battery_pct))  # Clamp to 0-100%
                            
                            logger.info(f"✅ WitMotion battery: {battery_pct}% ({voltage_v:.2f}V)")
                            return battery_pct
                    else:
                        logger.warning("Invalid or missing battery response")
                        
                except asyncio.TimeoutError:
                    logger.warning("Battery query timeout - no response received")
                    
                finally:
                    # Clean up notifications
                    await client.stop_notify(WITMOTION_DATA_UUID)
                    
            except Exception as e:
                logger.debug(f"WitMotion notification method failed: {e}")
            
            # Method 3: Try direct read approach (fallback)
            try:
                # Some devices may support direct characteristic reads
                battery_cmd = bytes([0xFF, 0xAA, 0x27, 0x64, 0x00])
                await client.write_gatt_char(WITMOTION_CONFIG_UUID, battery_cmd)
                await asyncio.sleep(0.5)  # Longer wait for response
                
                response = await client.read_gatt_char(WITMOTION_DATA_UUID)
                if response and len(response) >= 4 and response[0] == 0x55 and response[1] == 0x64:
                    voltage_raw = int.from_bytes(response[2:4], byteorder='little', signed=False)
                    voltage_v = voltage_raw / 100.0
                    
                    min_voltage = 3.0
                    max_voltage = 4.2
                    battery_pct = int(((voltage_v - min_voltage) / (max_voltage - min_voltage)) * 100)
                    battery_pct = max(0, min(100, battery_pct))
                    
                    logger.info(f"✅ WitMotion battery (direct read): {battery_pct}% ({voltage_v:.2f}V)")
                    return battery_pct
                else:
                    logger.debug(f"Direct read response: {response.hex() if response else 'None'}")
                    
            except Exception as e:
                logger.debug(f"WitMotion direct read failed: {e}")
            
            # Method 4: Debug - examine all readable characteristics
            logger.debug("Examining all characteristics for debugging...")
            try:
                if hasattr(client, 'get_services'):
                    services = await client.get_services()
                elif hasattr(client, 'services'):
                    services = client.services
                else:
                    services = []
                
                for service in services:
                    logger.debug(f"Service: {service.uuid}")
                    for char in service.characteristics:
                        if "read" in char.properties:
                            try:
                                char_data = await client.read_gatt_char(char.uuid)
                                logger.debug(f"  {char.uuid}: {char_data.hex()} ({len(char_data)} bytes)")
                            except Exception:
                                pass
                                
            except Exception as service_e:
                logger.debug(f"Service debug failed: {service_e}")
                
        except Exception as e:
            logger.error(f"Battery read failed: {e}")
        
        return None
    
    async def scan_all_devices(self) -> List[Dict[str, Any]]:
        """Scan all target devices for battery status"""
        results = []
        
        for address in self.target_devices:
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing device: {address}")
            logger.info(f"{'='*50}")
            
            result = await self.read_device_battery(address)
            results.append(result)
            
            # Add delay between devices to avoid BLE conflicts
            await asyncio.sleep(2)
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print summary of all results"""
        print(f"\n{'='*60}")
        print("BATTERY STATUS SUMMARY")
        print(f"{'='*60}")
        
        for result in results:
            status = "✅ CONNECTED" if result['connected'] else "❌ FAILED"
            battery = f"{result['battery_level']}%" if result['battery_level'] is not None else "Unknown"
            error = f" ({result['error']})" if result['error'] else ""
            
            print(f"{result['address']}: {status}")
            print(f"  Battery: {battery}")
            print(f"  Services: {len(result['services'])}")
            if error:
                print(f"  Error: {result['error']}")
            print()

async def main():
    """Main test function"""
    print("🔋 BT50 Battery Status Checker")
    print("=" * 40)
    
    checker = BatteryChecker()
    
    if len(sys.argv) > 1:
        # Check for scan mode
        if sys.argv[1] == "--scan":
            print("🔍 Scanning for all BLE devices...")
            devices = await checker.discover_all_devices(duration=15)
            print(f"\n✅ Scan complete. Found {len(devices)} total devices.")
            return
        
        # Test specific device
        address = sys.argv[1]
        print(f"Testing single device: {address}")
        result = await checker.read_device_battery(address)
        checker.print_summary([result])
    else:
        # Test all known devices
        print("Testing all known BT50 devices...")
        results = await checker.scan_all_devices()
        checker.print_summary(results)
        
        # Save results to file
        output_file = f"battery_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📄 Results saved to: {output_file}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")