#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# 1. Add per-sensor calibration storage in __init__
old_sensor_init = """        # Sensor-to-target mapping for enhanced logging
        self.sensor_mappings = {}  # {sensor_mac: {"sensor_id": "55:50", "target_num": 2, "stage": "Go Fast"}}
        self.current_sensor_mac = None  # Track which sensor triggered the notification
        self.bt50_clients = []  # List of all connected BT50 clients"""

new_sensor_init = """        # Sensor-to-target mapping for enhanced logging
        self.sensor_mappings = {}  # {sensor_mac: {"sensor_id": "55:50", "target_num": 2, "stage": "Go Fast"}}
        self.current_sensor_mac = None  # Track which sensor triggered the notification
        self.bt50_clients = []  # List of all connected BT50 clients
        
        # Per-sensor calibration data
        self.sensor_calibration = {}  # {sensor_mac: {"samples": [], "baseline": {}, "complete": False}}
        self.calibration_target_count = 100  # Samples per sensor"""

content = content.replace(old_sensor_init, new_sensor_init)

# 2. Update calibration notification handler to track per-sensor data
old_calibration_handler = """    async def calibration_notification_handler(self, characteristic, data):
        \"\"\"Collect calibration samples during startup\"\"\"
        if not self.collecting_calibration:
            return

        # For calibration, parse data even if shot_detector import failed
        try:
            if PARSER_AVAILABLE:
                # Use the imported parser
                result = parse_5561(data)
                if result and result[ samples]:
                    # Collect raw values from all samples in this notification
                    for sample in result[samples]:
                        vx_raw, vy_raw, vz_raw = sample[raw]
                        self.calibration_samples.append({
                            vx_raw: vx_raw,
                            vy_raw: vy_raw,
                            vz_raw: vz_raw,
                            timestamp: time.time()
                        })

                        # Stop when we have enough samples
                        if len(self.calibration_samples) >= CALIBRATION_SAMPLES:
                            self.collecting_calibration = False

        except Exception as e:
            self.logger.error(f"Calibration data collection failed: {e}")"""

new_calibration_handler = """    async def calibration_notification_handler(self, characteristic, data):
        \"\"\"Collect calibration samples per sensor during startup\"\"\"
        if not self.collecting_calibration:
            return

        # Identify which sensor sent this data by finding the characteristics device
