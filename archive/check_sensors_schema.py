#!/usr/bin/env python3
"""Check sensors table schema"""

import sqlite3

def check_sensors_schema():
    try:
        conn = sqlite3.connect('/home/jrwest/projects/LeadVille/leadville.db')
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(sensors)")
        columns = cursor.fetchall()
        
        print("Current sensors table schema:")
        for column in columns:
            print(f"  {column[1]}: {column[2]} {'NOT NULL' if column[3] else 'NULL'} {'DEFAULT ' + str(column[4]) if column[4] else ''}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    check_sensors_schema()