#!/usr/bin/env python3
"""
Fix get_current_sensor_info to use proper database configuration
"""

import re

def fix_database_config():
    # Read the current leadville_bridge.py file
    with open('leadville_bridge.py', 'r') as f:
        content = f.read()

    # Find the get_current_sensor_info function and fix the database session usage
    old_pattern = r'# Import database components\s+from src\.impact_bridge\.database\.models import Sensor, TargetConfig, StageConfig, Bridge\s+from src\.impact_bridge\.database\.database import get_database_session\s+with get_database_session\(\) as session:'
    
    new_code = '''# Import database components
                from src.impact_bridge.database.models import Sensor, TargetConfig, StageConfig, Bridge
                from src.impact_bridge.database.database import get_database_session, init_database
                from src.impact_bridge.config import DatabaseConfig
                
                # Initialize database with proper config
                db_config = DatabaseConfig()
                init_database(db_config)
                
                with get_database_session() as session:'''
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_code, content)
        
        # Write the updated content back to the file
        with open('leadville_bridge.py', 'w') as f:
            f.write(content)
        
        print("✅ Fixed get_current_sensor_info to use proper database configuration")
    else:
        print("❌ Could not find the database session pattern to replace")
        print("Searching for alternative patterns...")
        
        # Try a simpler pattern
        simple_pattern = r'with get_database_session\(\) as session:'
        if re.search(simple_pattern, content):
            print("Found simpler pattern, trying to replace...")
            # Replace the import section and session call
            content = re.sub(
                r'from src\.impact_bridge\.database\.database import get_database_session\s+with get_database_session\(\) as session:',
                '''from src.impact_bridge.database.database import get_database_session, init_database
                from src.impact_bridge.config import DatabaseConfig
                
                # Initialize database with proper config
                db_config = DatabaseConfig()
                init_database(db_config)
                
                with get_database_session() as session:''',
                content
            )
            
            # Write the updated content back to the file
            with open('leadville_bridge.py', 'w') as f:
                f.write(content)
            
            print("✅ Fixed database configuration with simpler pattern")
        else:
            print("❌ Could not find any database session pattern to replace")

if __name__ == "__main__":
    fix_database_config()