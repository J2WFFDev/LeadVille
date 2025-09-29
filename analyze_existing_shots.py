#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3

"""

LeadVille Existing Data Analysis""""""

Shows your existing shot test data from leadville_runtime.db

"""LeadVille Shot Analysis - Simple VersionLeadVille Shot Analysis - Correct Database Version



import sqlite3Analyzes existing shot/impact data from the correct leadville_runtime.db databaseAnalyzes existing shot/impact data from the correct leadville_runtime.db database

from datetime import datetime

from pathlib import Path""""""



def main():

    db_path = "/home/jrwest/projects/LeadVille/db/leadville_runtime.db"

    import sqlite3import sqlite3

    print("🎯 LEADVILLE SHOT TEST DATA FOUND!")

    print("=" * 50)from datetime import datetimeimport json

    

    conn = sqlite3.connect(db_path)from pathlib import Pathfrom datetime import datetime, timedelta

    cursor = conn.cursor()

    from pathlib import Path

    # Timer events

    print("\n⏰ RECENT TIMER EVENTS:")def analyze_existing_shot_data():

    cursor.execute("""

        SELECT datetime(ts_ns/1e9, 'unixepoch'), event_type, current_shot, string_total_time    """Analyze the existing shot test data from leadville_runtime.db"""def analyze_existing_shot_data(hours_back: int = 2):

        FROM timer_events ORDER BY ts_ns DESC LIMIT 8

    """)        """Analyze the existing shot test data from leadville_runtime.db"""

    for row in cursor.fetchall():

        print(f"   {row[0]} | {row[1]} #{row[2] or 'N/A'} | {row[3]}s")    db_path = "/home/jrwest/projects/LeadVille/db/leadville_runtime.db"    

    

    # Impacts          db_path = "/home/jrwest/projects/LeadVille/db/leadville_runtime.db"

    print("\n💥 RECENT IMPACTS:")

    cursor.execute("""    if not Path(db_path).exists():    

        SELECT datetime(impact_ts_ns/1e9, 'unixepoch'), sensor_mac, peak_mag

        FROM impacts ORDER BY impact_ts_ns DESC LIMIT 8        print(f"❌ Database not found: {db_path}")    if not Path(db_path).exists():

    """)

    for row in cursor.fetchall():        return        print(f"❌ Database not found: {db_path}")

        print(f"   {row[0]} | {row[1]} | {row[2]:.1f}g")

                return

    # Counts

    cursor.execute("SELECT COUNT(*) FROM timer_events")    print("🎯 LEADVILLE EXISTING SHOT DATA ANALYSIS")    

    timer_count = cursor.fetchone()[0]

        print("=" * 55)    print("🎯 LEADVILLE EXISTING SHOT DATA ANALYSIS")

    cursor.execute("SELECT COUNT(*) FROM impacts")

    impact_count = cursor.fetchone()[0]        print("=" * 55)

    

    print(f"\n📊 TOTALS:")    try:    

    print(f"   Timer events: {timer_count}")

    print(f"   Impact events: {impact_count}")        conn = sqlite3.connect(db_path)    try:

    print(f"\n✅ Your shot test data exists in: {db_path}")

            cursor = conn.cursor()        conn = sqlite3.connect(db_path)

    conn.close()

                cursor = conn.cursor()

