# LeadVille Database Inspection Queries
Quick reference for inspecting LeadVille databases

## 🔗 Connection Commands

```bash
# Connect to Pi
ssh jrwest@192.168.1.125

# Navigate to project
cd /home/jrwest/projects/LeadVille

# Connect to primary runtime database (contains shot data)
sqlite3 db/leadville_runtime.db

# Connect to configuration database
sqlite3 db/leadville.db

# Connect to BT50 samples database
sqlite3 logs/bt50_samples.db
```

## 📊 RECENT SHOT DATA QUERIES

### Recent Timer Events (Last 10)
```sql
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
```

### Recent Impacts (Last 10)
```sql
SELECT 
    datetime(impact_ts_ns/1e9, 'unixepoch', 'localtime') as time,
    sensor_mac,
    peak_mag,
    duration_ms,
    target_number
FROM impacts 
ORDER BY impact_ts_ns DESC 
LIMIT 10;
```

### Shot-Impact Correlation Analysis
```sql
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
```

## 🎯 DEVICE STATUS QUERIES (db/leadville.db)

### Device Pool Status
```sql
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
```

### Current Bridge Assignments
```sql
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
```

### Recent Device Events
```sql
SELECT 
    device_id,
    event_type,
    datetime(timestamp) as event_time,
    details
FROM device_pool_events 
ORDER BY timestamp DESC 
LIMIT 15;
```

## 📈 SUMMARY STATISTICS

### Total Event Counts
```sql
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
```

### Shot Strings Summary by Date
```sql
SELECT 
    date(ts_ns/1e9, 'unixepoch', 'localtime') as date,
    COUNT(CASE WHEN event_type = 'START' THEN 1 END) as strings_started,
    COUNT(CASE WHEN event_type = 'SHOT' THEN 1 END) as total_shots,
    COUNT(CASE WHEN event_type = 'STOP' THEN 1 END) as strings_completed,
    COUNT(DISTINCT device_id) as unique_devices
FROM timer_events 
GROUP BY date(ts_ns/1e9, 'unixepoch', 'localtime')
ORDER BY date DESC;
```

### Impact Sensor Performance
```sql
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
```

## 🔍 DIAGNOSTIC QUERIES

### Recent Database Activity (Last Hour vs 24 Hours)
```sql
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
```

### Timer Event Patterns
```sql
SELECT 
    event_type,
    COUNT(*) as count,
    COUNT(DISTINCT device_id) as unique_devices,
    AVG(CASE WHEN split_seconds IS NOT NULL THEN split_seconds END) as avg_split,
    MAX(current_shot) as max_shot_number
FROM timer_events 
GROUP BY event_type
ORDER BY count DESC;
```

## 🗂️ TABLE STRUCTURE QUERIES

### List All Tables in Runtime Database
```sql
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
```

### Get Table Schema
```sql
PRAGMA table_info(timer_events);
PRAGMA table_info(impacts);
PRAGMA table_info(device_pool);
```

### Row Counts for All Tables
```sql
SELECT 
    name as table_name,
    (SELECT COUNT(*) FROM timer_events) as timer_events,
    (SELECT COUNT(*) FROM impacts) as impacts,
    (SELECT COUNT(*) FROM sensor_events) as sensor_events
FROM sqlite_master WHERE name = 'timer_events';
```

## 💡 USEFUL ONE-LINERS

```bash
# Quick shot count today
sqlite3 db/leadville_runtime.db "SELECT COUNT(*) FROM timer_events WHERE event_type='SHOT' AND date(ts_ns/1e9, 'unixepoch', 'localtime') = date('now', 'localtime');"

# Last 5 timer events
sqlite3 db/leadville_runtime.db "SELECT datetime(ts_ns/1e9, 'unixepoch', 'localtime'), event_type, current_shot FROM timer_events ORDER BY ts_ns DESC LIMIT 5;"

# Impact count by sensor
sqlite3 db/leadville_runtime.db "SELECT sensor_mac, COUNT(*) FROM impacts GROUP BY sensor_mac;"

# Device pool summary
sqlite3 db/leadville.db "SELECT device_type, COUNT(*), status FROM device_pool GROUP BY device_type, status;"

# Today's shooting summary
sqlite3 db/leadville_runtime.db "SELECT COUNT(CASE WHEN event_type='SHOT' THEN 1 END) as shots, COUNT(DISTINCT device_id) as timers, MAX(current_shot) as max_shot FROM timer_events WHERE date(ts_ns/1e9, 'unixepoch', 'localtime') = date('now', 'localtime');"
```

## 🏃‍♂️ QUICK INSPECTION COMMANDS

```bash
# Run the full database inspector
python3 inspect_all_databases.py

# Run quick mode (just queries)
python3 inspect_all_databases.py --quick

# Copy to Pi and run
scp inspect_all_databases.py jrwest@192.168.1.125:/home/jrwest/projects/LeadVille/
ssh jrwest@192.168.1.125 "cd /home/jrwest/projects/LeadVille && python3 inspect_all_databases.py"
```