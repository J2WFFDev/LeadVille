# LeadVille Impact Bridge - GitHub Project Organization

This document provides a complete breakdown of the InterfaceLayer.md specification into actionable GitHub Issues organized by development phases.

## 🎯 Project Structure

### Milestones (Major Phases)
1. **Phase 1: Core Infrastructure** - Foundation systems and services
2. **Phase 2: BLE Integration** - Device connectivity and data ingestion  
3. **Phase 3: Web UI & Roles** - User interfaces and role-based access
4. **Phase 4: Production Ready** - Polish, monitoring, and deployment

### Labels for Organization
- **Type**: `epic`, `feature`, `bug`, `documentation`, `enhancement`
- **Priority**: `critical`, `high`, `medium`, `low`
- **Component**: `backend`, `frontend`, `ble`, `database`, `infrastructure`
- **Phase**: `phase-1`, `phase-2`, `phase-3`, `phase-4`
- **Status**: `needs-triage`, `ready`, `blocked`, `in-review`

## 📋 Detailed Issue Breakdown

### Phase 1: Core Infrastructure 🏗️

#### Epic #1: System Foundation
**Priority**: Critical | **Labels**: epic, infrastructure, phase-1

##### Issue #1.1: Raspberry Pi Base System Setup
- Set up Raspberry Pi OS with required packages
- Configure systemd services framework
- Implement auto-startup configuration
- **Acceptance Criteria**: Pi boots and runs LeadVille services automatically

##### Issue #1.2: Database Foundation (SQLite + SQLAlchemy)
- Implement SQLite database with WAL mode
- Set up SQLAlchemy ORM with models from InterfaceLayer.md
- Create Alembic migration system
- **Models**: Node, Sensor, Target, Stage, Match, TimerEvent, SensorEvent, Run, Shooter, Note

##### Issue #1.3: FastAPI Backend Foundation
- Create FastAPI application with basic structure
- Implement health check endpoints
- Set up logging framework (NDJSON, journald)
- Add CORS and security middleware

##### Issue #1.4: MQTT Internal Message Bus
- Install and configure mosquitto broker
- Create MQTT topics: `bridge/status`, `sensor/{id}/telemetry`, `timer/events`, `run/{id}/events`
- Implement Python MQTT client wrapper
- Add MQTT service monitoring

##### Issue #1.5: Networking Modes (Online/Offline)
- Implement hostapd + dnsmasq for AP mode
- Create captive portal redirecting to `bridge.local`
- Add network mode switching API
- Configure nginx reverse proxy

### Phase 2: BLE Device Integration 📡

#### Epic #2: Device Connectivity
**Priority**: Critical | **Labels**: epic, ble, phase-2

##### Issue #2.1: WTVB01-BT50 Sensor Integration
- Implement BLE ingestor service for WTVB01-BT50 sensors
- Parse WitMotion 5561 protocol (100Hz, 1mg resolution)
- Add sensor calibration and baseline establishment
- Implement sensor health monitoring (battery, RSSI)

##### Issue #2.2: AMG Labs Commander Timer Integration  
- Implement AMG Labs Commander BLE connectivity
- Parse frame-based protocol (START/SHOT/STOP events)
- Handle UUID: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- Process 14-byte frames with event types: 0x0105/0x0103/0x0108

##### Issue #2.3: Pluggable Timer Driver Architecture
- Create abstract timer driver interface
- Implement AMG Labs Commander driver
- Design SpecialPie timer driver placeholder
- Add timer vendor selection in Admin UI

##### Issue #2.4: Device Pairing and Management
- Implement BLE device discovery and pairing
- Create device assignment to targets/stages
- Add device configuration APIs (`/api/admin/devices`)
- Implement device health monitoring

##### Issue #2.5: Time Synchronization System
- Implement time sync protocol for sensors and timers
- Add drift monitoring and correction
- Create periodic resync (every N minutes, ±20ms drift detection)
- Expose drift metrics in Admin UI

### Phase 3: Web UI & Role Management 🖥️

#### Epic #3: User Interfaces
**Priority**: High | **Labels**: epic, frontend, phase-3

##### Issue #3.1: Frontend Foundation (React + Vite + Tailwind)
- Set up React + Vite + TypeScript development environment
- Configure Tailwind CSS for responsive, kiosk-friendly design
- Implement routing and layout components
- Add WebSocket client for real-time updates

##### Issue #3.2: Authentication & Role-Based Access
- Implement JWT authentication with refresh tokens
- Create role system: `admin`, `ro`, `scorekeeper`, `viewer`, `coach`
- Add login/logout flows with secure session management
- Implement CSRF protection for unsafe methods

