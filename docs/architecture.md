## LeadVille - Architecture and Component Map

This document maps the LeadVille project components, how they relate, and the runtime data/event flow from sensors to the frontend. It is intended as a developer-facing guide for debugging, systemd deployment, and code navigation.

### High-level overview
- The core BLE bridge runs on the Raspberry Pi and is started by `systemd` as the authoritative runtime. The bridge communicates with BT50 vibration sensors and AMG timer devices via BLE.
- The bridge produces NDJSON logs and emits real-time events to an `EventStreamer` (WebSockets / optional MQTT).
- A separate capture/ingest process writes NDJSON or bridge-generated events into the capture SQLite DB (`db/bt50_samples.db`), which exposes a `shot_log` view used by the FastAPI backend and frontend.

### Major components (files & purpose)
- `leadville_bridge.py` (repo root)
  - Minimal launcher used by `systemd` to ensure `src/` is on `sys.path` and to call the package entrypoint `impact_bridge.leadville_bridge:main()`.

- `src/impact_bridge/leadville_bridge.py`
  - A comprehensive, self-contained Bridge implementation (older/monolithic) that controls BLE connections, calibration, detection, and some direct database writes (best-effort). Useful for local debugging and historical reference.

- `src/impact_bridge/bridge.py`
  - A more modular, production-ready `Bridge` class that is configuration-driven (`AppConfig`). It uses BLE client abstractions, an NDJSON logger, and a `Detector` to create `HIT` and `T0` events.

- `src/impact_bridge/config.py`
  - YAML-based configuration loader for `AppConfig`, `SensorConfig`, `AmgConfig`, `LoggingConfig`, and `DatabaseConfig`. Use `load_config()` and `validate_config()` to load/run the `Bridge`.

- `src/impact_bridge/ble/witmotion_bt50.py`
  - `Bt50Client` and `Bt50Sample` implementations. Responsible for BLE connection, notification handling, parsing BT50 frames, and producing `Bt50Sample` objects.

- `src/impact_bridge/ble/amg.py` (and related AMG parsers)
  - AMG timer BLE client(s) used for T0/start/shot/stop messages. (See `leadville_bridge.py` and `bridge.py` for usage.)

- `src/impact_bridge/detector.py`
  - Detection core (`HitDetector`, `MultiPlateDetector`) implementing the logic to turn samples into hit events (peak detection, dead-time, ring filtering).

- `src/impact_bridge/logs.py`
  - `NdjsonLogger` and `DualNdjsonLogger`. The Bridge writes structured NDJSON logs here (status, event, debug). These logs are the primary capture input for the ingestion pipeline.

- `src/impact_bridge/event_streamer.py`
  - `EventStreamer` manages WebSocket client subscriptions and optional MQTT forwarding. The FastAPI server uses it to push real-time events to front-end clients.

- `src/impact_bridge/fastapi_backend.py`
  - HTTP/WebSocket server exposing admin endpoints, log access, and the `/api/shot-log` endpoint which reads the capture DB's `shot_log` view.

- `src/impact_bridge/database/` (models, `session.py`, `crud.py`, migrations)
  - SQLAlchemy models, CRUD helpers, and session factory used by the FastAPI backend and some bridge tools. Note: `session.py` currently constructs a session pointing to the Pi's expected DB path; the capture DB (`bt50_samples.db`) is a separate SQLite used by the ingest/capture pipeline.

- `frontend/`
  - React/Next frontend that consumes `/api/*` endpoints and WebSocket streams for live logs and controls (restart the bridge service, manage devices, assign sensors to targets).

- `scripts/` (repo helpers)
  - Project helpers such as `scripts/check_sensors_config.py` (validate config) and `scripts/cleanup_repo.py` (dry-run archiver). These are utilities — not systemd services.

### Runtime / systemd relationship
- `systemd` runs the bridge service (commonly `leadville-bridge`); the unit uses the repo launcher `leadville_bridge.py` or calls into the package module. The Pi is the authoritative runtime and data location.
- The FastAPI backend (`uvicorn`) is typically run as a separate service (or Docker) and serves the frontend and admin endpoints. The backend reads from the capture DB view `shot_log` to present combined timer and impact events.

### Runtime note (Pi)

The Raspberry Pi at the deployment site is the authoritative runtime. The Pi currently runs the monolithic bridge implementation via systemd:

