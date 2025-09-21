#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

print("🔧 Updating impact detection to use per-sensor baselines...")

# Add helper method to get sensor-specific baseline
helper_method = """
    def get_sensor_baseline(self, sensor_mac):
        \"\"\"Get individual sensor baseline for accurate impact detection\"\"\"
        if sensor_mac in self.sensor_baselines:
            baseline = self.sensor_baselines[sensor_mac]
            return (baseline[\"baseline_x\"], baseline[\"baseline_y\"], baseline[\"baseline_z\"])
        else:
            # Fallback to system baseline
            self.logger.warning(f\"No individual baseline for sensor {sensor_mac[-5:]}, using system baseline\")
            return (self.baseline_x, self.baseline_y, self.baseline_z)
"""

# Insert helper method before bt50_notification_handler
content = content.replace(
    "    def get_current_sensor_info(self):",
    helper_method + "\n    def get_current_sensor_info(self):"
)

# Update the bt50_notification_handler to identify sensor and use correct baseline
old_handler_start = """    async def bt50_notification_handler(self, characteristic, data):
        \"\"\"Handle BT50 sensor notifications with RAW VALUES and shot detection\"\"\"
        hex_data = data.hex()

        # Log raw data to debug only
        self.logger.debug(f\"BT50 raw: {hex_data[:64]}...\")

        if not PARSER_AVAILABLE:
            self.logger.warning(\"Parser not available, skipping impact detection\")
            return"""

new_handler_start = """    async def bt50_notification_handler(self, characteristic, data):
        \"\"\"Handle BT50 sensor notifications with per-sensor baseline correction\"\"\"
        hex_data = data.hex()

        # Identify which sensor sent this data for proper baseline correction
        sensor_mac = None
        try:
            device_addr = characteristic.service.device.address.upper()
            for mac in BT50_SENSORS:
                if mac.upper() == device_addr:
                    sensor_mac = mac
                    break
        except Exception as e:
            self.logger.debug(f\"Could not identify sensor device for impact detection: {e}\")

        # Log raw data to debug only
        self.logger.debug(f\"BT50 raw ({sensor_mac[-5:] if sensor_mac else  unknown}): {hex_data[:64]}...\")

        if not PARSER_AVAILABLE:
            self.logger.warning(\"Parser not available, skipping impact detection\")
            return"""

content = content.replace(old_handler_start, new_handler_start)

# Update the impact magnitude calculation to use sensor-specific baseline
old_magnitude_calc = """                    # Apply baseline correction BEFORE magnitude calculation
                    vx_corrected = vx_raw - self.baseline_x
                    vy_corrected = vy_raw - self.baseline_y
                    vz_corrected = vz_raw - self.baseline_z

                    # Calculate corrected magnitude
                    magnitude_corrected = math.sqrt(vx_corrected**2 + vy_corrected**2 + vz_corrected**2)"""

new_magnitude_calc = """                    # Get sensor-specific baseline for accurate correction
                    if sensor_mac:
                        baseline_x, baseline_y, baseline_z = self.get_sensor_baseline(sensor_mac)
                    else:
                        # Fallback to system baseline
                        baseline_x, baseline_y, baseline_z = self.baseline_x, self.baseline_y, self.baseline_z
                        self.logger.warning(\"Unknown sensor - using system baseline for impact detection\")

                    # Apply sensor-specific baseline correction
                    vx_corrected = vx_raw - baseline_x
                    vy_corrected = vy_raw - baseline_y
                    vz_corrected = vz_raw - baseline_z

                    # Calculate corrected magnitude with proper baseline
                    magnitude_corrected = math.sqrt(vx_corrected**2 + vy_corrected**2 + vz_corrected**2)"""

content = content.replace(old_magnitude_calc, new_magnitude_calc)

# Update get_current_sensor_info to use the identified sensor_mac
old_sensor_info = """    def get_current_sensor_info(self):
        \"\"\"Get current sensor information for logging based on connected sensor\"\"\"
        # For now, default to first sensor mapping if available
        if self.sensor_mappings:
            first_mapping = next(iter(self.sensor_mappings.values()))
            return first_mapping
        
        # Fallback to default values
        return {
            \"sensor_id\": \"12:E3\",
            \"target_num\": 1,
            \"stage\": \"Go Fast\"
        }"""

new_sensor_info = """    def get_current_sensor_info(self, sensor_mac=None):
        \"\"\"Get sensor information for logging based on specific sensor MAC\"\"\"
        # Use specific sensor if provided
        if sensor_mac and sensor_mac in self.sensor_mappings:
            return self.sensor_mappings[sensor_mac]
        
        # Fallback to first sensor mapping if available
        if self.sensor_mappings:
            first_mapping = next(iter(self.sensor_mappings.values()))
            return first_mapping
        
        # Final fallback to default values
        return {
            \"sensor_id\": \"12:E3\",
            \"target_num\": 1,
            \"stage\": \"Go Fast\"
        }"""

content = content.replace(old_sensor_info, new_sensor_info)

# Update the enhanced impact logging to pass sensor_mac
old_impact_logging = """                        # Get sensor info for enhanced logging
                        sensor_info = self.get_current_sensor_info()
                        stage_name = sensor_info[\"stage\"]
                        target_num = sensor_info[\"target_num\"]
                        sensor_id = sensor_info[\"sensor_id\"]"""

new_impact_logging = """                        # Get sensor info for enhanced logging with specific sensor
                        sensor_info = self.get_current_sensor_info(sensor_mac)
                        stage_name = sensor_info[\"stage\"]
                        target_num = sensor_info[\"target_num\"]
                        sensor_id = sensor_info[\"sensor_id\"]"""

content = content.replace(old_impact_logging, new_impact_logging)

# Update the legacy impact logging to pass sensor_mac
old_legacy_logging = """                    # Get sensor info for legacy logging
                    sensor_info = self.get_current_sensor_info()
                    stage_name = sensor_info[\"stage\"]
                    target_num = sensor_info[\"target_num\"]
                    sensor_id = sensor_info[\"sensor_id\"]"""

new_legacy_logging = """                    # Get sensor info for legacy logging with specific sensor
                    sensor_info = self.get_current_sensor_info(sensor_mac)
                    stage_name = sensor_info[\"stage\"]
                    target_num = sensor_info[\"target_num\"]
                    sensor_id = sensor_info[\"sensor_id\"]"""

content = content.replace(old_legacy_logging, new_legacy_logging)

# Update shot detection logging to pass sensor_mac
old_shot_logging = """                        # Get sensor info for logging
                        sensor_info = self.get_current_sensor_info()
                        stage_name = sensor_info[\"stage\"]
                        target_num = sensor_info[\"target_num\"]
                        sensor_id = sensor_info[\"sensor_id\"]"""

new_shot_logging = """                        # Get sensor info for logging with specific sensor
                        sensor_info = self.get_current_sensor_info(sensor_mac)
                        stage_name = sensor_info[\"stage\"]
                        target_num = sensor_info[\"target_num\"]
                        sensor_id = sensor_info[\"sensor_id\"]"""

content = content.replace(old_shot_logging, new_shot_logging)

# Write the enhanced file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Impact detection updated to use per-sensor baselines!")
print("Features:")
print(f"  🎯 Sensor identification in impact detection handler")
print(f"  📊 Individual baseline lookup per sensor")
print(f"  🔧 Accurate magnitude calculation with correct baseline")
print(f"  📝 Enhanced logging with proper sensor identification")
