#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Update to include both BT50 sensors from your Stage Setup
old_mac_section = """# Your discovered device MAC addresses (Orange-GoFast Bridge)
AMG_TIMER_MAC = "60:09:C3:1F:DC:1A"  # AMG Lab COMM DC1A
BT50_SENSOR_MAC = "EA:18:3D:6D:BA:E5"  # WTVB01-BT50-BA:E5 (Target 1)"""

new_mac_section = """# Your discovered device MAC addresses (Orange-GoFast Bridge - Go Fast Stage)
AMG_TIMER_MAC = "60:09:C3:1F:DC:1A"  # AMG Lab COMM DC1A

# Multiple BT50 sensors for Go Fast stage targets
BT50_SENSORS = [
    "EA:18:3D:6D:BA:E5",  # WTVB01-BT50-BA:E5 (Target 1)
    "C2:1B:DB:F0:55:50"   # WTVB01-BT50-55:50 (Target 2) 
]
BT50_SENSOR_MAC = BT50_SENSORS[0]  # Primary sensor for compatibility"""

# Replace the MAC section
new_content = content.replace(old_mac_section, new_mac_section)

# Update the devices list to include all BT50 sensors
old_devices_line = """        devices = [bt50_sensor_mac, amg_timer_mac]"""
new_devices_line = """        devices = BT50_SENSORS + [amg_timer_mac]"""

new_content = new_content.replace(old_devices_line, new_devices_line)

# Write the updated file
with open("leadville_bridge.py", "w") as f:
    f.write(new_content)

print("✅ Updated Bridge to connect to both BT50 sensors!")
print("Target 1: EA:18:3D:6D:BA:E5") 
print("Target 2: C2:1B:DB:F0:55:50")
print("AMG Timer: 60:09:C3:1F:DC:1A")