- Service: `leadville-bridge.service`
- ExecStart: `/usr/bin/python3 /home/jrwest/projects/LeadVille/leadville_bridge.py`

Because the Pi runs the monolithic `leadville_bridge.py`, the modular `Bridge` class implemented in `src/impact_bridge/bridge.py` is not active unless the systemd unit is updated. If you want the modular bridge to be active you should test it locally and then update the Pi's unit to run the modular entrypoint.

### Architecture diagram (Mermaid)

Below is a concise Mermaid diagram showing the runtime components and data flows (BLE -> Bridge -> NDJSON / capture DB -> Backend -> Frontend).

```mermaid
flowchart LR
  subgraph Pi[LeadVille Raspberry Pi]
    direction TB
    A[leadville_bridge.py (monolithic)] -->|BLE| B[AMG Timer]
    A -->|BLE| C[BT50 Sensors]
    A -->|NDJSON logs + best-effort DB writes| D[logs/ (NDJSON & debug)]
    A -->|writes| E[/home/jrwest/projects/LeadVille/logs/bt50_samples.db]
    subgraph Ingest[Optional ingest/capture process]
      direction LR
      D -->|consume NDJSON| E
    end
  end

  subgraph Backend[FastAPI Backend]
    direction TB
    F[fastapi_backend] -->|reads| E
    F -->|reads/writes| G[/home/jrwest/projects/LeadVille/leadville.db]
    F --> H[EventStreamer (WebSocket/MQTT)]
  end

  subgraph Frontend[Web UI]
    direction TB
    I[React/Next frontend] -->|REST/WebSocket| F
  end

  subgraph DevRepo[Repository]
    direction TB
    J[src/impact_bridge/bridge.py (modular)]
    J -->|NDJSON| D
    J -->|BLE| C
    J -. Not running by default .-> A
  end

  style Pi fill:#f9f,stroke:#333,stroke-width:1px
  style Backend fill:#efe,stroke:#333
  style Frontend fill:#eef,stroke:#333
  style DevRepo fill:#fffbe6,stroke:#333
```

Notes:

- `leadville_bridge.py` (monolithic) contains best-effort writes to `logs/bt50_samples.db` (timer_events and impacts) and also writes verbose NDJSON debug files under `logs/debug/`.
- The modular `Bridge` in `src/impact_bridge/bridge.py` uses `NdjsonLogger` to write canonical NDJSON events to `logs/` and is intended to be run as an alternate implementation; switching to it requires updating the Pi's service unit and validating behavior.
- The API (`fastapi_backend`) reads both `leadville.db` (app DB) and `bt50_samples.db` (capture DB / shot_log view) to serve the frontend and WebSocket clients.


### End-to-end event flow (sensor sample → frontend)
1. BLE Notification
   - The physical BT50 sensor sends BLE notifications which are received by `Bt50Client` in `src/impact_bridge/ble/witmotion_bt50.py`.
   - `Bt50Client._handle_notification()` parses raw bytes and produces a `Bt50Sample` (timestamp + vx/vy/vz + amplitude).

2. Bridge Buffering & Detection
   - `Bridge._on_bt50_sample()` (in `src/impact_bridge/bridge.py`) is called with the `Bt50Sample` and the sensor/plate identifiers.
   - Samples are buffered per-sensor for strip-chart debug and periodically flushed by `_process_bt50_buffer()`.
   - Each sample is passed into the `MultiPlateDetector` via `detector.process_sample()` which returns `hit_event` objects when an impact is detected.

3. Logging & Event Emission
   - When a hit is detected, `Bridge` calls `self.logger.event('HIT', ...)` to write a structured NDJSON record. `NdjsonLogger`/`DualNdjsonLogger` ensure records land in `logs/` (main + debug files).
   - The Bridge also calls into the `event_streamer` (or the FastAPI `event_streamer`) to broadcast the event over WebSocket and optionally publish to MQTT.

4. Capture / Ingest Process
   - A separate capture/ingest process (not necessarily in this repo) watches NDJSON logs or receives event messages and writes rows into `logs/bt50_samples.db`. This process creates/maintains schema and the `shot_log` view used by the API.
   - The bridge may also perform lightweight, best-effort writes directly (see `leadville_bridge.py` `_persist_timer_event()`), but long-term canonical storage is written by the capture/ingest pipeline on the Pi.

