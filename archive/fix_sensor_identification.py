#!/usr/bin/env python3
"""
Fix sensor identification by modifying handler signature and notification setup
"""

# Read the current file
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# 1. Update the handler signature to accept sensor_mac parameter
old_signature = "async def bt50_notification_handler(self, characteristic, data):"
new_signature = "async def bt50_notification_handler(self, characteristic, data, sensor_mac=None):"

if old_signature in content:
    content = content.replace(old_signature, new_signature)
    print("✅ Updated bt50_notification_handler signature")
else:
    print("❌ Handler signature not found")

# 2. Update the sensor identification logic to use the parameter
old_identification = """        # Identify which sensor sent this data - use first available sensor for now
        sensor_mac = None
        if self.sensor_mappings:
            sensor_mac = list(self.sensor_mappings.keys())[0]  # Use first available sensor

        # Final fallback: create a default sensor_mac
        if not sensor_mac:
            sensor_mac = "UNKNOWN:SENSOR" """

new_identification = """        # Use the sensor_mac parameter passed from the sensor-specific handler
        if sensor_mac is None:
            # Fallback: use first available sensor if no parameter provided
            if self.sensor_mappings:
                sensor_mac = list(self.sensor_mappings.keys())[0]
            else:
                sensor_mac = "UNKNOWN:SENSOR" """

if old_identification in content:
    content = content.replace(old_identification, new_identification)
    print("✅ Updated sensor identification logic")
else:
    print("❌ Sensor identification logic not found")

# 3. Update the notification setup to use sensor-specific handlers
old_setup = """            # Switch all sensors to impact notification handler
            for i, client in enumerate(self.bt50_clients):
                await client.stop_notify(BT50_SENSOR_UUID)
                await client.start_notify(BT50_SENSOR_UUID, self.bt50_notification_handler)
                sensor_id = BT50_SENSORS[i][-5:].replace(":", "")
                self.logger.debug(f"Impact notifications enabled for sensor {sensor_id}")"""

new_setup = """            # Switch all sensors to impact notification handler with individual sensor identification
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
                self.logger.debug(f"Impact notifications enabled for sensor {sensor_id} ({sensor_mac})")"""

if old_setup in content:
    content = content.replace(old_setup, new_setup)
    print("✅ Updated notification setup with sensor-specific handlers")
else:
    print("❌ Notification setup not found")

# Write the updated file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Sensor identification fix applied successfully!")
print("✅ Each sensor will now properly identify itself in impact logs")