#!/usr/bin/env python3
"""
Quick Shot Data Viewer
Shows your shot test data in an easy-to-read format
"""

import sqlite3
import json
from datetime import datetime

def view_shot_data():
    """Display shot test data from leadville_runtime.db"""
    
    db_path = "/home/jrwest/projects/LeadVille/db/leadville_runtime.db"
    
    print("🎯 YOUR LEADVILLE SHOT TEST DATA")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Show recent shot string
    print("\n📊 LATEST SHOT STRING:")
    cursor.execute("""
        SELECT 
            datetime(ts_ns/1e9, 'unixepoch') as time,
            event_type,
            current_shot,
            string_total_time,
            split_seconds
        FROM timer_events 
        WHERE event_type IN ('START', 'SHOT', 'STOP')
        ORDER BY ts_ns DESC 
        LIMIT 15
    """)
    
    for i, row in enumerate(cursor.fetchall()):
        time, event_type, shot_num, string_time, split_time = row
        if event_type == 'START':
            print(f"   🟢 START  | {time}")
        elif event_type == 'SHOT':
            print(f"   🎯 SHOT #{shot_num:2d} | {time} | String: {string_time:5.2f}s | Split: {split_time or 0:5.2f}s")
        elif event_type == 'STOP':
            print(f"   🔴 STOP   | {time} | Final: {string_time:5.2f}s")
        
        if i == 0:  # Add separator after most recent event
            print("   " + "-" * 60)
    
    # Show impact summary
    print(f"\n💥 IMPACT SUMMARY:")
    cursor.execute("""
        SELECT 
            sensor_mac,
            COUNT(*) as impact_count,
            datetime(MIN(impact_ts_ns)/1e9, 'unixepoch') as first_impact,
            datetime(MAX(impact_ts_ns)/1e9, 'unixepoch') as last_impact,
            ROUND(AVG(peak_mag), 1) as avg_magnitude,
            ROUND(MAX(peak_mag), 1) as max_magnitude
        FROM impacts 
        GROUP BY sensor_mac
        ORDER BY impact_count DESC
    """)
    
    for row in cursor.fetchall():
        sensor, count, first, last, avg_mag, max_mag = row
        print(f"   📡 {sensor}")
        print(f"      {count} impacts | Avg: {avg_mag}g | Peak: {max_mag}g")
        print(f"      First: {first}")
        print(f"      Last:  {last}")
    
    # Show recent impacts
    print(f"\n💥 RECENT IMPACTS:")
    cursor.execute("""
        SELECT 
            datetime(impact_ts_ns/1e9, 'unixepoch') as time,
            sensor_mac,
            ROUND(peak_mag, 1) as magnitude
        FROM impacts 
        ORDER BY impact_ts_ns DESC 
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        time, sensor, mag = row
        print(f"   {time} | {sensor} | {mag}g")
    
    # Show correlation potential
    print(f"\n🔗 CORRELATION ANALYSIS:")
    cursor.execute("""
        WITH recent_shots AS (
            SELECT ts_ns, current_shot, string_total_time
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
            datetime(rs.ts_ns/1e9, 'unixepoch') as shot_time,
            datetime(ri.impact_ts_ns/1e9, 'unixepoch') as impact_time,
            ROUND((ri.impact_ts_ns - rs.ts_ns) / 1e9, 3) as time_diff,
            ri.sensor_mac,
            ROUND(ri.peak_mag, 1) as magnitude
        FROM recent_shots rs
        CROSS JOIN recent_impacts ri
        WHERE (ri.impact_ts_ns - rs.ts_ns) / 1e9 BETWEEN 0 AND 2
        ORDER BY rs.ts_ns DESC, time_diff ASC
        LIMIT 8
    """)
    
    correlations = cursor.fetchall()
    if correlations:
        print(f"   Found {len(correlations)} potential shot-impact pairs:")
        for corr in correlations:
            shot_num, shot_time, impact_time, time_diff, sensor, mag = corr
            quality = "🎯 excellent" if time_diff <= 0.2 else "✅ good" if time_diff <= 0.5 else "⚠️  fair"
            print(f"   Shot #{shot_num} → Impact: {time_diff}s ({quality})")
            print(f"     {shot_time.split()[1]} → {impact_time.split()[1]} | {sensor} | {mag}g")
    else:
        print("   No recent correlations found in timeframe")
    
    # Database summary
    cursor.execute("SELECT COUNT(*) FROM timer_events")
    timer_total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM impacts")
    impact_total = cursor.fetchone()[0]
    
    print(f"\n📈 DATABASE TOTALS:")
    print(f"   Timer events: {timer_total}")
    print(f"   Impact events: {impact_total}")
    print(f"   Database: db/leadville_runtime.db")
    
    conn.close()
    
    print(f"\n💡 To view in browser: http://192.168.1.125:8001/api/shot-log")

if __name__ == "__main__":
    view_shot_data()