#!/usr/bin/env python3

def initialize_database_with_current_sensors():
    """Initialize database with current sensor assignments from UI"""
    try:
        from src.impact_bridge.database.database import get_database_session, init_database
        from src.impact_bridge.database.models import Bridge, Sensor, StageConfig, TargetConfig
        from src.impact_bridge.config import DatabaseConfig
        
        db_config = DatabaseConfig()
        init_database(db_config)
        
        with get_database_session(db_config) as session:
            # Create Bridge MCU1 if it doesn't exist
            bridge = session.query(Bridge).filter_by(bridge_id="MCU1").first()
            if not bridge:
                bridge = Bridge(
                    bridge_id="MCU1",
                    name="Orange-GoFast Bridge",
                    current_stage="Go Fast"
                )
                session.add(bridge)
                session.flush()  # Get the bridge.id
                print("✅ Created Bridge: MCU1 (Orange-GoFast Bridge)")
            
            # Create sensors from current assignments
            sensors_to_create = [
                {
                    "hw_addr": "C2:1B:DB:F0:55:50",
                    "label": "WTVB01-BT50-55:50",
                    "sensor_type": "BT50",
                    "target_number": 2
                },
                {
                    "hw_addr": "CA:8B:D6:7F:76:5B", 
                    "label": "WTVB01-BT50-76:5B",
                    "sensor_type": "BT50",
                    "target_number": 3
                },
                {
                    "hw_addr": "60:09:C3:1F:DC:1A",
                    "label": "AMG Lab COMM DC1A",
                    "sensor_type": "AMG_TIMER",
                    "target_number": None
                }
            ]
            
            for sensor_data in sensors_to_create:
                existing_sensor = session.query(Sensor).filter_by(hw_addr=sensor_data["hw_addr"]).first()
                if not existing_sensor:
                    sensor = Sensor(
                        hw_addr=sensor_data["hw_addr"],
                        label=sensor_data["label"],
                        sensor_type=sensor_data["sensor_type"],
                        bridge_id=bridge.id
                    )
                    session.add(sensor)
                    print(f"✅ Created Sensor: {sensor_data['hw_addr']} ({sensor_data['label']})")
                else:
                    print(f"ℹ️ Sensor already exists: {sensor_data['hw_addr']}")
            
            session.commit()
            print("🎯 Database initialized with current sensor assignments!")
            print("🔄 Bridge will now load sensors from database instead of hardcoded values")
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    initialize_database_with_current_sensors()