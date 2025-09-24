#!/usr/bin/env python3

# Debug script to add sensor mapping logging

import re

def add_sensor_mapping_debug():
    # Read current file
    with open('leadville_bridge.py', 'r') as f:
        content = f.read()
    
    # Find where we store sensor mappings and add debug logging
    pattern = r'(self\.sensor_mappings\[sensor_mac\] = \{.*?\})'
    
    def add_debug_after_mapping(match):
        original = match.group(1)
        debug_lines = '\n                    # DEBUG: Log the sensor mapping that was just stored\n                    self.logger.info(f"🔍 DEBUG: Stored mapping for {sensor_mac} -> {self.sensor_mappings[sensor_mac]}")'
        return original + debug_lines
    
    # Apply the change
    modified_content = re.sub(pattern, add_debug_after_mapping, content, flags=re.DOTALL)
    
    if modified_content != content:
        # Write back to file
        with open('leadville_bridge.py', 'w') as f:
            f.write(modified_content)
        print("✅ Added sensor mapping debug logging")
        return True
    else:
        print("❌ Could not find pattern to add sensor mapping debug logging")
        return False

if __name__ == "__main__":
    success = add_sensor_mapping_debug()
    if success:
        print("🔧 Sensor mapping debug logging added.")
    else:
        print("❌ Failed to add sensor mapping debug logging.")