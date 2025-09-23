#!/usr/bin/env python3
"""
Create Bridge table and add bridge_id column to sensors
Manual database migration for Bridge support
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_bridge_table():
    """Create Bridge table and update sensors table"""
    try:
        from src.impact_bridge.database.models import Base, Bridge, Sensor
        from src.impact_bridge.config import DatabaseConfig
        from sqlalchemy import create_engine, text
        
        # Initialize database
        config = DatabaseConfig()
        config.dir = str(project_root)
        config.file = "leadville.db"
        
        engine = create_engine(f"sqlite:///{config.path}")
        
        print("Creating Bridge table and updating sensors...")
        
        # Create all tables (including Bridge)
        Base.metadata.create_all(engine)
        
        with engine.connect() as conn:
            # Check if bridge_id column exists in sensors table
            result = conn.execute(text("PRAGMA table_info(sensors)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'bridge_id' not in columns:
                print("Adding bridge_id column to sensors table...")
                conn.execute(text("ALTER TABLE sensors ADD COLUMN bridge_id INTEGER"))
                conn.execute(text("CREATE INDEX idx_sensor_bridge ON sensors(bridge_id)"))
            else:
                print("bridge_id column already exists in sensors table")
            
            # Create default Bridge if none exists
            result = conn.execute(text("SELECT COUNT(*) FROM bridges"))
            bridge_count = result.fetchone()[0]
            
            if bridge_count == 0:
                print("Creating default Bridge...")
                conn.execute(text("""
                    INSERT INTO bridges (name, bridge_id, created_at, updated_at) 
                    VALUES ('Default Bridge', 'bridge-001', datetime('now'), datetime('now'))
                """))
                
                # Assign existing sensors to the default Bridge
                conn.execute(text("""
                    UPDATE sensors 
                    SET bridge_id = (SELECT id FROM bridges WHERE bridge_id = 'bridge-001' LIMIT 1)
                    WHERE bridge_id IS NULL
                """))
                
                print("Assigned existing sensors to default Bridge")
            
            conn.commit()
        
        print("✅ Bridge table creation completed successfully!")
        
        # Verify the setup
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name, bridge_id FROM bridges"))
            bridges = result.fetchall()
            print(f"Bridges in database: {bridges}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM sensors WHERE bridge_id IS NOT NULL"))
            sensor_count = result.fetchone()[0]
            print(f"Sensors assigned to Bridges: {sensor_count}")
        
    except Exception as e:
        print(f"❌ Error creating Bridge table: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_bridge_table()