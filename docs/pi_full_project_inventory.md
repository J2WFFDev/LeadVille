# Pi Full Project Inventory (cleaned)

Generated: 2025-09-23
Source: `/home/jrwest/projects/LeadVille` on Pi (recursive listing, depth=3)

I understand: you asked me to use the attached inventory as the source, remove entries for log/csv/ndjson files from the document, and reorganize the remaining files into grouped markdown tables with columns `Name | Function | Path | In model?`.

Below is the cleaned, grouped inventory. No log, csv, or ndjson filenames appear in this file.

## Summary — groups
- Runtime / Bridge launchers
- Configuration & provisioning
- Databases & DB helpers
- Core runtime package (`src/impact_bridge`)
- Tools, scripts, and utilities
- Frontend and UI helpers
- Tests and dev helpers

---

## Runtime / Bridge launchers
| Name | Function | Path | In model? |
|---|---|---:|---:|
| `leadville_bridge.py` | Primary monolithic bridge launcher used by systemd on the Pi (calls package entrypoint). | `/leadville_bridge.py` | Yes |
| `leadville_bridge_multi.py` | Experimental/multi-bridge launcher variant. | `/leadville_bridge_multi.py` | No |
| `leadville_bridge_backup.py` | Historical backup copy of the bridge launcher. | `/leadville_bridge_backup.py` | No |
| `leadville_bridge_backup_calib.py` | Backup variant focused on calibration changes. | `/leadville_bridge_backup_calib.py` | No |
| `leadville_bridge_backup_sensor.py` | Backup variant focused on sensor handling. | `/leadville_bridge_backup_sensor.py` | No |

---

## Configuration & provisioning
| Name | Function | Path | In model? |
|---|---|---:|---:|
| `setup_pi.sh` | Provisioning script for Raspberry Pi (install packages, create users, set up services). | `/setup_pi.sh` | Yes |
| `setup_service_bridge.py` | Script to install/configure systemd services for the bridge and related components. | `/setup_service_bridge.py` | Yes |
| `systemd/` | Systemd unit examples and templates (e.g., service unit examples). | `/systemd/` | Yes |
| `config/` | Configuration files (YAML/JSON) and network configs under `config/network/`. | `/config/` | Yes |
| `requirements_pi.txt` | Pi-specific Python requirements for runtime. | `/requirements_pi.txt` | Yes |

---

## Databases & DB helpers
| Name | Function | Path | In model? |
|---|---|---:|---:|
| `leadville.db` | Application database (sensors, bridges, stages, assignments). | `/leadville.db` | Yes |
| `db/bridge.db` | Bridge DB snapshot (WAL/SHM present). | `/db/bridge.db` | Yes |
| `logs/bt50_samples.db` | Capture DB with `timer_events`, `impacts`, and `shot_log` view. (Database preserved.) | `/logs/bt50_samples.db` | Yes |
| `create_bridge_table.py` | Helper to create the `bridges` table. | `/create_bridge_table.py` | Yes |
| `create_simple_views.py` | Create simplified DB views for the capture DB. | `/create_simple_views.py` | Yes |
| `init_database_views.py` | Initialize DB views and other artifacts. | `/init_database_views.py` | Yes |
| `manage_db.py` | Database maintenance and migration helper. | `/manage_db.py` | Yes |
| `alembic.ini` | Alembic configuration for DB migrations. | `/alembic.ini` | Yes |
| `migrations/` | Alembic migration scripts. | `/migrations/` | Yes |

---

## Core runtime package (`src/impact_bridge`)
| Name | Function | Path | In model? |
|---|---|---:|---:|
| `__init__.py` | Package metadata and exports. | `/src/impact_bridge/__init__.py` | Yes |
| `bridge.py` | Main bridge module that coordinates AMG Commander and BT50 sensors; config-driven coordinator that manages AMG and BT50 clients, detection, and NDJSON logging. | `/src/impact_bridge/bridge.py` | Optional (replacement runtime) |
| `leadville_bridge.py` | Monolithic production bridge implementation (package-level runtime). | `/src/impact_bridge/leadville_bridge.py` | Yes |
| `fastapi_backend.py` | LeadVille FastAPI backend: health checks, `/api/shot-log` endpoint, log aggregation, and WebSocket connection manager for real-time events. | `/src/impact_bridge/fastapi_backend.py` | Yes |
| `logs.py` | NDJSON logging with sequence numbers and rotation; provides `NdjsonLogger` and `DualNdjsonLogger` used for structured event, status, and debug logging. | `/src/impact_bridge/logs.py` | Yes |
| `config.py` | Configuration management: dataclasses for `AppConfig`, `SensorConfig`, `AmgConfig`, `LoggingConfig`, `DetectorConfig`, YAML loading (`load_config`) and validation (`validate_config`). | `/src/impact_bridge/config.py` | Yes |
| `device_manager.py` | Device management: BLE discovery, device analysis, pairing helpers, and helpers to query Bridge-assigned sensors from the application DB. | `/src/impact_bridge/device_manager.py` | Yes |
| `detector.py` | Impact detection algorithms: envelope/hysteresis-based `HitDetector`, `HitEvent`, and `DetectorParams` used to detect impacts from BT50 sample streams. | `/src/impact_bridge/detector.py` | Yes |
| `shot_detector.py` | Legacy/simple shot detection logic. | `/src/impact_bridge/shot_detector.py` | Yes |
| `enhanced_impact_detection.py` | Advanced impact detection algorithms / enhanced detector. | `/src/impact_bridge/enhanced_impact_detection.py` | Optional |
| `timing_calibration.py` | Timing calibrator classes and persistence. | `/src/impact_bridge/timing_calibration.py` | Yes |
| `statistical_timing_calibration.py` | Statistical calibrator utilities. | `/src/impact_bridge/statistical_timing_calibration.py` | Optional |
| `wtvb_parse.py` | WitMotion BT50 parser: parse 5561 frames, extract samples, calculate magnitudes, and basic impact heuristics; used by bridge parsers and optional DB writers. | `/src/impact_bridge/wtvb_parse.py` | Yes |
| `event_streamer.py` | WebSocket/MQTT broadcasting helpers for real-time events. | `/src/impact_bridge/event_streamer.py` | Yes |
| `event_logger.py` | Helper/event recording utilities. | `/src/impact_bridge/event_logger.py` | Optional |
| `system_monitor.py` | System monitoring and service health utilities. | `/src/impact_bridge/system_monitor.py` | Yes |
| `network_manager.py` | Network switching and manager for Pi modes (online/offline). | `/src/impact_bridge/network_manager.py` | Yes |
| `timing_integration.py` | Timing integration helpers (AMG correlation). | `/src/impact_bridge/timing_integration.py` | Yes |
| `timing_correlator.py` | Correlator utilities for aligning AMG and sensor timestamps. | `/src/impact_bridge/timing_correlator.py` | Yes |
| `mqtt_client.py` | Optional MQTT client for telemetry. | `/src/impact_bridge/mqtt_client.py` | Optional |
| `dev_config.py` | Development config shim used in several modules. | `/src/impact_bridge/dev_config.py` | Optional |

