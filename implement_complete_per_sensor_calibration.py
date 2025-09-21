#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

print("🔧 Implementing complete per-sensor calibration system...")

# 1. Add per-sensor calibration storage in __init__
old_init = """        self.bt50_clients = []  # List of all connected BT50 clients"""

new_init = """        self.bt50_clients = []  # List of all connected BT50 clients
        
        # Per-sensor calibration system
        self.per_sensor_calibration = {}  # {sensor_mac: {"samples": [], "baseline": {}, "complete": False}}
        self.sensor_target_count = 100  # Samples required per sensor
        self.sensor_baselines = {}  # {sensor_mac: {"baseline_x": int, "noise_x": float, etc}}"""

content = content.replace(old_init, new_init)

# 2. Replace the entire calibration notification handler for per-sensor collection
old_handler = """    async def calibration_notification_handler(self, characteristic, data):
        \"\"\"Collect calibration samples during startup\"\"\"
        if not self.collecting_calibration:
            return

        # For calibration, parse data even if shot_detector import failed
        try:
            if PARSER_AVAILABLE:
                # Identify which sensor sent this data
                sensor_mac = \"unknown\"
                try:
                    device_addr = characteristic.service.device.address.upper()
                    for mac in BT50_SENSORS:
                        if mac.upper() == device_addr:
                            sensor_mac = mac
                            break
                except:
                    pass
                
                # Collect raw values from all samples in this notification
                for sample in result[\"samples\"]:
                    vx_raw, vy_raw, vz_raw = sample[\"raw\"]
                    self.calibration_samples.append({
                        \"vx_raw\": vx_raw,
                        \"vy_raw\": vy_raw,
                        \"vz_raw\": vz_raw,
                        \"timestamp\": time.time(),
                        \"sensor_mac\": sensor_mac
                    })

                    # Stop when we have enough samples
                    if len(self.calibration_samples) >= CALIBRATION_SAMPLES:
                        self.collecting_calibration = False

        except Exception as e:
            self.logger.error(f\"Calibration data collection failed: {e}\")"""

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
            self.logger.debug(f\"Could not identify sensor device: {e}\")

        if not sensor_mac:
            self.logger.warning(\"Could not identify sensor for calibration data - skipping\")
            return

        # Initialize per-sensor storage if needed
        if sensor_mac not in self.per_sensor_calibration:
            self.per_sensor_calibration[sensor_mac] = {
                \"samples\": [],
                \"baseline\": {},
                \"complete\": False,
                \"target_samples\": self.sensor_target_count
            }

        # Parse and collect samples for this specific sensor
        try:
            if PARSER_AVAILABLE:
                result = parse_5561(data)
                if result and result[\"samples\"]:
                    sensor_cal = self.per_sensor_calibration[sensor_mac]
                    
                    # Collect raw values from all samples in this notification
                    for sample in result[\"samples\"]:
                        if len(sensor_cal[\"samples\"]) >= self.sensor_target_count:
                            break  # This sensor is complete
                            
                        vx_raw, vy_raw, vz_raw = sample[\"raw\"]
                        sensor_cal[\"samples\"].append({
                            \"vx_raw\": vx_raw,
                            \"vy_raw\": vy_raw,
                            \"vz_raw\": vz_raw,
                            \"timestamp\": time.time(),
                            \"sensor_mac\": sensor_mac
                        })

                    # Check if this sensor completed its calibration
                    if (len(sensor_cal[\"samples\"]) >= self.sensor_target_count and 
                        not sensor_cal[\"complete\"]):
                        sensor_cal[\"complete\"] = True
                        sensor_id = sensor_mac[-5:]
                        self.logger.debug(f\"✅ Sensor {sensor_id} calibration complete: {len(sensor_cal[ samples])} samples\")

                    # Check if ALL sensors have completed calibration
                    all_complete = True
                    for mac in BT50_SENSORS:
                        if mac not in self.per_sensor_calibration:
                            all_complete = False
                            break
                        if not self.per_sensor_calibration[mac].get(\"complete\", False):
                            all_complete = False
                            break
                    
                    if all_complete:
                        self.collecting_calibration = False
                        self.logger.debug(\"🎯 All sensors completed calibration collection\")

        except Exception as e:
            self.logger.error(f\"Per-sensor calibration data collection failed: {e}\")"""

content = content.replace(old_handler, new_handler)

# 3. Replace calibration processing with per-sensor baseline calculation
old_processing = """            # Process calibration data
            if len(self.calibration_samples) < CALIBRATION_SAMPLES:
                self.logger.error(f\"Insufficient calibration samples: {len(self.calibration_samples)}\")
                print(f\"❌ Insufficient samples collected: {len(self.calibration_samples)}\")
                return False

            # Analyze per-sensor calibration data
            import statistics
            sensor_stats = {}
            
            # Group samples by sensor
            for sample in self.calibration_samples:
                sensor_mac = sample.get(\"sensor_mac\", \"unknown\")
                if sensor_mac not in sensor_stats:
                    sensor_stats[sensor_mac] = []
                sensor_stats[sensor_mac].append(sample)
            
            # Calculate per-sensor baselines and noise
            self.logger.info(f\"📊 Calibration Analysis - Total samples: {len(self.calibration_samples)}\")
            
            all_vx = []
            all_vy = []  
            all_vz = []
            
            for sensor_mac, samples in sensor_stats.items():
                if sensor_mac == \"unknown\":
                    continue
                    
                vx_values = [s[\"vx_raw\"] for s in samples]
                vy_values = [s[\"vy_raw\"] for s in samples]
                vz_values = [s[\"vz_raw\"] for s in samples]
                
                if len(vx_values) < 10:  # Skip sensors with too few samples
                    continue
                
                sensor_baseline_x = int(sum(vx_values) / len(vx_values))
                sensor_baseline_y = int(sum(vy_values) / len(vy_values))
                sensor_baseline_z = int(sum(vz_values) / len(vz_values))
                
                sensor_noise_x = statistics.stdev(vx_values) if len(set(vx_values)) > 1 else 0
                sensor_noise_y = statistics.stdev(vy_values) if len(set(vy_values)) > 1 else 0
                sensor_noise_z = statistics.stdev(vz_values) if len(set(vz_values)) > 1 else 0
                
                # Get sensor info for logging
                sensor_id = sensor_mac[-5:]
                target_num = self.sensor_mappings.get(sensor_mac, {}).get(\"target_num\", \"?\")
                
                self.logger.info(f\"📊 Sensor {sensor_id} (Target {target_num}): {len(samples)} samples\")
                self.logger.info(f\"📊   Baseline: X={sensor_baseline_x}, Y={sensor_baseline_y}, Z={sensor_baseline_z}\")
                self.logger.info(f\"📊   Noise: X=±{sensor_noise_x:.1f}, Y=±{sensor_noise_y:.1f}, Z=±{sensor_noise_z:.1f}\")
                
                # Collect for overall average
                all_vx.extend(vx_values)
                all_vy.extend(vy_values)
                all_vz.extend(vz_values)
            
            # Calculate overall baseline (for compatibility)
            if all_vx:
                self.baseline_x = int(sum(all_vx) / len(all_vx))
                self.baseline_y = int(sum(all_vy) / len(all_vy))
                self.baseline_z = int(sum(all_vz) / len(all_vz))
                
                noise_x = statistics.stdev(all_vx) if len(set(all_vx)) > 1 else 0
                noise_y = statistics.stdev(all_vy) if len(set(all_vy)) > 1 else 0
                noise_z = statistics.stdev(all_vz) if len(set(all_vz)) > 1 else 0
            else:
                # Fallback - use original method
                vx_values = [s[\"vx_raw\"] for s in self.calibration_samples]
                vy_values = [s[\"vy_raw\"] for s in self.calibration_samples]
                vz_values = [s[\"vz_raw\"] for s in self.calibration_samples]

                self.baseline_x = int(sum(vx_values) / len(vx_values))
                self.baseline_y = int(sum(vy_values) / len(vy_values))
                self.baseline_z = int(sum(vz_values) / len(vz_values))

                noise_x = statistics.stdev(vx_values) if len(set(vx_values)) > 1 else 0
                noise_y = statistics.stdev(vy_values) if len(set(vy_values)) > 1 else 0
                noise_z = statistics.stdev(vz_values) if len(set(vz_values)) > 1 else 0"""

new_processing = """            # Process per-sensor calibration data
            import statistics
            
            # Validate we have calibration data for all connected sensors
            total_samples = 0
            missing_sensors = []
            
            for sensor_mac in BT50_SENSORS:
                if sensor_mac not in self.per_sensor_calibration:
                    missing_sensors.append(sensor_mac[-5:])
                else:
                    sensor_samples = len(self.per_sensor_calibration[sensor_mac][\"samples\"])
                    total_samples += sensor_samples
                    if sensor_samples < 50:  # Minimum threshold
                        missing_sensors.append(f\"{sensor_mac[-5:]}({sensor_samples})\")
            
            if missing_sensors:
                self.logger.error(f\"Insufficient calibration data for sensors: { .join(missing_sensors)}\")
                print(f\"❌ Calibration failed - insufficient data for: { .join(missing_sensors)}\")
                return False

            self.logger.info(f\"📊 Per-Sensor Calibration Analysis - Total: {total_samples} samples\")
            print(f\"\\n📊 Per-Sensor Calibration Results:\")
            
            # Process each sensor individually
            all_vx, all_vy, all_vz = [], [], []
            
            for sensor_mac in BT50_SENSORS:
                sensor_data = self.per_sensor_calibration[sensor_mac]
                samples = sensor_data[\"samples\"]
                
                if len(samples) < 10:
                    continue
                
                # Calculate individual sensor baseline and noise
                vx_values = [s[\"vx_raw\"] for s in samples]
                vy_values = [s[\"vy_raw\"] for s in samples]  
                vz_values = [s[\"vz_raw\"] for s in samples]
                
                baseline_x = int(sum(vx_values) / len(vx_values))
                baseline_y = int(sum(vy_values) / len(vy_values))
                baseline_z = int(sum(vz_values) / len(vz_values))
                
                noise_x = statistics.stdev(vx_values) if len(set(vx_values)) > 1 else 0
                noise_y = statistics.stdev(vy_values) if len(set(vy_values)) > 1 else 0
                noise_z = statistics.stdev(vz_values) if len(set(vz_values)) > 1 else 0
                
                # Store individual sensor baseline
                self.sensor_baselines[sensor_mac] = {
                    \"baseline_x\": baseline_x,
                    \"baseline_y\": baseline_y,
                    \"baseline_z\": baseline_z,
                    \"noise_x\": noise_x,
                    \"noise_y\": noise_y,
                    \"noise_z\": noise_z,
                    \"sample_count\": len(samples)
                }
                
                # Log individual sensor results
                sensor_id = sensor_mac[-5:]
                target_num = self.sensor_mappings.get(sensor_mac, {}).get(\"target_num\", \"?\")
                
                self.logger.info(f\"📊 Sensor {sensor_id} (Target {target_num}): {len(samples)} samples\")
                self.logger.info(f\"📊   Individual Baseline: X={baseline_x}, Y={baseline_y}, Z={baseline_z}\")
                self.logger.info(f\"📊   Individual Noise: X=±{noise_x:.1f}, Y=±{noise_y:.1f}, Z=±{noise_z:.1f}\")
                
                print(f\"  🎯 Target {target_num} Sensor {sensor_id}: Baseline X={baseline_x}, Noise ±{noise_x:.1f} ({len(samples)} samples)\")
                
                # Collect for system average (compatibility)
                all_vx.extend(vx_values)
                all_vy.extend(vy_values)
                all_vz.extend(vz_values)
            
            # Calculate system-wide baseline for compatibility
            if all_vx:
                self.baseline_x = int(sum(all_vx) / len(all_vx))
                self.baseline_y = int(sum(all_vy) / len(all_vy))
                self.baseline_z = int(sum(all_vz) / len(all_vz))
                
                noise_x = statistics.stdev(all_vx) if len(set(all_vx)) > 1 else 0
                noise_y = statistics.stdev(all_vy) if len(set(all_vy)) > 1 else 0
                noise_z = statistics.stdev(all_vz) if len(set(all_vz)) > 1 else 0
            else:
                self.logger.error(\"No valid calibration data processed\")
                return False"""

content = content.replace(old_processing, new_processing)

# 4. Update progress display for per-sensor tracking
old_progress = """                # Show per-sensor progress
                total_samples = sum(len(cal.get(\"samples\", [])) for cal in self.sensor_calibration.values())
                sensor_progress = []
                for mac in BT50_SENSORS:
                    sensor_id = mac[-5:]
                    count = len(self.sensor_calibration.get(mac, {}).get(\"samples\", []))
                    sensor_progress.append(f\"{sensor_id}:{count}\")
                
                progress_str = f\"📊 Collected {total_samples} total samples ({ .join(sensor_progress)})\"
                print(f\"\\r{progress_str}\", end=', flush=True)"""

new_progress = """                # Show per-sensor progress
                sensor_progress = []
                total_samples = 0
                
                for mac in BT50_SENSORS:
                    sensor_id = mac[-5:]
                    if mac in self.per_sensor_calibration:
                        count = len(self.per_sensor_calibration[mac][\"samples\"])
                        target = self.sensor_target_count
                        status = \"✅\" if count >= target else f\"{count}/{target}\"
                        sensor_progress.append(f\"{sensor_id}:{status}\")
                        total_samples += count
                    else:
                        sensor_progress.append(f\"{sensor_id}:0/{self.sensor_target_count}\")
                
                progress_str = f\"📊 Calibration Progress: { .join(sensor_progress)} (Total: {total_samples})\")
                print(f\"\\r{progress_str}\", end=', flush=True)"""

content = content.replace(old_progress, new_progress)

# 5. Initialize calibration storage at start of perform_startup_calibration
old_reset = """        # Reset calibration state
        self.calibration_samples = []
        self.collecting_calibration = True"""

new_reset = """        # Reset per-sensor calibration state
        self.per_sensor_calibration = {}
        self.sensor_baselines = {}
        self.collecting_calibration = True
        
        # Initialize storage for each connected sensor
        for sensor_mac in BT50_SENSORS:
            self.per_sensor_calibration[sensor_mac] = {
                \"samples\": [],
                \"baseline\": {},
                \"complete\": False,
                \"target_samples\": self.sensor_target_count
            }"""

content = content.replace(old_reset, new_reset)

# Write the enhanced file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Complete per-sensor calibration system implemented!")
print("Features:")
print("  🎯 Individual 100-sample collection per sensor")
print("  📊 Separate baseline calculation for each sensor")
print("  📈 Individual noise characteristics per sensor")
print("  🔄 Per-sensor progress tracking during calibration")
print("  💾 Sensor-specific baseline storage for impact detection")
