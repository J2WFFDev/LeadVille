#!/usr/bin/env python3

import sqlite3
from datetime import datetime

# Connect to main database
main_db = sqlite3.connect("leadville.db")
main_cursor = main_db.cursor()

try:
    # Create bridges table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS bridges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        bridge_id VARCHAR(50) UNIQUE NOT NULL,
        current_stage_id INTEGER,
        match_id INTEGER,
        match_name VARCHAR(100),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    main_cursor.execute(create_table_sql)
    
    # Insert Orange-GoFast Bridge
    now = datetime.now().isoformat()
    insert_sql = """
    INSERT OR REPLACE INTO bridges 
    (name, bridge_id, current_stage_id, match_id, match_name, created_at, updated_at) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    main_cursor.execute(insert_sql, (
        "Orange-GoFast", 
        "MCP-001", 
        3,  # Go Fast stage ID
        None, 
        None, 
        now, 
        now
    ))
    
    main_db.commit()
    print("✅ Orange-GoFast Bridge created in main database")
    
    # Verify creation
    main_cursor.execute("SELECT * FROM bridges")
    bridges = main_cursor.fetchall()
    print(f"Bridges in main database: {len(bridges)}")
    for bridge in bridges:
        print(f"  ID:{bridge[0]} {bridge[1]} ({bridge[2]}) -> Stage {bridge[3]}")
        
    # Verify sensor assignments
    main_cursor.execute("SELECT hw_addr, label, bridge_id FROM sensors WHERE bridge_id IS NOT NULL")
    sensors = main_cursor.fetchall()
    print(f"Sensors assigned to Bridge: {len(sensors)}")
    for sensor in sensors:
        print(f"  {sensor[1]}: {sensor[0]} -> Bridge {sensor[2]}")
        
finally:
    main_db.close()

print("Bridge setup complete!")
