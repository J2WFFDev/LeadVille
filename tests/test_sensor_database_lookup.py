#!/usr/bin/env python3
"""
Test the database lookup for sensor-to-target mapping
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.impact_bridge.database.models import Sensor, TargetConfig, StageConfig, Bridge
    from src.impact_bridge.database.database import get_database_session, init_database
    from src.impact_bridge.config import DatabaseConfig
    
    print("Testing database lookup for sensor mappings...")
    
    # Initialize database
    db_config = DatabaseConfig()
    init_database(db_config)
    
    test_macs = ["C2:1B:DB:F0:55:50", "CA:8B:D6:7F:76:5B"]
    
    with get_database_session() as session:
        for mac in test_macs:
            print(f"\nTesting MAC: {mac}")
            
            # Find the sensor by MAC address
            sensor = session.query(Sensor).filter(Sensor.hw_addr == mac).first()
            
            if sensor:
                print(f"  ✅ Found sensor: {sensor.label}")
                print(f"  📍 Bridge ID: {sensor.bridge_id}")
                print(f"  🎯 Target Config ID: {sensor.target_config_id}")
                
                if sensor.target_config_id:
                    # Get target configuration
                    target = session.query(TargetConfig).filter(TargetConfig.id == sensor.target_config_id).first()
                    if target:
                        print(f"  🏹 Target Number: {target.target_number}")
                        
                        # Get stage information
                        stage = session.query(StageConfig).filter(StageConfig.id == target.stage_config_id).first()
                        stage_name = stage.name if stage else "Unknown Stage"
                        print(f"  🏟️ Stage: {stage_name}")
                        
                        # Get bridge information
                        bridge = session.query(Bridge).filter(Bridge.id == sensor.bridge_id).first()
                        bridge_name = bridge.name if bridge else "Unknown Bridge"
                        print(f"  🌉 Bridge: {bridge_name}")
                        
                        print(f"  📝 Result: {bridge_name} | {stage_name} | Target {target.target_number} | {mac[-5:]}")
                    else:
                        print(f"  ❌ Target config not found for ID {sensor.target_config_id}")
                else:
                    print(f"  ⚠️ No target assigned to sensor")
            else:
                print(f"  ❌ Sensor not found")
                
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()