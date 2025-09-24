#!/usr/bin/env python3

# Debug script to add detailed logging to get_current_sensor_info

import re

def add_sensor_info_debug():
    # Read current file
    with open('leadville_bridge.py', 'r') as f:
        content = f.read()
    
    # Find the get_current_sensor_info function and add detailed debug logging
    pattern = r'(def get_current_sensor_info\(self, sensor_mac=None\):.*?"""Get sensor information for logging based on specific sensor MAC""")'
    
    def add_debug_to_function(match):
        original = match.group(1)
        debug_lines = '\n        # DEBUG: Log what sensor_mac was passed and what mappings we have\n        self.logger.info(f"🔍 DEBUG: get_current_sensor_info called with sensor_mac={sensor_mac}")\n        self.logger.info(f"🔍 DEBUG: Available sensor_mappings: {list(self.sensor_mappings.keys())}")\n        if sensor_mac and sensor_mac in self.sensor_mappings:\n            self.logger.info(f"🔍 DEBUG: Found exact match for {sensor_mac}: {self.sensor_mappings[sensor_mac]}")\n        else:\n            self.logger.info(f"🔍 DEBUG: No exact match found, will use fallback")'
        return original + debug_lines
    
    # Apply the change
    modified_content = re.sub(pattern, add_debug_to_function, content, flags=re.DOTALL)
    
    if modified_content != content:
        # Write back to file
        with open('leadville_bridge.py', 'w') as f:
            f.write(modified_content)
        print("✅ Added detailed debug logging to get_current_sensor_info")
        return True
    else:
        print("❌ Could not find pattern to add debug logging")
        return False

if __name__ == "__main__":
    success = add_sensor_info_debug()
    if success:
        print("🔧 Detailed sensor info debug logging added.")
    else:
        print("❌ Failed to add sensor info debug logging.")