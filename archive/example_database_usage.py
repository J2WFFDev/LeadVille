#!/usr/bin/env python3
"""
Example integration of database with LeadVille Bridge

Shows how to store sensor events and timer events in the database.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from impact_bridge.config import DatabaseConfig
from impact_bridge.database import init_database, get_database_session, DatabaseCRUD


async def example_database_usage():
    """Example of using the database with sensor and timer events"""
    
    # Initialize database
    config = DatabaseConfig()
    init_database(config)
    print(f"✓ Database initialized: {config.path}")
    
    # Create some example data
    with get_database_session() as session:
        # Create a node (Pi device)
        node = DatabaseCRUD.nodes.create(
            session, 
            name="pi-leadville-01",
            mode="online",
            ip_addr="192.168.1.124"
        )
        print(f"✓ Created node: {node.name}")
        
        # Create sensors
        bt50_sensor = DatabaseCRUD.sensors.create(
            session,
            hw_addr="F8:FE:92:31:12:E3",
            label="BT50-001",
            node_id=node.id
        )
        print(f"✓ Created sensor: {bt50_sensor.label}")
        
        # Update sensor status (like you do in leadville_bridge.py)
        DatabaseCRUD.sensors.update_status(
            session,
            bt50_sensor.id,
            battery=85,
            rssi=-45,
            last_seen=datetime.utcnow()
        )
        print(f"✓ Updated sensor status")
        
        # Create timer events (like AMG timer)
        timer_start = DatabaseCRUD.timer_events.create(
            session,
            ts_utc=datetime.utcnow(),
            event_type="START",
            raw="AMG Timer Start Event"
        )
        
        timer_shot = DatabaseCRUD.timer_events.create(
            session,
            ts_utc=datetime.utcnow(),
            event_type="SHOT",
            raw="AMG Timer Shot #1"
        )
        print(f"✓ Created timer events")
        
        # Create sensor events (like BT50 impacts)
        impact_event = DatabaseCRUD.sensor_events.create(
            session,
            ts_utc=datetime.utcnow(),
            sensor_id=bt50_sensor.id,
            magnitude=194.9,
            features_json={
                "raw_value": 1900.0,
                "threshold": 150.0,
                "device_id": "BT50-001"
            }
        )
        print(f"✓ Created sensor impact event")
        
        # Query recent events
        recent_timer_events = DatabaseCRUD.timer_events.list_recent(session, limit=10)
        recent_sensor_events = DatabaseCRUD.sensor_events.list_recent(session, limit=10)
        
        print(f"\n📊 Recent Events:")
        print(f"  Timer events: {len(recent_timer_events)}")
        print(f"  Sensor events: {len(recent_sensor_events)}")
        
        # Show system stats
        stats = DatabaseCRUD.get_system_stats(session)
        print(f"\n📈 Database Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


def integration_example():
    """
    Example of how to integrate database calls into your existing leadville_bridge.py
    
    In your existing code, you would add database calls like this:
    """
    
    print("\n" + "="*60)
    print("INTEGRATION EXAMPLE FOR LEADVILLE_BRIDGE.PY")
    print("="*60)
    
    example_code = '''
# At the top of leadville_bridge.py, add:
from impact_bridge.database import init_database, get_database_session, DatabaseCRUD
from impact_bridge.config import DatabaseConfig

# In your Bridge.__init__() method, add:
def __init__(self):
    # ... existing initialization code ...
    
    # Initialize database
    db_config = DatabaseConfig()
    init_database(db_config)
    self.logger.info(f"Database initialized: {db_config.path}")

# In your AMG timer event handler, add:
async def handle_amg_event(self, event_type: str, raw_data: str):
    # ... existing timer processing ...
    
    # Store in database
    with get_database_session() as session:
        DatabaseCRUD.timer_events.create(
            session,
            ts_utc=datetime.utcnow(),
            event_type=event_type,
            raw=raw_data
        )

# In your BT50 impact handler, add:
async def handle_bt50_impact(self, device_id: str, magnitude: float, raw_value: float):
    # ... existing impact processing ...
    
    # Store in database
    with get_database_session() as session:
        # Get sensor by hardware address
        sensor = DatabaseCRUD.sensors.get_by_hw_addr(session, device_id)
        if sensor:
            DatabaseCRUD.sensor_events.create(
                session,
                ts_utc=datetime.utcnow(),
                sensor_id=sensor.id,
                magnitude=magnitude,
                features_json={
                    "raw_value": raw_value,
                    "device_id": device_id
                }
            )
'''
    
    print(example_code)
    print("="*60)


if __name__ == "__main__":
    print("LeadVille Database Integration Example")
    print("=" * 40)
    
    # Run the example
    asyncio.run(example_database_usage())
    
    # Show integration example
    integration_example()
    
    print("\n✓ Example completed successfully!")
    print("\nNext steps:")
    print("1. Install requirements: pip install sqlalchemy alembic")
    print("2. Run: python manage_db.py init")
    print("3. Integrate database calls in leadville_bridge.py")
    print("4. Test with: python example_database_usage.py")