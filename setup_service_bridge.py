#!/usr/bin/env python3

# Use the same database initialization that the service uses
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.impact_bridge.database.database import get_database_session, init_database
from src.impact_bridge.database.models import Bridge, Sensor
from src.impact_bridge.config import DatabaseConfig
from datetime import datetime

# Initialize database exactly like the service does
db_config = DatabaseConfig()
print(f"Database config path: {db_config.path}")
init_database(db_config)

with get_database_session() as session:
    # Create Orange-GoFast Bridge
    bridge = Bridge(
        name="Orange-GoFast",
        bridge_id="MCP-001", 
        current_stage_id=3,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    session.add(bridge)
    session.commit()
    session.refresh(bridge)
    
    print(f"✅ Created Bridge: {bridge.name} (ID: {bridge.id})")
    
    # Update sensor assignments
    sensors = session.query(Sensor).all()
    print(f"Found {len(sensors)} sensors to assign")
    
    for sensor in sensors:
        sensor.bridge_id = bridge.id
        print(f"  Assigned {sensor.label} to Bridge {bridge.id}")
    
    session.commit()
    print("✅ All sensors assigned to Bridge")
    
    # Verify the setup
    bridge_check = session.query(Bridge).first()
    if bridge_check:
        assigned_sensors = session.query(Sensor).filter_by(bridge_id=bridge_check.id).all()
        print(f"✅ Verification: Bridge {bridge_check.name} has {len(assigned_sensors)} sensors")
        for sensor in assigned_sensors:
            print(f"  - {sensor.label}: {sensor.hw_addr}")
    else:
        print("❌ Bridge verification failed")
        
print("Service database setup complete!")
