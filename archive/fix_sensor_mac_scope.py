#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

print("🔧 Fixing sensor_mac scope issue and enhancing calibration reporting...")

# 1. Fix sensor_mac scope issue by adding fallback after the try/except block
old_sensor_identification = """        # Identify which sensor sent this data for proper baseline correction
        sensor_mac = None
        try:
            device_addr = characteristic.service.device.address.upper()
            for mac in BT50_SENSORS:
                if mac.upper() == device_addr:
                    sensor_mac = mac
                    break
        except Exception as e:
            self.logger.debug(f\"Could not identify sensor device for impact detection: {e}\")"""

new_sensor_identification = """        # Identify which sensor sent this data for proper baseline correction
        sensor_mac = None
        try:
            device_addr = characteristic.service.device.address.upper()
            for mac in BT50_SENSORS:
                if mac.upper() == device_addr:
                    sensor_mac = mac
                    break
        except Exception as e:
            self.logger.debug(f\"Could not identify sensor device for impact detection: {e}\")
        
        # Ensure sensor_mac is always defined to prevent NameError
        if sensor_mac is None:
            sensor_mac = BT50_SENSORS[0] if BT50_SENSORS else \"unknown\"
            self.logger.warning(f\"Could not identify sensor for impact detection, using fallback: {sensor_mac[-5:] if sensor_mac !=  unknown else unknown}\")"""

content = content.replace(old_sensor_identification, new_sensor_identification)

# 2. Enhance per-sensor calibration reporting
old_reporting = """            self.logger.info(f\"📊 Per-Sensor Calibration Analysis - Total: {total_samples} samples\")
            print(f\"\\n📊 Per-Sensor Calibration Results:\")"""

new_reporting = """            self.logger.info(f\"📊 Per-Sensor Calibration Analysis - Total: {total_samples} samples\")
            print(f\"\\n📊 Per-Sensor Calibration Results:\")
            print(f\"\" + \"=\"*60)"""

content = content.replace(old_reporting, new_reporting)

# 3. Add detailed per-sensor calibration console output
old_console_output = """                print(f\"  🎯 Target {target_num} Sensor {sensor_id}: Baseline X={baseline_x}, Noise ±{noise_x:.1f} ({len(samples)} samples)\")"""

new_console_output = """                print(f\"  🎯 Target {target_num} Sensor {sensor_id}: Baseline X={baseline_x}, Noise ±{noise_x:.1f} ({len(samples)} samples)\")
                print(f\"     Individual Baseline: X={baseline_x}, Y={baseline_y}, Z={baseline_z}\")
                print(f\"     Noise Characteristics: X=±{noise_x:.1f}, Y=±{noise_y:.1f}, Z=±{noise_z:.1f}\")
                print()"""

content = content.replace(old_console_output, new_console_output)

# 4. Add completion summary to console output
old_completion = """            # Calculate system-wide baseline for compatibility
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

new_completion = """            # Calculate system-wide baseline for compatibility
            if all_vx:
                self.baseline_x = int(sum(all_vx) / len(all_vx))
                self.baseline_y = int(sum(all_vy) / len(all_vy))
                self.baseline_z = int(sum(all_vz) / len(all_vz))
                
                noise_x = statistics.stdev(all_vx) if len(set(all_vx)) > 1 else 0
                noise_y = statistics.stdev(all_vy) if len(set(all_vy)) > 1 else 0
                noise_z = statistics.stdev(all_vz) if len(set(all_vz)) > 1 else 0
                
                # Console summary
                print(f\"\\n📊 System Summary (Averaged):\")
                print(f\"     System Baseline: X={self.baseline_x}, Y={self.baseline_y}, Z={self.baseline_z}\")
                print(f\"     System Noise: X=±{noise_x:.1f}, Y=±{noise_y:.1f}, Z=±{noise_z:.1f}\")
                print(f\"\" + \"=\"*60)
            else:
                self.logger.error(\"No valid calibration data processed\")
                return False"""

content = content.replace(old_completion, new_completion)

# Write the enhanced file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Fixed sensor_mac scope issue and enhanced calibration reporting!")
print("Changes:")
print("  🔧 Added sensor_mac fallback to prevent NameError")
print("  📊 Enhanced per-sensor calibration console output")
print("  📈 Added detailed baseline and noise reporting per sensor")
print("  📋 Added system summary with averaged values")
