Nice! YoYoYou are You are building an embedded-friendly web application for a Raspberry Pi 4/5 ("Bridge Host") that coordinates multiple WTVB01-BT50 impact sensors and an AMG Labs Commander shot timer for a shooting match. The system must run **offline** (Pi as access point + captive portal) and **online** (Pi joins Wi-Fi). Optimize for reliability, low-latency telemetry, and simple ops in the field.

*Note: Current implementation uses WTVB01-BT50 sensors (WitMotion BLE accelerometers) and AMG Labs Commander timer. Future versions may support custom ESP32-based sensors and alternative timer vendors (SpecialPie, etc.).*uilding an embedded-friendly web application for a Raspberry Pi 4/5 ("Bridge Host") that coordinates multi## BLE & timing

* On session start, sensors and timer receive a time sync (document endpoint/characteristic); resync every N minutes or on drift>±20 ms.
* All events stored with monotonic time and UTC ISO8601.
* Include a "drift monitor" and expose drift in UI.
* **AMG Labs Commander**: Frame-based BLE protocol (UUID: 6e400003-b5a3-f393-e0a9-e50e24dcca9e), 14-byte frames with START(0x0105)/SHOT(0x0103)/STOP(0x0108) event types.
* **Alternative timers**: Pluggable driver architecture for SpecialPie and other vendor protocols, common event interface for START/SHOT/STOP events.
* **WTVB01-BT50 specifics**: WitMotion 5561 protocol, ~100Hz sampling, requires calibration for baseline establishment, 1mg scale factor for acceleration data.
* **Future ESP32 sensors**: Programmable sampling rates, configurable thresholds, enhanced battery reporting, custom BLE characteristics.TVB01-BT50 impact sensors and a shot timer for a shooting match. The system must run **offline** (Pi as access point + captive portal) and **online** (Pi joins Wi-Fi). Optimize for reliability, low-latency telemetry, and simple ops in the field.

*Note: Current implementation uses WTVB01-BT50 sensors (WitMotion BLE accelerometers). Future versions may migrate to custom ESP32-based sensors for enhanced capabilities.* are building an embedded-friendly web application for a Raspberry Pi 4/5 ("Bridge Host") that coordinates multiple WTVB01-BT50 impact sensors and a shot timer for a shooting match. The system must run **offline** (Pi as access point + captive portal) and **online** (Pi joins Wi-Fi). Optimize for reliability, low-latency telemetry, and simple ops in the field.

*Note: Current implementation uses WTVB01-BT50 sensors (WitMotion BLE accelerometers). Future versions may migrate to custom ESP32-based sensors for enhanced capabilities.*’ve got a solid nucleus: one sensor + one timer + a Pi “bridge.” Let’s turn that into a crisp prompt you can drop into an AI dev tool to generate a working Raspberry Pi app—plus a recommended stack and DB choice that fit your offline/online, AP-mode, and role-based UI needs.

# Copy-paste “build prompt”

Use this whole block as your prompt to an AI code generator. Swap any `{braced}` values you like.

---

You are building an embedded-friendly web application for a Raspberry Pi 4/5 (“Bridge Host”) that coordinates multiple ESP32-based impact sensors and a shot timer for a shooting match. The system must run **offline** (Pi as access point + captive portal) and **online** (Pi joins Wi-Fi). Optimize for reliability, low-latency telemetry, and simple ops in the field.

## System context

* **Hardware**

  * Raspberry Pi (Debian/Raspberry Pi OS), BLE + Wi-Fi.
  * **Impact Sensors**: WTVB01-BT50 (WitMotion BLE accelerometers, ~100Hz sampling, 1mg resolution).
  * **Shot Timer**: AMG Labs Commander (BLE, START/SHOT/STOP events, frame-based protocol).
  * HDMI-attached screen (optional) for on-device status.
  * *Future sensors*: Custom ESP32 modules with programmable thresholds and enhanced battery reporting.
  * *Future timers*: Support for SpecialPie timers and other vendor protocols via pluggable timer drivers.
* **Networking modes**

  1. **Online**: Pi joins venue Wi-Fi as client.
  2. **Offline**: Pi becomes AP (hostapd + dnsmasq), serves captive portal.
* **Time**

  * Pi is the time authority; sensors/timer sync to Pi on session start and periodically.
* **Logging**

  * Structured logs (NDJSON), journald, and app logs; tail visible in UI.

## Roles & screens

