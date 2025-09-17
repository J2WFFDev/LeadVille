# LeadVille Impact Bridge - GitHub Project Organization# LeadVille Impact Bridge - GitHub Project Organization



This document provides a complete breakdown of the InterfaceLayer.md specification into actionable GitHub Issues organized by development phases.This document provides a complete breakdown of the InterfaceLayer.md specification into actionable GitHub Issues organized by development phases.



## 🎯 Project Structure## 🎯 Project Structure



### Milestones (Major Phases)### Milestones (Major Phases)

1. **Phase 1: Core Infrastructure** - Foundation systems and services1. **Phase 1: Core Infrastructure** - Foundation systems and services

2. **Phase 2: BLE Integration** - Device connectivity and data ingestion  2. **Phase 2: BLE Integration** - Device connectivity and data ingestion  

3. **Phase 3: Web UI & Roles** - User interfaces and role-based access3. **Phase 3: Web UI & Roles** - User interfaces and role-based access

4. **Phase 4: Production Ready** - Polish, monitoring, and deployment4. **Phase 4: Production Ready** - Polish, monitoring, and deployment



### Labels for Organization### Labels for Organization

- **Type**: `epic`, `feature`, `bug`, `documentation`, `enhancement`- **Type**: `epic`, `feature`, `bug`, `documentation`, `enhancement`

- **Priority**: `critical`, `high`, `medium`, `low`- **Priority**: `critical`, `high`, `medium`, `low`

- **Component**: `backend`, `frontend`, `ble`, `database`, `infrastructure`- **Component**: `backend`, `frontend`, `ble`, `database`, `infrastructure`

- **Phase**: `phase-1`, `phase-2`, `phase-3`, `phase-4`- **Phase**: `phase-1`, `phase-2`, `phase-3`, `phase-4`

- **Status**: `needs-triage`, `ready`, `blocked`, `in-review`- **Status**: `needs-triage`, `ready`, `blocked`, `in-review`



## 📋 Detailed Issue Breakdown## 📋 Detailed Issue Breakdown



### Phase 1: Core Infrastructure 🏗️### Phase 1: Core Infrastructure 🏗️



#### Epic #1: System Foundation#### Epic #1: System Foundation

**Priority**: Critical | **Labels**: epic, infrastructure, phase-1**Priority**: Critical | **Labels**: epic, infrastructure, phase-1



##### Issue #1.1: Raspberry Pi Base System Setup ✅ COMPLETE##### Issue #1.1: Raspberry Pi Base System Setup

- Set up Raspberry Pi OS with required packages- Set up Raspberry Pi OS with required packages

- Configure systemd services framework- Configure systemd services framework

- Implement auto-startup configuration- Implement auto-startup configuration

- **Acceptance Criteria**: Pi boots and runs LeadVille services automatically- **Acceptance Criteria**: Pi boots and runs LeadVille services automatically

- **Status**: ✅ Working - systemd service running, clean Pi environment

##### Issue #1.2: Database Foundation (SQLite + SQLAlchemy)

##### Issue #1.2: Database Foundation (SQLite + SQLAlchemy)- Implement SQLite database with WAL mode

- Implement SQLite database with WAL mode- Set up SQLAlchemy ORM with models from InterfaceLayer.md

- Set up SQLAlchemy ORM with models from InterfaceLayer.md- Create Alembic migration system

- Create Alembic migration system- **Models**: Node, Sensor, Target, Stage, Match, TimerEvent, SensorEvent, Run, Shooter, Note

- **Models**: Node, Sensor, Target, Stage, Match, TimerEvent, SensorEvent, Run, Shooter, Note

##### Issue #1.3: FastAPI Backend Foundation

##### Issue #1.3: FastAPI Backend Foundation- Create FastAPI application with basic structure

- Create FastAPI application with basic structure- Implement health check endpoints

- Implement health check endpoints- Set up logging framework (NDJSON, journald)

- Set up logging framework (NDJSON, journald)- Add CORS and security middleware

- Add CORS and security middleware

##### Issue #1.4: MQTT Internal Message Bus

##### Issue #1.4: MQTT Internal Message Bus- Install and configure mosquitto broker

- Install and configure mosquitto broker- Create MQTT topics: `bridge/status`, `sensor/{id}/telemetry`, `timer/events`, `run/{id}/events`

- Create MQTT topics: `bridge/status`, `sensor/{id}/telemetry`, `timer/events`, `run/{id}/events`- Implement Python MQTT client wrapper

- Implement Python MQTT client wrapper- Add MQTT service monitoring

- Add MQTT service monitoring

##### Issue #1.5: Networking Modes (Online/Offline)

##### Issue #1.5: Networking Modes (Online/Offline)- Implement hostapd + dnsmasq for AP mode

