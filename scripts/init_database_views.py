#!/usr/bin/env python3
"""
Initialize and test database views for LeadVille Impact Bridge

Creates the shot_log and string_summary views and tests them with existing data.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from impact_bridge.database.database import init_database
from impact_bridge.database.views import create_shot_log_view, create_string_summary_view, drop_views
from impact_bridge.config import DatabaseConfig
from sqlalchemy import text
import sqlite3


def main():
    """Initialize views and test with existing data"""
    
    # Database configuration
    db_config = DatabaseConfig(
        dir="logs",
        file="bt50_samples.db",
        echo=False
    )
    
    print("🔧 Initializing database and views...")
    
    # Initialize database session
    db_session = init_database(db_config)
    engine = db_session.engine
    
    try:
        # Drop existing views (clean slate)
        print("🗑️  Dropping existing views...")
        drop_views(engine)
        
        # Create new views
        print("🏗️  Creating shot_log view...")
        create_shot_log_view(engine)
        
        print("📊 Creating string_summary view...")
        create_string_summary_view(engine)
        
        print("✅ Views created successfully!")
        
        # Test views with existing data
        print("\n🧪 Testing views with existing data...")
        test_views(engine)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


def test_views(engine):
    """Test the created views with existing data"""
    
    with engine.connect() as conn:
        
        # Test 1: Check if shot_log view exists and has data
        print("\n📋 Testing shot_log view...")
        try:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT run_id) as unique_runs,
                    COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) as shot_events,
                    COUNT(CASE WHEN event_status = 'correlated' THEN 1 END) as correlated_events,
                    COUNT(CASE WHEN event_status = 'timer_only' THEN 1 END) as timer_only_events
                FROM shot_log
            """)).fetchone()
            
            if result:
                print(f"   Total records: {result.total_records}")
                print(f"   Unique runs: {result.unique_runs}")
                print(f"   Shot events: {result.shot_events}")
                print(f"   Correlated events: {result.correlated_events}")
                print(f"   Timer-only events: {result.timer_only_events}")
            else:
                print("   No data found in shot_log view")
                
        except Exception as e:
            print(f"   Error testing shot_log: {e}")
        
        # Test 2: Show sample shot_log records
        print("\n📋 Sample shot_log records...")
        try:
            result = conn.execute(text("""
                SELECT 
                    log_id,
                    event_type,
                    shot_sequence,
                    timer_event_time,
                    impact_time,
                    correlation_quality,
                    event_status,
                    shot_time,
                    impact_magnitude
                FROM shot_log 
                ORDER BY timer_event_time DESC 
                LIMIT 5
            """)).fetchall()
            
            if result:
                for row in result:
                    print(f"   {row.log_id}: {row.event_type} | {row.event_status} | {row.correlation_quality}")
            else:
                print("   No sample records found")
                
        except Exception as e:
            print(f"   Error fetching samples: {e}")
        
        # Test 3: Check string_summary view
        print("\n📊 Testing string_summary view...")
        try:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_strings,
                    AVG(total_shots) as avg_shots_per_string,
                    AVG(final_time) as avg_final_time,
                    AVG(confirmed_hits) as avg_confirmed_hits
                FROM string_summary
            """)).fetchone()
            
            if result and result.total_strings > 0:
                print(f"   Total strings: {result.total_strings}")
                print(f"   Avg shots per string: {result.avg_shots_per_string:.1f}")
                print(f"   Avg final time: {result.avg_final_time:.2f}s" if result.avg_final_time else "   Avg final time: N/A")
                print(f"   Avg confirmed hits: {result.avg_confirmed_hits:.1f}")
            else:
                print("   No string summary data found")
                
        except Exception as e:
            print(f"   Error testing string_summary: {e}")
        
        # Test 4: Show sample string summaries
        print("\n📊 Sample string summaries...")
        try:
            result = conn.execute(text("""
                SELECT 
                    shooter_name,
                    stage_name,
                    total_shots,
                    confirmed_hits,
                    final_time,
                    avg_correlation_score
                FROM string_summary 
                ORDER BY run_started DESC 
                LIMIT 3
            """)).fetchall()
            
            if result:
                for row in result:
                    shooter = row.shooter_name or "Unknown"
                    stage = row.stage_name or "Unknown Stage"
                    print(f"   {shooter} @ {stage}: {row.total_shots} shots, {row.confirmed_hits} hits, {row.final_time:.2f}s" if row.final_time else f"   {shooter} @ {stage}: {row.total_shots} shots, {row.confirmed_hits} hits")
            else:
                print("   No string summaries found")
                
        except Exception as e:
            print(f"   Error fetching string summaries: {e}")
        
        # Test 5: Raw data availability check
        print("\n🔍 Raw data availability check...")
        try:
            timer_count = conn.execute(text("SELECT COUNT(*) FROM timer_events")).scalar()
            sensor_count = conn.execute(text("SELECT COUNT(*) FROM sensor_events")).scalar()
            
            print(f"   Timer events in database: {timer_count}")
            print(f"   Sensor events in database: {sensor_count}")
            
            if timer_count == 0 and sensor_count == 0:
                print("   ⚠️  No raw data found - views will be empty until timer/sensor data is captured")
            elif timer_count > 0 and sensor_count == 0:
                print("   ℹ️  Only timer data available - impacts will show as 'timer_only'")
            elif timer_count == 0 and sensor_count > 0:
                print("   ℹ️  Only sensor data available - impacts will show as 'impact_only'")
            else:
                print("   ✅ Both timer and sensor data available for correlation")
                
        except Exception as e:
            print(f"   Error checking raw data: {e}")


if __name__ == "__main__":
    sys.exit(main())