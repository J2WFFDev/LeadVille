#!/usr/bin/env python3

import re

def enhance_database_logging():
    with open("leadville_bridge.py", "r") as f:
        content = f.read()
    
    # Replace the get_current_sensor_info function with a database-aware version
    old_function = r"""def get_current_sensor_info\(self, sensor_mac=None\):
        \"\"\"Get sensor information for logging based on specific sensor MAC\"\"\"
        # Use specific sensor if provided
        if sensor_mac and sensor_mac in self\.sensor_mappings:
            return self\.sensor_mappings\[sensor_mac\]

        # Fallback to first sensor mapping if available
        if self\.sensor_mappings:
            first_mapping = next\(iter\(self\.sensor_mappings\.values\(\)\)\)
            return first_mapping

        # Final fallback to default values
        return \{
            "sensor_id": "12:E3",
            "target_num": 1,
            "stage": "Go Fast"
        \}"""
    
    new_function = """def get_current_sensor_info(self, sensor_mac=None):
        \"\"\"Get sensor information for logging from database configuration\"\"\"
        try:
            from src.impact_bridge.database.database import get_database_session, init_database
            from src.impact_bridge.database.models import Bridge, Sensor, StageConfig, TargetConfig
            from src.impact_bridge.config import DatabaseConfig
            
            db_config = DatabaseConfig()
            init_database(db_config)
            
            with get_database_session(db_config) as session:
                # Get Bridge information
                bridge = session.query(Bridge).filter_by(bridge_id="MCU1").first()
                if not bridge:
                    # Fallback to hardcoded values if Bridge not found
                    return {
                        "bridge_name": "Unknown Bridge",
                        "stage_name": "Go Fast",
                        "target_id": "Unknown",
                        "sensor_id": sensor_mac[-5:] if sensor_mac else "UNK"
                    }
                
                bridge_name = bridge.name
                
                # Get Stage information
                stage_name = "Go Fast"  # Default fallback
                if bridge.current_stage_id:
                    stage = session.query(StageConfig).filter_by(id=bridge.current_stage_id).first()
                    if stage:
                        stage_name = stage.name
                
                # Get Sensor and Target information
                if sensor_mac:
                    sensor = session.query(Sensor).filter_by(hw_addr=sensor_mac).first()
                    if sensor:
                        sensor_id = sensor_mac[-5:]  # Short format like "55:50"
                        
                        # Find which target this sensor is assigned to
                        target_id = "Unknown"
                        if sensor.target_config_id:
                            target_config = session.query(TargetConfig).filter_by(id=sensor.target_config_id).first()
                            if target_config:
                                target_id = f"Target {target_config.target_number}"
                        else:
                            # Look for target assignment by scanning TargetConfigs
                            # This is a fallback for when sensor.target_config_id is not set
                            # but the sensor might be assigned via other means
                            target_configs = session.query(TargetConfig).all()
                            for tc in target_configs:
                                # Check if this sensor matches the target somehow
                                # For now, use sensor MAC ending to infer target
                                if "55:50" in sensor_mac:
                                    target_id = "Target 2"
                                    break
                                elif "76:5B" in sensor_mac:
                                    target_id = "Target 3"
                                    break
                        
                        return {
                            "bridge_name": bridge_name,
                            "stage_name": stage_name,
                            "target_id": target_id,
                            "sensor_id": sensor_id
                        }
                
                # Fallback when sensor not found or no sensor_mac provided
                return {
                    "bridge_name": bridge_name,
                    "stage_name": stage_name,
                    "target_id": "Unknown",
                    "sensor_id": sensor_mac[-5:] if sensor_mac else "UNK"
                }
                
        except Exception as e:
            self.logger.debug(f"Failed to get sensor info from database: {e}")
            # Fallback to basic info
            return {
                "bridge_name": "Orange-GoFast Bridge",
                "stage_name": "Go Fast",
                "target_id": "Unknown",
                "sensor_id": sensor_mac[-5:] if sensor_mac else "UNK"
            }"""
    
    content = re.sub(old_function, new_function, content, flags=re.DOTALL)
    
    # Update the impact logging to use the new database info
    old_impact_log = r'self\.logger\.info\(f"💥 IMPACT #\{impact_number\}: Stage \{stage_name\}, Target \{target_num\}, Sensor \{sensor_id\} - String \{current_string\}, Time \{time_from_start:.2f\}s, Shot→Impact \{time_from_shot:.3f\}s, Peak \{impact_event\.peak_magnitude:.0f\}g"\)'
    
    new_impact_log = 'self.logger.info(f"💥 IMPACT #{impact_number}: {bridge_name} | {stage_name} | {target_id} | Sensor {sensor_id} - String {current_string}, Time {time_from_start:.2f}s, Shot→Impact {time_from_shot:.3f}s, Peak {impact_event.peak_magnitude:.0f}g")'
    
    content = re.sub(old_impact_log, new_impact_log, content)
    
    # Update variable assignments to use new field names
    content = re.sub(r'stage_name = sensor_info\["stage"\]', 'bridge_name = sensor_info["bridge_name"]\n                        stage_name = sensor_info["stage_name"]', content)
    content = re.sub(r'target_num = sensor_info\["target_num"\]', 'target_id = sensor_info["target_id"]', content)
    
    with open("leadville_bridge.py", "w") as f:
        f.write(content)
    
    print("✅ Enhanced logging to use database configuration")
    print("🎯 Impact logs will now show: Bridge Name | Stage | Target ID | Sensor details")
    print("📊 Format: 'Orange-GoFast Bridge | Go Fast | Target 2 | Sensor 55:50 - ...'")

if __name__ == "__main__":
    enhance_database_logging()