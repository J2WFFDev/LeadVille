# Analysis of `/home/jrwest/projects/LeadVille/leadville_bridge.py`

## File Overview
This is a **754-line Python script** that serves as the main production BLE-based impact sensor system for LeadVille. It's designed to bridge communication between shooting timers and impact sensors.

## Core Architecture

### Main Class: `LeadVilleBridge`
- **Purpose**: Central orchestrator for the entire impact detection system
- **Initialization**: Sets up database connections, BLE clients, and detection components
- **State Management**: Tracks calibration status, shot counters, and device connections

## Key Components

### 1. Device Configuration
- **Dynamic device assignment**: Reads from `bridge_device_config.json` or database
- **Default devices**: AMG timer (`60:09:C3:1F:DC:1A`) and BT50 sensor (`EA:18:3D:6D:BA:E5`)
- **Multi-device support**: Can handle multiple sensors per bridge

### 2. BLE Communication
- **AMG Timer**: Uses UUID `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- **BT50 Sensor**: Uses UUID `0000ffe4-0000-1000-8000-00805f9a34fb`
- **Connection management**: Automatic reset and reconnection logic

### 3. Calibration System
- **100-sample automatic calibration** on startup
- **Outlier filtering**: Uses interquartile range method
- **Baseline correction**: Establishes X/Y/Z baseline values
- **Timeout handling**: 30-second calibration timeout

### 4. Detection Pipeline
- **ShotDetector**: Traditional impact detection
- **EnhancedImpactDetector**: Onset-based detection with confidence scoring
- **Statistical calibrator**: 83ms primary offset with ±94ms uncertainty
- **Real-time timing calibrator**: Dynamic delay adjustment

## Data Flow

### Timer Events (AMG)
- **START beep** (0x0105): String initialization
- **SHOT event** (0x0103): Individual shot timing
- **STOP beep** (0x0108): String completion

### Sensor Events (BT50)
- **Raw data parsing**: Uses `parse_5561()` function
- **Baseline correction**: Applies calibrated offsets
- **Impact detection**: Multiple threshold-based algorithms
- **Timing correlation**: Matches shots to impacts

## Logging System

### Dual logging setup
- **Console output**: Real-time status with timestamps
- **File logging**: Complete logs in `logs/console/bridge_console_YYYYMMDD_HHMMSS.log`
- **Debug logging**: Detailed diagnostics in `logs/debug/bridge_debug_YYYYMMDD_HHMMSS.log`
- **Database persistence**: Timer events saved to `leadville_runtime.db`

## Configuration Dependencies

### Required imports from `src/impact_bridge/`
- `dev_config`: Development configuration management
- `database/`: SQLAlchemy models and session management
- `shot_detector`: Traditional impact detection
- `enhanced_impact_detection`: Onset-based detection
- `timing_calibration`: Real-time timing correlation
- `wtvb_parse`: BLE data parsing functions

## Operational States

### Startup Sequence
1. Database initialization
2. Component initialization (calibrators, detectors)
3. BLE reset and device connections
4. Automatic calibration (100 samples)
5. Notification handler setup
6. Main operation loop

### Runtime Behavior
- Continuous BLE monitoring
- Real-time impact detection
- Shot-to-impact correlation
- Database event logging
- Statistics tracking

## Current Integration

The file is designed to work with:
- **SystemD service**: `leadville-bridge.service`
- **FastAPI backend**: Separate service for web API
- **React frontend**: Device management interface
- **Database system**: Multiple SQLite databases
- **SpecialPie/AMG timers**: BLE protocol handlers we implemented

## Code Structure
- **Lines 1-100**: Imports and logging setup
- **Lines 101-200**: Component initialization
- **Lines 201-400**: Device configuration and connection
- **Lines 401-600**: Notification handlers (AMG and BT50)
- **Lines 601-754**: Main run loop and cleanup

This is the core production file that ties together all the LeadVille impact detection components into a cohesive system.

## Data Flow Architecture

### Complete Data Pipeline
The bridge implements a comprehensive data flow from device events to web display:

```
Bridge → Database Tables → Database View → FastAPI → React Frontend
   ↓           ↓              ↓             ↓           ↓
Timer &    timer_events   shot_log    /api/shot-log  Live Log
Impact  +  sensor_events    view                      Page
Events        tables
```

### Database Persistence Details

**Database Location**: `db/leadville_runtime.db`

#### Table 1: `timer_events`
- **Written by**: `_persist_timer_event()` method in bridge
- **Event Types**: START, SHOT, STOP, UNKNOWN (AMG timer events)
- **Key Columns**: `ts_ns`, `device_id`, `event_type`, `split_seconds`, `raw_hex`
- **Schema Issue**: INSERT attempts 11 columns but table defines 7 (schema mismatch)

#### Table 2: `sensor_events` (via bt50_samples)
- **Written by**: `scan_and_parse()` function when sample logging enabled
- **Event Types**: BT50 sensor impact data
- **Key Columns**: Impact magnitudes, velocity data, timestamps
- **Location**: May be in separate `db/bt50_samples.db`

### Database View Integration

#### `shot_log` View
- **Purpose**: Intelligently merges timer and sensor events
- **Correlation**: Matches timer SHOT events with sensor impacts within 2 seconds
- **Analysis**: Provides correlation quality scores (excellent/good/fair/poor)
- **Event Status**: correlated, timer_only, impact_only, timer_control

### API and Frontend Access

#### FastAPI Endpoint
- **URL**: `http://192.168.1.125:8001/api/shot-log`
- **Source**: Reads from `shot_log` database view (not raw tables)
- **Response**: JSON with merged timer + impact data

#### React Frontend
- **Live Log Page**: `/live-log` route at `http://192.168.1.125:5173/#/live-log`
- **Console Page**: `/console` route for WebSocket log streaming
- **Refresh**: Auto-refreshes every 5 seconds from shot-log API
- **Features**: Search filtering, level filtering, real-time correlation display

This architecture provides real-time correlated shot analysis by combining timer events with impact sensor data through a sophisticated database view system.