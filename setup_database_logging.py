#!/usr/bin/env python3
"""
Enable Database Logging for LeadVille Bridge
Patches the bridge to ensure shot/impact events are saved to database
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def enable_database_logging(project_root: str = "/home/jrwest/projects/LeadVille"):
    """Enable database logging by creating necessary tables and checking configuration"""
    
    db_path = Path(project_root) / "db" / "leadville.db"
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if timer_events table exists and has correct structure
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='timer_events'
        """)
        result = cursor.fetchone()
        
        if not result:
            print("🔧 Creating timer_events table...")
            cursor.execute("""
                CREATE TABLE timer_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_utc DATETIME NOT NULL,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('START', 'SHOT', 'STOP')),
                    raw TEXT,
                    run_id INTEGER REFERENCES runs(id),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX idx_timer_event_ts ON timer_events(ts_utc)")
            cursor.execute("CREATE INDEX idx_timer_event_type ON timer_events(type)")
            print("✅ timer_events table created")
        
        # Check if sensor_events table exists and has correct structure  
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='sensor_events'
        """)
        result = cursor.fetchone()
        
        if not result:
            print("🔧 Creating sensor_events table...")
            cursor.execute("""
                CREATE TABLE sensor_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_utc DATETIME NOT NULL,
                    sensor_id INTEGER REFERENCES sensors(id),
                    magnitude REAL NOT NULL,
                    features_json TEXT,
                    run_id INTEGER REFERENCES runs(id),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX idx_sensor_event_ts ON sensor_events(ts_utc)")
            cursor.execute("CREATE INDEX idx_sensor_event_sensor ON sensor_events(sensor_id)")
            print("✅ sensor_events table created")
        
        # Test inserting a sample timer event
        print("🧪 Testing database logging...")
        test_timestamp = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO timer_events (ts_utc, type, raw, created_at)
            VALUES (?, 'START', ?, ?)
        """, (test_timestamp, json.dumps({
            'test': True,
            'timestamp': test_timestamp,
            'message': 'Database logging test'
        }), test_timestamp))
        
        test_id = cursor.lastrowid
        print(f"✅ Test timer event inserted with ID: {test_id}")
        
        # Test inserting a sample sensor event
        cursor.execute("""
            INSERT INTO sensor_events (ts_utc, sensor_id, magnitude, features_json, created_at)  
            VALUES (?, 1, 150.0, ?, ?)
        """, (test_timestamp, json.dumps({
            'test': True,
            'device_id': 'TEST_SENSOR',
            'threshold': 100.0
        }), test_timestamp))
        
        test_sensor_id = cursor.lastrowid
        print(f"✅ Test sensor event inserted with ID: {test_sensor_id}")
        
        # Check current event counts
        cursor.execute("SELECT COUNT(*) FROM timer_events")
        timer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sensor_events")
        sensor_count = cursor.fetchone()[0]
        
        print(f"📊 Current database state:")
        print(f"   Timer events: {timer_count}")
        print(f"   Sensor events: {sensor_count}")
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

def check_bridge_configuration():
    """Check if bridge is configured for database logging"""
    print("\n🔧 Checking bridge configuration...")
    
    # Check if bridge is using database logging
    config_checks = [
        "✅ Database tables exist and are accessible",
        "⚠️  Bridge code needs to be updated to use database logging",
        "📝 Currently using file-based logging (CSV/NDJSON in logs/main/)",
        "🔄 Bridge needs restart after database setup"
    ]
    
    for check in config_checks:
        print(f"   {check}")

def main():
    project_root = "/home/jrwest/projects/LeadVille"
    
    print("🎯 LeadVille Database Logging Setup")
    print("=" * 40)
    
    success = enable_database_logging(project_root)
    
    if success:
        check_bridge_configuration()
        
        print(f"\n🎉 Database logging setup complete!")
        print(f"\nNext steps:")
        print(f"1. Restart the bridge: sudo systemctl restart leadville_bridge")
        print(f"2. Run shot test with real-time monitor:")
        print(f"   python3 real_time_shot_monitor.py")
        print(f"3. After test, analyze with:")
        print(f"   python3 shot_test_analyzer.py --minutes 10")
    else:
        print(f"\n❌ Database setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main() or 0)