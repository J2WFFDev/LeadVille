#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Add second sensor connection attempt
old_section = """        except Exception as e:
            self.logger.error(f"BT50 sensor connection failed: {e}")

        # Final ready status - only if both devices connected successfully"""

new_section = """        except Exception as e:
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
                self.logger.error(f"Second BT50 sensor (Target 2) connection failed: {e}")

        # Final ready status - only if both devices connected successfully"""

new_content = content.replace(old_section, new_section)

# Write the updated file
with open("leadville_bridge.py", "w") as f:
    f.write(new_content)

print("✅ Added Target 2 sensor connection attempt!")
print("The Bridge will now try both sensors:")
print("  1. Target 1: EA:18:3D:6D:BA:E5")
print("  2. Target 2: C2:1B:DB:F0:55:50 (fallback if Target 1 fails)")
