#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Add sensor mapping initialization to __init__ method
old_init_end = """        # Timing integration components
        self.timing_calibrator = None
        self.timing_correlator = None"""

new_init_end = """        # Timing integration components
        self.timing_calibrator = None
        self.timing_correlator = None
        
        # Sensor-to-target mapping for enhanced logging
        self.sensor_mappings = {}  # {sensor_mac: {\"sensor_id\": \"55:50\", \"target_num\": 2, \"stage\": \"Go Fast\"}}
        self.current_sensor_mac = None  # Track which sensor triggered the notification"""

content = content.replace(old_init_end, new_init_end)

# Update sensor connection to store mapping information
old_sensor_connect = """                self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target {target_num})")
                self.log_event("Status", "Sensor", sensor_id, f"Target {target_num}", "Connected")
                connected_count += 1"""

new_sensor_connect = """                self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target {target_num})")
                self.log_event("Status", "Sensor", sensor_id, f"Target {target_num}", "Connected")
                
                # Store sensor mapping for impact logging
                ble_id = sensor_mac[-5:]  # Last 5 chars (55:50 format)
                self.sensor_mappings[sensor_mac] = {
                    \"sensor_id\": ble_id,
                    \"target_num\": target_num,
                    \"stage\": \"Go Fast\",  # TODO: Get from Bridge configuration
                    \"full_mac\": sensor_mac
                }
                self.logger.debug(f\"Stored sensor mapping: {ble_id} -> Target {target_num}, Stage Go Fast\")
                
                connected_count += 1"""

content = content.replace(old_sensor_connect, new_sensor_connect)

# Enhance the shot detection logging
old_shot_log = """                        self.logger.info(f"🎯 SHOT DETECTED #{shot_event.shot_id}: duration {shot_event.duration_ms:.0f}ms, deviation {shot_event.max_deviation} counts")

                        self.log_event("Shot", "Sensor", "12:E3", "Plate 1",
                                     f"Shot #{shot_event.shot_id}: duration {shot_event.duration_samples} samples ({shot_event.duration_ms:.0f}ms), "
                                     f"max deviation {shot_event.max_deviation} counts, X-range [{min(shot_event.x_values)}-{max(shot_event.x_values)}]")"""

new_shot_log = """                        # Get sensor info for logging
                        sensor_info = self.get_current_sensor_info()
                        stage_name = sensor_info[\"stage\"]
                        target_num = sensor_info[\"target_num\"]
                        sensor_id = sensor_info[\"sensor_id\"]
                        
                        self.logger.info(f"�� SHOT DETECTED #{shot_event.shot_id}: Stage {stage_name}, Target {target_num}, Sensor {sensor_id} - Duration {shot_event.duration_ms:.0f}ms, Deviation {shot_event.max_deviation} counts")

                        self.log_event("Shot", "Sensor", sensor_id, f"Target {target_num}",
                                     f"Shot #{shot_event.shot_id}: duration {shot_event.duration_samples} samples ({shot_event.duration_ms:.0f}ms), "
                                     f"max deviation {shot_event.max_deviation} counts, X-range [{min(shot_event.x_values)}-{max(shot_event.x_values)}]")"""

content = content.replace(old_shot_log, new_shot_log)

# Enhance the enhanced impact detection logging
old_impact_log = """                        # Console impact logging
                        self.logger.info(f"💥 String {current_string}, Impact #{impact_number} - Time {time_from_start:.2f}s, Shot->Impact {time_from_shot:.3f}s, Peak {impact_event.peak_magnitude:.0f}g")

                        # Track impact peak magnitudes for final statistics
                        if not hasattr(self, \"recent_impact_peaks\"):
                            self.recent_impact_peaks = []
                        self.recent_impact_peaks.append(impact_event.peak_magnitude)

                        # Log structured event data
                        self.log_event("Impact", "Sensor", "12:E3", "Plate 1",
                                     f"Enhanced impact: onset {impact_event.onset_magnitude:.1f}g → peak {impact_event.peak_magnitude:.1f}g, "
                                     f"duration {impact_event.duration_ms:.1f}ms, confidence {impact_event.confidence:.2f}")"""

