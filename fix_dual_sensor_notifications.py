#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# 1. Add a list to store all BT50 clients in __init__
old_sensor_mappings = """        # Sensor-to-target mapping for enhanced logging
        self.sensor_mappings = {}  # {sensor_mac: {"sensor_id": "55:50", "target_num": 2, "stage": "Go Fast"}}
        self.current_sensor_mac = None  # Track which sensor triggered the notification"""

new_sensor_mappings = """        # Sensor-to-target mapping for enhanced logging
        self.sensor_mappings = {}  # {sensor_mac: {"sensor_id": "55:50", "target_num": 2, "stage": "Go Fast"}}
        self.current_sensor_mac = None  # Track which sensor triggered the notification
        self.bt50_clients = []  # List of all connected BT50 clients for multi-sensor notifications"""

content = content.replace(old_sensor_mappings, new_sensor_mappings)

# 2. Store all connected clients in the connection loop
old_client_storage = """                    # Use first sensor as primary for compatibility
                    if i == 0:
                        self.bt50_client = client

                    self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target {target_num})")"""

new_client_storage = """                    # Store all clients for multi-sensor notifications
                    self.bt50_clients.append(client)
                    
                    # Use first sensor as primary for compatibility
                    if i == 0:
                        self.bt50_client = client

                    self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target {target_num})")"""

content = content.replace(old_client_storage, new_client_storage)

# 3. Update calibration to use all sensors
old_calibration_start = """        # Start calibration notifications
        try:
            await self.bt50_client.start_notify(BT50_SENSOR_UUID, self.calibration_notification_handler)"""

new_calibration_start = """        # Start calibration notifications on all sensors
        try:
            # Enable notifications for all connected BT50 sensors
            for client in self.bt50_clients:
                await client.start_notify(BT50_SENSOR_UUID, self.calibration_notification_handler)
            self.logger.debug(f"Calibration notifications enabled on {len(self.bt50_clients)} sensors")"""

content = content.replace(old_calibration_start, new_calibration_start)

# 4. Update calibration completion to switch all sensors to impact notifications
old_switch_notifications = """            # Switch back to normal notification handler
            await self.bt50_client.stop_notify(BT50_SENSOR_UUID)
            await self.bt50_client.start_notify(BT50_SENSOR_UUID, self.bt50_notification_handler)

            # Show listening status
            self.logger.info("📝 Status: Sensor 12:E3 - Listening")"""

new_switch_notifications = """            # Switch all sensors to impact notification handler
            for i, client in enumerate(self.bt50_clients):
                await client.stop_notify(BT50_SENSOR_UUID)
                await client.start_notify(BT50_SENSOR_UUID, self.bt50_notification_handler)
                sensor_id = BT50_SENSORS[i][-5:].replace(":", "")
                self.logger.debug(f"Impact notifications enabled for sensor {sensor_id}")

            # Show listening status for all sensors
            self.logger.info(f"📝 Status: All {len(self.bt50_clients)} sensors - Listening")"""

content = content.replace(old_switch_notifications, new_switch_notifications)

# 5. Update the final notification message
old_final_message = """            self.logger.info("BT50 sensor and impact notifications enabled")"""

new_final_message = """            self.logger.info(f"BT50 sensors ({len(self.bt50_clients)}) and impact notifications enabled")"""

content = content.replace(old_final_message, new_final_message)

# Write the enhanced file
with open("leadville_bridge.py", "w") as f:
    f.write(content)

print("✅ Fixed dual sensor notifications!")
print("Changes made:")
print("  - Added bt50_clients list to store all connected sensors")
print("  - Enable calibration notifications on all sensors")
print("  - Switch all sensors to impact notifications after calibration")
print("  - Updated logging to reflect multi-sensor status")
