#!/usr/bin/env python3

import sqlite3
import json

# Connect to both databases
bridge_db = sqlite3.connect("db/bridge.db")
main_db = sqlite3.connect("leadville.db")

try:
    # Get Bridge data from bridge.db
    bridge_cursor = bridge_db.cursor()
    bridge_cursor.execute("SELECT * FROM bridges")
    bridge_rows = bridge_cursor.fetchall()
    
    # Get column names
    bridge_cursor.execute("PRAGMA table_info(bridges)")
    bridge_columns = [col[1] for col in bridge_cursor.fetchall()]
    
    print(f"Found {len(bridge_rows)} bridges in bridge.db")
    
    if bridge_rows:
        # Create bridges table in main database if it doesnt exist
        main_cursor = main_db.cursor()
        
        # Create the table structure
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bridges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            bridge_id VARCHAR(50) UNIQUE NOT NULL,
            current_stage_id INTEGER,
            match_id INTEGER,
            match_name VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (current_stage_id) REFERENCES stage_configs (id)
        )
        """
        main_cursor.execute(create_table_sql)
        
        # Insert Bridge data
        placeholders = "?" + ",?" * (len(bridge_columns) - 1)
        insert_sql = f"INSERT OR REPLACE INTO bridges ({ .join(bridge_columns)}) VALUES ({placeholders})"
        
        for row in bridge_rows:
            main_cursor.execute(insert_sql, row)
            
        main_db.commit()
        print("✅ Bridge data copied to main database")
        
        # Verify the copy
        main_cursor.execute("SELECT name, bridge_id FROM bridges")
        copied_bridges = main_cursor.fetchall()
        for name, bridge_id in copied_bridges:
            print(f"  - {name} ({bridge_id})")
            
    # Get sensor data and update bridge_id assignments
    bridge_cursor.execute("SELECT * FROM sensors WHERE bridge_id IS NOT NULL")
    sensor_rows = bridge_cursor.fetchall()
    
    if sensor_rows:
        print(f"Found {len(sensor_rows)} sensors with bridge assignments")
        
        # Update sensors in main database
        main_cursor = main_db.cursor()
        
        # Add bridge_id column if it doesnt exist
        try:
            main_cursor.execute("ALTER TABLE sensors ADD COLUMN bridge_id INTEGER")
            main_db.commit()
            print("Added bridge_id column to sensors table")
        except sqlite3.OperationalError:
            print("bridge_id column already exists in sensors table")
        
        # Update sensor bridge assignments
        for sensor in sensor_rows:
            # Find sensor by hw_addr and update bridge_id
            main_cursor.execute("UPDATE sensors SET bridge_id = ? WHERE hw_addr = ?", 
                              (sensor[9], sensor[1]))  # Assuming bridge_id is column 9, hw_addr is column 1
        
        main_db.commit()
        print("✅ Sensor bridge assignments updated")
        
finally:
    bridge_db.close()
    main_db.close()

print("Database synchronization complete!")
