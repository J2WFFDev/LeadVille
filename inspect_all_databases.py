#!/usr/bin/env python3
"""
LeadVille Database Inspector
Comprehensive inspection of all LeadVille databases with useful queries
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

def inspect_database(db_path: str, db_name: str):
    """Inspect database contents with comprehensive queries"""
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n{'='*80}")
        print(f"🔍 INSPECTING: {db_name}")
        print(f"📁 Path: {db_path}")
        print(f"{'='*80}")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Tables ({len(tables)}): {', '.join(tables)}")
        
        # Inspect each table
        for table in tables:
            print(f"\n📋 TABLE: {table}")
            print("-" * 60)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"Columns ({len(columns)}):")
            for col in columns:
                col_id, name, data_type, not_null, default, pk = col
                pk_marker = " 🔑" if pk else ""
                not_null_marker = " ⚠️" if not_null else ""
                print(f"  {name} ({data_type}){pk_marker}{not_null_marker}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            print(f"Row count: {row_count}")
            
            # Show sample data if table has content
            if row_count > 0:
                print("Sample data (last 3 rows):")
                cursor.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 3")
                sample_rows = cursor.fetchall()
                
                # Print column headers
                col_names = [desc[0] for desc in cursor.description]
                print("  " + " | ".join(f"{name[:12]:12}" for name in col_names))
                print("  " + "-" * (15 * len(col_names)))
                
                # Print sample rows
                for row in sample_rows:
                    formatted_row = []
                    for item in row:
                        if item is None:
                            formatted_row.append("NULL")
                        elif isinstance(item, str) and len(item) > 12:
                            formatted_row.append(item[:9] + "...")
                        else:
                            formatted_row.append(str(item))
                    print("  " + " | ".join(f"{item[:12]:12}" for item in formatted_row))
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")

def generate_useful_queries():
    """Generate useful SQL queries for LeadVille databases"""
    
    queries = {
        "📊 RECENT SHOT DATA": {
            "database": "db/leadville_runtime.db",
            "queries": [
                {
                    "description": "Recent timer events (last 10)",
                    "sql": """
SELECT 
    datetime(ts_ns/1e9, 'unixepoch', 'localtime') as time,
    event_type,
    device_id,
    current_shot,
    split_seconds,
    string_total_time
FROM timer_events 
ORDER BY ts_ns DESC 
LIMIT 10;
"""
                },
                {
                    "description": "Recent impacts (last 10)",
                    "sql": """
SELECT 
    datetime(impact_ts_ns/1e9, 'unixepoch', 'localtime') as time,
    sensor_mac,
    peak_mag,
    duration_ms,
    target_number
FROM impacts 
ORDER BY impact_ts_ns DESC 
LIMIT 10;
"""
                },
                {
                    "description": "Shot correlation analysis",
                    "sql": """
WITH recent_shots AS (
    SELECT ts_ns, current_shot, device_id
    FROM timer_events 
    WHERE event_type = 'SHOT'
    ORDER BY ts_ns DESC LIMIT 10
),
recent_impacts AS (
    SELECT impact_ts_ns, sensor_mac, peak_mag
    FROM impacts
    ORDER BY impact_ts_ns DESC LIMIT 10
)
SELECT 
    rs.current_shot,
    datetime(rs.ts_ns/1e9, 'unixepoch', 'localtime') as shot_time,
    datetime(ri.impact_ts_ns/1e9, 'unixepoch', 'localtime') as impact_time,
    ROUND((ri.impact_ts_ns - rs.ts_ns) / 1e9, 3) as time_diff_sec,
    ri.sensor_mac,
    ROUND(ri.peak_mag, 1) as magnitude
FROM recent_shots rs
CROSS JOIN recent_impacts ri
WHERE (ri.impact_ts_ns - rs.ts_ns) / 1e9 BETWEEN 0 AND 2
ORDER BY rs.ts_ns DESC, time_diff_sec ASC;
"""
                }
            ]
        },
        "🎯 DEVICE STATUS": {
            "database": "db/leadville.db",
            "queries": [
                {
                    "description": "Device pool status",
                    "sql": """
SELECT 
    hw_addr,
    device_type,
    label,
    status,
    battery,
    rssi,
    datetime(last_seen) as last_seen,
    datetime(created_at) as created
FROM device_pool 
ORDER BY last_seen DESC;
"""
                },
                {
                    "description": "Bridge assignments",
                    "sql": """
SELECT 
    bc.bridge_id,
    bc.timer_address,
    bta.target_number,
    bta.sensor_address,
    bta.sensor_label,
    datetime(bta.created_at) as assigned
FROM bridge_configurations bc
LEFT JOIN bridge_target_assignments bta ON bc.bridge_id = bta.bridge_id
ORDER BY bta.target_number;
"""
                },
                {
                    "description": "Recent device events",
                    "sql": """
SELECT 
    device_id,
    event_type,
    datetime(timestamp) as event_time,
    details
FROM device_pool_events 
ORDER BY timestamp DESC 
LIMIT 15;
"""
                }
            ]
        },
        "📈 SUMMARY STATISTICS": {
            "database": "db/leadville_runtime.db",
            "queries": [
                {
                    "description": "Total event counts",
                    "sql": """
