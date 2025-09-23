#!/usr/bin/env python3
"""
Create simplified database views for current LeadVille schema

Works with the existing timer_events table structure.
"""

import sqlite3
import sys
import os
from pathlib import Path


def create_simple_views():
    """Create views that work with current schema"""
    
    db_path = Path("logs/bt50_samples.db")
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    try:
        cursor = conn.cursor()
        
        # Drop existing views
        print("🗑️  Dropping existing views...")
        cursor.execute("DROP VIEW IF EXISTS shot_log_simple")
        cursor.execute("DROP VIEW IF EXISTS timer_summary")
        
        # Create simplified shot_log view for current schema
        print("🏗️  Creating shot_log_simple view...")
        cursor.execute("""
        CREATE VIEW shot_log_simple AS
        SELECT 
            id as log_id,
            datetime(ts_ns / 1000000000, 'unixepoch') as event_time,
            event_type,
            current_shot as shot_number,
            total_shots,
            current_round as round_number,
            split_seconds as shot_time,
            string_total_time,
            device_id as timer_device,
            raw_hex,
            parsed_json,
            
            -- Add sequence number
            ROW_NUMBER() OVER (ORDER BY ts_ns) as sequence,
            
            -- Add timing analysis
            CASE 
                WHEN event_type = 'START' THEN 'timer_start'
                WHEN event_type = 'STOP' THEN 'timer_stop'  
                WHEN event_type = 'SHOT' THEN 'timer_shot'
                ELSE 'unknown'
            END as event_category,
            
            -- Add JSON parsed fields if available
            CASE 
                WHEN parsed_json IS NOT NULL AND parsed_json != '' THEN 
                    json_extract(parsed_json, '$.shot_state')
                ELSE NULL 
            END as shot_state,
            
            CASE 
                WHEN parsed_json IS NOT NULL AND parsed_json != '' THEN 
                    json_extract(parsed_json, '$.timing_data.shot_time')
                ELSE split_seconds 
            END as precise_shot_time
            
        FROM timer_events
        ORDER BY ts_ns
        """)
        
        # Create timer summary view
        print("📊 Creating timer_summary view...")  
        cursor.execute("""
        CREATE VIEW timer_summary AS
        SELECT 
            device_id as timer_device,
            COUNT(*) as total_events,
            COUNT(CASE WHEN event_type = 'START' THEN 1 END) as start_events,
            COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) as shot_events,
            COUNT(CASE WHEN event_type = 'STOP' THEN 1 END) as stop_events,
            
            -- Timing analysis
            MAX(string_total_time) as max_string_time,
            AVG(CASE WHEN event_type = 'SHOT' THEN split_seconds END) as avg_split_time,
            MIN(CASE WHEN event_type = 'SHOT' AND split_seconds > 0 THEN split_seconds END) as first_shot_time,
            MAX(CASE WHEN event_type = 'SHOT' THEN split_seconds END) as last_shot_time,
            
            -- Shot analysis
            MAX(current_shot) as max_shots,
            MAX(total_shots) as max_total_shots,
            MAX(current_round) as max_rounds,
            
            -- Time range
            datetime(MIN(ts_ns) / 1000000000, 'unixepoch') as first_event,
            datetime(MAX(ts_ns) / 1000000000, 'unixepoch') as last_event,
            
            -- Data quality
            COUNT(CASE WHEN parsed_json IS NOT NULL AND parsed_json != '' THEN 1 END) as events_with_json,
            COUNT(CASE WHEN raw_hex IS NOT NULL AND raw_hex != '' THEN 1 END) as events_with_raw_data
            
        FROM timer_events
        GROUP BY device_id
        ORDER BY MAX(ts_ns) DESC
        """)
        
        conn.commit()
        print("✅ Views created successfully!")
        
        # Test the views
        test_views(cursor)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating views: {e}")
        return False
        
    finally:
        conn.close()


def test_views(cursor):
    """Test the created views"""
    
    print("\n🧪 Testing views with existing data...")
    
    # Test shot_log_simple
    print("\n📋 Testing shot_log_simple view...")
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) as shot_events,
                COUNT(CASE WHEN event_type = 'START' THEN 1 END) as start_events,
                COUNT(CASE WHEN event_type = 'STOP' THEN 1 END) as stop_events,
                MAX(total_shots) as max_shots_in_string
            FROM shot_log_simple
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"   Total records: {result[0]}")
            print(f"   Shot events: {result[1]}")
            print(f"   Start events: {result[2]}")
            print(f"   Stop events: {result[3]}")
            print(f"   Max shots in string: {result[4]}")
            
    except Exception as e:
        print(f"   Error testing shot_log_simple: {e}")
    
    # Show sample records
    print("\n📋 Sample shot_log_simple records...")
    try:
        cursor.execute("""
            SELECT 
                log_id,
                event_time,
                event_type,
                shot_number,
                shot_time,
                string_total_time,
                event_category
            FROM shot_log_simple 
            ORDER BY log_id DESC 
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        if results:
            for row in results:
                event_time = row[1][:19] if row[1] else "N/A"  # Truncate datetime
                print(f"   {row[0]}: {row[2]} | Shot #{row[3]} | {row[4]}s | Total {row[5]}s | {event_time}")
        else:
            print("   No sample records found")
            
    except Exception as e:
        print(f"   Error fetching samples: {e}")
    
    # Test timer_summary
    print("\n📊 Testing timer_summary view...")
    try:
        cursor.execute("""
            SELECT 
                timer_device,
                total_events,
                shot_events,
                max_string_time,
                avg_split_time,
                max_shots,
                first_event,
                last_event
            FROM timer_summary
        """)
        
        results = cursor.fetchall()
        if results:
            for row in results:
                device = row[0] or "Unknown"
                first_time = row[6][:19] if row[6] else "N/A"
                last_time = row[7][:19] if row[7] else "N/A"
                avg_split = f"{row[4]:.2f}s" if row[4] else "N/A"
                max_time = f"{row[3]:.2f}s" if row[3] else "N/A"
                print(f"   {device}: {row[1]} events, {row[2]} shots, Max time {max_time}, Avg split {avg_split}")
                print(f"     Range: {first_time} to {last_time}")
        else:
            print("   No timer summaries found")
            
    except Exception as e:
        print(f"   Error testing timer_summary: {e}")
    
    # Show latest shot sequence
    print("\n🎯 Latest shot sequence...")
    try:
        cursor.execute("""
            SELECT 
                event_time,
                event_type,
                shot_number,
                shot_time,
                string_total_time
            FROM shot_log_simple 
            WHERE shot_number IS NOT NULL AND shot_number > 0
            ORDER BY log_id DESC 
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        if results:
            print("   Recent shots:")
            for row in results:
                event_time = row[0][-8:] if row[0] else "N/A"  # Just show time
                shot_time = f"{row[3]:.2f}s" if row[3] else "N/A"
                total_time = f"{row[4]:.2f}s" if row[4] else "N/A"
                print(f"     {event_time}: Shot #{row[2]} @ {shot_time} (Total: {total_time})")
        else:
            print("   No recent shots found")
            
    except Exception as e:
        print(f"   Error fetching shot sequence: {e}")


if __name__ == "__main__":
    if create_simple_views():
        print("\n🎉 Database views ready for web app integration!")
        sys.exit(0)
    else:
        sys.exit(1)