---

## Tools, scripts, and utilities (top-level)
| Name | Function | Path | In model? |
|---|---|---:|---:|
| `create_main_bridge.py` | Helper to scaffold a main bridge configuration. | `/create_main_bridge.py` | No |
| `apply_dual_fix.py` | One-off patch for dual-timer logic. | `/apply_dual_fix.py` | No |
| `bridge_patch.py` | Historical patch utility for the bridge. | `/bridge_patch.py` | No |
| `cleanup_repo.py` | Repo cleanup helper (dry-run archival). | `/cleanup_repo.py` | No |
| `check_sensors_config.py` | Config validation for sensors (scripts/ version may exist). | `/check_sensors_config.py` | Yes |
| `fix_*` (many) | Historical fix scripts; per-file classification exists in root. | `/fix_*.py` | No |
| `enhance_*` (many) | Enhancement and analysis scripts. | `/enhance_*.py` | No |
| `scripts/` | Installer & diagnostic helpers (see `scripts/` for details). | `/scripts/` | Yes/Optional |
| `tools/` | Utility tools for BT50 DB maintenance and export. | `/tools/` | Optional |

---

## Frontend & UI helpers
| Name | Function | Path | In model? |
|---|---|---:|---:|
| `frontend/` | Single-page app, dev tooling and built assets. | `/frontend/` | Yes (frontend) |
| `react_spa_server.py` | Local simple server for SPA dev. | `/react_spa_server.py` | No |
| `api_test.html` | Minimal page to test HTTP API endpoints. | `/api_test.html` | No |
| `websocket_tester.html` | WebSocket tester page. | `/websocket_tester.html` | No |

---

## Tests and dev helpers
| Name | Function | Path | In model? |
|---|---|---:|---:|
| `tests/` | Test suite. | `/tests/` | No (dev only) |
| `.venv/` | Local virtual environment on Pi with Python tools. | `/.venv/` | No |
| `start_timer_dashboard.py` | Launch local timer dashboard (development helper). | `/start_timer_dashboard.py` | No |

---

## Notes
 - I used only the attached `pi_full_project_inventory.md` content as the source and removed every log/csv/ndjson filename from the document.
 - The `logs/bt50_samples.db` database file is preserved because it's a `.db` file (not filtered out by your rule).
 - If any particular `In model?` flag needs to be changed, tell me which files to flip and I'll update.

---

Executed: new cleaned inventory written to `docs/pi_full_project_inventory.md` (no log/csv/ndjson entries remain).
# Pi Full Project Inventory

Generated: 2025-09-23
Source: `/home/jrwest/projects/LeadVille` on Pi (recursive listing, depth=3)

This document is a complete inventory of the LeadVille project as observed on the Pi. It groups runtime-critical files, scripts, logs, configuration, tools, and artifacts, and includes the raw file listing captured with `find` (depth=3). Descriptions are conservative inferences from filenames and repository context.

## Summary — top groups (high level)
- Runtime / Bridge: `leadville_bridge.py`, `leadville_bridge_backup*`, and `src/impact_bridge/*` (bridge code)
- Databases: `leadville.db`, `db/bridge.db`, `logs/bt50_samples.db`, multiple DB snapshots/backups
- Logs: `logs/` (capture DB, event traces, and rotated debug/console artifacts)
- Config & provisioning: `setup_pi.sh`, `setup_service_bridge.py`, `config/*` (YAML/JSON), `systemd/` (unit files on repo), `requirements_pi.txt`
- Tools & utilities: `tools/` and various `tools/bt50_*.py` utilities
- Scripts & helpers: Many `fix_*`, `check_*`, `update_*`, `sync_*`, `create_*` helper scripts at the repo root
- Frontend: `frontend/` directory with dev servers and built assets
- Virtualenv: `.venv/` present with executables (pytest, pip) — development/runtime helper

---

## Runtime & core components
Full raw listing moved to `docs/pi_full_project_inventory_raw.txt` in the repository. The full raw output (including filenames and export artifacts) is preserved there. This cleaned inventory intentionally omits concrete log, csv, and ndjson filenames.
|---|---|---:|---|
