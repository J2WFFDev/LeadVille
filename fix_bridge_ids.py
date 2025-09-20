#!/usr/bin/env python3

import sqlite3

# Connect to main database
main_db = sqlite3.connect("leadville.db")
main_cursor = main_db.cursor()

try:
    # Check current state
    main_cursor.execute("SELECT id, name, bridge_id FROM bridges")
    bridges = main_cursor.fetchall()
    print("Current bridges:")
    for bridge in bridges:
        print(f"  ID:{bridge[0]} {bridge[1]} ({bridge[2]})")
    
    # Update sensor assignments to point to the correct Bridge ID
    if bridges:
        correct_bridge_id = bridges[0][0]  # Use the first Bridge ID
        main_cursor.execute("UPDATE sensors SET bridge_id = ?", (correct_bridge_id,))
        main_db.commit()
        print(f"✅ Updated all sensors to Bridge ID {correct_bridge_id}")
        
        # Verify the update
        main_cursor.execute("SELECT COUNT(*) FROM sensors WHERE bridge_id = ?", (correct_bridge_id,))
        sensor_count = main_cursor.fetchone()[0]
        print(f"Sensors assigned to Bridge {correct_bridge_id}: {sensor_count}")
        
finally:
    main_db.close()

print("Bridge ID fix complete!")
