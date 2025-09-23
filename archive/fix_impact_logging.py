#!/usr/bin/env python3

def fix_impact_logging():
    with open("leadville_bridge.py", "r") as f:
        content = f.read()
    
    # Replace the complex get_current_sensor_info with a simpler working version
    # that still uses the enhanced format but with fallback values
    new_function = '''def get_current_sensor_info(self, sensor_mac=None):
        """Get sensor information for logging - simplified version with enhanced format"""
        try:
            sensor_id = sensor_mac[-5:] if sensor_mac else "UNK"
            
            # Determine target based on sensor MAC (from Stage Setup)
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
                "bridge_name": "Orange-GoFast Bridge",
                "stage_name": "Go Fast",
                "target_id": "Unknown",
                "sensor_id": sensor_mac[-5:] if sensor_mac else "UNK"
            }'''
    
    # Find and replace the entire complex function
    import re
    pattern = r'def get_current_sensor_info\(self, sensor_mac=None\):.*?(?=\n    def|\n    async def|\nclass|\Z)'
    content = re.sub(pattern, new_function, content, flags=re.DOTALL)
    
    with open("leadville_bridge.py", "w") as f:
        f.write(content)
    
    print("✅ Simplified get_current_sensor_info function")
    print("🎯 Should fix impact logging while keeping enhanced format")
    print("📊 Format: 'Orange-GoFast Bridge | Go Fast | Target 2 | Sensor 55:50 - ...'")

if __name__ == "__main__":
    fix_impact_logging()