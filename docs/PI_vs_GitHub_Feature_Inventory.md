# LeadVille Pi vs GitHub Issues Feature Inventory

| Feature / Issue (GitHub)                                   | Status on Pi (Deployed/Working)         | Status in Codebase (Implemented)         | Notes / Gaps                                      |
|------------------------------------------------------------|-----------------------------------------|------------------------------------------|---------------------------------------------------|
| **Phase 1: Core Infrastructure**                           |                                         |                                          |                                                   |
| Pi Base System Setup (systemd, auto-start)                 | ✅ Deployed, systemd running             | ✅ Implemented                           | Complete                                          |
| Database Foundation (SQLite + SQLAlchemy, Alembic)         | ✅ SQLite in WAL mode, Alembic present   | ✅ Models, migrations, CLI implemented   | Complete                                          |
| FastAPI Backend Foundation                                 | ❌ Flask-SocketIO currently running      | ⚠️ FastAPI structure not yet migrated    | Flask in use, FastAPI migration pending           |
| MQTT Internal Message Bus (mosquitto, paho-mqtt)           | ✅ Mosquitto broker, Python client       | ✅ MQTT wrapper, topics implemented      | Complete                                          |
| Networking Modes (AP/captive portal, nginx)                | ⚠️ Standard networking, no AP/captive    | ⚠️ Scripts/configs not fully present     | AP/captive portal not yet implemented             |
|                                                            |                                         |                                          |                                                   |
| **Phase 2: BLE Device Integration**                        |                                         |                                          |                                                   |
| WTVB01-BT50 Sensor Integration                             | ✅ BLE sensors working                   | ✅ Ingestor, protocol, calibration       | Complete                                          |
| AMG Labs Commander Timer Integration                       | ✅ BLE timer working                     | ✅ Driver, protocol implemented          | Complete                                          |
| Pluggable Timer Driver Architecture                        | ✅ AMG driver, placeholder for others    | ✅ Abstract interface, selection in UI   | Complete                                          |
| Device Pairing and Management                              | ⚠️ Basic pairing, some UI present        | ⚠️ Device config APIs partial            | Needs full device management UI/API               |
| Time Synchronization System                                | ⚠️ Basic time sync, drift monitoring     | ⚠️ Protocol partial, UI metrics missing  | Needs periodic resync, UI drift metrics           |
|                                                            |                                         |                                          |                                                   |
| **Phase 3: Web UI & Role Management**                      |                                         |                                          |                                                   |
| Frontend Foundation (React + Vite + Tailwind)              | ✅ Deployed, running on Pi               | ✅ Implemented, responsive UI            | Complete                                          |
| Authentication & Role-Based Access (JWT, roles)            | ✅ JWT login, roles, session mgmt        | ✅ Core logic, endpoints, tests          | Final session pattern fix in progress             |
| Admin Dashboard & System Monitoring                        | ⚠️ Console log viewer working            | ⚠️ System monitoring partial             | Needs CPU/temp/disk, BLE quality, health UI       |
| Range Officer (RO) View                                    | ⚠️ Basic layout, no live hit markers     | ⚠️ Stage layout, status badges partial   | Needs live impact visualization, summary panel    |
| Scorekeeper Interface                                      | ⚠️ Basic runs view, no full filtering    | ⚠️ Tabular view, audit trail partial     | Needs full data management, export, audit trail   |
| Spectator & Coach Views                                    | ⚠️ Read-only dashboard partial           | ⚠️ Coach notes, bookmarks partial        | Needs privacy toggle, notes export                |
| WebSocket Real-time Updates                                | ⚠️ Log viewer works, event streaming WIP | ⚠️ WebSocket infra exists, events WIP    | Needs full event push, reconnection, <150ms UI    |
|                                                            |                                         |                                          |                                                   |
| **Phase 4: Production Features**                           |                                         |                                          |                                                   |
| Boot Status Screen (Kiosk Mode)                            | ❌ Not present                           | ❌ Not implemented                       | Needs fullscreen status, service LEDs, auto-refresh|
| Simulation Mode & Testing Framework                        | ⚠️ Demo scripts present                  | ⚠️ Pytest, Playwright, controls partial  | Needs full simulation, e2e tests, controls        |
| Data Export & Analytics (CSV, NDJSON, Parquet)             | ⚠️ Some export scripts                   | ⚠️ NDJSON, CSV partial, Parquet missing  | Needs analytics, schema versioning, offload       |
| Installation & Deployment System (install_pi.sh, docs)     | ✅ install_pi.sh, docs present           | ✅ Implemented, systemd units present    | Complete                                          |
| Monitoring & Observability (metrics, logs, LEDs)           | ⚠️ Basic logs, no metrics/LEDs           | ⚠️ Structured logging partial            | Needs metrics endpoint, health LEDs, alerting     |

**Legend:**
- ✅ = Complete/Working
- ⚠️ = Partial/Work in Progress
- ❌ = Not present/Not implemented

**Summary:**
- Most Phase 1 and 2 features are complete and running on the Pi.
- Phase 3 (UI, roles, monitoring) is partially complete; core UI and auth work, but advanced features are pending.
- Phase 4 (production polish, monitoring, analytics) is mostly pending or partial.
- The Pi is closely aligned with the GitHub issues, with the main gaps in FastAPI migration, advanced UI/system monitoring, and production polish features.
