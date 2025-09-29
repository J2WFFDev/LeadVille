# BT50 Raw Data Queries
Comprehensive guide for querying BT50 sensor raw data

## 📍 **BT50 Raw Data Location**

**Table**: `bt50_samples`  
**Database**: `db/leadville_runtime.db` (746 samples currently)  
**Alternative**: `logs/bt50_samples.db` (empty - not currently used)

## 🗄️ **Table Schema**

```sql
CREATE TABLE bt50_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_ns INTEGER DEFAULT (strftime('%s','now') || '000000000'),
    sensor_mac TEXT,
    frame_hex TEXT,
    parser TEXT,
    vx INTEGER, vy INTEGER, vz INTEGER,                -- Velocity X,Y,Z (counts)
    angle_x INTEGER, angle_y INTEGER, angle_z INTEGER, -- Angle X,Y,Z (degrees)
    temp_raw INTEGER, temperature_c REAL,              -- Temperature (raw + Celsius)
    disp_x INTEGER, disp_y INTEGER, disp_z INTEGER,    -- Displacement X,Y,Z
    freq_x INTEGER, freq_y INTEGER, freq_z INTEGER     -- Frequency X,Y,Z
);
```

## 🔗 **Connection Command**

```bash
ssh jrwest@192.168.1.125
cd /home/jrwest/projects/LeadVille
sqlite3 db/leadville_runtime.db
```

## 📊 **Essential BT50 Queries**

### **1. Recent Raw Samples (Last 10)**
```sql
SELECT 
    ts_ns,
    sensor_mac,
    vx, vy, vz,
    temperature_c,
    frame_hex
FROM bt50_samples 
ORDER BY ts_ns DESC 
LIMIT 10;
```

### **2. Non-Zero Velocity Readings (Impact Detection)**
```sql
SELECT 
    ts_ns,
    sensor_mac,
    vx, vy, vz,
    temperature_c,
    SQRT(vx*vx + vy*vy + vz*vz) as magnitude
FROM bt50_samples 
WHERE vx != 0 OR vy != 0 OR vz != 0
ORDER BY ts_ns DESC 
LIMIT 20;
```

### **3. High Velocity Events (Potential Impacts)**
```sql
SELECT 
    ts_ns,
    sensor_mac,
    vx, vy, vz,
    SQRT(vx*vx + vy*vy + vz*vz) as magnitude,
    temperature_c
FROM bt50_samples 
WHERE ABS(vx) > 10 OR ABS(vy) > 10 OR ABS(vz) > 10
ORDER BY ts_ns DESC;
```

### **4. Sensor Activity by MAC Address**
```sql
SELECT 
    sensor_mac,
    COUNT(*) as sample_count,
    MIN(ts_ns) as first_sample,
    MAX(ts_ns) as last_sample,
    AVG(temperature_c) as avg_temp,
    MAX(ABS(vx)) as max_vx,
    MAX(ABS(vy)) as max_vy,
    MAX(ABS(vz)) as max_vz
FROM bt50_samples 
GROUP BY sensor_mac
ORDER BY sample_count DESC;
```

### **5. Time-Range Query (Last Hour)**
```sql
SELECT 
    ts_ns,
    sensor_mac,
    vx, vy, vz,
    temperature_c
FROM bt50_samples 
WHERE ts_ns > (strftime('%s', 'now') - 3600) * 1000000000
ORDER BY ts_ns DESC;
```

### **6. Movement Detection Analysis**
```sql
SELECT 
    sensor_mac,
    COUNT(*) as total_samples,
    COUNT(CASE WHEN vx = 0 AND vy = 0 AND vz = 0 THEN 1 END) as zero_velocity,
    COUNT(CASE WHEN ABS(vx) > 0 OR ABS(vy) > 0 OR ABS(vz) > 0 THEN 1 END) as movement_detected,
    ROUND(100.0 * COUNT(CASE WHEN ABS(vx) > 0 OR ABS(vy) > 0 OR ABS(vz) > 0 THEN 1 END) / COUNT(*), 2) as movement_percentage
FROM bt50_samples 
GROUP BY sensor_mac;
```

### **7. Temperature Monitoring**
```sql
SELECT 
    sensor_mac,
    COUNT(*) as samples,
    ROUND(MIN(temperature_c), 1) as min_temp,
    ROUND(AVG(temperature_c), 1) as avg_temp,
    ROUND(MAX(temperature_c), 1) as max_temp
FROM bt50_samples 
GROUP BY sensor_mac;
```

### **8. Raw Hex Frame Analysis**
```sql
SELECT 
    ts_ns,
    sensor_mac,
    frame_hex,
    parser,
    vx, vy, vz
FROM bt50_samples 
WHERE vx != 0 OR vy != 0 OR vz != 0
ORDER BY ts_ns DESC 
LIMIT 10;
```

## 🔍 **Diagnostic Queries**

### **Check Data Freshness**
```sql
SELECT 
    sensor_mac,
    MAX(ts_ns) as last_sample_ns,
    (strftime('%s', 'now') * 1000000000 - MAX(ts_ns)) / 1000000000 as seconds_ago
FROM bt50_samples 
GROUP BY sensor_mac;
```

