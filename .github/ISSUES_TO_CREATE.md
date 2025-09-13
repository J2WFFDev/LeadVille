# Ready-to-Copy GitHub Issues

## Issue #1: Raspberry Pi Base System Setup

**Template**: Use Feature Request template

**Title**: `[FEATURE] Raspberry Pi Base System Setup`

**Copy-paste this content:**

```markdown
## Feature Description
Set up the foundational Raspberry Pi system with all required packages, systemd services framework, and auto-startup configuration for LeadVille Impact Bridge.

## User Story
As a System Administrator, I want the Raspberry Pi to automatically boot and run LeadVille services so that the impact sensor system is ready for use without manual intervention.

## Acceptance Criteria
- [ ] Raspberry Pi OS configured with required packages (Python 3.11, pip, git, etc.)
- [ ] Systemd service framework created for LeadVille components
- [ ] Auto-startup configuration working (services start on boot)
- [ ] Basic system logging configured (journald integration)
- [ ] System health monitoring basics in place
- [ ] Documentation for Pi setup process

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5
- [ ] SD card (32GB+ recommended)
- [ ] Network connectivity (Wi-Fi/Ethernet)

### System Integration
- [ ] systemd service units
- [ ] Python virtual environment setup
- [ ] Log rotation configuration
- [ ] Basic security hardening

## Implementation Notes
- Use Raspberry Pi OS (Debian-based)
- Create dedicated user for LeadVille services
- Set up proper file permissions and service isolation
- Include watchdog configuration for reliability

## Related Issues
- Blocks all Phase 1 issues
- Foundation for Issues #2-5

## Phase/Milestone
- [x] Phase 1: Core Infrastructure
```

**Labels to add**: `feature`, `critical`, `infrastructure`, `phase-1`
**Milestone**: Phase 1: Core Infrastructure

---

## Issue #2: Database Foundation (SQLite + SQLAlchemy)

**Template**: Use Feature Request template

**Title**: `[FEATURE] Database Foundation with SQLite and SQLAlchemy ORM`

**Copy-paste this content:**

```markdown
## Feature Description
Implement the core database system using SQLite with WAL mode, SQLAlchemy ORM, and Alembic migrations to support all LeadVille data storage requirements.

## User Story
As a Developer, I want a robust, zero-maintenance database system so that sensor data, timer events, and match information are reliably stored and easily accessible.

## Acceptance Criteria
- [ ] SQLite database configured with WAL (Write-Ahead Logging) mode
- [ ] SQLAlchemy ORM models created for all entities:
  - [ ] Node(id, name, mode, ssid, ip_addr, versions, created_at)
  - [ ] Sensor(id, hw_addr, label, target_id, calib, last_seen, battery, rssi)
  - [ ] Target(id, stage_id, name, geometry, notes)
  - [ ] Stage(id, match_id, name, number, layout_json)
  - [ ] Match(id, name, date, location, metadata_json)
  - [ ] TimerEvent(id, ts_utc, type, raw, run_id)
  - [ ] SensorEvent(id, ts_utc, sensor_id, magnitude, features_json, run_id)
  - [ ] Run(id, match_id, stage_id, shooter_id, started_ts, ended_ts, status, annotations_json, audit_json)
  - [ ] Shooter(id, name, squad, metadata_json)
  - [ ] Note(id, run_id, author_role, content, ts_utc)
- [ ] Alembic migration system configured
- [ ] Database connection pooling and optimization
- [ ] Basic CRUD operations tested
- [ ] Data integrity constraints implemented

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5 (sufficient storage on SD card)

### System Integration
- [ ] SQLAlchemy Core and ORM setup
- [ ] Alembic migrations configured
- [ ] Connection string management
- [ ] Transaction handling patterns
- [ ] Error handling and logging

## Implementation Notes
- Use SQLite WAL mode for better concurrent access
- Implement proper foreign key constraints
- Add indexes for performance on frequently queried fields
- Include created_at/updated_at timestamps where appropriate
- Design for future migration to PostgreSQL if needed

## Related Issues
- Depends on: #1 (Pi Base System)
- Blocks: #3 (FastAPI Backend)
- Related to: All data storage features

## Phase/Milestone
- [x] Phase 1: Core Infrastructure
```

