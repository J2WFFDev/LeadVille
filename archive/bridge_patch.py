#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Add the Bridge device lookup method after the logging setup
bridge_method = """
    def get_bridge_assigned_devices(self):
        \"\"\"Get devices assigned to this Bridge from database\"\"\"
        try:
            from src.impact_bridge.database.database import get_database_session
            from src.impact_bridge.database.models import Bridge, Sensor
            
            with get_database_session() as session:
                # Get the first/default Bridge
                bridge = session.query(Bridge).first()
                if not bridge:
                    self.logger.warning("No Bridge found in database - using hardcoded devices")
                    return {}
                    
                # Get sensors assigned to this Bridge
                sensors = session.query(Sensor).filter_by(bridge_id=bridge.id).all()
                device_map = {}
                
                for sensor in sensors:
                    label = sensor.label.lower()
                    if "timer" in label or "amg" in label:
                        device_map["amg_timer"] = sensor.hw_addr
                        self.logger.info(f"🎯 Bridge-assigned AMG timer: {sensor.hw_addr} ({sensor.label})")
                    elif "bt50" in label:
                        device_map["bt50_sensor"] = sensor.hw_addr  
                        self.logger.info(f"🎯 Bridge-assigned BT50 sensor: {sensor.hw_addr} ({sensor.label})")
                        
                return device_map
                
        except Exception as e:
            self.logger.error(f"Failed to get Bridge-assigned devices: {e}")
            return {}
"""

# Find where to insert the method (after class definition)
class_line = content.find("class ")
if class_line == -1:
    print("Could not find class definition")
    exit(1)

# Find the first method after class definition to insert before it
insert_pos = content.find("    def ", class_line)
if insert_pos == -1:
    print("Could not find method insertion point")
    exit(1)

# Insert the Bridge method
new_content = content[:insert_pos] + bridge_method + "\n" + content[insert_pos:]

# Replace hardcoded MAC usage in connect_devices method
old_connect = """        devices = [BT50_SENSOR_MAC, AMG_TIMER_MAC]"""
new_connect = """        # Get Bridge-assigned devices
        assigned_devices = self.get_bridge_assigned_devices()
        
        # Use Bridge-assigned devices or fall back to hardcoded
        amg_timer_mac = assigned_devices.get("amg_timer", AMG_TIMER_MAC)
        bt50_sensor_mac = assigned_devices.get("bt50_sensor", BT50_SENSOR_MAC)
        
        devices = [bt50_sensor_mac, amg_timer_mac]"""

new_content = new_content.replace(old_connect, new_connect)

# Replace AMG timer connection
old_amg = """            self.amg_client = BleakClient(AMG_TIMER_MAC)"""
new_amg = """            self.amg_client = BleakClient(amg_timer_mac)"""
new_content = new_content.replace(old_amg, new_amg)

# Replace BT50 sensor connection  
old_bt50 = """            self.bt50_client = BleakClient(BT50_SENSOR_MAC)"""
new_bt50 = """            self.bt50_client = BleakClient(bt50_sensor_mac)"""
new_content = new_content.replace(old_bt50, new_bt50)

# Write the patched file
with open("leadville_bridge.py", "w") as f:
    f.write(new_content)

print("✅ Bridge-enhanced leadville_bridge.py created successfully!")
