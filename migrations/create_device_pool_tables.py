"""
Device Pool Management Migration
Adds tables for shared device pool, session management, and temporary assignments.
"""

import sqlite3
import sys
from pathlib import Path

def create_device_pool_tables(db_path: str):
    """Create device pool management tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create device_pool table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_pool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hw_addr VARCHAR(17) NOT NULL UNIQUE,
                device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('timer', 'sensor', 'shot_timer', 'other')),
                label VARCHAR(100) NOT NULL,
                vendor VARCHAR(50),
                model VARCHAR(50),
                status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'leased', 'offline', 'maintenance')),
                last_seen DATETIME,
                battery INTEGER CHECK (battery >= 0 AND battery <= 100),
                rssi INTEGER CHECK (rssi >= -100 AND rssi <= 0),
                notes TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for device_pool
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pool_hw_addr ON device_pool (hw_addr)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pool_status ON device_pool (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pool_device_type ON device_pool (device_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pool_last_seen ON device_pool (last_seen)")
        
        # Create active_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name VARCHAR(100) NOT NULL,
                bridge_id INTEGER NOT NULL,
                stage_id INTEGER,
                status VARCHAR(20) NOT NULL DEFAULT 'idle' CHECK (status IN ('active', 'idle', 'ended')),
                started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                last_activity DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY(bridge_id) REFERENCES bridges(id),
                FOREIGN KEY(stage_id) REFERENCES stages(id)
            )
        """)
        
        # Create indexes for active_sessions
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_bridge ON active_sessions (bridge_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_status ON active_sessions (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_started ON active_sessions (started_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_stage ON active_sessions (stage_id)")
        
        # Create device_leases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_leases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                session_id INTEGER NOT NULL,
                target_assignment VARCHAR(50),
                leased_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                released_at DATETIME,
                is_connected BOOLEAN NOT NULL DEFAULT FALSE,
                connection_attempts INTEGER NOT NULL DEFAULT 0,
                last_connection_attempt DATETIME,
                notes TEXT,
                CHECK (released_at IS NULL OR released_at >= leased_at),
                FOREIGN KEY(device_id) REFERENCES device_pool(id),
                FOREIGN KEY(session_id) REFERENCES active_sessions(id)
            )
        """)
        
        # Create indexes for device_leases
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lease_device ON device_leases (device_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lease_session ON device_leases (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lease_active ON device_leases (device_id, released_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lease_leased_at ON device_leases (leased_at)")
        
        # Create device_pool_events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_pool_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                session_id INTEGER,
                event_type VARCHAR(20) NOT NULL CHECK (event_type IN ('lease', 'release', 'connect', 'disconnect', 'status_change', 'discovered', 'error')),
                event_data TEXT,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(device_id) REFERENCES device_pool(id),
                FOREIGN KEY(session_id) REFERENCES active_sessions(id)
            )
        """)
        
        # Create indexes for device_pool_events
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pool_event_device ON device_pool_events (device_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pool_event_session ON device_pool_events (session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pool_event_timestamp ON device_pool_events (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pool_event_type ON device_pool_events (event_type)")
        
        # Create trigger to update updated_at on device_pool
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_device_pool_timestamp 
            AFTER UPDATE ON device_pool
            BEGIN
                UPDATE device_pool SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        """)
        
        # Create trigger to update last_activity on active_sessions when device_leases change
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_session_activity 
            AFTER INSERT ON device_leases
            BEGIN
                UPDATE active_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = NEW.session_id;
            END
        """)
        
        conn.commit()
        print("✅ Device pool management tables created successfully")
        
        # Show table summary
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%pool%' OR name LIKE '%session%' OR name LIKE '%lease%'")
        tables = cursor.fetchall()
        print(f"📋 Created {len(tables)} device pool tables: {', '.join([t[0] for t in tables])}")
        
    except Exception as e:
        print(f"❌ Error creating device pool tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_existing_sensors_to_pool(db_path: str):
    """Migrate existing sensors to device pool (optional)"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if there are existing sensors to migrate
        cursor.execute("SELECT COUNT(*) FROM sensors")
        sensor_count = cursor.fetchone()[0]
        
        if sensor_count == 0:
            print("📝 No existing sensors to migrate")
            return
        
        # Get all sensors currently assigned to targets
        cursor.execute("""
            SELECT DISTINCT hw_addr, label 
            FROM sensors 
            WHERE hw_addr IS NOT NULL 
            AND target_id IS NOT NULL
        """)
        assigned_sensors = cursor.fetchall()
        
        print(f"🔄 Found {len(assigned_sensors)} assigned sensors to add to pool")
        
        for hw_addr, label in assigned_sensors:
            # Add to device pool if not already there
            cursor.execute("""
                INSERT OR IGNORE INTO device_pool (hw_addr, device_type, label, status)
                VALUES (?, 'sensor', ?, 'leased')
            """, (hw_addr, label))
        
        conn.commit()
        print(f"✅ Added {len(assigned_sensors)} existing sensors to device pool")
        
    except Exception as e:
        print(f"❌ Error migrating sensors: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python create_device_pool_tables.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"❌ Database file does not exist: {db_path}")
        sys.exit(1)
    
    print(f"🚀 Creating device pool tables in: {db_path}")
    
    try:
        create_device_pool_tables(db_path)
        migrate_existing_sensors_to_pool(db_path)
        print("✅ Device Pool Management migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()