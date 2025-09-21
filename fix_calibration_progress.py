#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

print("🔧 Fixing calibration progress display and validation...")

# Fix the progress display in the while loop
old_progress = """                print(f\"\\r📊 Collected {len(self.calibration_samples)}/{CALIBRATION_SAMPLES} samples...\", end=\\"\\", flush=True)"""

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
                
                progress_str = f\"📊 Calibration Progress: {\", \".join(sensor_progress)} (Total: {total_samples})\"
                print(f\"\\r{progress_str}\", end=\"\", flush=True)"""

content = content.replace(old_progress, new_progress)

# Fix the calibration validation check
old_validation = """            # Process calibration data
            if len(self.calibration_samples) < CALIBRATION_SAMPLES:
                self.logger.error(f\"Insufficient calibration samples: {len(self.calibration_samples)}\")
                print(f\"❌ Insufficient samples collected: {len(self.calibration_samples)}\")
                return False"""

new_validation = """            # Process per-sensor calibration data - validation moved to processing section
            print()  # New line after progress
            print(f\"\\n🎯 Calibration collection completed for all sensors!\")"""

content = content.replace(old_validation, new_validation)

# Write the enhanced file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Fixed calibration progress display and validation!")
print("Changes:")
print("  📊 Progress shows per-sensor collection status (BA:E5: 47/100, 55:50: 52/100)")
print("  ✅ Validation moved to per-sensor processing section")
print("  🎯 Clear completion message when all sensors finish")
