import re

with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Add sensor identification to calibration
old_section = """                    # Collect raw values from all samples in this notification
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
                            self.collecting_calibration = False"""

new_section = """                    # Identify which sensor sent this data
                    sensor_mac = \\"unknown\\"
                    try:
                        device_addr = characteristic.service.device.address.upper()
                        for mac in BT50_SENSORS:
                            if mac.upper() == device_addr:
                                sensor_mac = mac
                                break
                    except:
                        pass
                    
                    # Collect raw values from all samples in this notification
                    for sample in result[\\"samples\\"]:
                        vx_raw, vy_raw, vz_raw = sample[\\"raw\\"]
                        self.calibration_samples.append({
                            \\"vx_raw\\": vx_raw,
                            \\"vy_raw\\": vy_raw,
                            \\"vz_raw\\": vz_raw,
                            \\"timestamp\\": time.time(),
                            \\"sensor_mac\\": sensor_mac
                        })

                        # Stop when we have enough samples
                        if len(self.calibration_samples) >= CALIBRATION_SAMPLES:
                            self.collecting_calibration = False"""

content = content.replace(old_section, new_section)

with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Added sensor MAC identification to calibration samples")