SELECT 
    'Timer Events' as type,
    COUNT(*) as count,
    MIN(datetime(ts_ns/1e9, 'unixepoch', 'localtime')) as earliest,
    MAX(datetime(ts_ns/1e9, 'unixepoch', 'localtime')) as latest
FROM timer_events
UNION ALL
SELECT 
    'Impact Events' as type,
    COUNT(*) as count,
    MIN(datetime(impact_ts_ns/1e9, 'unixepoch', 'localtime')) as earliest,
    MAX(datetime(impact_ts_ns/1e9, 'unixepoch', 'localtime')) as latest
FROM impacts
UNION ALL
SELECT 
    'Sensor Events' as type,
    COUNT(*) as count,
    MIN(datetime(ts_utc)) as earliest,
    MAX(datetime(ts_utc)) as latest
FROM sensor_events;
"""
                },
                {
                    "description": "Shot strings summary",
                    "sql": """
SELECT 
    date(ts_ns/1e9, 'unixepoch', 'localtime') as date,
    COUNT(CASE WHEN event_type = 'START' THEN 1 END) as strings_started,
    COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) as total_shots,
    COUNT(CASE WHEN event_type = 'STOP' THEN 1 END) as strings_completed,
    COUNT(DISTINCT device_id) as unique_devices
FROM timer_events 
GROUP BY date(ts_ns/1e9, 'unixepoch', 'localtime')
ORDER BY date DESC;
"""
                },
                {
                    "description": "Impact sensor performance",
                    "sql": """
SELECT 
    sensor_mac,
    COUNT(*) as impact_count,
    ROUND(AVG(peak_mag), 1) as avg_magnitude,
    ROUND(MAX(peak_mag), 1) as max_magnitude,
    ROUND(AVG(duration_ms), 1) as avg_duration_ms,
    datetime(MIN(impact_ts_ns/1e9), 'unixepoch', 'localtime') as first_impact,
    datetime(MAX(impact_ts_ns/1e9), 'unixepoch', 'localtime') as last_impact
FROM impacts 
GROUP BY sensor_mac
ORDER BY impact_count DESC;
"""
                }
            ]
        },
        "🔍 DIAGNOSTIC QUERIES": {
            "database": "db/leadville_runtime.db",
            "queries": [
                {
                    "description": "Recent database activity",
                    "sql": """
SELECT 
    'timer_events' as table_name,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN datetime(ts_ns/1e9, 'unixepoch') > datetime('now', '-1 hour') THEN 1 END) as last_hour,
    COUNT(CASE WHEN datetime(ts_ns/1e9, 'unixepoch') > datetime('now', '-24 hours') THEN 1 END) as last_24h
FROM timer_events
UNION ALL
SELECT 
    'impacts' as table_name,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN datetime(impact_ts_ns/1e9, 'unixepoch') > datetime('now', '-1 hour') THEN 1 END) as last_hour,
    COUNT(CASE WHEN datetime(impact_ts_ns/1e9, 'unixepoch') > datetime('now', '-24 hours') THEN 1 END) as last_24h
FROM impacts;
"""
                },
                {
                    "description": "Timer event patterns",
                    "sql": """
SELECT 
    event_type,
    COUNT(*) as count,
    COUNT(DISTINCT device_id) as unique_devices,
    AVG(CASE WHEN split_seconds IS NOT NULL THEN split_seconds END) as avg_split,
    MAX(current_shot) as max_shot_number
FROM timer_events 
GROUP BY event_type
ORDER BY count DESC;
"""
                }
            ]
        }
    }
    
    return queries

def main():
    """Main inspection function"""
    print("🎯 LEADVILLE DATABASE INSPECTOR")
    print("=" * 80)
    print("Comprehensive analysis of all LeadVille databases")
    print()
    
    # Database paths
    databases = [
        ("db/leadville_runtime.db", "Runtime Database (PRIMARY - Shot Data)"),
        ("db/leadville.db", "Configuration Database"),
        ("logs/bt50_samples.db", "BT50 Samples Database"),
        ("leadville.db", "Root Database (if exists)")
    ]
    
    project_root = "/home/jrwest/projects/LeadVille"
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick mode - just show useful queries
        print("📋 USEFUL QUERIES FOR LEADVILLE DATABASES")
        print("Copy and paste these into sqlite3 to inspect your data:")
        print()
        
        queries = generate_useful_queries()
        for category, info in queries.items():
            print(f"\n{category}")
            print("=" * 60)
            print(f"Database: {info['database']}")
            print(f"Connect with: sqlite3 {project_root}/{info['database']}")
            print()
            
            for i, query in enumerate(info['queries'], 1):
                print(f"{i}. {query['description']}")
                print("-" * 40)
                print(query['sql'].strip())
                print()
        
        return
    
    # Full inspection mode
    for db_path, db_name in databases:
        full_path = f"{project_root}/{db_path}"
        inspect_database(full_path, db_name)
    
    print(f"\n{'='*80}")
    print("✅ DATABASE INSPECTION COMPLETE")
    print("💡 Run with --quick for useful query templates")
    print("💡 Connect to databases with: ssh jrwest@192.168.1.125")
    print("💡 Then: cd /home/jrwest/projects/LeadVille && sqlite3 db/leadville_runtime.db")

if __name__ == "__main__":
    main()