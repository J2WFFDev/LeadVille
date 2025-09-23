#!/usr/bin/env python3

# Read the current leadville_bridge.py  
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Replace single bt50_client with multiple clients
old_init = """        self.amg_client = None
        self.bt50_client = None"""

new_init = """        self.amg_client = None
        self.bt50_clients = {}  # Dictionary to hold multiple BT50 clients {mac: client}
        self.bt50_client = None  # Keep for compatibility"""

new_content = content.replace(old_init, new_init)

# Update the connect_devices method to handle multiple BT50 sensors
old_connect_section = """        try:
            # Connect BT50 Sensor
            self.logger.info("Connecting to BT50 sensor...")
            self.bt50_client = BleakClient(BT50_SENSOR_MAC)
            await self.bt50_client.connect()
            self.logger.info("📝 Status: Sensor 12:E3 - Connected")
            self.log_event("Status", "Sensor", "12:E3", "Plate 1", "Connected")

            # Wait for connection to stabilize before calibration
            await asyncio.sleep(1.0)

            # Perform startup calibration
            calibration_success = await self.perform_startup_calibration()
            if not calibration_success:
                self.logger.error("Startup calibration failed - cannot proceed")

        except Exception as e:
            self.logger.error(f"BT50 sensor connection failed: {e}")"""

new_connect_section = """        # Connect multiple BT50 sensors
        for i, bt50_mac in enumerate(BT50_SENSORS):
            try:
                sensor_id = bt50_mac[-5:].replace(":", "")  # Last 5 chars for ID
                target_num = i + 1
                
                self.logger.info(f"Connecting to BT50 sensor {target_num} ({sensor_id})...")
                client = BleakClient(bt50_mac)
                await client.connect()
                
                self.bt50_clients[bt50_mac] = client
                if i == 0:  # Set primary sensor for compatibility
                    self.bt50_client = client
                
                self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target {target_num})")
                self.log_event("Status", "Sensor", sensor_id, f"Target {target_num}", "Connected")
                
                # Wait for connection to stabilize
                await asyncio.sleep(1.0)
                
                # Perform calibration for this sensor
                calibration_success = await self.perform_sensor_calibration(client, sensor_id, target_num)
                if not calibration_success:
                    self.logger.warning(f"Calibration failed for sensor {sensor_id} - continuing with others")
                    
            except Exception as e:
                self.logger.error(f"BT50 sensor {target_num} connection failed: {e}")"""

new_content = new_content.replace(old_connect_section, new_connect_section)

# Write the updated file
with open("leadville_bridge_multi.py", "w") as f:
    f.write(new_content)

print("✅ Created enhanced multi-sensor Bridge architecture!")
print("Features:")
print("  - Multiple BT50 sensor support")
print("  - Individual sensor calibration") 
print("  - Target-specific logging")
print("  - Backward compatibility")
print()
print("File saved as: leadville_bridge_multi.py")
print("Review the changes before deploying to production")
