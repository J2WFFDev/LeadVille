#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

print("🔧 Replacing old calibration handler with per-sensor version...")

# Find and replace the entire old calibration_notification_handler method
old_handler = """    async def calibration_notification_handler(self, characteristic, data):
        \"\"\"Collect calibration samples during startup\"\"\"
        if not self.collecting_calibration:
            return

        # For calibration, parse data even if shot_detector import failed
        try:
            if PARSER_AVAILABLE:
                # Use the imported parser
                result = parse_5561(data)
                if result and result[\\"samples\\"]:
                    # Collect raw values from all samples in this notification
                    for sample in result[\\"samples\\"]:
                        vx_raw, vy_raw, vz_raw = sample[\\"raw\\"]
                        self.calibration_samples.append({
                            \\"vx_raw\\": vx_raw,
                            \\"vy_raw\\": vy_raw,
                            \\"vz_raw\\": vz_raw,
                            \\"timestamp\\": time.time()
                        })

                        # Stop when we have enough samples
                        if len(self.calibration_samples) >= CALIBRATION_SAMPLES:
                            self.collecting_calibration = False

        except Exception as e:
            self.logger.error(f\\"Calibration data collection failed: {e}\\")"""

new_handler = """    async def calibration_notification_handler(self, characteristic, data):
        \"\"\"Collect per-sensor calibration samples during startup\"\"\"
        if not self.collecting_calibration:
            return

        # Identify which sensor sent this data
        sensor_mac = None
        try:
            device_addr = characteristic.service.device.address.upper()
            for mac in BT50_SENSORS:
                if mac.upper() == device_addr:
                    sensor_mac = mac
                    break
        except Exception as e:
            self.logger.debug(f\\"Could not identify sensor device: {e}\\")

        if not sensor_mac:
            self.logger.warning(\\"Could not identify sensor for calibration data - skipping\\")
            return

        # Initialize per-sensor storage if needed
        if sensor_mac not in self.per_sensor_calibration:
            self.per_sensor_calibration[sensor_mac] = {
                \\"samples\\": [],
                \\"baseline\\": {},
                \\"complete\\": False,
                \\"target_samples\\": self.sensor_target_count
            }

        # Parse and collect samples for this specific sensor
        try:
            if PARSER_AVAILABLE:
                result = parse_5561(data)
                if result and result[\\"samples\\"]:
                    sensor_cal = self.per_sensor_calibration[sensor_mac]
                    
                    # Collect raw values from all samples in this notification
                    for sample in result[\\"samples\\"]:
                        if len(sensor_cal[\\"samples\\"]) >= self.sensor_target_count:
                            break  # This sensor is complete
                            
                        vx_raw, vy_raw, vz_raw = sample[\\"raw\\"]
                        sensor_cal[\\"samples\\"].append({
                            \\"vx_raw\\": vx_raw,
                            \\"vy_raw\\": vy_raw,
                            \\"vz_raw\\": vz_raw,
                            \\"timestamp\\": time.time(),
                            \\"sensor_mac\\": sensor_mac
                        })

                    # Check if this sensor completed its calibration
                    if (len(sensor_cal[\\"samples\\"]) >= self.sensor_target_count and 
                        not sensor_cal[\\"complete\\"]):
                        sensor_cal[\\"complete\\"] = True
                        sensor_id = sensor_mac[-5:]
                        self.logger.debug(f\\"✅ Sensor {sensor_id} calibration complete: {len(sensor_cal[ samples])} samples\\")

                    # Check if ALL sensors have completed calibration
                    all_complete = True
                    for mac in BT50_SENSORS:
                        if mac not in self.per_sensor_calibration:
                            all_complete = False
                            break
                        if not self.per_sensor_calibration[mac].get(\\"complete\\", False):
                            all_complete = False
                            break
                    
                    if all_complete:
                        self.collecting_calibration = False
                        self.logger.debug(\\"🎯 All sensors completed calibration collection\\")

        except Exception as e:
            self.logger.error(f\\"Per-sensor calibration data collection failed: {e}\\")"""

content = content.replace(old_handler, new_handler)

# Write the enhanced file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Replaced old calibration handler with per-sensor version!")
print("The system should now:")
print("  🎯 Collect samples separately for each sensor")
print("  📊 Show detailed per-sensor calibration results")
print("  ✅ Track progress per sensor during collection")