**Labels to add**: `feature`, `critical`, `database`, `backend`, `phase-1`
**Milestone**: Phase 1: Core Infrastructure

---

## Issue #3: FastAPI Backend Foundation

**Template**: Use Feature Request template  

**Title**: `[FEATURE] FastAPI Backend Foundation with Health Checks and Logging`

**Copy-paste this content:**

```markdown
## Feature Description
Create the core FastAPI backend application with basic structure, health check endpoints, comprehensive logging, and security middleware.

## User Story
As a Developer, I want a well-structured FastAPI backend so that I can build reliable APIs for the LeadVille Impact Bridge system with proper monitoring and security.

## Acceptance Criteria
- [ ] FastAPI application created with proper project structure
- [ ] Health check endpoints implemented:
  - [ ] `/health` - Basic health status
  - [ ] `/health/detailed` - Component health (DB, MQTT, BLE services)
- [ ] Logging framework configured:
  - [ ] NDJSON structured logging
  - [ ] Integration with systemd journald
  - [ ] Configurable log levels
  - [ ] Request/response logging middleware
- [ ] Security middleware configured:
  - [ ] CORS handling
  - [ ] Rate limiting
  - [ ] Security headers
  - [ ] Request validation
- [ ] Error handling and exception management
- [ ] API documentation (automatic OpenAPI/Swagger)
- [ ] Development/production configuration management

## Technical Requirements
### Hardware Dependencies
- [x] Raspberry Pi 4/5

### System Integration
- [ ] FastAPI with Uvicorn ASGI server
- [ ] Pydantic models for request/response validation
- [ ] SQLAlchemy integration for database operations
- [ ] MQTT client integration ready
- [ ] Environment-based configuration

## Implementation Notes
- Use FastAPI dependency injection for database sessions
- Implement proper async/await patterns
- Add request ID tracking for distributed logging
- Include metrics endpoint for monitoring
- Design API versioning strategy

## Related Issues
- Depends on: #2 (Database Foundation)
- Blocks: #4 (MQTT Message Bus), #5 (Networking Modes)
- Related to: All API development

## Phase/Milestone
- [x] Phase 1: Core Infrastructure
```

**Labels to add**: `feature`, `critical`, `backend`, `phase-1`
**Milestone**: Phase 1: Core Infrastructure

---

## Issue #4: WTVB01-BT50 Sensor BLE Integration

**Template**: Use Feature Request template

**Title**: `[FEATURE] WTVB01-BT50 Sensor BLE Integration and Data Processing`

**Copy-paste this content:**