5. API & Frontend
   - The FastAPI server reads the `shot_log` view from the capture DB at `/home/jrwest/projects/LeadVille/logs/bt50_samples.db` and exposes `/api/shot-log` for the frontend.
   - The frontend fetches `/api/shot-log` and subscribes to `/ws/live` for real-time updates.

### Timer (AMG) event flow
- AMG timer BLE notifications are parsed either by `leadville_bridge.py` or `AmgClient` (depending on which bridge implementation is running).
- Timer events (START/SHOT/STOP) are logged via the NDJSON logger and/or persisted directly to the capture DB (best-effort writes in `leadville_bridge.py`). Timer events are then visible in the `shot_log` view when the capture process consolidates them.

### Configuration & where to look
- Bridge configuration (which sensors to run) is YAML-driven via `src/impact_bridge/config.py` and `AppConfig`. Typical config locations:
  - `/etc/leadville/bridge.yaml` or a repo-local `config/` folder (deployment-specific). The running `systemd` unit normally points to the config path used at boot.
- Use `scripts/check_sensors_config.py` to validate YAML with the same loader as the bridge.

### Important file / endpoint quick-reference
- Launcher: `leadville_bridge.py` (repo root)
- Bridge class: `src/impact_bridge/bridge.py` (config-driven)
- Monolithic bridge: `src/impact_bridge/leadville_bridge.py` (older, feature-rich)
- BLE client: `src/impact_bridge/ble/witmotion_bt50.py` (BT50 parser & client)
- Logging: `src/impact_bridge/logs.py` (NDJSON logging)
- Event streaming: `src/impact_bridge/event_streamer.py` (WebSockets/MQTT)
- API: `src/impact_bridge/fastapi_backend.py` (endpoints, `/api/shot-log`)
- DB session & CRUD: `src/impact_bridge/database/session.py`, `src/impact_bridge/database/crud.py`

### Parsers and packet formats

- `src/impact_bridge/ble/witmotion_bt50.py`
  - Primary BT50 parser used by the `Bt50Client`. It expects 20-byte frames with header bytes `0x55,0x61` and parses int16 vx/vy/vz values. It returns `Bt50Sample` objects with timestamp and amplitude.

- `src/impact_bridge/ble/wtvb_parse.py` (and variants)
  - A more feature-rich parser referenced as `scan_and_parse`, `parse_flag61_frame`, and `parse_wtvb32_frame` in the monolithic bridge. It supports verbose parsing and optionally writing raw parsed frames into the capture DB for offline analysis (`write_db=True`). This is used when `dev_config` or `dev` mode enables sample logging.

- `src/impact_bridge/ble/wtvb_parse_simple.py` (exports `parse_5561`)
  - A compact/simple parser that returns scaled samples used by detection path and for real-time processing where low overhead is important.

- `src/impact_bridge/ble/amg_parse.py` / `format_amg_event`
  - AMG timer parsers that decode timer frames into structured START/SHOT/STOP semantics and optional richer fields (current_shot, total_shots, timer_time). The Bridge uses these to persist `timer_events` and to correlate with `sensor_events`.

Notes on parsers:
- Parsers are organized as BLE-specific modules under `src/impact_bridge/ble/`.
- Simple parser (`parse_5561`) is safe for the hot path (low CPU, used inside notification handler). Verbose parsers are allowed to perform additional IO (writing to DB or files) but should be called in an error-tolerant wrapper so detection isn't blocked by storage issues.

### Backend: services, important modules, and endpoints

- `src/impact_bridge/fastapi_backend.py` (main API)
  - Health: `GET /api/health`, `GET /api/health/detailed`
  - Logs: `GET /api/logs` (tail/parse NDJSON and plain logs)
  - Shot log: `GET /api/shot-log?limit=...` — reads `logs/bt50_samples.db`'s `shot_log` view and returns combined timer+impact records.
  - Admin endpoints: device management (`/api/admin/devices*`), services (`/api/admin/services` + `POST /api/admin/services/restart`), network (`/api/admin/network`), system (`/api/admin/system`). These endpoints call into `src/impact_bridge/system_monitor`, `device_manager`, `network_manager`, etc.
  - WebSockets: `/ws/logs` (log batches) and `/ws/live` (real-time event streaming via `EventStreamer`).

