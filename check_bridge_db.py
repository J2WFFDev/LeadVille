#!/usr/bin/env python3
"""Check bridge.db schema"""

import sqlite3

def check_bridge_db():
    try:
        conn = sqlite3.connect('db/bridge.db')
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(sensors)")
        columns = cursor.fetchall()
        
        print("bridge.db sensors columns:")
        column_names = []
        for col in columns:
            print(f"  {col[1]}: {col[2]}")
            column_names.append(col[1])
        
        print(f"Has target_config_id: {'target_config_id' in column_names}")
        
        # Count sensors
        cursor.execute("SELECT COUNT(*) FROM sensors")
        count = cursor.fetchone()[0]
        print(f"Sensors count: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_bridge_db()