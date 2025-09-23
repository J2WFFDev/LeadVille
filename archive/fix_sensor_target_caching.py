#!/usr/bin/env python3
"""
Fix sensor target mapping caching issue
Replace hardcoded sensor-to-target mapping with dynamic database lookup
"""

import re

def fix_sensor_target_mapping():
    # Read the current leadville_bridge.py file
    with open('leadville_bridge.py', 'r') as f:
        content = f.read()

    # New get_current_sensor_info function that queries database for mappings
    new_function = '''def get_current_sensor_info(self, sensor_mac=None):
        """Get sensor information for logging - database-aware version"""
        try:
            sensor_id = sensor_mac[-5:] if sensor_mac else "UNK"

            # Query database for current sensor-to-target assignments
            try:
                # Import database components
                from src.impact_bridge.database.models import Sensor, TargetConfig, StageConfig, Bridge
                from src.impact_bridge.database.database import get_database_session
                
                with get_database_session() as session:
                    # Find the sensor by MAC address
                    sensor = session.query(Sensor).filter(Sensor.hw_addr == sensor_mac).first()
                    
                    if sensor and sensor.target_config_id:
                        # Get target configuration
                        target = session.query(TargetConfig).filter(TargetConfig.id == sensor.target_config_id).first()
                        if target:
                            target_id = f"Target {target.target_number}"
                            
                            # Get stage information
                            stage = session.query(StageConfig).filter(StageConfig.id == target.stage_config_id).first()
                            stage_name = stage.name if stage else "Unknown Stage"
                            
                            # Get bridge information
                            bridge = session.query(Bridge).filter(Bridge.id == sensor.bridge_id).first()
                            bridge_name = bridge.name if bridge else "Unknown Bridge"
                            
                            return {
                                "bridge_name": bridge_name,
                                "stage_name": stage_name,
                                "target_id": target_id,
                                "sensor_id": sensor_id
                            }
            
            except Exception as db_error:
                self.logger.debug(f"Database lookup failed: {db_error}")
            
            # Fallback: Use MAC-based mapping if database lookup fails
            target_id = "Unknown"
            if sensor_mac:
                if "55:50" in sensor_mac:
                    target_id = "Target 2"
                elif "76:5B" in sensor_mac:
                    target_id = "Target 3"
                else:
                    target_id = "Target 1"

            return {
                "bridge_name": "Orange-GoFast Bridge",
                "stage_name": "Go Fast",
                "target_id": target_id,
                "sensor_id": sensor_id
            }

        except Exception as e:
            self.logger.debug(f"Error in get_current_sensor_info: {e}")
            # Absolute fallback
            return {
                "bridge_name": "Default Bridge",
                "stage_name": "Default Stage", 
                "target_id": "Target 1",
                "sensor_id": sensor_mac[-5:] if sensor_mac else "UNK"
            }'''

    # Find and replace the existing get_current_sensor_info function
    pattern = r'def get_current_sensor_info\(self, sensor_mac=None\):.*?(?=\n    def|\n    async def|\nclass|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_function, content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open('leadville_bridge.py', 'w') as f:
            f.write(content)
        
        print("✅ Updated get_current_sensor_info to use database for sensor-to-target mapping")
    else:
        print("❌ Could not find get_current_sensor_info function to replace")

if __name__ == "__main__":
    fix_sensor_target_mapping()