new_impact_log = """                        # Get sensor info for enhanced logging
                        sensor_info = self.get_current_sensor_info()
                        stage_name = sensor_info[\"stage\"]
                        target_num = sensor_info[\"target_num\"]
                        sensor_id = sensor_info[\"sensor_id\"]
                        
                        # Enhanced console impact logging with Stage/Target/Sensor info
                        self.logger.info(f"💥 IMPACT #{impact_number}: Stage {stage_name}, Target {target_num}, Sensor {sensor_id} - String {current_string}, Time {time_from_start:.2f}s, Shot→Impact {time_from_shot:.3f}s, Peak {impact_event.peak_magnitude:.0f}g")

                        # Track impact peak magnitudes for final statistics
                        if not hasattr(self, \"recent_impact_peaks\"):
                            self.recent_impact_peaks = []
                        self.recent_impact_peaks.append(impact_event.peak_magnitude)

                        # Log structured event data
                        self.log_event("Impact", "Sensor", sensor_id, f"Target {target_num}",
                                     f"Enhanced impact: onset {impact_event.onset_magnitude:.1f}g → peak {impact_event.peak_magnitude:.1f}g, "
                                     f"duration {impact_event.duration_ms:.1f}ms, confidence {impact_event.confidence:.2f}")"""

content = content.replace(old_impact_log, new_impact_log)

# Enhance legacy impact detection logging
old_legacy_log = """                    # Log clean impact message with corrected values only
                    self.logger.info(f"📝 Legacy Impact: Sensor 12:E3 Mag = {magnitude_corrected:.0f} [{vx_corrected:.0f}, {vy_corrected:.0f}, {vz_corrected:.0f}] at {timestamp.strftime(\"%H:%M:%S.%f\")[:-3]}")
                    self.log_event("Impact", "Sensor", "12:E3", "Plate 1",
                                 f"Legacy impact: Mag={magnitude_corrected:.1f} corrected[{vx_corrected:.1f},{vy_corrected:.1f},{vz_corrected:.1f}] (threshold: {IMPACT_THRESHOLD})")"""

new_legacy_log = """                    # Get sensor info for legacy logging
                    sensor_info = self.get_current_sensor_info()
                    stage_name = sensor_info[\"stage\"]
                    target_num = sensor_info[\"target_num\"]
                    sensor_id = sensor_info[\"sensor_id\"]
                    
                    # Enhanced legacy impact logging
                    self.logger.info(f"📝 LEGACY IMPACT: Stage {stage_name}, Target {target_num}, Sensor {sensor_id} - Mag {magnitude_corrected:.0f}g [{vx_corrected:.0f}, {vy_corrected:.0f}, {vz_corrected:.0f}] at {timestamp.strftime(\"%H:%M:%S.%f\")[:-3]}")
                    self.log_event("Impact", "Sensor", sensor_id, f"Target {target_num}",
                                 f"Legacy impact: Mag={magnitude_corrected:.1f} corrected[{vx_corrected:.1f},{vy_corrected:.1f},{vz_corrected:.1f}] (threshold: {IMPACT_THRESHOLD})")"""

content = content.replace(old_legacy_log, new_legacy_log)

# Add helper method to get current sensor info
helper_method = """
    def get_current_sensor_info(self):
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
        }
"""

# Insert the helper method before the bt50_notification_handler
content = content.replace("    async def bt50_notification_handler(self, characteristic, data):", 
                         helper_method + "\n    async def bt50_notification_handler(self, characteristic, data):")

# Write the enhanced file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Enhanced impact logging with Stage/Target/Sensor information!")
print("Features added:")
print("  - Sensor-to-target mapping during connection")
print("  - BLE ID format (55:50) for sensor identification")
print("  - Stage name in impact logs")
print("  - Target number in impact logs")
print("  - Enhanced console output format")
print("  - Applies to both Enhanced and Legacy impact detection")