- Implement hostapd + dnsmasq for AP mode- Create captive portal redirecting to `bridge.local`

- Create captive portal redirecting to `bridge.local`- Add network mode switching API

- Add network mode switching API- Configure nginx reverse proxy

- Configure nginx reverse proxy

### Phase 2: BLE Device Integration 📡

### Phase 2: BLE Device Integration 📡

#### Epic #2: Device Connectivity

#### Epic #2: Device Connectivity**Priority**: Critical | **Labels**: epic, ble, phase-2

**Priority**: Critical | **Labels**: epic, ble, phase-2

##### Issue #2.1: WTVB01-BT50 Sensor Integration

##### Issue #2.1: WTVB01-BT50 Sensor Integration ✅ COMPLETE- Implement BLE ingestor service for WTVB01-BT50 sensors

- Implement BLE ingestor service for WTVB01-BT50 sensors- Parse WitMotion 5561 protocol (100Hz, 1mg resolution)

- Parse WitMotion 5561 protocol (100Hz, 1mg resolution)- Add sensor calibration and baseline establishment

- Add sensor calibration and baseline establishment- Implement sensor health monitoring (battery, RSSI)

- Implement sensor health monitoring (battery, RSSI)

- **Status**: ✅ Working - BLE sensors integrated in leadville_bridge.py##### Issue #2.2: AMG Labs Commander Timer Integration  

- Implement AMG Labs Commander BLE connectivity

##### Issue #2.2: AMG Labs Commander Timer Integration ✅ COMPLETE- Parse frame-based protocol (START/SHOT/STOP events)

- Implement AMG Labs Commander BLE connectivity- Handle UUID: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`

- Parse frame-based protocol (START/SHOT/STOP events)- Process 14-byte frames with event types: 0x0105/0x0103/0x0108

- Handle UUID: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`

- Process 14-byte frames with event types: 0x0105/0x0103/0x0108##### Issue #2.3: Pluggable Timer Driver Architecture

- **Status**: ✅ Working - AMG timer integrated in leadville_bridge.py- Create abstract timer driver interface

- Implement AMG Labs Commander driver

##### Issue #2.3: Pluggable Timer Driver Architecture- Design SpecialPie timer driver placeholder

- Create abstract timer driver interface- Add timer vendor selection in Admin UI

- Implement AMG Labs Commander driver

- Design SpecialPie timer driver placeholder##### Issue #2.4: Device Pairing and Management

- Add timer vendor selection in Admin UI- Implement BLE device discovery and pairing

- Create device assignment to targets/stages

##### Issue #2.4: Device Pairing and Management- Add device configuration APIs (`/api/admin/devices`)

- Implement BLE device discovery and pairing- Implement device health monitoring

- Create device assignment to targets/stages

- Add device configuration APIs (`/api/admin/devices`)##### Issue #2.5: Time Synchronization System

- Implement device health monitoring- Implement time sync protocol for sensors and timers

- Add drift monitoring and correction

##### Issue #2.5: Time Synchronization System- Create periodic resync (every N minutes, ±20ms drift detection)

- Implement time sync protocol for sensors and timers- Expose drift metrics in Admin UI

- Add drift monitoring and correction

- Create periodic resync (every N minutes, ±20ms drift detection)### Phase 3: Web UI & Role Management 🖥️

- Expose drift metrics in Admin UI

#### Epic #3: User Interfaces

### Phase 3: Web UI & Role Management 🖥️**Priority**: High | **Labels**: epic, frontend, phase-3



#### Epic #3: User Interfaces##### Issue #3.1: Frontend Foundation (React + Vite + Tailwind)

**Priority**: High | **Labels**: epic, frontend, phase-3- Set up React + Vite + TypeScript development environment

- Configure Tailwind CSS for responsive, kiosk-friendly design

##### Issue #3.1: Frontend Foundation (React + Vite + Tailwind) ✅ COMPLETE- Implement routing and layout components

- Set up React + Vite + TypeScript development environment- Add WebSocket client for real-time updates

- Configure Tailwind CSS for responsive, kiosk-friendly design

- Implement routing and layout components##### Issue #3.2: Authentication & Role-Based Access

- Add WebSocket client for real-time updates- Implement JWT authentication with refresh tokens

- **Status**: ✅ Working - React frontend with console log viewer- Create role system: `admin`, `ro`, `scorekeeper`, `viewer`, `coach`

- Add login/logout flows with secure session management

##### Issue #3.2: Authentication & Role-Based Access- Implement CSRF protection for unsafe methods

- Implement JWT authentication with refresh tokens

- Create role system: `admin`, `ro`, `scorekeeper`, `viewer`, `coach`##### Issue #3.3: Admin Dashboard & System Monitoring

- Add login/logout flows with secure session management- Create Admin node management (`/api/admin/node`)

