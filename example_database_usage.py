#!/usr/bin/env python3
"""Example script demonstrating database usage in LeadVille Impact Bridge."""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from impact_bridge.config import DatabaseConfig
from impact_bridge.database import (
    initialize_database,
    get_database_session,
    get_database_info,
    DatabaseCRUD,
)


def main():
    """Demonstrate database functionality."""
    print("🎯 LeadVille Impact Bridge - Database Example")
    print("=" * 50)
    
    # Configure database
    config = DatabaseConfig(
        dir="./example_db",
        file="example.db",
        echo_sql=False  # Set to True to see SQL queries
    )
    
    # Initialize database
    print("\n📊 Initializing database...")
    initialize_database(config)
    
    # Get database info
    info = get_database_info(config)
    print(f"✅ Database initialized: {info['database_path']}")
    print(f"   SQLite version: {info['sqlite_version']}")
    print(f"   Tables created: {len(info['tables'])}")
    
    # Demo data creation
    print("\n🏗️  Creating demo data...")
    
    with get_database_session(config) as session:
        # Create a node (Raspberry Pi)
        node = DatabaseCRUD.nodes.create(
            session,
            name="leadville-pi-01",
            mode="simulation",
            ssid="LeadVille-Range",
            ip_addr="192.168.1.100",
            versions={"software": "2.0.0", "firmware": "1.3.2"}
        )
        print(f"   📡 Created node: {node.name} ({node.mode})")
        
        # Create sensors
        sensor1 = DatabaseCRUD.sensors.create(
            session,
            hw_addr="F8:FE:92:31:12:E3",
            label="BT50-Target-1",
            node_id=node.id,
            battery=87.5,
            rssi=-42
        )
        
        sensor2 = DatabaseCRUD.sensors.create(
            session,
            hw_addr="F8:FE:92:31:12:E4",
            label="BT50-Target-2", 
            node_id=node.id,
            battery=91.2,
            rssi=-38
        )
        print(f"   📳 Created sensors: {sensor1.label}, {sensor2.label}")
        
        # Create a match
        match = DatabaseCRUD.matches.create(
            session,
            name="Monthly Practice Match",
            date=datetime(2024, 1, 15, 9, 0, 0),
            location="LeadVille Shooting Range",
            metadata_json={
                "type": "practice",
                "rounds": 150,
                "weather": "sunny, 72°F"
            }
        )
        print(f"   🏆 Created match: {match.name}")
        
        # Create stages
        stage1 = DatabaseCRUD.stages.create(
            session,
            match_id=match.id,
            name="El Presidente",
            number=1,
            layout_json={
                "targets": 3,
                "distance": "7 yards",
                "par_time": 10.0,
                "scoring": "comstock"
            }
        )
        
        stage2 = DatabaseCRUD.stages.create(
            session,
            match_id=match.id,
            name="Ball and Dummy",
            number=2,
            layout_json={
                "targets": 2,
                "distance": "15 yards", 
                "par_time": 15.0,
                "scoring": "virginia count"
            }
        )
        print(f"   🎯 Created stages: {stage1.name}, {stage2.name}")
        
        # Create targets
        target1 = DatabaseCRUD.targets.create(
            session,
            stage_id=stage1.id,
            name="T1-Center",
            geometry={
                "type": "IPSC",
                "position": {"x": 0, "y": 7, "z": 1.4},
                "scoring_zones": ["A", "C", "D"]
            },
            notes="Standard IPSC target, center position"
        )
        print(f"   🎯 Created target: {target1.name}")
        
        # Assign sensor to target
        DatabaseCRUD.sensors.update(
            session,
            sensor1.id,
            target_id=target1.id
        )
        print(f"   🔗 Assigned {sensor1.label} to {target1.name}")
        
        # Create shooters
        shooter1 = DatabaseCRUD.shooters.create(
            session,
            name="John Smith",
            squad="Alpha",
            metadata_json={
                "division": "Production",
                "class": "A",
                "member_id": "12345"
            }
        )
        
        shooter2 = DatabaseCRUD.shooters.create(
            session,
            name="Jane Doe",
            squad="Alpha", 
            metadata_json={
                "division": "Carry Optics",
                "class": "B",
                "member_id": "67890"
            }
        )
        print(f"   🎯 Created shooters: {shooter1.name}, {shooter2.name}")
        
        # Create a run
        run = DatabaseCRUD.runs.create(
            session,
            match_id=match.id,
            stage_id=stage1.id,
            shooter_id=shooter1.id
        )
        print(f"   🏃 Created run for {shooter1.name} on {stage1.name}")
        
        # Simulate run lifecycle
        print("\n⏱️  Simulating run lifecycle...")
        
        # Start the run
        DatabaseCRUD.runs.start_run(session, run.id)
        print(f"   ✅ Run started")
        
        # Create timer events
        start_time = datetime.utcnow()
        timer_start = DatabaseCRUD.timer_events.create(
            session,
            ts_utc=start_time,
            event_type="START",
            raw="AMG_START_0x0105",
            run_id=run.id
        )
        
        # Simulate shots
        shot_time1 = datetime.utcnow()
        timer_shot1 = DatabaseCRUD.timer_events.create(
            session,
            ts_utc=shot_time1,
            event_type="SHOT",
            raw="AMG_SHOT_0x0103",
            run_id=run.id
        )
        
        # Simulate sensor impacts
        impact_time1 = datetime.utcnow()
        sensor_impact = DatabaseCRUD.sensor_events.create(
            session,
            ts_utc=impact_time1,
            sensor_id=sensor1.id,
            magnitude=18.5,
            features_json={
                "peak_magnitude": 18.5,
                "duration_ms": 45,
                "onset_threshold": 3.2,
                "correlation_confidence": 0.95
            },
            run_id=run.id
        )
        
        print(f"   🔫 Timer events: START, SHOT")
        print(f"   💥 Sensor impact: {sensor_impact.magnitude}g on {sensor1.label}")
        
        # Add notes
        note = DatabaseCRUD.notes.create(
            session,
            run_id=run.id,
            author_role="RO",
            content="Clean run, no procedural penalties. Good shooting!",
            shooter_id=shooter1.id
        )
        print(f"   📝 Added RO note")
        
        # Finish the run
        DatabaseCRUD.runs.finish_run(session, run.id, "completed")
        print(f"   🏁 Run completed")
    
    # Show final statistics
    print("\n📈 Final Statistics:")
    final_info = get_database_info(config)
    for table, count in final_info['tables'].items():
        if count > 0:
            print(f"   {table}: {count} records")
    
    print(f"\n💾 Database file: {final_info['database_path']}")
    print(f"   Size: {final_info['file_size_mb']} MB")
    
    print("\n✅ Database example completed successfully!")
    print("   You can inspect the database file with any SQLite browser.")


if __name__ == "__main__":
    main()