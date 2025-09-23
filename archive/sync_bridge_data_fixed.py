#!/usr/bin/env python3

import sqlite3

# Connect to both databases
bridge_db = sqlite3.connect("db/bridge.db")
main_db = sqlite3.connect("leadville.db")

try:
    # Get Bridge data from bridge.db
    bridge_cursor = bridge_db.cursor()
    bridge_cursor.execute("SELECT * FROM bridges")
    bridge_rows = bridge_cursor.fetchall()
    
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
        insert_sql = "INSERT OR REPLACE INTO bridges (id, name, bridge_id, current_stage_id, match_id, match_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        
        for row in bridge_rows:
            main_cursor.execute(insert_sql, row)
            
        main_db.commit()
        print("✅ Bridge data copied to main database")
        
        # Verify the copy
        main_cursor.execute("SELECT name, bridge_id FROM bridges")
        copied_bridges = main_cursor.fetchall()
        for name, bridge_id in copied_bridges:
            print(f"  - {name} ({bridge_id})")
            
    # Update sensor bridge assignments
    main_cursor = main_db.cursor()
    
    # Add bridge_id column if it doesnt exist
    try:
        main_cursor.execute("ALTER TABLE sensors ADD COLUMN bridge_id INTEGER")
        main_db.commit()
        print("Added bridge_id column to sensors table")
    except sqlite3.OperationalError:
        print("bridge_id column already exists in sensors table")
    
    # Assign all sensors to the first Bridge (Orange-GoFast)
    main_cursor.execute("UPDATE sensors SET bridge_id = 1")
    main_db.commit()
    print("✅ All sensors assigned to Bridge 1")
        
finally:
    bridge_db.close()
    main_db.close()

print("Database synchronization complete!")
