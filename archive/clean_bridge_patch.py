#!/usr/bin/env python3

# Read the working leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    lines = f.readlines()

# Find the line with AMG_TIMER_MAC definition
for i, line in enumerate(lines):
    if "AMG_TIMER_MAC" in line and "=" in line:
        # Insert the Bridge method just before the MAC definitions
        bridge_method_lines = [
            "\n",
            "# Bridge-assigned device lookup method\n",
            "def get_bridge_assigned_devices():\n",
            "    \"\"\"Get devices assigned to this Bridge from database\"\"\"\n", 
            "    try:\n",
            "        from src.impact_bridge.database.database import get_database_session\n",
            "        from src.impact_bridge.database.models import Bridge, Sensor\n",
            "        \n",
            "        with get_database_session() as session:\n",
            "            bridge = session.query(Bridge).first()\n",
            "            if not bridge:\n",
            "                return {}\n",
            "                \n",
            "            sensors = session.query(Sensor).filter_by(bridge_id=bridge.id).all()\n",
            "            device_map = {}\n",
            "            \n",
            "            for sensor in sensors:\n",
            "                label = sensor.label.lower()\n",
            "                if \"timer\" in label or \"amg\" in label:\n",
            "                    device_map[\"amg_timer\"] = sensor.hw_addr\n",
            "                    print(f\"🎯 Bridge-assigned AMG timer: {sensor.hw_addr} ({sensor.label})\")\n",
            "                elif \"bt50\" in label:\n",
            "                    device_map[\"bt50_sensor\"] = sensor.hw_addr  \n",
            "                    print(f\"🎯 Bridge-assigned BT50 sensor: {sensor.hw_addr} ({sensor.label})\")\n",
            "                    \n",
            "            return device_map\n",
            "            \n",
            "    except Exception as e:\n",
            "        print(f\"Failed to get Bridge-assigned devices: {e}\")\n",
            "        return {}\n",
            "\n"
        ]
        
        # Insert the method before AMG_TIMER_MAC line
        lines = lines[:i] + bridge_method_lines + lines[i:]
        break

# Now update the MAC assignments to use Bridge devices
for i, line in enumerate(lines):
    if "AMG_TIMER_MAC = " in line:
        lines[i] = "# Get Bridge-assigned devices\nassigned_devices = get_bridge_assigned_devices()\n\n# Use Bridge-assigned or fallback to hardcoded\nAMG_TIMER_MAC = assigned_devices.get(\"amg_timer\", \"60:09:C3:1F:DC:1A\")\n"
    elif "BT50_SENSOR_MAC = " in line:
        lines[i] = "BT50_SENSOR_MAC = assigned_devices.get(\"bt50_sensor\", \"F8:FE:92:31:12:E3\")\n"

# Write the patched file
with open("leadville_bridge.py", "w") as f:
    f.writelines(lines)

print("✅ Clean Bridge patch applied successfully!")
