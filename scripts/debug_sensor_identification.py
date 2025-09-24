#!/usr/bin/env python3

# Quick debug script to add sensor MAC logging to the bt50_notification_handler

import re

def add_sensor_debug_logging():
    # Read current file
    with open('leadville_bridge.py', 'r') as f:
        content = f.read()
    
    # Find the bt50_notification_handler function and add debug logging right after the sensor_mac assignment
    pattern = r'(async def bt50_notification_handler\(self, characteristic, data, sensor_mac=None\):.*?sensor_mac = "UNKNOWN:SENSOR")'
    
    def add_debug_after_sensor_assignment(match):
        original = match.group(1)
        debug_line = '\n        # DEBUG: Log which sensor MAC we\'re using\n        self.logger.info(f"🔍 DEBUG: bt50_notification_handler called with sensor_mac={sensor_mac}")'
        return original + debug_line
    
    # Apply the change
    modified_content = re.sub(pattern, add_debug_after_sensor_assignment, content, flags=re.DOTALL)
    
    if modified_content != content:
        # Write back to file
        with open('leadville_bridge.py', 'w') as f:
            f.write(modified_content)
        print("✅ Added sensor MAC debug logging to bt50_notification_handler")
        return True
    else:
        print("❌ Could not find pattern to add debug logging")
        return False

if __name__ == "__main__":
    success = add_sensor_debug_logging()
    if success:
        print("🔧 Debug logging added. You can now restart the service to see which sensor MAC is being used.")
    else:
        print("❌ Failed to add debug logging. Check the file manually.")