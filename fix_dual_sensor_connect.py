#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Replace the single sensor connection with dual sensor approach
old_bt50_section = """        try:
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

            # Calibration handles the listening status message
            self.logger.info("BT50 sensor and impact notifications enabled")

        except Exception as e:
            self.logger.error(f"BT50 sensor connection failed: {e}")

        # Attempt to connect to second BT50 sensor (Target 2) if available
        if len(BT50_SENSORS) > 1:
            try:
                second_sensor_mac = BT50_SENSORS[1]  # Target 2 sensor
                sensor_id = second_sensor_mac[-5:].replace(":", "")
                self.logger.info(f"Attempting second BT50 sensor - Target 2 ({sensor_id})")
                self.logger.info(f"Target 2 MAC: {second_sensor_mac}")
                
                # Try to connect to second sensor
                second_client = BleakClient(second_sensor_mac)
                await second_client.connect()
                
                # If successful, use it as primary sensor
                if not (self.bt50_client and self.bt50_client.is_connected):
                    self.bt50_client = second_client
                    self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target 2)")
                    self.log_event("Status", "Sensor", sensor_id, "Target 2", "Connected")
                    
                    # Perform calibration on second sensor
                    await asyncio.sleep(1.0)
                    calibration_success = await self.perform_startup_calibration()
                    if calibration_success:
                        self.logger.info("BT50 Target 2 sensor and impact notifications enabled")
                else:
                    # First sensor was connected, disconnect second for now (single sensor mode)
                    await second_client.disconnect()
                    self.logger.info(f"Target 2 sensor found but using Target 1 (single sensor mode)")
                    
            except Exception as e:
                self.logger.error(f"Second BT50 sensor (Target 2) connection failed: {e}")"""

new_bt50_section = """        # Connect to ALL BT50 sensors for multi-target detection
        connected_sensors = []
        
        for i, sensor_mac in enumerate(BT50_SENSORS):
            target_num = i + 1
            sensor_id = sensor_mac[-5:].replace(":", "")
            
            try:
                self.logger.info(f"Connecting to BT50 sensor - Target {target_num} ({sensor_id})...")
                self.logger.info(f"Target {target_num} MAC: {sensor_mac}")
                
                client = BleakClient(sensor_mac)
                await client.connect()
                
                self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target {target_num})")
                self.log_event("Status", "Sensor", sensor_id, f"Target {target_num}", "Connected")
                
                # Store the client (for now, use first as primary for compatibility)
                if i == 0:
                    self.bt50_client = client
                
                # Wait for connection to stabilize
                await asyncio.sleep(1.0)
                
                # Perform calibration for this sensor
                self.logger.info(f"🎯 Starting calibration for Target {target_num} sensor...")
                calibration_success = await self.perform_startup_calibration()
                
                if calibration_success:
                    self.logger.info(f"BT50 Target {target_num} sensor calibrated and notifications enabled")
                    connected_sensors.append(f"Target {target_num} ({sensor_id})")
                else:
                    self.logger.warning(f"Calibration failed for Target {target_num} sensor")
                    
            except Exception as e:
                self.logger.error(f"BT50 Target {target_num} sensor connection failed: {e}")
        
        if connected_sensors:
            self.logger.info(f"✅ Multi-sensor setup complete: { .join(connected_sensors)}")
        else:
            self.logger.error("❌ No BT50 sensors connected")"""

# Apply the replacement
new_content = content.replace(old_bt50_section, new_bt50_section)

# Write the updated file
with open("leadville_bridge.py", "w") as f:
    f.write(new_content)

print("✅ Updated Bridge for DUAL sensor connection!")
print("Changes:")
print("  - Connects to ALL BT50 sensors simultaneously")
print("  - Calibrates each sensor individually") 
print("  - Logs each target connection and calibration")
print("  - Reports multi-sensor setup status")