- `src/impact_bridge/database/`
  - `session.py` constructs SQLAlchemy sessions (note: contains Pi deployment path defaults).
  - `crud.py` contains high-level CRUD wrappers used by API endpoints and admin tools (Sensors, TimerEvent, SensorEvent, Run, etc.).

- `src/impact_bridge/event_streamer.py`
  - Centralized broadcaster for WebSocket clients and optional MQTT integration. Methods: `send_sensor_event`, `send_timer_event`, `start_periodic_tasks`.

- Optional background services (capture/ingest)
  - The ingestion/capture process that writes NDJSON or parsed events into `logs/bt50_samples.db` is usually a separate service running on the Pi. It is responsible for creating the `shot_log` view used by the API. This process may be implemented externally or by a script in `tools/` (search for `bt50_capture_db` / `bt50_export_csv` in the repo for historical helpers).

### Frontend: pages and what they do

- `frontend/src/pages/ConsolePage.tsx`
  - Live console view, can restart bridge service (`/api/admin/services/restart`), tail logs via WebSocket, and show system actions.

- `frontend/src/pages/LiveLogPage.tsx`
  - Real-time event view; subscribes to `/ws/live` and displays sensor/timer events.

- `frontend/src/pages/SettingsPage.tsx`
  - Admin operations (network switching, bridge restart, device discovery/pairing). Calls the admin endpoints on the FastAPI backend.

Notes:
- Frontend pages call the backend admin endpoints for device discovery, pairing, bridge config, and service control. These operations usually require sudo/system privileges on the Pi (bridge restart uses `systemctl restart leadville-bridge`).

### Data model & `shot_log` view

- The canonical capture DB (`logs/bt50_samples.db`) contains raw sample tables and a `shot_log` view that merges timer events and impact events into a single feed for the UI.
- Common fields produced by the view (see `fastapi_backend.py` query):
  - `log_id`, `record_type` ("shot", "impact", "timer_control"), `event_time` (formatted), `device_id`, `event_type` (START/SHOT/STOP/IMPACT), `current_shot`, `split_seconds`, `string_total_time`, `sensor_mac`, `impact_magnitude`, `ts_ns`.

### Developer notes & where to extend

- Adding / improving a parser
  - Add parser code under `src/impact_bridge/ble/` and expose a small, fast `parse_` function for use in notification handlers. If you need verbose persistence, keep that behind a flag and call it from a background task or guarded `try/except` so detection latency is not affected.

- Instrumenting the Bridge for debugging
  - Use `NdjsonLogger.status()` and `NdjsonLogger.event()` so the capture pipeline can pick up events. Add clear `Configured BT50 sensors` status messages at startup to confirm selection.

- Testing & CI suggestions
  - Add unit tests for parser functions (provide representative binary frames and assert parsed values).
  - Add a small integration test that runs `Bridge` against a synthetic `Bt50Client` stub that emits known samples and assert `HIT` events are emitted.

### Security & deployment notes
- Restart endpoints (`/api/admin/services/restart`) rely on system privileges to perform `systemctl` calls. The FastAPI service usually runs under a low-privileged user; allow a controlled sudoers entry for the web service user to restart the `leadville-bridge` service without a password if automation is required.
- Avoid writing secrets or credentials into the repo; use env vars and the `DatabaseConfig` / `dev_config` files for local overrides.

---

If you'd like, I can now:
- generate a Mermaid diagram of the flow and add it to `docs/architecture.md`, or
- inspect the Pi `systemd` unit and log files to determine which bridge implementation is running and whether the configured sensors are loaded.

## Tools, helpers, and runbook

This section inventories repository tools that are not part of the hot-path runtime but are useful for debugging, ingest, migration, or offline analysis. It also includes a minimal systemd/runbook for the bridge service and sample data formats.

### Tools & helpers inventory (non-exhaustive)
- `scripts/check_sensors_config.py` — Validate YAML config using `src/impact_bridge/config.py` loader.
- `scripts/cleanup_repo.py` — Dry-run archiver for noisy scripts (move to `archive/`).
- `tools/bt50_capture_db.py` (historical) — helpers to import/export BT50 samples into SQLite (search for `bt50_capture_db` or `bt50_export_csv`).
- `console_viewer.py` / `console_viewer_latest.py` — local viewers for printed logs and NDJSON files.
- `create_simple_views.py`, `init_database_views.py` — helpers to create the `shot_log` view and other convenience SQL views used by the FastAPI UI.
- `manage_db.py` / `init_sensor_database.py` — database initialization and schema helpers.

