#!/usr/bin/env python3

import re

def fix_dynamic_sensor_loading():
    with open("leadville_bridge.py", "r") as f:
        content = f.read()
    
    # Find the Bridge initialization and add dynamic sensor loading
    init_pattern = r"(def __init__\(self\):.*?# Sensor-to-target mapping for enhanced logging)"
    
    def add_dynamic_loading(match):
        init_code = match.group(1)
        new_code = init_code + """
        
        # Load Bridge-assigned sensors from database (replaces hardcoded sensors)
        print("🔄 Loading Bridge-assigned sensors from database...")
        bridge_devices = get_bridge_assigned_devices()
        
        if bridge_devices:
            # Build BT50_SENSORS list from database assignments
            self.bt50_sensors = []
            
            # Get all BT50 sensors assigned to this Bridge
            try:
                from src.impact_bridge.database.database import get_database_session, init_database
                from src.impact_bridge.database.models import Bridge, Sensor, TargetConfig
                from src.impact_bridge.config import DatabaseConfig
                
                db_config = DatabaseConfig()
                init_database(db_config)
                
                with get_database_session(db_config) as session:
                    # Get Bridge ID (assuming we're using Bridge MCU1)
                    bridge = session.query(Bridge).filter_by(bridge_id="MCU1").first()
                    if bridge:
                        # Get sensors assigned to this Bridge's targets
                        sensors = session.query(Sensor).filter_by(bridge_id=bridge.id).all()
                        
                        for sensor in sensors:
                            if "BT50" in sensor.label.upper():
                                self.bt50_sensors.append(sensor.hw_addr)
                                print(f"🎯 Loaded BT50 sensor: {sensor.hw_addr} ({sensor.label})")
                        
                        print(f"✅ Loaded {len(self.bt50_sensors)} BT50 sensors from database")
                    else:
                        print("⚠️ Bridge MCU1 not found in database, using hardcoded sensors")
                        self.bt50_sensors = BT50_SENSORS
                        
            except Exception as e:
                print(f"⚠️ Failed to load sensors from database: {e}")
                print("🔄 Falling back to hardcoded sensors")
                self.bt50_sensors = BT50_SENSORS
        else:
            print("⚠️ No Bridge-assigned devices found, using hardcoded sensors")
            self.bt50_sensors = BT50_SENSORS"""
        
        return new_code
    
    content = re.sub(init_pattern, add_dynamic_loading, content, flags=re.DOTALL)
    
    # Update the connect_devices method to use self.bt50_sensors instead of BT50_SENSORS
    content = re.sub(r"BT50_SENSORS\[i\]", "self.bt50_sensors[i]", content)
    content = re.sub(r"len\(BT50_SENSORS\)", "len(self.bt50_sensors)", content)
    content = re.sub(r"for i in range\(len\(BT50_SENSORS\)\):", "for i in range(len(self.bt50_sensors)):", content)
    
    with open("leadville_bridge.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed Bridge to load sensors dynamically from database")
    print("🎯 Bridge will now use sensor assignments from Stage Setup UI")
    print("🔄 Sensors will be loaded from database instead of hardcoded values")

if __name__ == "__main__":
    fix_dynamic_sensor_loading()