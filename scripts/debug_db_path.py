#!/usr/bin/env python3
"""Debug database path and column existence"""

import sqlite3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def check_database_path():
    # Check different possible database locations
    paths = [
        '/home/jrwest/projects/LeadVille/leadville.db',
        '/home/jrwest/projects/LeadVille/database.db', 
        'leadville.db',
        'database.db'
    ]
    
    print("=== Checking Database Paths ===")
    for path in paths:
        if os.path.exists(path):
            print(f"✓ Found: {path}")
            size = os.path.getsize(path)
            print(f"  Size: {size} bytes")
            
            # Check if sensors table exists and has target_config_id
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(sensors)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'target_config_id' in column_names:
                    print(f"  ✓ sensors.target_config_id exists")
                else:
                    print(f"  ✗ sensors.target_config_id missing")
                    print(f"  Available columns: {column_names}")
                
                # Count sensors
                cursor.execute("SELECT COUNT(*) FROM sensors")
                count = cursor.fetchone()[0]
                print(f"  Sensors count: {count}")
                
                conn.close()
            except Exception as e:
                print(f"  Error accessing database: {e}")
        else:
            print(f"✗ Not found: {path}")
    
    print("\n=== Testing SQLAlchemy Connection ===")
    try:
        # Test with the path from session.py
        db_path = "sqlite:////home/jrwest/projects/LeadVille/leadville.db"
        engine = create_engine(db_path)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM sensors"))
            count = result.scalar()
            print(f"SQLAlchemy connection successful, sensors count: {count}")
            
            # Test the problematic query
            try:
                result = conn.execute(text("SELECT target_config_id FROM sensors LIMIT 1"))
                print("✓ target_config_id column accessible via SQLAlchemy")
            except Exception as e:
                print(f"✗ target_config_id column error: {e}")
                
    except SQLAlchemyError as e:
        print(f"SQLAlchemy connection error: {e}")

if __name__ == "__main__":
    check_database_path()