### **Velocity Distribution**
```sql
SELECT 
    sensor_mac,
    'vx' as axis,
    MIN(vx) as min_val,
    AVG(vx) as avg_val, 
    MAX(vx) as max_val
FROM bt50_samples 
GROUP BY sensor_mac
UNION ALL
SELECT 
    sensor_mac,
    'vy' as axis,
    MIN(vy) as min_val,
    AVG(vy) as avg_val,
    MAX(vy) as max_val
FROM bt50_samples 
GROUP BY sensor_mac
UNION ALL
SELECT 
    sensor_mac,
    'vz' as axis,
    MIN(vz) as min_val,
    AVG(vz) as avg_val,
    MAX(vz) as max_val
FROM bt50_samples 
GROUP BY sensor_mac
ORDER BY sensor_mac, axis;
```

### **Sample Rate Analysis**
```sql
SELECT 
    sensor_mac,
    COUNT(*) as total_samples,
    (MAX(ts_ns) - MIN(ts_ns)) / 1000000000 as duration_seconds,
    ROUND(COUNT(*) * 1.0 / ((MAX(ts_ns) - MIN(ts_ns)) / 1000000000), 2) as samples_per_second
FROM bt50_samples 
WHERE ts_ns > 0
GROUP BY sensor_mac;
```

## 💡 **One-Line Terminal Queries**

```bash
# Quick sample count
sqlite3 db/leadville_runtime.db "SELECT COUNT(*) FROM bt50_samples;"

# Recent movement
sqlite3 db/leadville_runtime.db "SELECT sensor_mac, vx, vy, vz FROM bt50_samples WHERE vx!=0 OR vy!=0 OR vz!=0 ORDER BY ts_ns DESC LIMIT 5;"

# Sensor summary
sqlite3 db/leadville_runtime.db "SELECT sensor_mac, COUNT(*) FROM bt50_samples GROUP BY sensor_mac;"

# Max velocities
sqlite3 db/leadville_runtime.db "SELECT sensor_mac, MAX(ABS(vx)), MAX(ABS(vy)), MAX(ABS(vz)) FROM bt50_samples GROUP BY sensor_mac;"

# Temperature check
sqlite3 db/leadville_runtime.db "SELECT sensor_mac, AVG(temperature_c) FROM bt50_samples GROUP BY sensor_mac;"
```

## 🎯 **Impact Detection Queries**

### **Find Potential Bullet Impacts (Threshold Analysis)**
```sql
-- Check for velocity spikes above various thresholds
SELECT 
    'Threshold 5' as threshold,
    COUNT(*) as events,
    COUNT(DISTINCT sensor_mac) as sensors
FROM bt50_samples 
WHERE ABS(vx) > 5 OR ABS(vy) > 5 OR ABS(vz) > 5
UNION ALL
SELECT 
    'Threshold 10' as threshold,
    COUNT(*) as events,
    COUNT(DISTINCT sensor_mac) as sensors
FROM bt50_samples 
WHERE ABS(vx) > 10 OR ABS(vy) > 10 OR ABS(vz) > 10
UNION ALL
SELECT 
    'Threshold 25' as threshold,
    COUNT(*) as events,
    COUNT(DISTINCT sensor_mac) as sensors
FROM bt50_samples 
WHERE ABS(vx) > 25 OR ABS(vy) > 25 OR ABS(vz) > 25
UNION ALL
SELECT 
    'Threshold 50' as threshold,
    COUNT(*) as events,
    COUNT(DISTINCT sensor_mac) as sensors
FROM bt50_samples 
WHERE ABS(vx) > 50 OR ABS(vy) > 50 OR ABS(vz) > 50;
```

### **Time-Correlated Impact Search (with Timer Events)**
```sql
-- Find BT50 velocity spikes near timer shot events
WITH timer_shots AS (
    SELECT ts_ns, current_shot, device_id
    FROM timer_events 
    WHERE event_type = 'SHOT'
    ORDER BY ts_ns DESC LIMIT 10
),
velocity_spikes AS (
    SELECT ts_ns, sensor_mac, vx, vy, vz,
           SQRT(vx*vx + vy*vy + vz*vz) as magnitude
    FROM bt50_samples 
    WHERE ABS(vx) > 5 OR ABS(vy) > 5 OR ABS(vz) > 5
)
SELECT 
    ts.current_shot,
    ts.ts_ns as shot_time,
    vs.ts_ns as spike_time,
    (vs.ts_ns - ts.ts_ns) / 1000000 as time_diff_ms,
    vs.sensor_mac,
    vs.vx, vs.vy, vs.vz,
    ROUND(vs.magnitude, 1) as magnitude
FROM timer_shots ts
CROSS JOIN velocity_spikes vs
WHERE ABS(vs.ts_ns - ts.ts_ns) < 2000000000  -- Within 2 seconds
ORDER BY ts.ts_ns DESC, ABS(vs.ts_ns - ts.ts_ns);
```

## 📈 **Current Data Status**

Based on your current data:
- **✅ 746 BT50 samples** in `db/leadville_runtime.db`  
- **✅ Active sensor**: `EA:18:3D:6D:BA:E5`
- **✅ Recent velocity readings**: vx/vy/vz values ranging 0-21 counts
- **✅ Temperature monitoring**: ~25°C average

The BT50 raw data table contains all the detailed sensor readings including velocity, angle, temperature, and displacement data that the bridge processes for impact detection.