- Implement CSRF protection for unsafe methods- Build network configuration interface (Online/Offline switching)

- Add system monitoring: CPU/temp/disk, service health, BLE quality

##### Issue #3.3: Admin Dashboard & System Monitoring 🔄 PARTIAL- Implement log tail viewer (last 200 lines, autoscroll)

- Create Admin node management (`/api/admin/node`)

- Build network configuration interface (Online/Offline switching)##### Issue #3.4: Range Officer (RO) View

- Add system monitoring: CPU/temp/disk, service health, BLE quality- Create visual stage layout with SVG/Canvas

- Implement log tail viewer (last 200 lines, autoscroll)- Display per-target status badges (OK/Degraded/Offline)

- **Status**: 🔄 Partial - Console log viewer working, need system monitoring- Implement live hit markers and impact visualization

- Add last-string summary panel with timestamps

##### Issue #3.4: Range Officer (RO) View- Create history sidebar for prior strings review

- Create visual stage layout with SVG/Canvas

- Display per-target status badges (OK/Degraded/Offline)##### Issue #3.5: Scorekeeper Interface

- Implement live hit markers and impact visualization- Build tabular runs view with filtering (stage/squad)

- Add last-string summary panel with timestamps- Implement timer alignment validation with bounded edits

- Create history sidebar for prior strings review- Add audit trail for data corrections

- Create export functionality (CSV, NDJSON)

##### Issue #3.5: Scorekeeper Interface

- Build tabular runs view with filtering (stage/squad)##### Issue #3.6: Spectator & Coach Views  

- Implement timer alignment validation with bounded edits- Create read-only spectator dashboard with privacy toggle

- Add audit trail for data corrections- Implement coach notes interface with per-run annotations

- Create export functionality (CSV, NDJSON)- Add bookmark functionality for key moments

- Enable coach notes export

##### Issue #3.6: Spectator & Coach Views  

- Create read-only spectator dashboard with privacy toggle##### Issue #3.7: WebSocket Real-time Updates

- Implement coach notes interface with per-run annotations- Implement WebSocket endpoint (`/ws/live`)

- Add bookmark functionality for key moments- Push real-time events: `status`, `sensor_event`, `timer_event`, `run_update`

- Enable coach notes export- Add client-side WebSocket reconnection handling

- Ensure <150ms end-to-end UI update latency

##### Issue #3.7: WebSocket Real-time Updates 🔄 PARTIAL

- Implement WebSocket endpoint (`/ws/live`)### Phase 4: Production Features 🚀

- Push real-time events: `status`, `sensor_event`, `timer_event`, `run_update`

- Add client-side WebSocket reconnection handling#### Epic #4: Production Readiness

- Ensure <150ms end-to-end UI update latency**Priority**: Medium | **Labels**: epic, production, phase-4

- **Status**: 🔄 Partial - WebSocket infrastructure exists, need event streaming

##### Issue #4.1: Boot Status Screen (Kiosk Mode)

### Phase 4: Production Features 🚀- Create fullscreen on-boot status display

- Show Node name, network mode, SSID, IPs (v4/v6)

#### Epic #4: Production Readiness- Add service status LEDs and last 20 log lines

**Priority**: Medium | **Labels**: epic, production, phase-4- Implement 2-second auto-refresh without login prompt



##### Issue #4.1: Boot Status Screen (Kiosk Mode)##### Issue #4.2: Simulation Mode & Testing Framework

- Create fullscreen on-boot status display- Create demo match with fake WTVB01-BT50 sensors and AMG timer

- Show Node name, network mode, SSID, IPs (v4/v6)- Generate realistic impact patterns and timer sequences

- Add service status LEDs and last 20 log lines- Implement pytest unit tests and Playwright e2e tests

- Implement 2-second auto-refresh without login prompt- Add simulation controls for development/demo



##### Issue #4.2: Simulation Mode & Testing Framework##### Issue #4.3: Data Export & Analytics

- Create demo match with fake WTVB01-BT50 sensors and AMG timer- Implement comprehensive CSV export (one row per run)

- Generate realistic impact patterns and timer sequences- Create NDJSON export for raw analysis with schema versioning

- Implement pytest unit tests and Playwright e2e tests- Add optional Parquet batch export for analytics

- Add simulation controls for development/demo- Create "data offload" feature for match archives



##### Issue #4.3: Data Export & Analytics##### Issue #4.4: Installation & Deployment System

- Implement comprehensive CSV export (one row per run)- Create `install_pi.sh` script for one-click Pi setup

- Create NDJSON export for raw analysis with schema versioning- Write comprehensive setup documentation (Online/Offline modes)

- Add optional Parquet batch export for analytics- Generate API OpenAPI specification

- Create "data offload" feature for match archives- Create systemd unit files for all services



