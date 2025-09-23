#!/usr/bin/env python3

# Script to remove all debug logging we added

import re

def remove_debug_logging():
    # Read current file
    with open('leadville_bridge.py', 'r') as f:
        content = f.read()
    
    changes_made = []
    
    # Remove debug logging from bt50_notification_handler
    pattern1 = r'\n        # DEBUG: Log which sensor MAC we\'re using\n        self\.logger\.info\(f"🔍 DEBUG: bt50_notification_handler called with sensor_mac=\{sensor_mac\}"\)'
    if re.search(pattern1, content):
        content = re.sub(pattern1, '', content)
        changes_made.append("Removed bt50_notification_handler debug logging")
    
    # Remove debug logging from get_current_sensor_info
    pattern2 = r'\n        # DEBUG: Log what sensor_mac was passed and what mappings we have\n        self\.logger\.info\(f"🔍 DEBUG: get_current_sensor_info called with sensor_mac=\{sensor_mac\}"\)\n        self\.logger\.info\(f"🔍 DEBUG: Available sensor_mappings: \{list\(self\.sensor_mappings\.keys\(\)\)\}"\)\n        if sensor_mac and sensor_mac in self\.sensor_mappings:\n            self\.logger\.info\(f"🔍 DEBUG: Found exact match for \{sensor_mac\}: \{self\.sensor_mappings\[sensor_mac\]\}"\)\n        else:\n            self\.logger\.info\(f"🔍 DEBUG: No exact match found, will use fallback"\)'
    if re.search(pattern2, content):
        content = re.sub(pattern2, '', content)
        changes_made.append("Removed get_current_sensor_info debug logging")
    
    # Remove debug logging from sensor mapping storage
    pattern3 = r'\n                    # DEBUG: Log the sensor mapping that was just stored\n                    self\.logger\.info\(f"🔍 DEBUG: Stored mapping for \{sensor_mac\} -> \{self\.sensor_mappings\[sensor_mac\]\}"\)'
    if re.search(pattern3, content):
        content = re.sub(pattern3, '', content)
        changes_made.append("Removed sensor mapping storage debug logging")
    
    if changes_made:
        # Write back to file
        with open('leadville_bridge.py', 'w') as f:
            f.write(content)
        
        print("✅ Successfully removed debug logging:")
        for change in changes_made:
            print(f"   - {change}")
        return True
    else:
        print("❌ No debug logging patterns found to remove")
        return False

if __name__ == "__main__":
    success = remove_debug_logging()
    if success:
        print("🧹 Console log should now be clean of debug noise!")
    else:
        print("🤔 Nothing to clean up.")