1. **Admin (on Pi or remote)**

   * Setup/update Bridge node name, firmware/app versions, timezone.
   * Network setup: choose Online vs Offline (create SSID/password), show IPs, interface status.
   * Sensor management: scan/paired devices, assign sensors to **Targets** (plates) within **Stages**; set sampling rate, thresholds, calibration, and health checks (battery/RSSI).
   * Timer management: pair AMG Labs Commander or SpecialPie timers, select protocol driver, verify clock sync, test event ingestion (START/SHOT/STOP frames).
   * Match metadata: match name, stages, squads, shooters, RO assignments.
   * System monitor: CPU/temp/disk, service health, BLE link quality.
   * **On-boot static info screen** (no login prompt): big-font panel showing Node Name, network mode, SSID/IP, service status, and a live console tail.

2. **RO (Range Officer) view**

   * Visual stage layout with plates; live statuses per sensor/bridge/timer (connected, last heartbeat, battery).
   * Live last-string summary (start time, impacts per target, order/timestamps, timer raw/parsed).
   * Quick review of prior strings in this stage; simple tag/flag for anomalies.
   * Future-ready controls (start/stop, mark reshoot, mark malfunction) but initial version may be read-only.

3. **Scorekeeper view**

   * Tabular runs with authoritative timestamps and mapping to timer events.
   * Per-target hits, misses, no-shoots (placeholder columns), penalties.
   * Controls to validate or correct timer alignment (bounded edits with audit trail).
   * Export selected runs to CSV and NDJSON that conform to a documented schema.

4. **Spectator/Parents/Competitors view**

   * Read-only dashboard of latest stage results and current run status.
   * Privacy toggle to anonymize shooter names.

5. **Coach view**

   * Notes per string; per-target annotations; bookmark moments; export notes.

## Non-functional requirements

* **Latency**: <150 ms end-to-end UI update for new impact events on LAN.
* **Resilience**: Works without internet; auto-restart (systemd); data persisted across power loss.
* **Security**: Role-based access; JWT sessions; default strong password; HTTPS in online mode; self-signed acceptable in offline mode.
* **Observability**: Structured logs, metrics endpoint, log tail in Admin screen.
* **Modularity**: Decouple BLE ingestion from web stack via message bus.

## Architecture (implement this)

* **Backend**: Python 3.11 + FastAPI.
* **Real-time**: WebSockets for live updates; optional MQTT (mosquitto) for internal pub/sub:

  * Topics: `bridge/status`, `sensor/{id}/telemetry`, `timer/events`, `run/{id}/events`.
* **Device IO services (separate processes)**:

  * `ble_ingestor`: Handles BLE for sensors and timer, emits events to MQTT and persists to DB.
  * `sync_service`: Periodic time sync to devices; health checks; retry/backoff.
* **DB**: SQLite (WAL) via SQLAlchemy + Alembic migrations. Use a `blob/` directory for raw NDJSON captures and optional Parquet exports.
* **Frontend**: React + Vite + TypeScript + Tailwind; responsive, kiosk-capable.
* **Pi services**: systemd units for backend, ingestor, mqtt; hostapd + dnsmasq for AP; nginx reverse proxy; autologin disabled; on-boot kiosk dashboard instead of login prompt.
* **AP mode**: captive portal that redirects to `http://bridge.local` home.

## Data model (minimum)

* `Node(id, name, mode, ssid, ip_addr, versions, created_at)`
* `Sensor(id, hw_addr, label, target_id, calib, last_seen, battery, rssi)`
* `Target(id, stage_id, name, geometry, notes)`
* `Stage(id, match_id, name, number, layout_json)`
* `Match(id, name, date, location, metadata_json)`
* `TimerEvent(id, ts_utc, type, raw, run_id)`
* `SensorEvent(id, ts_utc, sensor_id, magnitude, features_json, run_id)`
* `Run(id, match_id, stage_id, shooter_id, started_ts, ended_ts, status, annotations_json, audit_json)`
* `Shooter(id, name, squad, metadata_json)`
* `Note(id, run_id, author_role, content, ts_utc)`

## APIs (representative)

* `/api/admin/node` GET/PUT
* `/api/admin/network` GET/POST (switch mode, show IPs/SSID)
* `/api/admin/devices` GET/POST (scan/pair/unpair)
* `/api/admin/assign` POST (sensor→target)
* `/api/stages` CRUD; `/api/targets` CRUD; `/api/matches` CRUD
* `/api/runs` GET/POST; `/api/runs/{id}` GET/PATCH
* `/api/events/sensor` POST (ingestor writes); `/api/events/timer` POST
* `/api/export/runs.csv` and `.ndjson`
* `/ws/live` WebSocket: push `status`, `sensor_event`, `timer_event`, `run_update`

