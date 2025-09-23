#!/usr/bin/env python3
"""
Fix database configuration to use leadville.db instead of db/bridge.db
"""

import re

def fix_database_path():
    # Read the current config.py file
    with open('src/impact_bridge/config.py', 'r') as f:
        content = f.read()

    # Replace the database configuration to point to leadville.db
    old_config = r'dir: str = "\./db"\s+file: str = "bridge\.db"'
    new_config = 'dir: str = "."\n    file: str = "leadville.db"'
    
    if re.search(old_config, content):
        content = re.sub(old_config, new_config, content)
        
        # Write the updated content back
        with open('src/impact_bridge/config.py', 'w') as f:
            f.write(content)
        
        print("✅ Updated database config to use leadville.db")
    else:
        print("❌ Could not find database config pattern to replace")
        print("Current database config section:")
        # Show the current database config for debugging
        config_match = re.search(r'@dataclass\s+class DatabaseConfig:.*?@property', content, re.DOTALL)
        if config_match:
            print(config_match.group(0))

if __name__ == "__main__":
    fix_database_path()