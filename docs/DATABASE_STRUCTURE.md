# LeadVille Database Structure

## Database Consolidation - September 24, 2025

The LeadVille system now uses **2 consolidated databases** with clear separation of concerns:

## 📊 **leadville.db** - Configuration Database (303KB)
**Purpose**: Store all configuration data for stages, sensors, and bridge assignments

**Tables & Data**:
- ✅ **2 leagues** (SASP, Steel Challenge)  
- ✅ **16 stage_configs** (Exclamation, V, Go Fast, 5 to Go, etc.)
- ✅ **81 target_configs** (complete target layouts with positions)
- ✅ **1 bridge** (Main Bridge assigned to stages)
- ✅ **3 sensors** (AMG Timer + BT50 sensors with bridge assignments)

**Used by**:
- 🌐 Web UI (FastAPI endpoints for configuration)
- 🔧 Bridge service (reads sensor assignments and stage configs)

**Key Features**:
- Bridge-to-stage assignments
- Sensor-to-target assignments  
- Complete stage/target geometry data
- User configuration via web interface

## 📈 **leadville_runtime.db** - Runtime/Capture Database (438KB)  
**Purpose**: Store all live sensor data and shot logs during operation

**Tables & Data**:
- ✅ **746 bt50_samples** (raw sensor acceleration data)
- ✅ **126 shot_log** entries (timer events + impact detections)
- ✅ **shot_log_simple** view (consolidated timer/sensor events)
- ✅ **device_status** and **impacts** tables

**Used by**:
- 📊 FastAPI shot-log API endpoints (`/api/shot-log`)
- 🔧 Bridge service (writes runtime sensor data)
- 📈 Live dashboard (real-time data streaming)

**Key Features**:
- Real-time sensor sample storage
- Impact detection events
- Timer event correlation
- Shot log with consolidated view

## 🗑️ **Removed Databases**

### ~~bridge.db~~ - **DELETED** (obsolete)
- Created during troubleshooting
- Had incomplete data (no leagues/stages)  
- Backed up to `bridge.db.backup.20250924_084129`
- All useful data migrated to `leadville.db`

## 📋 **Database Usage by Component**

| Component | leadville.db | leadville_runtime.db |
|-----------|-------------|----------------|
| **Web UI Configuration** | ✅ Read/Write | ❌ |
| **Bridge Service** | ✅ Read config | ✅ Write samples |
| **FastAPI /api/admin/** | ✅ Read/Write | ❌ |  
| **FastAPI /api/shot-log** | ❌ | ✅ Read |
| **Live Dashboard** | ✅ Read config | ✅ Read data |

## 🔧 **Configuration Flow**

```
Web UI → FastAPI → leadville.db → Bridge Service → BLE Devices
                                      ↓
                                 leadville_runtime.db ← Sensor Data
```

## 📝 **Maintenance Notes**

- **leadville.db**: Contains configuration - backup before major changes
- **leadville_runtime.db**: Grows during operation - monitor size and archive old data
- Both databases use SQLite WAL mode for concurrent access
- Bridge service requires both databases to function properly

## 🚀 **Clean LeadVille Naming Achieved!**

✅ **Consolidated from 3 databases to 2 databases**  
✅ **Both databases now use "leadville" naming convention**  
✅ **Clear separation of configuration vs. runtime data**  
✅ **All code references updated to use new names**