if __name__ == "__main__":

    main()        # Show recent timer events        

        print(f"\n⏰ TIMER EVENTS (Most Recent 10):")        # Analyze timer events

        cursor.execute("""        print(f"\n⏰ TIMER EVENTS ANALYSIS:")

            SELECT         

                datetime(ts_ns/1e9, 'unixepoch') as timestamp,        # Recent timer events

                event_type,        cursor.execute("""

                device_id,            SELECT 

                current_shot,                datetime(ts_ns/1e9, 'unixepoch') as timestamp,

                string_total_time,                event_type,

                split_seconds                device_id,

            FROM timer_events                 current_shot,

            ORDER BY ts_ns DESC                string_total_time,

            LIMIT 10                split_seconds

        """)            FROM timer_events 

                    WHERE datetime(ts_ns/1e9, 'unixepoch') >= datetime('now', '-{0} hours')

        for row in cursor.fetchall():            ORDER BY ts_ns DESC

            timestamp, event_type, device_id, shot_num, string_time, split_time = row            LIMIT 20

            print(f"   {timestamp} | {event_type} #{shot_num or 'N/A'} | {device_id} | String: {string_time}s")        """.format(hours_back))

                

        # Show recent impacts        recent_shots = cursor.fetchall()

        print(f"\n💥 IMPACT EVENTS (Most Recent 10):")        print(f"   Recent shots (last {hours_back} hours): {len(recent_shots)}")

        cursor.execute("""        

            SELECT         if recent_shots:

                datetime(impact_ts_ns/1e9, 'unixepoch') as timestamp,            print(f"   Latest shots:")

                sensor_mac,            for shot in recent_shots[:10]:

                peak_mag,                timestamp, event_type, device_id, shot_num, string_time, split_time = shot

                duration_ms                print(f"     {timestamp} | {event_type} #{shot_num or 'N/A'} | {device_id} | String: {string_time}s | Split: {split_time}s")

            FROM impacts         

            ORDER BY impact_ts_ns DESC        # Get shot strings (groups of shots)

            LIMIT 10        cursor.execute("""

        """)            SELECT 

                        COUNT(*) as shot_count,

        for row in cursor.fetchall():                MAX(current_shot) as max_shot,

            timestamp, sensor, magnitude, duration = row                MIN(datetime(ts_ns/1e9, 'unixepoch')) as start_time,

            print(f"   {timestamp} | {sensor} | {magnitude:.1f}g | {duration}ms")                MAX(datetime(ts_ns/1e9, 'unixepoch')) as end_time,

                        MAX(string_total_time) as final_time

        # Summary counts            FROM timer_events 

        cursor.execute("SELECT COUNT(*) FROM timer_events")            WHERE event_type = 'SHOT' 

        timer_count = cursor.fetchone()[0]            AND datetime(ts_ns/1e9, 'unixepoch') >= datetime('now', '-{} hours')

                """.format(hours_back))

        cursor.execute("SELECT COUNT(*) FROM impacts")        

        impact_count = cursor.fetchone()[0]        shot_summary = cursor.fetchone()

                if shot_summary and shot_summary[0] > 0:

        print(f"\n📊 SUMMARY:")            shot_count, max_shot, start_time, end_time, final_time = shot_summary

        print(f"   Total timer events: {timer_count}")            print(f"\n📊 SHOT STRING SUMMARY (last {hours_back} hours):")

        print(f"   Total impacts: {impact_count}")            print(f"   Total shots detected: {shot_count}")

                    print(f"   Highest shot number: {max_shot}")

        # Recent correlations            print(f"   String duration: {start_time} to {end_time}")

        print(f"\n🔗 CHECKING FOR CORRELATIONS:")            print(f"   Final string time: {final_time}s")

        cursor.execute("""        

            WITH shots AS (        # Analyze impacts

                SELECT ts_ns as shot_ts, current_shot, device_id as timer_id        print(f"\n💥 IMPACT EVENTS ANALYSIS:")

                FROM timer_events         

                WHERE event_type = 'SHOT'        cursor.execute("""

                ORDER BY ts_ns DESC            SELECT 

                LIMIT 20                COUNT(*) as impact_count,

            ),                sensor_mac,

            recent_impacts AS (                datetime(MIN(impact_ts_ns)/1e9, 'unixepoch') as first_impact,

                SELECT impact_ts_ns, sensor_mac, peak_mag                datetime(MAX(impact_ts_ns)/1e9, 'unixepoch') as last_impact,

                FROM impacts                AVG(peak_mag) as avg_magnitude,

                ORDER BY impact_ts_ns DESC                  MAX(peak_mag) as max_magnitude

                LIMIT 20            FROM impacts 

            )            WHERE datetime(impact_ts_ns/1e9, 'unixepoch') >= datetime('now', '-{} hours')

            SELECT             GROUP BY sensor_mac

                shots.current_shot,            ORDER BY impact_count DESC

                datetime(shots.shot_ts/1e9, 'unixepoch') as shot_time,        """.format(hours_back))

                datetime(recent_impacts.impact_ts_ns/1e9, 'unixepoch') as impact_time,        

                (recent_impacts.impact_ts_ns - shots.shot_ts) / 1e9 as time_diff,        impact_summary = cursor.fetchall()

                recent_impacts.sensor_mac,        if impact_summary:

                recent_impacts.peak_mag            print(f"   Impact sensors (last {hours_back} hours):")

            FROM shots            total_impacts = 0

            CROSS JOIN recent_impacts            for sensor_data in impact_summary:

            WHERE (recent_impacts.impact_ts_ns - shots.shot_ts) / 1e9 BETWEEN 0 AND 3                count, sensor, first, last, avg_mag, max_mag = sensor_data

            ORDER BY shots.shot_ts DESC, time_diff ASC                total_impacts += count

            LIMIT 10                print(f"     {sensor}: {count} impacts | Avg: {avg_mag:.1f}g | Peak: {max_mag:.1f}g")

        """)                print(f"       Time range: {first} to {last}")

                    

        correlations = cursor.fetchall()            print(f"   Total impacts detected: {total_impacts}")

        if correlations:        

            print(f"   Found {len(correlations)} potential shot-impact correlations:")        # Correlation analysis

            for corr in correlations:        print(f"\n🔗 SHOT-IMPACT CORRELATION ANALYSIS:")

                shot_num, shot_time, impact_time, time_diff, sensor, magnitude = corr        

                quality = "excellent" if time_diff <= 0.2 else "good" if time_diff <= 0.5 else "fair"        # Get shots and impacts in the same timeframe for correlation

                print(f"     Shot #{shot_num} → Impact: {time_diff:.3f}s delay ({quality})")        cursor.execute("""

                print(f"       {shot_time} → {impact_time} | {sensor} | {magnitude:.1f}g")            SELECT 

        else:                'SHOT' as type,

            print("   No recent correlations found")                ts_ns as timestamp,

                        event_type,

        conn.close()                current_shot,

                        device_id,

        print(f"\n🎉 Analysis complete!")                string_total_time

        if correlations:            FROM timer_events 

            print(f"✅ Your system has {len(correlations)} shot-impact correlations!")            WHERE event_type = 'SHOT' 

        print(f"💡 Data is in: {db_path}")            AND datetime(ts_ns/1e9, 'unixepoch') >= datetime('now', '-{} hours')

                    

    except Exception as e:            UNION ALL

        print(f"❌ Analysis error: {e}")            

            SELECT 

if __name__ == "__main__":                'IMPACT' as type,

    analyze_existing_shot_data()                impact_ts_ns as timestamp,
                'IMPACT' as event_type,
                NULL as current_shot,
                sensor_mac as device_id,
                peak_mag as string_total_time
            FROM impacts 
            WHERE datetime(impact_ts_ns/1e9, 'unixepoch') >= datetime('now', '-{} hours')
            
            ORDER BY timestamp
        """.format(hours_back))
        
        events = cursor.fetchall()
        
        # Find shot-impact pairs within 3 seconds
        shots = [e for e in events if e[0] == 'SHOT']
        impacts = [e for e in events if e[0] == 'IMPACT']
        
        correlations = []
        for shot in shots:
            shot_time = shot[1] / 1e9
            shot_num = shot[3]
            
            for impact in impacts:
                impact_time = impact[1] / 1e9
                time_diff = impact_time - shot_time
                
                # Look for impacts 0-3 seconds after shot
                if 0 <= time_diff <= 3.0:
                    correlations.append({
                        'shot_num': shot_num,
                        'shot_time': datetime.fromtimestamp(shot_time),
                        'impact_time': datetime.fromtimestamp(impact_time),
                        'time_diff': time_diff,
                        'sensor': impact[4],
                        'magnitude': impact[5]
                    })
        
        if correlations:
            print(f"   Found {len(correlations)} shot-impact correlations:")
            for i, corr in enumerate(correlations[:10], 1):  # Show first 10
                quality = "excellent" if corr['time_diff'] <= 0.2 else "good" if corr['time_diff'] <= 0.5 else "fair"
                print(f"     {i}. Shot #{corr['shot_num']} → Impact: {corr['time_diff']:.3f}s delay ({quality})")
                print(f"        Shot: {corr['shot_time'].strftime('%H:%M:%S')}")
                print(f"        Impact: {corr['impact_time'].strftime('%H:%M:%S')} | {corr['sensor']} | {corr['magnitude']:.1f}g")
        else:
            print(f"   No correlations found in recent data")
        
        # Show ALL data if requested
        print(f"\n📈 ALL AVAILABLE DATA SUMMARY:")
        
        cursor.execute("SELECT COUNT(*) FROM timer_events")
        total_timer = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM impacts")  
        total_impacts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bt50_samples")
        total_samples = cursor.fetchone()[0]
        
        print(f"   Total timer events in database: {total_timer}")
        print(f"   Total impacts in database: {total_impacts}")  
        print(f"   Total BT50 samples in database: {total_samples}")
        
        # Most recent activity
        cursor.execute("""
            SELECT 
                datetime(MAX(ts_ns)/1e9, 'unixepoch') as last_timer_event
            FROM timer_events
        """)
        last_timer = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                datetime(MAX(impact_ts_ns)/1e9, 'unixepoch') as last_impact
            FROM impacts
        """)
        last_impact = cursor.fetchone()[0]
        
        print(f"   Last timer event: {last_timer}")
        print(f"   Last impact event: {last_impact}")
        
        conn.close()
        
        print(f"\n🎉 Analysis complete!")
        print(f"💡 This data represents your previous shot testing sessions")
        print(f"💡 For new shot tests, the bridge should write to this same database")
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")

def main():
    analyze_existing_shot_data(hours_back=24)  # Look at last 24 hours

if __name__ == "__main__":
    main()