If a script looks like a one-off (has `backup`/`patch`/`fix` in its name), it's likely archival and safe to move to `archive/` after verifying it isn't used by systemd or startup scripts.

### Minimal systemd runbook (bridge service)

Unit file hints (check on the Pi):

```ini
[Unit]
Description=LeadVille Bridge (BLE)
After=network.target

[Service]
Type=simple
User=leadville
WorkingDirectory=/home/jrwest/projects/LeadVille
ExecStart=/usr/bin/python3 /home/jrwest/projects/LeadVille/leadville_bridge.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Commands to manage the service (on Pi):

```pwsh
ssh rpi 'sudo systemctl daemon-reload'
ssh rpi 'sudo systemctl enable --now leadville-bridge'
ssh rpi 'sudo systemctl status leadville-bridge --no-pager'
ssh rpi 'sudo journalctl -u leadville-bridge -n 200 --no-pager'
```

Ensure the `ExecStart` in the unit points to the intended launcher (`leadville_bridge.py`) or a direct package invocation (e.g., `python -m impact_bridge.leadville_bridge`). If it points to a different script (e.g., a legacy backup), update the unit and restart.

### Sample NDJSON record (from `NdjsonLogger`) — event and status

Event (HIT):

```json
{
  "seq": 12345,
  "type": "event",
  "ts_ms": 1234.567,
  "msg": "HIT",
  "t_rel_ms": 512.34,
  "plate": "P1",
  "data": {
    "sensor_id": "S1",
    "peak_amplitude": 2.34,
    "duration_ms": 5
  },
  "hms": "12:34:56.789"
}
```

Status:

```json
{
  "seq": 12346,
  "type": "status",
  "ts_ms": 1235.000,
  "msg": "Configured BT50 sensors",
  "data": {"sensors": [{"sensor": "S1", "mac": "EA:18:3D:6D:BA:E5", "plate": "P1"}]},
  "hms": "12:34:56.890"
}
```

### `shot_log` view — minimal schema sample

The `shot_log` view merges timer events and impact events. A simplified set of columns looks like:

```sql
CREATE VIEW shot_log AS
SELECT
  id as log_id,
  'shot' as record_type,
  datetime(ts_ns/1e9, 'unixepoch') as event_time,
  device_id,
  event_type,
  current_shot,
  split_seconds,
  string_total_time,
  sensor_mac,
  impact_magnitude,
  ts_ns
FROM sensor_events
UNION ALL
SELECT
  id as log_id,
  'timer_control' as record_type,
  datetime(ts_ns/1e9, 'unixepoch') as event_time,
  device_id,
  event_type,
  current_shot,
  split_seconds,
  string_total_time,
  NULL as sensor_mac,
  NULL as impact_magnitude,
  ts_ns
