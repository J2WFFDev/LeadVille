#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Replace the MAC address assignments with your actual sensor MACs
old_lines = """# Get Bridge-assigned devices
assigned_devices = get_bridge_assigned_devices()

# Use Bridge-assigned or fallback to hardcoded
AMG_TIMER_MAC = assigned_devices.get("amg_timer", "60:09:C3:1F:DC:1A")
BT50_SENSOR_MAC = assigned_devices.get("bt50_sensor", "F8:FE:92:31:12:E3")"""

new_lines = """# Your discovered device MAC addresses (Orange-GoFast Bridge)
AMG_TIMER_MAC = "60:09:C3:1F:DC:1A"  # AMG Lab COMM DC1A
BT50_SENSOR_MAC = "EA:18:3D:6D:BA:E5"  # WTVB01-BT50-BA:E5 (Target 1)"""

# Replace in the content
new_content = content.replace(old_lines, new_lines)

# Write the updated file
with open("leadville_bridge.py", "w") as f:
    f.write(new_content)

print("✅ Updated Bridge with your actual sensor MAC addresses!")
print("AMG Timer: 60:09:C3:1F:DC:1A")
print("BT50 Sensor: EA:18:3D:6D:BA:E5 (Target 1 sensor)")
