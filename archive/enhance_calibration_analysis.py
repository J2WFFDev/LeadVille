with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Replace the calibration processing section to add per-sensor analysis
old_processing = """            # Calculate baseline averages
            vx_values = [s[\\"vx_raw\\"] for s in self.calibration_samples]
            vy_values = [s[\\"vy_raw\\"] for s in self.calibration_samples]
            vz_values = [s[\\"vz_raw\\"] for s in self.calibration_samples]

            self.baseline_x = int(sum(vx_values) / len(vx_values))
            self.baseline_y = int(sum(vy_values) / len(vy_values))
            self.baseline_z = int(sum(vz_values) / len(vz_values))

            # Calculate noise characteristics
            import statistics
            noise_x = statistics.stdev(vx_values) if len(set(vx_values)) > 1 else 0
            noise_y = statistics.stdev(vy_values) if len(set(vy_values)) > 1 else 0
            noise_z = statistics.stdev(vz_values) if len(set(vz_values)) > 1 else 0"""

new_processing = """            # Analyze per-sensor calibration data
            import statistics
            sensor_stats = {}
            
            # Group samples by sensor
            for sample in self.calibration_samples:
                sensor_mac = sample.get(\\"sensor_mac\\", \\"unknown\\")
                if sensor_mac not in sensor_stats:
                    sensor_stats[sensor_mac] = []
                sensor_stats[sensor_mac].append(sample)
            
            # Calculate per-sensor baselines and noise
            self.logger.info(f\\"📊 Calibration Analysis - Total samples: {len(self.calibration_samples)}\\")
            
            all_vx = []
            all_vy = []  
            all_vz = []
            
            for sensor_mac, samples in sensor_stats.items():
                if sensor_mac == \\"unknown\\":
                    continue
                    
                vx_values = [s[\\"vx_raw\\"] for s in samples]
                vy_values = [s[\\"vy_raw\\"] for s in samples]
                vz_values = [s[\\"vz_raw\\"] for s in samples]
                
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
                target_num = self.sensor_mappings.get(sensor_mac, {}).get(\\"target_num\\", \\"?\\"")
                
                self.logger.info(f\\"📊 Sensor {sensor_id} (Target {target_num}): {len(samples)} samples\\")
                self.logger.info(f\\"📊   Baseline: X={sensor_baseline_x}, Y={sensor_baseline_y}, Z={sensor_baseline_z}\\")
                self.logger.info(f\\"📊   Noise: X=±{sensor_noise_x:.1f}, Y=±{sensor_noise_y:.1f}, Z=±{sensor_noise_z:.1f}\\")
                
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
                vx_values = [s[\\"vx_raw\\"] for s in self.calibration_samples]
                vy_values = [s[\\"vy_raw\\"] for s in self.calibration_samples]
                vz_values = [s[\\"vz_raw\\"] for s in self.calibration_samples]

                self.baseline_x = int(sum(vx_values) / len(vx_values))
                self.baseline_y = int(sum(vy_values) / len(vy_values))
                self.baseline_z = int(sum(vz_values) / len(vz_values))

                noise_x = statistics.stdev(vx_values) if len(set(vx_values)) > 1 else 0
                noise_y = statistics.stdev(vy_values) if len(set(vy_values)) > 1 else 0
                noise_z = statistics.stdev(vz_values) if len(set(vz_values)) > 1 else 0"""

content = content.replace(old_processing, new_processing)

with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Enhanced calibration analysis with per-sensor reporting")