FROM timer_events;
```

Adjustments and additional fields are common; use `create_simple_views.py` / `init_database_views.py` to regenerate the view if the schema changes.

### Short troubleshooting runbook (quick checks)
1. Are sensors configured and selected?
   - Check NDJSON status logs for `Configured BT50 sensors`.
   - `ssh rpi 'grep -i "Configured BT50 sensors" /home/jrwest/projects/LeadVille/logs/debug/*.ndjson | tail -n 20'`

2. Is the bridge service running?
   - `ssh rpi 'sudo systemctl status leadville-bridge'`
   - Check journal: `ssh rpi 'sudo journalctl -u leadville-bridge -n 200 --no-pager'`

3. Are events reaching the capture DB?
   - `ssh rpi 'sqlite3 /home/jrwest/projects/LeadVille/logs/bt50_samples.db "SELECT COUNT(*) FROM sensor_events;"'`
   - Check recent shot_log rows: `ssh rpi 'sqlite3 /home/jrwest/projects/LeadVille/logs/bt50_samples.db "SELECT * FROM shot_log ORDER BY ts_ns DESC LIMIT 10;"'`

4. If the bridge logs hits but DB is not changing:
   - Verify ingest/capture process is running and has permissions to write the DB.
   - Inspect capture service logs (systemd unit or script logs) and `/var/log` or service-specific logs.

5. Validate YAML config used by the running unit:
   - Check systemd `ExecStart` for config path or search for commonly used config locations in `/etc/leadville`, `~/.config/leadville`, or the repo `config/` folder.

---

I completed the doc additions. I'll mark this todo completed unless you'd like more sections added (e.g., a complete file-by-file index or automated script that generates the inventory).

### Troubleshooting checklist (validation commands)
- Check systemd status of bridge on the Pi:

```pwsh
ssh rpi 'sudo systemctl status leadville-bridge --no-pager'
ssh rpi 'sudo journalctl -u leadville-bridge -n 200 --no-pager'
```

- Tail bridge NDJSON logs on the Pi (show status/events):

```pwsh
ssh rpi 'tail -f /home/jrwest/projects/LeadVille/logs/bridge_*.ndjson'
ssh rpi 'tail -f /home/jrwest/projects/LeadVille/logs/debug/bridge_debug_*.ndjson'
```

- Inspect capture DB `shot_log` view:

```pwsh
ssh rpi 'sqlite3 /home/jrwest/projects/LeadVille/logs/bt50_samples.db "SELECT * FROM shot_log ORDER BY ts_ns DESC LIMIT 10;"'
```

- Check that the Bridge created `Configured BT50 sensors` status records (confirm selection):

```pwsh
ssh rpi 'grep -i "Configured BT50 sensors" /home/jrwest/projects/LeadVille/logs/debug/*.ndjson | tail -n 20'
```

- Validate YAML config locally using helper (from repo root):

```pwsh
python scripts/check_sensors_config.py path/to/bridge.yaml
```

### Edge cases & notes
- There are two Bridge implementations in the repo: the monolithic `leadville_bridge.py` and the modular `Bridge` class in `src/impact_bridge/bridge.py`. The `systemd` unit may point to either; check the unit file on the Pi to know which is running.
- The capture/ingest pipeline is separate — the Bridge writes NDJSON and events; if the DB doesn't update, first verify the capture service on the Pi is running.
- Some DB paths are hard-coded in code (see `src/impact_bridge/database/session.py` and `src/impact_bridge/fastapi_backend.py`) — these reflect the Pi deployment layout; update carefully if deploying to a different host.

### Next steps (recommended)
1. Confirm which bridge implementation the `systemd` unit runs on the Pi and standardize to `src/impact_bridge/bridge.py` where practical.
2. Verify the capture/ingest service is running on the Pi and writing to `logs/bt50_samples.db`.
3. Use the `scripts/check_sensors_config.py` helper to confirm YAML `sensors:` entries used by the running bridge.
4. After stabilization, run the repo cleanup (`scripts/cleanup_repo.py --apply`) to archive noisy scripts (review dry-run output first).

If you want, I can: (A) create a rendered diagram (Mermaid) for this flow, (B) inspect the Pi `systemd` unit and the active logs, or (C) run the config check against a given YAML file. Tell me which next step you want me to do.


flowchart LR
    subgraph Sensors
        BT50["BT50 Vibration Sensor"]
        AMG["AMG Timer"]
    end

    subgraph Bridge["Bridge (Raspberry Pi, systemd)"]
        BLE["BLE Clients (witmotion_bt50.py, amg.py)"]
        DET["Detector (detector.py)"]
        LOG["NDJSON Logger (logs.py)"]
        STREAM["EventStreamer (WebSocket / MQTT)"]
    end

    subgraph Capture["Capture/Ingest Process"]
        NDJSON["NDJSON Logs"]
        DB["SQLite DB (bt50_samples.db, shot_log view)"]
    end

    subgraph Backend["FastAPI Backend (fastapi_backend.py)"]
        API["/api/shot-log"]
        WS["/ws/live"]
    end

    subgraph Frontend["React/Next Frontend"]
        UI["Match Admin & RO Screens"]
    end

    %% Flows
    BT50 -->|BLE Notify| BLE
    AMG -->|BLE Notify| BLE
    BLE --> DET
    DET -->|HIT/T0 Events| LOG
    DET --> STREAM
    LOG --> NDJSON
    STREAM --> WS
    NDJSON -->|Ingest| DB
    DB --> API
    API --> UI
    WS --> UI