```markdown
## Feature Description
Implement complete BLE integration for WTVB01-BT50 sensors including WitMotion 5561 protocol parsing, sensor calibration, and real-time data processing.

## User Story
As a Range Officer, I want the system to automatically connect to and process data from WTVB01-BT50 impact sensors so that shot impacts are detected and recorded in real-time.

## Acceptance Criteria
- [ ] BLE ingestor service for WTVB01-BT50 sensors created
- [ ] WitMotion 5561 protocol parser implemented:
  - [ ] 100Hz sampling rate handling
  - [ ] 1mg resolution acceleration data
  - [ ] Proper scale factor application (0.000902)
  - [ ] Multi-sample frame parsing
- [ ] Sensor calibration system:
  - [ ] Automatic baseline establishment (100+ samples)
  - [ ] Outlier filtering with IQR method
  - [ ] Dynamic zero-point correction
  - [ ] Calibration status monitoring
- [ ] Real-time data processing:
  - [ ] Impact detection algorithms
  - [ ] Threshold-based event triggering
  - [ ] Magnitude calculations
  - [ ] Noise filtering
- [ ] Sensor health monitoring:
  - [ ] Battery level tracking
  - [ ] RSSI (signal strength) monitoring
  - [ ] Connection status tracking
  - [ ] Last-seen timestamp updates
- [ ] MQTT integration for sensor events
- [ ] Database persistence of sensor events

## Technical Requirements
### Hardware Dependencies
- [x] WTVB01-BT50 sensors (WitMotion BLE accelerometers)
- [x] Raspberry Pi 4/5 with BLE capability

### System Integration
- [ ] Python `bleak` library for BLE connectivity
- [ ] WitMotion protocol implementation
- [ ] MQTT event publishing
- [ ] Database event storage
- [ ] Real-time WebSocket updates

## Implementation Notes
- BLE UUID: `0000ffe4-0000-1000-8000-00805f9a34fb`
- Implement connection retry with exponential backoff
- Handle multiple sensors simultaneously
- Include sensor MAC address management
- Add simulation mode for testing without hardware

## Related Issues
- Related to: #7 (AMG Commander Timer Integration)
- Depends on: Phase 1 infrastructure (#1-5)
- Blocks: RO dashboard development

## Phase/Milestone
- [x] Phase 2: BLE Integration
```

**Labels to add**: `feature`, `critical`, `ble`, `backend`, `phase-2`
**Milestone**: Phase 2: BLE Integration

---

## Issue #5: AMG Labs Commander Timer Integration

**Template**: Use Feature Request template

**Title**: `[FEATURE] AMG Labs Commander Timer BLE Integration and Event Processing`

**Copy-paste this content:**

```markdown
## Feature Description
Implement complete BLE integration for AMG Labs Commander shot timer including frame-based protocol parsing and START/SHOT/STOP event processing.

## User Story
As a Range Officer, I want the system to automatically receive and process timing events from the AMG Labs Commander timer so that shot sequences are accurately timed and correlated with sensor impacts.

## Acceptance Criteria
- [ ] AMG Labs Commander BLE connectivity implemented
- [ ] Frame-based protocol parser created:
  - [ ] UUID: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
  - [ ] 14-byte frame processing
  - [ ] Event type parsing: START(0x0105), SHOT(0x0103), STOP(0x0108)
  - [ ] Shot number extraction
  - [ ] Frame validation and error handling
- [ ] Timer event processing:
  - [ ] Real-time event ingestion
  - [ ] Event timestamp correlation
  - [ ] Shot sequence tracking
  - [ ] Timer status monitoring
- [ ] Time synchronization:
  - [ ] Clock sync between Pi and timer
  - [ ] Drift detection and correction
  - [ ] Periodic resync (configurable interval)
- [ ] Timer health monitoring:
  - [ ] Connection status tracking
  - [ ] Battery level monitoring (if available)
  - [ ] Signal quality (RSSI) tracking
- [ ] MQTT integration for timer events
- [ ] Database persistence of timer events

## Technical Requirements
### Hardware Dependencies
- [x] AMG Labs Commander timer
- [x] Raspberry Pi 4/5 with BLE capability

### System Integration
- [ ] Python `bleak` library for BLE connectivity
- [ ] AMG protocol implementation
- [ ] MQTT event publishing: `timer/events` topic
- [ ] Database TimerEvent storage
- [ ] Real-time WebSocket updates

## Implementation Notes
- MAC address: `60:09:C3:1F:DC:1A` (document as example)
- Implement robust connection handling with auto-reconnect
- Add frame validation and checksum verification
- Include timer simulation mode for testing
- Design for future multi-vendor timer support

## Related Issues
- Related to: #6 (WTVB01-BT50 Sensor Integration)
- Depends on: Phase 1 infrastructure (#1-5)
- Enables: Shot-to-impact correlation features

## Phase/Milestone
- [x] Phase 2: BLE Integration
```

**Labels to add**: `feature`, `critical`, `ble`, `backend`, `phase-2`
**Milestone**: Phase 2: BLE Integration