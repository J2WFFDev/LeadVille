#!/usr/bin/env python3
"""
Create BT50 Samples Database for LeadVille Bridge
Creates the proper logs/bt50_samples.db with all required tables for shot/impact logging
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

def create_samples_database(project_root: str = "/home/jrwest/projects/LeadVille"):
    """Create the bt50_samples.db database with proper schema"""
    
    db_path = Path(project_root) / "logs" / "bt50_samples.db"
    
    # Ensure logs directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔧 Creating samples database: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Create bt50_samples table (raw sensor data)
        print("📊 Creating bt50_samples table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bt50_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_ns INTEGER DEFAULT (strftime('%s','now') || substr(strftime('%f','now'), 4, 6)),
                sensor_mac TEXT,
                frame_hex TEXT,
                parser TEXT,
                vx INTEGER, vy INTEGER, vz INTEGER,
                angle_x INTEGER, angle_y INTEGER, angle_z INTEGER,
                temp_raw INTEGER, temperature_c REAL,
                disp_x INTEGER, disp_y INTEGER, disp_z INTEGER,
                freq_x INTEGER, freq_y INTEGER, freq_z INTEGER
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bt50_samples_ts ON bt50_samples(ts_ns)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bt50_samples_mac ON bt50_samples(sensor_mac)")
        
        # Create timer_events table (AMG timer events)
        print("⏰ Creating timer_events table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timer_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_ns INTEGER,
                device_id TEXT,
                event_type TEXT,
                split_seconds REAL,
                split_cs INTEGER,
                raw_hex TEXT,
                current_shot INTEGER,
                total_shots INTEGER,
                current_round INTEGER,
                string_total_time REAL,
                parsed_json TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timer_events_ts ON timer_events(ts_ns)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timer_events_type ON timer_events(event_type)")
        
        # Create impacts table (detected impacts)
        print("💥 Creating impacts table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS impacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_mac TEXT,
                impact_ts_ns INTEGER,
                detection_ts_ns INTEGER,
                peak_mag REAL,
                pre_mag REAL,
                post_mag REAL,
                duration_ms REAL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_impacts_ts ON impacts(impact_ts_ns)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_impacts_mac ON impacts(sensor_mac)")
        
        # Create device_status table (current device status)
        print("📱 Creating device_status table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_status (
                sensor_mac TEXT PRIMARY KEY,
                last_seen_ns INTEGER,
                temperature_c REAL,
                temp_raw INTEGER,
                battery_pct REAL,
                battery_mv INTEGER,
                last_history_ns INTEGER
            )
        """)
        
        # Create device_status_history table (historical device status)
        print("📈 Creating device_status_history table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_mac TEXT,
                ts_ns INTEGER,
                temperature_c REAL,
                temp_raw INTEGER,
                battery_pct REAL,
                battery_mv INTEGER
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_history_ts ON device_status_history(ts_ns)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_history_mac ON device_status_history(sensor_mac)")
        
        # Create shot_log view (combines timer and impact events)
        print("🎯 Creating shot_log view...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS shot_log AS
            SELECT 
                id as log_id,
                'shot' as record_type,
                datetime(ts_ns/1e9, 'unixepoch') as event_time,
                device_id,
                event_type,
                current_shot,
                split_seconds,
                string_total_time,
                NULL as sensor_mac,
                NULL as impact_magnitude,
                ts_ns
            FROM timer_events
            UNION ALL
            SELECT
                id as log_id,
                'impact' as record_type, 
                datetime(impact_ts_ns/1e9, 'unixepoch') as event_time,
                sensor_mac as device_id,
                'IMPACT' as event_type,
                NULL as current_shot,
                NULL as split_seconds,
                NULL as string_total_time,
                sensor_mac,
                peak_mag as impact_magnitude,
                impact_ts_ns as ts_ns
            FROM impacts
            ORDER BY ts_ns
        """)
        
        # Create shot_log_simple view (simplified for dashboard)
        print("📋 Creating shot_log_simple view...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS shot_log_simple AS
            SELECT
                log_id,
                event_time,
                event_type,
                current_shot as shot_number,
                total_shots,
                split_seconds as shot_time,
                string_total_time,
                device_id as timer_device
            FROM (
                SELECT 
                    id as log_id,
                    datetime(ts_ns/1e9, 'unixepoch') as event_time,
                    event_type,
                    current_shot,
                    total_shots, 
                    split_seconds,
                    string_total_time,
                    device_id,
                    ts_ns
                FROM timer_events
                WHERE event_type IN ('START', 'SHOT', 'STOP')
                ORDER BY ts_ns
            )
        """)
        
        # Test inserting sample data
        print("🧪 Testing sample data insertion...")
        test_timestamp = int(datetime.now().timestamp() * 1e9)
        
        # Test timer event
        cursor.execute("""
            INSERT INTO timer_events (ts_ns, device_id, event_type, raw_hex)
            VALUES (?, 'TEST_TIMER', 'START', 'test_setup')
        """, (test_timestamp,))
        
        # Test impact event
        cursor.execute("""
            INSERT INTO impacts (sensor_mac, impact_ts_ns, detection_ts_ns, peak_mag, duration_ms)
            VALUES ('TEST_SENSOR', ?, ?, 150.0, 50.0)
        """, (test_timestamp, test_timestamp))
        
        # Test device status
        cursor.execute("""
            INSERT OR REPLACE INTO device_status 
            (sensor_mac, last_seen_ns, temperature_c, battery_pct)
            VALUES ('TEST_SENSOR', ?, 25.0, 85.0)
        """, (test_timestamp,))
        
        conn.commit()
        
        # Verify table creation
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='view' 
            ORDER BY name
        """)
        views = [row[0] for row in cursor.fetchall()]
        
        print(f"\n✅ Database created successfully!")
        print(f"📊 Tables: {', '.join(tables)}")
        print(f"👀 Views: {', '.join(views)}")
        
        # Show record counts
        cursor.execute("SELECT COUNT(*) FROM timer_events")
        timer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM impacts")
        impact_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bt50_samples")
        sample_count = cursor.fetchone()[0]
        
        print(f"\n📈 Current record counts:")
        print(f"   Timer events: {timer_count}")
        print(f"   Impacts: {impact_count}")  
        print(f"   BT50 samples: {sample_count}")
        
        # Test shot_log view
        cursor.execute("SELECT COUNT(*) FROM shot_log")
        shot_log_count = cursor.fetchone()[0]
        print(f"   Shot log entries: {shot_log_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database creation error: {e}")
        return False

def main():
    project_root = "/home/jrwest/projects/LeadVille"
    
    print("🎯 LeadVille BT50 Samples Database Setup")
    print("=" * 45)
    
    success = create_samples_database(project_root)
    
    if success:
        print(f"\n🎉 Samples database setup complete!")
        print(f"\n📍 Database location: logs/bt50_samples.db")
        print(f"\nNext steps:")
        print(f"1. Bridge will now write timer/impact events to this database")
        print(f"2. Run your shot test again")
        print(f"3. Use analysis tools:")
        print(f"   python3 shot_test_analyzer.py --minutes 10")
        print(f"   python3 real_time_shot_monitor.py")
        print(f"\n💡 Bridge should automatically detect and use this database!")
    else:
        print(f"\n❌ Database setup failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())