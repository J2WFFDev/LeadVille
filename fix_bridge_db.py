#!/usr/bin/env python3

# Read the current leadville_bridge.py
with open("leadville_bridge.py", "r") as f:
    content = f.read()

# Replace the Bridge lookup function with a version that initializes the database
old_function = """def get_bridge_assigned_devices():
    \"\"\"Get devices assigned to this Bridge from database\"\"\"
    try:
        from src.impact_bridge.database.database import get_database_session
        from src.impact_bridge.database.models import Bridge, Sensor
        
        with get_database_session() as session:
            bridge = session.query(Bridge).first()
            if not bridge:
                return {}
                
            sensors = session.query(Sensor).filter_by(bridge_id=bridge.id).all()
            device_map = {}
            
            for sensor in sensors:
                label = sensor.label.lower()
                if \"timer\" in label or \"amg\" in label:
                    device_map[\"amg_timer\"] = sensor.hw_addr
                    print(f\"🎯 Bridge-assigned AMG timer: {sensor.hw_addr} ({sensor.label})\")
                elif \"bt50\" in label:
                    device_map[\"bt50_sensor\"] = sensor.hw_addr  
                    print(f\"🎯 Bridge-assigned BT50 sensor: {sensor.hw_addr} ({sensor.label})\")
                    
            return device_map
            
    except Exception as e:
        print(f\"Failed to get Bridge-assigned devices: {e}\")
        return {}"""

new_function = """def get_bridge_assigned_devices():
    \"\"\"Get devices assigned to this Bridge from database\"\"\"
    try:
        from src.impact_bridge.database.database import get_database_session, init_database
        from src.impact_bridge.database.models import Bridge, Sensor
        from src.impact_bridge.config import DatabaseConfig
        
        # Initialize database
        db_config = DatabaseConfig()
        init_database(db_config)
        
        with get_database_session() as session:
            bridge = session.query(Bridge).first()
            if not bridge:
                print("No Bridge found in database")
                return {}
                
            sensors = session.query(Sensor).filter_by(bridge_id=bridge.id).all()
            device_map = {}
            
            print(f\"Found {len(sensors)} sensors assigned to Bridge {bridge.name}\")
            
            for sensor in sensors:
                label = sensor.label.lower()
                if \"timer\" in label or \"amg\" in label:
                    device_map[\"amg_timer\"] = sensor.hw_addr
                    print(f\"🎯 Bridge-assigned AMG timer: {sensor.hw_addr} ({sensor.label})\")
                elif \"bt50\" in label:
                    device_map[\"bt50_sensor\"] = sensor.hw_addr  
                    print(f\"🎯 Bridge-assigned BT50 sensor: {sensor.hw_addr} ({sensor.label})\")
                    
            return device_map
            
    except Exception as e:
        print(f\"Failed to get Bridge-assigned devices: {e}\")
        return {}"""

# Replace the function
new_content = content.replace(old_function, new_function)

# Write the updated file
with open("leadville_bridge.py", "w") as f:
    f.write(new_content)

print("✅ Bridge database initialization fixed!")
