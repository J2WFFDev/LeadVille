#!/usr/bin/env python3
"""
Test script for current AMG handler implementation
Tests the existing AMG notification handler logic and database persistence
"""

import os
import sys
import sqlite3
import time
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_persist_timer_event():
    """Test the _persist_timer_event function from leadville_bridge.py"""
    
    def persist_timer_event(event_type, raw_hex, split_seconds=None, split_cs=None):
        """Replicated from leadville_bridge.py for testing"""
        try:
            db_path = Path(__file__).parent / 'logs' / 'bt50_samples.db'
            db_path.parent.mkdir(parents=True, exist_ok=True)
            con = sqlite3.connect(str(db_path))
            cur = con.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            # Ensure timer_events table exists
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS timer_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_ns INTEGER,
                    device_id TEXT,
                    event_type TEXT,
                    split_seconds REAL,
                    split_cs INTEGER,
                    raw_hex TEXT
                )
                """
            )
            ts_ns = int(time.time() * 1e9)
            cur.execute(
                "INSERT INTO timer_events (ts_ns, device_id, event_type, split_seconds, split_cs, raw_hex) VALUES (?,?,?,?,?,?)",
                (ts_ns, "TEST_AMG_DEVICE", event_type, split_seconds, split_cs, raw_hex),
            )
            con.commit()
            con.close()
            return True
        except Exception as e:
            print(f"Error persisting timer event: {e}")
            return False
    
    # Test data based on current AMG handler patterns
    test_cases = [
        # START beep (0x0105)
        {
            'data': bytes.fromhex("010500010000000000000000000D"),
            'event_type': 'START',
            'expected_pattern': 'START beep',
        },
        # SHOT event (0x0103) 
        {
            'data': bytes.fromhex("01030001000A001E003200460005"),
            'event_type': 'SHOT', 
            'expected_pattern': 'SHOT event',
        },
        # STOP beep (0x0108)
        {
            'data': bytes.fromhex("010800010032000000000000000A"),
            'event_type': 'STOP',
            'expected_pattern': 'STOP beep',
        }
    ]
    
    print("Testing Current AMG Handler Logic")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        data = test_case['data']
        hex_data = data.hex().upper()
        
        print(f"\nTest {i}: {test_case['expected_pattern']}")
        print(f"Raw data: {hex_data}")
        
        # Simulate current AMG handler logic
        if len(data) >= 2:
            frame_header = data[0]
            frame_type = data[1]
            
            # Handle START beep (0x0105)
            if frame_header == 0x01 and frame_type == 0x05:
                string_number = data[13] if len(data) >= 14 else 1
                print(f"✅ Detected START beep - String #{string_number}")
                success = persist_timer_event('START', hex_data, split_seconds=None, split_cs=None)
                print(f"   Database persist: {'✅ SUCCESS' if success else '❌ FAILED'}")
                
            # Handle SHOT event (0x0103)
            elif frame_header == 0x01 and frame_type == 0x03 and len(data) >= 14:
                time_cs = (data[4] << 8) | data[5]
                split_cs = (data[6] << 8) | data[7]  
                first_cs = (data[8] << 8) | data[9]
                
                timer_split_seconds = split_cs / 100.0
                first_seconds = first_cs / 100.0
                
                print(f"✅ Detected SHOT event - Time: {timer_split_seconds:.2f}s, First: {first_seconds:.2f}s")
                success = persist_timer_event('SHOT', hex_data, split_seconds=timer_split_seconds, split_cs=split_cs)
                print(f"   Database persist: {'✅ SUCCESS' if success else '❌ FAILED'}")
                    
            # Handle STOP beep (0x0108)
            elif frame_header == 0x01 and frame_type == 0x08:
                if len(data) >= 14:
                    string_number = data[13]
                    time_cs = (data[4] << 8) | data[5]
                    timer_seconds = time_cs / 100.0
                else:
                    string_number = 1
                    timer_seconds = 0
                    
                print(f"✅ Detected STOP beep - String #{string_number}, Total: {timer_seconds:.2f}s")
                success = persist_timer_event('STOP', hex_data, split_seconds=timer_seconds, split_cs=time_cs if len(data) >= 14 else None)
                print(f"   Database persist: {'✅ SUCCESS' if success else '❌ FAILED'}")
            else:
                print(f"❌ Unknown AMG pattern: {frame_header:02X} {frame_type:02X}")
        else:
            print(f"❌ Data too short: {len(data)} bytes")

def check_database_contents():
    """Check what's in the timer_events table"""
    print("\n" + "=" * 50)
    print("DATABASE CONTENTS CHECK")
    print("=" * 50)
    
    db_path = Path(__file__).parent / 'logs' / 'bt50_samples.db'
    
    if not db_path.exists():
        print("❌ Database file does not exist yet")
        return
    
    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        
        # Check if timer_events table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timer_events'")
        if not cur.fetchone():
            print("❌ timer_events table does not exist")
            con.close()
            return
        
        # Get table schema
        cur.execute("PRAGMA table_info(timer_events)")
        columns = cur.fetchall()
        print("✅ timer_events table schema:")
        for col in columns:
            print(f"   {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        # Get record count
        cur.execute("SELECT COUNT(*) FROM timer_events")
        count = cur.fetchone()[0]
        print(f"\n📊 Total records: {count}")
        
        # Show recent records
        if count > 0:
            cur.execute("SELECT * FROM timer_events ORDER BY ts_ns DESC LIMIT 10")
            records = cur.fetchall()
            print(f"\n📋 Recent records (last {min(count, 10)}):")
            for record in records:
                ts_ns, device_id, event_type, split_seconds, split_cs, raw_hex = record[1:]
                ts_datetime = datetime.fromtimestamp(ts_ns / 1e9)
                print(f"   {ts_datetime.strftime('%H:%M:%S.%f')[:-3]} | {event_type:5} | {device_id:15} | {split_seconds:8} | {raw_hex}")
        
        con.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def compare_with_bt50_samples():
    """Check if bt50_samples table exists for comparison"""
    print("\n" + "=" * 50)
    print("COMPARISON WITH WTVB (bt50_samples)")
    print("=" * 50)
    
    db_path = Path(__file__).parent / 'logs' / 'bt50_samples.db'
    
    if not db_path.exists():
        print("❌ Database file does not exist - no comparison possible")
        return
    
    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        
        # Check if bt50_samples table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bt50_samples'")
        if cur.fetchone():
            cur.execute("SELECT COUNT(*) FROM bt50_samples")
            bt50_count = cur.fetchone()[0]
            print(f"✅ bt50_samples table exists with {bt50_count} records")
        else:
            print("❌ bt50_samples table does not exist")
        
        # Check timer_events vs bt50_samples
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        print(f"\n📋 All tables in database: {', '.join(tables)}")
        
        con.close()
        
    except Exception as e:
        print(f"❌ Error comparing tables: {e}")

if __name__ == "__main__":
    print("AMG Current Implementation Test")
    print("=" * 50)
    print("Testing the existing AMG handler logic and database persistence")
    print("Based on leadville_bridge.py lines 413-498")
    
    # Run tests
    test_persist_timer_event()
    check_database_contents()
    compare_with_bt50_samples()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)