## UI requirements

* **Admin dashboard**: cards for Node/Network/Services; “Tail logs” pane (last 200 lines; autoscroll).
* **Boot status screen** (fullscreen): Node name, network mode, SSID, IPs (v4/v6), service LEDs, last 20 log lines; refreshes every 2s.
* **RO view**: canvas/SVG stage map; per-target badges (OK/Degraded/Offline); live hit markers; last string summary panel; history sidebar.
* **Scorekeeper**: grid with runs; filters by stage/squad; inline validation; export buttons.
* **Spectator**: simple, high-contrast live ticker.
* **Coach**: notes panel tied to run; export notes.

## BLE & timing

* On session start, sensors and timer receive a time sync (document endpoint/characteristic); resync every N minutes or on drift>±20 ms.
* All events stored with monotonic time and UTC ISO8601.
* Include a “drift monitor” and expose drift in UI.

## Exports

* CSV (one row per run with aggregates).
* NDJSON (one event per line) for raw analysis; include schema version.
* Optional Parquet batch for offline analytics.

## Security & roles

* Roles: `admin`, `ro`, `scorekeeper`, `viewer`, `coach`.
* JWT w/ refresh; role claims; CSRF for unsafe methods; default creds rotated on first boot.

## Testing & ops

* Seed script creates a demo match with fake WTVB01-BT50 sensors and AMG Commander timer; simulation mode generates realistic impact patterns and timer event sequences.
* Headless e2e tests (Playwright) and unit tests (pytest).
* systemd unit files + install script: `install_pi.sh` provisions packages, enables services, configures AP.

## Deliverables

* Repo with frontend, backend, services, systemd units, install script, docs.
* README with setup for **Online** and **Offline/AP** paths.
* Data schema doc + API OpenAPI spec.
* One-click build: `./install_pi.sh` on fresh Raspberry Pi OS.

Acceptance criteria: app boots to status screen; can switch online/offline; can pair fake WTVB01-BT50 sensors and AMG Commander timer in sim mode; live RO dashboard shows timer events and sensor impacts; Scorekeeper exports CSV; logs tail works; role-based login enforced.

---

# Recommended stack (why these choices)

* **Backend: FastAPI (Python)** — excellent on a Pi, typed, async, easy to package; rich OpenAPI for your tools.
* **Real-time: WebSockets** — lighter than polling; pairs well with FastAPI. Internal **MQTT** (mosquitto) gives you elastic fan-out between BLE ingest and the web app, and lets you simulate devices easily.
* **Database: SQLite (WAL)** — zero-ops, robust on SD cards, perfect for edge nodes. Use SQLAlchemy + Alembic for migrations. Store bulky raw event captures as NDJSON files and optionally Parquet for analytics. If you later need time-series acceleration, you can add DuckDB for ad-hoc queries against Parquet without changing the operational DB.
* **Frontend: React + Vite + Tailwind** — fast dev loop, kiosk-friendly, good component ecosystem. You could also do SvelteKit; React has broader examples for WebSocket dashboards.
* **Reverse proxy: nginx** — TLS termination, gzip, caches static assets; simple systemd integration.
* **AP mode: hostapd + dnsmasq** — battle-tested; captive portal via simple DNS hijack to `bridge.local`.
* **Services: systemd** — restarts on failure, logs to journald; you can tail from the Admin UI.

# Database options, briefly

* **SQLite (WAL)** → ✅ Recommended. Single-node edge, minimal maintenance, safe under power loss, fine for tens of GB. Add FTS5 for fast text search in notes/logs.
* **PostgreSQL** → Overkill for a field Pi; adds babysitting. Only consider if you must host many concurrent writers or plan multi-bridge federation.
* **Influx/Time-series DBs** → Nice graphs, but extra moving parts and storage. Your event volume and offline constraint favor keeping it simple.

# Small extras that will save you headaches

* Use a **unified event schema** (versioned) for sensor and timer events; include monotonic and wall-clock timestamps plus a `source` field.
* Put **health LEDs** in the UI: BLE link, MQTT broker, DB, disk space, NTP drift.
* Bundle a **simulation mode** so you can demo without live fire.
* Add a **“data offload”** button that zips a match archive (DB + NDJSON + exports) for upload.

If you want, I can turn this into a starter repo layout with systemd unit files and the install script so you can flash a card and see that boot screen talk to you.
