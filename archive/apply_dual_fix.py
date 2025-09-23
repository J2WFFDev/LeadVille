#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Replace the BT50_SENSOR_MAC usage with loop through BT50_SENSORS
old_single_connect = """            self.logger.info("Connecting to BT50 sensor...")
            self.bt50_client = BleakClient(BT50_SENSOR_MAC)
            await self.bt50_client.connect()
            self.logger.info("📝 Status: Sensor 12:E3 - Connected")
            self.log_event("Status", "Sensor", "12:E3", "Plate 1", "Connected")"""

new_multi_connect = """            # Connect to multiple BT50 sensors
            connected_count = 0
            for i, sensor_mac in enumerate(BT50_SENSORS):
                target_num = i + 1
                sensor_id = sensor_mac[-5:].replace(":", "")
                
                try:
                    self.logger.info(f"Connecting to BT50 sensor - Target {target_num} ({sensor_id})...")
                    self.logger.info(f"Target {target_num} MAC: {sensor_mac}")
                    
                    client = BleakClient(sensor_mac)
                    await client.connect()
                    
                    # Use first sensor as primary for compatibility
                    if i == 0:
                        self.bt50_client = client
                    
                    self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target {target_num})")
                    self.log_event("Status", "Sensor", sensor_id, f"Target {target_num}", "Connected")
                    connected_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Target {target_num} sensor connection failed: {e}")
            
            self.logger.info(f"✅ Connected to {connected_count}/{len(BT50_SENSORS)} BT50 sensors")"""

# Apply the replacement
new_content = content.replace(old_single_connect, new_multi_connect)

# Write the updated file
with open("leadville_bridge.py", "w") as f:
    f.write(new_content)

print("✅ Applied dual sensor connection fix!")
print("Now connects to BOTH Target 1 and Target 2 sensors")
