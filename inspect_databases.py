#!/usr/bin/env python3
"""
Quick database inspector for LeadVille databases
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

def inspect_database(db_path: str):
    """Inspect database contents"""
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔍 Inspecting: {db_path}")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Tables: {', '.join(tables)}")
        
        # Check timer_events if it exists
        if 'timer_events' in tables:
            print(f"\n⏰ TIMER_EVENTS:")
            cursor.execute("SELECT COUNT(*) FROM timer_events")
            count = cursor.fetchone()[0]
            print(f"   Total records: {count}")
            
            if count > 0:
                # Get column info
                cursor.execute("PRAGMA table_info(timer_events)")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"   Columns: {', '.join(columns)}")
                
                # Show recent records
                if 'ts_ns' in columns:
                    cursor.execute("""
                        SELECT ts_ns, event_type, device_id, current_shot, string_total_time 
                        FROM timer_events 
                        ORDER BY ts_ns DESC 
                        LIMIT 5
                    """)
                else:
                    cursor.execute("""
                        SELECT * FROM timer_events 
                        ORDER BY rowid DESC 
                        LIMIT 3
                    """)
                
                print(f"   Recent records:")
                for row in cursor.fetchall():
                    if 'ts_ns' in columns and row[0]:
                        timestamp = datetime.fromtimestamp(row[0] / 1e9).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"     {timestamp} | {row[1:4]} | shot: {row[3]} | time: {row[4]}")
                    else:
                        print(f"     {row}")
        
        # Check impacts if it exists
        if 'impacts' in tables:
            print(f"\n💥 IMPACTS:")
            cursor.execute("SELECT COUNT(*) FROM impacts")
            count = cursor.fetchone()[0]
            print(f"   Total records: {count}")
            
            if count > 0:
                cursor.execute("PRAGMA table_info(impacts)")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"   Columns: {', '.join(columns)}")
                
                cursor.execute("SELECT * FROM impacts ORDER BY rowid DESC LIMIT 3")
                print(f"   Recent records:")
                for row in cursor.fetchall():
                    print(f"     {row}")
        
        # Check sensor_events if it exists
        if 'sensor_events' in tables:
            print(f"\n🎯 SENSOR_EVENTS:")
            cursor.execute("SELECT COUNT(*) FROM sensor_events")
            count = cursor.fetchone()[0]
            print(f"   Total records: {count}")
            
            if count > 0:
                cursor.execute("PRAGMA table_info(sensor_events)")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"   Columns: {', '.join(columns)}")
                
                cursor.execute("SELECT * FROM sensor_events ORDER BY rowid DESC LIMIT 3")
                print(f"   Recent records:")
                for row in cursor.fetchall():
                    print(f"     {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")

def main():
    project_root = "/home/jrwest/projects/LeadVille"
    
    # Check all databases
    databases = [
        "db/leadville.db",
        "db/leadville_runtime.db", 
        "logs/bt50_samples.db",
        "logs/bt50_samples_backup_20250922_114521.db"
    ]
    
    for db_path in databases:
        full_path = f"{project_root}/{db_path}"
        if Path(full_path).exists():
            inspect_database(full_path)
            print()

if __name__ == "__main__":
    main()