##### Issue #4.4: Installation & Deployment System ✅ COMPLETE##### Issue #4.5: Monitoring & Observability

- Create `install_pi.sh` script for one-click Pi setup- Add metrics endpoint for system health

- Write comprehensive setup documentation (Online/Offline modes)- Implement structured logging with log levels

- Generate API OpenAPI specification- Create health LEDs: BLE link, MQTT broker, DB, disk space, NTP drift

- Create systemd unit files for all services- Add performance monitoring and alerting

- **Status**: ✅ Working - systemd service configured, Pi deployment working

## 🔄 Development Workflow

##### Issue #4.5: Monitoring & Observability

- Add metrics endpoint for system health### Sprint Planning (2-week sprints recommended)

- Implement structured logging with log levels1. **Sprint 1-2**: Phase 1 foundation (Issues #1.1-1.5)

- Create health LEDs: BLE link, MQTT broker, DB, disk space, NTP drift2. **Sprint 3-4**: Phase 2 BLE integration (Issues #2.1-2.5)  

- Add performance monitoring and alerting3. **Sprint 5-7**: Phase 3 UI development (Issues #3.1-3.7)

4. **Sprint 8-9**: Phase 4 production features (Issues #4.1-4.5)

## 📊 Current Status Summary

### Definition of Done

### ✅ **Completed (Ready for Production)**- [ ] Code reviewed and approved

- **Issue #1.1**: Pi Base System Setup - systemd service running- [ ] Unit tests written and passing

- **Issue #2.1**: WTVB01-BT50 Sensor Integration - BLE sensors working- [ ] Integration tests passing (where applicable)

- **Issue #2.2**: AMG Labs Commander Timer - BLE timer working  - [ ] Documentation updated

- **Issue #3.1**: Frontend Foundation - React + Vite + Tailwind- [ ] Deployed and tested on Pi

- **Issue #4.4**: Deployment System - systemd + Pi setup- [ ] Issue acceptance criteria met



### 🔄 **Partially Complete** ### GitHub Project Board Columns

- **Issue #3.3**: Admin Dashboard - Console log viewer working, need system monitoring1. **Backlog** - All created issues awaiting prioritization

- **Issue #3.7**: WebSocket Updates - Infrastructure exists, need event streaming2. **Sprint Ready** - Issues refined and ready for development

3. **In Progress** - Currently being worked on

### 🎯 **Next Priority Recommendations**4. **In Review** - Pull request created, awaiting review

1. **Issue #1.2**: Database Foundation - Store sensor/timer data5. **Testing** - Being tested on Pi hardware

2. **Issue #1.3**: FastAPI Backend - Proper API structure6. **Done** - Completed and deployed

3. **Issue #3.4**: Range Officer View - Visual stage layout

4. **Issue #3.5**: Scorekeeper Interface - Data management## 🏷️ Labels Reference



## 🔄 Development Workflow### Type Labels

- `epic` - Large multi-issue features

### Sprint Planning (2-week sprints recommended)- `feature` - New functionality 

1. **Sprint 1-2**: Phase 1 foundation (Issues #1.1-1.5)- `enhancement` - Improvements to existing features

2. **Sprint 3-4**: Phase 2 BLE integration (Issues #2.1-2.5)  - `bug` - Something isn't working

3. **Sprint 5-7**: Phase 3 UI development (Issues #3.1-3.7)- `documentation` - Documentation updates

4. **Sprint 8-9**: Phase 4 production features (Issues #4.1-4.5)

### Priority Labels  

### Definition of Done- `critical` - Blocks other work or system unusable

- [ ] Code reviewed and approved- `high` - Important for milestone completion

- [ ] Unit tests written and passing- `medium` - Standard priority

- [ ] Integration tests passing (where applicable)- `low` - Nice to have, future consideration

- [ ] Documentation updated

- [ ] Deployed and tested on Pi### Component Labels

- [ ] Issue acceptance criteria met- `backend` - FastAPI, database, APIs

- `frontend` - React UI components

### GitHub Project Board Columns- `ble` - Bluetooth device integration

1. **Backlog** - All created issues awaiting prioritization- `infrastructure` - System setup, networking, services

2. **Sprint Ready** - Issues refined and ready for development- `database` - SQLite, migrations, data models

3. **In Progress** - Currently being worked on

4. **In Review** - Pull request created, awaiting review### Phase Labels

5. **Testing** - Being tested on Pi hardware- `phase-1` - Core Infrastructure

6. **Done** - Completed and deployed- `phase-2` - BLE Integration  

- `phase-3` - Web UI & Roles

## 🏷️ Labels Reference- `phase-4` - Production Features



### Type LabelsThis organization provides clear tracking, accountability, and progress visibility for the entire LeadVille Impact Bridge development effort.
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