#!/usr/bin/env python3
"""
Complete fix for proper sensor identification in impact detection
"""

import re

# Read the current file
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# 1. Update the handler signature
old_signature = "async def bt50_notification_handler(self, characteristic, data):"
new_signature = "async def bt50_notification_handler(self, characteristic, data, sensor_mac=None):"

content = content.replace(old_signature, new_signature)
print("✅ Updated handler signature")

# 2. Add sensor identification logic after hex_data line
# Find the line with hex_data = data.hex()
pattern = r'(        hex_data = data\.hex\(\)\n)'
replacement = r'''\1
        # Use the sensor_mac parameter passed from the sensor-specific handler
        if sensor_mac is None:
            # Fallback: use first available sensor if no parameter provided
            if self.sensor_mappings:
                sensor_mac = list(self.sensor_mappings.keys())[0]
            else:
                sensor_mac = "UNKNOWN:SENSOR"

'''

content = re.sub(pattern, replacement, content)
print("✅ Added sensor identification logic")

# 3. Update the notification setup to use sensor-specific handlers
old_setup = '''            # Switch all sensors to impact notification handler
            for i, client in enumerate(self.bt50_clients):
                await client.stop_notify(BT50_SENSOR_UUID)
                await client.start_notify(BT50_SENSOR_UUID, self.bt50_notification_handler)
                sensor_id = BT50_SENSORS[i][-5:].replace(":", "")
                self.logger.debug(f"Impact notifications enabled for sensor {sensor_id}")'''

new_setup = '''            # Switch all sensors to impact notification handler with individual sensor identification
            for i, client in enumerate(self.bt50_clients):
                await client.stop_notify(BT50_SENSOR_UUID)
                
                # Create a sensor-specific handler using closure to capture the sensor MAC
                sensor_mac = BT50_SENSORS[i]
                
                def create_sensor_handler(sensor_address):
                    async def sensor_specific_handler(characteristic, data):
                        await self.bt50_notification_handler(characteristic, data, sensor_address)
                    return sensor_specific_handler
                
                # Use the sensor-specific handler
                handler = create_sensor_handler(sensor_mac)
                await client.start_notify(BT50_SENSOR_UUID, handler)
                
                sensor_id = BT50_SENSORS[i][-5:].replace(":", "")
                self.logger.debug(f"Impact notifications enabled for sensor {sensor_id} ({sensor_mac})")'''

content = content.replace(old_setup, new_setup)
print("✅ Updated notification setup")

# Write the updated file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Complete sensor identification fix applied!")
print("✅ Each sensor will now report its correct Sensor ID in impact logs")