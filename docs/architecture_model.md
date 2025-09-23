# LeadVille — Comprehensive Architecture Model

This document expands `docs/architecture.md` into a structured, actionable architecture model: what runs where, component responsibilities, data flows, key contracts, runtime invariants, and where to look when troubleshooting.

## Purpose
Provide a clear, auditable model of the LeadVille system so operators and developers can reason about:
- Where code executes (Pi vs backend vs frontend vs dev workstation)
- The authoritative data stores and their responsibilities
- Component boundaries and message contracts (NDJSON, shot_log view)
- Operational runbook items required to change runtime behavior safely

## High-level components (brief)
- Bridge (monolithic): `leadville_bridge.py` — authoritative, systemd-run process on the Pi that manages BLE connections, AMG timer parsing, BT50 parsing, detection, debug logging, and best-effort DB writes.
- Bridge (modular): `src/impact_bridge/bridge.py` — configuration-driven implementation intended as a safer, modular replacement that writes canonical NDJSON logs and integrates with `EventStreamer`.
- BLE Clients / Parsers: `src/impact_bridge/ble/*` — BT50, AMG parsers; produce `Bt50Sample` and `timer_event` objects.
- Detector: `src/impact_bridge/detector.py` — signal processing & peak detection turning sampled frames into `HIT` events.
- Ndjson Logger: `src/impact_bridge/logs.py` — primary event emitter used by the modular Bridge; writes NDJSON into `logs/` and `logs/debug/`.
- Ingest / Capture pipeline: Ingest process watches NDJSON or receives events and writes canonical rows into `logs/bt50_samples.db` (creates `shot_log` view). This service may be external to this repository on the Pi.
- FastAPI backend: `src/impact_bridge/fastapi_backend.py` — reads `leadville.db` and `bt50_samples.db` and exposes `/api/shot-log` and admin endpoints.
- Frontend: `frontend/` — React/Next app consuming REST + WebSocket endpoints.

## Data stores and contracts
- `logs/` (NDJSON + debug): primary stream of events from the Bridge implementation. Format: NDJSON records with `type` (`event` / `status`), `msg`, `data` and timestamps. This is the canonical streaming input for capture/ingest.
- `logs/bt50_samples.db` (capture DB): canonical persisted rows including `bt50_samples`, `impacts`, `timer_events`, plus helpful views `shot_log`, `shot_log_simple`, `string_summary`. The API reads `shot_log` to render the Console and Live logs.
- `leadville.db` (app DB): sensors, bridges, stages, runs, targets, configuration, and assignment metadata used by the backend and admin UI.

## Runtime mapping & invariants
- Pi: responsible for BLE connectivity to sensors/timers and producing events. The Pi is the authoritative runtime: systemd runs `leadville_bridge.py`. Ingest/capture also typically runs on the Pi (writes `bt50_samples.db`).
- Backend: stateless application reads DBs and serves UI and WebSocket clients. Backend expects `bt50_samples.db` to exist on the Pi and be readable by the backend (or the backend to query it via an agreed path). Ensure file permissions allow access.
- Frontend: consumers of REST and WebSocket, not authoritative for event storage.

Invariants:
- NDJSON events must be append-only and time-ordered per file to allow deterministic ingest.
- The `shot_log` view merges timer events and impact events by timestamp and must be re-created if the capture DB schema changes.
- Bridge assignments (sensors -> bridge_id, sensors -> target_config_id) live in `leadville.db`; if sensors appear in captures but are not correlated in UI, check assignment records.

## Component responsibilities (detailed)
- leadville_bridge.py (monolithic)
  - BLE scanning, connection management, notification handlers for both AMG and BT50.
  - Parsing with verbose parsers used historically; may perform direct writes into `logs/bt50_samples.db` for timer events via `_persist_timer_event()`.
  - Writes debug/ndjson logs under `logs/debug/` and `logs/` (depending on config).

- src/impact_bridge/bridge.py (modular)
  - Reads YAML config via `src/impact_bridge/config.py`.
  - Instantiates sensor clients and `Detector` objects, uses `NdjsonLogger.event()` and `status()`.
  - Designed for clear separation of detection and IO; NDJSON + EventStreamer for broadcast.

- Parsers under `src/impact_bridge/ble/`
  - `witmotion_bt50.py`: lightweight frame parser (`0x55,0x61`) producing `Bt50Sample` objects (vx/vy/vz, amplitude).
  - `wtvb_parse.py` / `wtvb_parse_simple.py`: verbose & compact parser variants for different runtime needs.

- Detector
  - `detector.py` processes sample streams per sensor, implements dead-time, pre/post windows, peak detection, and produces `hit_event` dictionaries consumed by logger/streamer.

- Ndjson Logger
  - Standardized NDJSON format used for ingestion; `status` records are used to capture startup configuration such as "Configured BT50 sensors".

- Capture/Ingest
  - Responsible for consolidating NDJSON and direct writes into the capture DB. Produces canonical tables and helpful SQL views. Usually runs as a separate process/service (check systemd units on the Pi).

- FastAPI backend
  - Serves REST endpoints for logs and admin control; admin endpoints may call `systemctl` on the Pi to restart the bridge service.

## Operational runbook (change & troubleshooting)
1. Confirm runtime: `sudo systemctl status leadville-bridge` on Pi. The ExecStart indicates which bridge implementation is active.
2. If switching to modular `Bridge`: test locally with dev config, then change systemd ExecStart to `python -m impact_bridge.leadville_bridge` or a wrapper that runs the modular entrypoint; use `systemctl daemon-reload` and restart.
3. If events appear in NDJSON but not in `bt50_samples.db`: check ingest/capture service logs and permissions; the capture process may have crashed or lost write privileges.
4. Confirm selection of sensors: search NDJSON logs for `Configured BT50 sensors` status messages to verify bridge loaded configuration as expected.

## Sequence (high-level)
1. BLE notification (BT50) -> parser -> `Bt50Sample` object
2. Bridge buffers sample -> Detector processes sample -> if HIT generated, publish via `NdjsonLogger.event()` and `EventStreamer`
3. Capture/ingest consumes NDJSON -> writes `impacts` / `bt50_samples` -> updates `shot_log` view
4. FastAPI reads `shot_log` -> returns to frontend via `/api/shot-log` or WebSocket

## Extensions & migration notes
- When migrating from monolithic to modular Bridge, ensure:
  - NDJSON format is identical (or ingestion adapted)
  - Sensor assignment semantics stay the same (fields used to join sensor MAC to sensors table)
  - The modular Bridge's `NdjsonLogger` creates the exact set of fields expected by the ingest process (or update ingest accordingly)

## Where files live (quick map)
- Repo root: `leadville_bridge.py` (launcher), `logs/` (on Pi), `logs/bt50_samples.db` (capture DB on Pi), `leadville.db` (app DB)
- Source: `src/impact_bridge/*` — main code for modular implementation, parsers, backend
- Frontend: `frontend/` — React/Next app
- Systemd unit: `systemd/` (provides sample unit files)

---

This model is intended to be used with the `docs/pi_project_inventory.md` inventory I generated alongside this document; the inventory maps file names to the model membership flag ("part of model? yes/no") and provides a path + short function description to help triage and archive decisions.

If you want, I can also produce a machine-readable JSON representation of this model (components, ports, contracts, data stores) for automated tooling or diagram generation.