##### Issue #3.3: Admin Dashboard & System Monitoring
- Create Admin node management (`/api/admin/node`)
- Build network configuration interface (Online/Offline switching)
- Add system monitoring: CPU/temp/disk, service health, BLE quality
- Implement log tail viewer (last 200 lines, autoscroll)

##### Issue #3.4: Range Officer (RO) View
- Create visual stage layout with SVG/Canvas
- Display per-target status badges (OK/Degraded/Offline)
- Implement live hit markers and impact visualization
- Add last-string summary panel with timestamps
- Create history sidebar for prior strings review

##### Issue #3.5: Scorekeeper Interface
- Build tabular runs view with filtering (stage/squad)
- Implement timer alignment validation with bounded edits
- Add audit trail for data corrections
- Create export functionality (CSV, NDJSON)

##### Issue #3.6: Spectator & Coach Views  
- Create read-only spectator dashboard with privacy toggle
- Implement coach notes interface with per-run annotations
- Add bookmark functionality for key moments
- Enable coach notes export

##### Issue #3.7: WebSocket Real-time Updates
- Implement WebSocket endpoint (`/ws/live`)
- Push real-time events: `status`, `sensor_event`, `timer_event`, `run_update`
- Add client-side WebSocket reconnection handling
- Ensure <150ms end-to-end UI update latency

### Phase 4: Production Features 🚀

#### Epic #4: Production Readiness
**Priority**: Medium | **Labels**: epic, production, phase-4

##### Issue #4.1: Boot Status Screen (Kiosk Mode)
- Create fullscreen on-boot status display
- Show Node name, network mode, SSID, IPs (v4/v6)
- Add service status LEDs and last 20 log lines
- Implement 2-second auto-refresh without login prompt

##### Issue #4.2: Simulation Mode & Testing Framework
- Create demo match with fake WTVB01-BT50 sensors and AMG timer
- Generate realistic impact patterns and timer sequences
- Implement pytest unit tests and Playwright e2e tests
- Add simulation controls for development/demo

##### Issue #4.3: Data Export & Analytics
- Implement comprehensive CSV export (one row per run)
- Create NDJSON export for raw analysis with schema versioning
- Add optional Parquet batch export for analytics
- Create "data offload" feature for match archives

##### Issue #4.4: Installation & Deployment System
- Create `install_pi.sh` script for one-click Pi setup
- Write comprehensive setup documentation (Online/Offline modes)
- Generate API OpenAPI specification
- Create systemd unit files for all services

##### Issue #4.5: Monitoring & Observability
- Add metrics endpoint for system health
- Implement structured logging with log levels
- Create health LEDs: BLE link, MQTT broker, DB, disk space, NTP drift
- Add performance monitoring and alerting

## 🔄 Development Workflow

### Sprint Planning (2-week sprints recommended)
1. **Sprint 1-2**: Phase 1 foundation (Issues #1.1-1.5)
2. **Sprint 3-4**: Phase 2 BLE integration (Issues #2.1-2.5)  
3. **Sprint 5-7**: Phase 3 UI development (Issues #3.1-3.7)
4. **Sprint 8-9**: Phase 4 production features (Issues #4.1-4.5)

### Definition of Done
- [ ] Code reviewed and approved
- [ ] Unit tests written and passing
- [ ] Integration tests passing (where applicable)
- [ ] Documentation updated
- [ ] Deployed and tested on Pi
- [ ] Issue acceptance criteria met

### GitHub Project Board Columns
1. **Backlog** - All created issues awaiting prioritization
2. **Sprint Ready** - Issues refined and ready for development
3. **In Progress** - Currently being worked on
4. **In Review** - Pull request created, awaiting review
5. **Testing** - Being tested on Pi hardware
6. **Done** - Completed and deployed

## 🏷️ Labels Reference

### Type Labels
- `epic` - Large multi-issue features
- `feature` - New functionality 
- `enhancement` - Improvements to existing features
- `bug` - Something isn't working
- `documentation` - Documentation updates

### Priority Labels  
- `critical` - Blocks other work or system unusable
- `high` - Important for milestone completion
- `medium` - Standard priority
- `low` - Nice to have, future consideration

### Component Labels
- `backend` - FastAPI, database, APIs
- `frontend` - React UI components
- `ble` - Bluetooth device integration
- `infrastructure` - System setup, networking, services
- `database` - SQLite, migrations, data models

### Phase Labels
- `phase-1` - Core Infrastructure
- `phase-2` - BLE Integration  
- `phase-3` - Web UI & Roles
- `phase-4` - Production Features

This organization provides clear tracking, accountability, and progress visibility for the entire LeadVille Impact Bridge development effort.