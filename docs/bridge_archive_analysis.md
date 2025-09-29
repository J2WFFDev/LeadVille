# Bridge File Archive Documentation

## Multi-Sensor Bridge Implementation Found

### 📂 Archive Locations on Pi

#### **Multi-Sensor Bridge Files**:
- **`/home/jrwest/projects/LeadVille/archive/leadville_bridge_backup_sensor.py`** ⭐ **BEST CANDIDATE**
  - Size: 56,912 bytes
  - Date: Sep 23, 2025
  - Features: Full multi-sensor support with per-sensor calibration
  - Architecture: `bt50_clients = []` list for multiple BT50 connections

#### **Other Bridge Variants**:
- **`/home/jrwest/projects/LeadVille/archive/leadville_bridge_multi.py`**
  - Size: 46,374 bytes
  - Features: Dictionary-based multi-client support (`bt50_clients = {}`)
  
- **`/home/jrwest/projects/LeadVille/archive/leadville_bridge_backup_calib.py`**
  - Size: 51,982 bytes
  - Focus: Enhanced calibration features

#### **Legacy Locations**:
- `/home/jrwest/backup_/LeadVille_original/leadville_bridge.py`
- `/home/jrwest/projects/LeadVille_archive_/src/impact_bridge/enhanced_bridge.py`
- `/home/jrwest/projects/LeadVille_archive_/leadville_bridge.py`

## Multi-Sensor Capabilities Found

### **Multi-Sensor Architecture** (from `leadville_bridge_backup_sensor.py`)

#### **Connection Management**:
```python
self.bt50_clients = []  # List of all connected BT50 clients

# Connect to multiple BT50 sensors
for i, sensor_mac in enumerate(BT50_SENSORS):
    target_num = i + 1
    client = BleakClient(sensor_mac)
    await client.connect()
    self.bt50_clients.append(client)
```

#### **Per-Sensor Calibration**:
```python
self.per_sensor_calibration = {}  # {sensor_mac: {"samples": [], "baseline": {}, "complete": False}}
self.sensor_baselines = {}  # {sensor_mac: {"baseline_x": int, "noise_x": float, etc}}

# Initialize storage for each connected sensor
for sensor_mac in BT50_SENSORS:
    self.per_sensor_calibration[sensor_mac] = {
        "samples": [],
        "baseline": {},
        "complete": False,
        "target_samples": self.sensor_target_count
    }
```

#### **Multi-Sensor Notifications**:
```python
# Enable notifications for all connected BT50 sensors
for client in self.bt50_clients:
    await client.start_notify(BT50_SENSOR_UUID, self.bt50_notification_handler)
```

## Recommended Actions

1. **✅ Extract multi-sensor logic** from `leadville_bridge_backup_sensor.py`
2. **✅ Update current bridge** to support multiple BT50 connections
3. **🗑️ Clean up archive files** after extracting useful code
4. **📋 Document** the enhanced bridge capabilities

## Files to Remove Later

After extracting multi-sensor code, these files can be removed:
- `/home/jrwest/projects/LeadVille/archive/leadville_bridge_*.py` (multiple backup versions)
- `/home/jrwest/backup_/LeadVille_original/` (old backup directory)
- `/home/jrwest/projects/LeadVille_archive_/` (archive directory)