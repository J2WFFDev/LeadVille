#!/usr/bin/env python3
"""
Battery Refresh Integration Script
Updates device battery levels in the LeadVille database using our working battery checker
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from bleak import BleakClient
    from tools.battery_checker import BatteryChecker
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the LeadVille project directory")
    sys.exit(1)

class BatteryRefreshService:
    """Service to refresh battery levels for devices in the pool"""
    
    def __init__(self):
        self.api_base = "http://localhost:8001"
        self.bt50_devices = [
            "EA:18:3D:6D:BA:E5",  # BT50 Device 1
            "DB:10:38:B6:13:6B",  # BT50 Device 2  
            "C2:1B:DB:F0:55:50",  # BT50 Device 3
        ]

    async def read_device_battery(self, mac_address: str) -> int:
        """Read battery level from a BT50 device using WitMotion protocol"""
        WITMOTION_CONFIG_UUID = "0000ffe9-0000-1000-8000-00805f9a34fb"
        WITMOTION_DATA_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"
        
        battery_response = None
        notification_received = asyncio.Event()
        
        def notification_handler(sender, data):
            nonlocal battery_response
            # Parse multi-frame notifications to find battery data
            offset = 0
            while offset < len(data) - 3:
                if data[offset] == 0x55:
                    frame_type = data[offset + 1]
                    if frame_type == 0x71 and offset + 5 < len(data):
                        # Found battery/status frame: 55 71 64 00 [voltage_low] [voltage_high] ...
                        if data[offset + 2] == 0x64 and data[offset + 3] == 0x00:
                            battery_response = data[offset:offset + 20]
                            notification_received.set()
                            return
                    elif frame_type == 0x64 and offset + 5 < len(data):
                        # Original format: 55 64 [voltage_low] [voltage_high]
                        battery_response = data[offset:offset + 20]
                        notification_received.set()
                        return
                offset += 1
        
        try:
            async with BleakClient(mac_address, timeout=8.0) as client:
                print(f"  Connected to {mac_address}")
                
                # Enable notifications
                await client.start_notify(WITMOTION_DATA_UUID, notification_handler)
                
                # Send battery command
                battery_cmd = bytes([0xFF, 0xAA, 0x27, 0x64, 0x00])
                await client.write_gatt_char(WITMOTION_CONFIG_UUID, battery_cmd)
                
                # Wait for response
                try:
                    await asyncio.wait_for(notification_received.wait(), timeout=3.0)
                    
                    if battery_response and len(battery_response) >= 6:
                        if battery_response[0] == 0x55 and battery_response[1] == 0x71:
                            # Parse voltage from 55 71 64 00 [voltage_low] [voltage_high]
                            voltage_raw = int.from_bytes(battery_response[4:6], byteorder='little', signed=False)
                            voltage_v = voltage_raw / 100.0
                            
                            # Convert to percentage (3.0V-4.2V range)
                            battery_pct = int(((voltage_v - 3.0) / (4.2 - 3.0)) * 100)
                            battery_pct = max(0, min(100, battery_pct))
                            
                            print(f"  ✅ Battery: {battery_pct}% ({voltage_v:.2f}V)")
                            return battery_pct
                            
                except asyncio.TimeoutError:
                    print(f"  ❌ Battery query timeout")
                    
                finally:
                    await client.stop_notify(WITMOTION_DATA_UUID)
                    
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
        
        return None
    
    async def update_device_health(self, mac_address: str, battery: int) -> bool:
        """Update device health via API"""
        try:
            import subprocess
            result = subprocess.run([
                'curl', '-s', '-X', 'PUT', 
                '-H', 'Content-Type: application/json',
                '-d', f'{{"battery": {battery}}}',
                f'{self.api_base}/api/admin/devices/{mac_address}/health'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                if response.get('status') == 'updated':
                    print(f"  ✅ Database updated")
                    return True
                else:
                    print(f"  ❌ API error: {response}")
            else:
                print(f"  ❌ API call failed: {result.stderr}")
                
        except Exception as e:
            print(f"  ❌ Update failed: {e}")
        
        return False
    
    async def refresh_all_batteries(self):
        """Refresh battery levels for all BT50 devices"""
        print("🔋 BT50 Battery Refresh Service")
        print("=" * 40)
        
        successful = 0
        total = len(self.bt50_devices)
        
        for mac_address in self.bt50_devices:
            print(f"\n📱 Processing {mac_address}:")
            
            # Read battery level
            battery_level = await self.read_device_battery(mac_address)
            
            if battery_level is not None:
                # Update in database
                if await self.update_device_health(mac_address, battery_level):
                    successful += 1
            
            # Delay between devices
            await asyncio.sleep(1)
        
        print(f"\n{'=' * 40}")
        print(f"✅ Batch complete: {successful}/{total} devices updated")
        
        return successful, total

async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        # Test single device
        if len(sys.argv) < 3:
            print("Usage: python3 battery_refresh_service.py --single <MAC_ADDRESS>")
            sys.exit(1)
        
        service = BatteryRefreshService()
        mac_address = sys.argv[2]
        
        print(f"Testing single device: {mac_address}")
        battery_level = await service.read_device_battery(mac_address)
        if battery_level is not None:
            await service.update_device_health(mac_address, battery_level)
    else:
        # Refresh all devices
        service = BatteryRefreshService()
        await service.refresh_all_batteries()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")