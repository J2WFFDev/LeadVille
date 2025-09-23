# Pi Project Folder Inventory

This inventory lists the top-level project files and groups them by function. For each item it gives: name, short function, repository path, and whether it is part of the comprehensive architecture model described in `docs/architecture_model.md`.

Legend: "In model?" = Yes means the file is referenced in the architecture model (critical runtime or component). "No" means it is likely auxiliary, archival, or helper scripts.

## Runtime & core components
| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `leadville_bridge.py` | Runtime launcher used by systemd to start the monolithic bridge runtime (calls package entrypoint). | `/leadville_bridge.py` | Yes |
| `src/impact_bridge/leadville_bridge.py` | Monolithic bridge: BLE connections, detection, debug logging, and best-effort DB writes. Running on Pi under systemd in current deployment. | `/src/impact_bridge/leadville_bridge.py` | Yes |
| `src/impact_bridge/bridge.py` | Modular Bridge class (config-driven). Intended replacement for monolithic bridge. | `/src/impact_bridge/bridge.py` | Yes |
| `src/impact_bridge/ble/witmotion_bt50.py` | BT50 BLE client & parser (parses 0x55/0x61 frames). | `/src/impact_bridge/ble/witmotion_bt50.py` | Yes |
| `src/impact_bridge/ble/wtvb_parse.py` | Verbose BT50 parser used in some bridge modes. | `/src/impact_bridge/ble/wtvb_parse.py` | Yes |
| `src/impact_bridge/logs.py` | `NdjsonLogger` / `DualNdjsonLogger` used by Bridge and ingestion pipeline. | `/src/impact_bridge/logs.py` | Yes |
| `src/impact_bridge/event_streamer.py` | WebSocket/MQTT event broadcaster used by backend to send realtime events. | `/src/impact_bridge/event_streamer.py` | Yes |
| `src/impact_bridge/fastapi_backend.py` | FastAPI server exposing `/api/shot-log` and admin endpoints. | `/src/impact_bridge/fastapi_backend.py` | Yes |
| `logs/bt50_samples.db` | Capture DB used by backend; contains `timer_events`, `impacts`, `shot_log` view. (Often on the Pi.) | `/logs/bt50_samples.db` | Yes |
| `leadville.db` | Application DB (sensors, bridges, stages, assignments). | `/leadville.db` | Yes |

## Configuration & deployment
| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `config.example.yaml` | Sample config for Bridge. | `/config.example.yaml` | Yes |
| `pyproject.toml` | Python project configuration. | `/pyproject.toml` | Yes |
| `requirements_pi.txt` | Pi-specific Python dependencies / install list. | `/requirements_pi.txt` | Yes |
| `setup_pi.sh` | Pi setup script for provisioning the runtime environment. | `/setup_pi.sh` | Yes |
| `systemd/` | Directory with sample systemd unit files for running the bridge and services. | `/systemd/*` | Yes |

## Backend & DB helpers
| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `create_simple_views.py` | Helper to create `shot_log` and related views in the capture DB. | `/create_simple_views.py` | Yes |
| `init_database_views.py` | Another helper to initialize views and related DB constructs. | `/init_database_views.py` | Yes |
| `manage_db.py` | DB utility for migrations or maintenance. | `/manage_db.py` | Yes |
| `alembic.ini` | Alembic configuration for DB migrations. | `/alembic.ini` | Yes |

## Frontend
| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `frontend/` | React/Next frontend application (UI consuming API + WebSocket). | `/frontend/*` | Yes |

## Tools, scripts, and helpers (archive candidates)
These files are helper scripts, one-off fixes, experimental patches, or archived tools. Many are useful for debugging but are not part of the hot-path runtime.

| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `scripts/check_sensors_config.py` | Validate YAML config using the same loader as the bridge. Useful for diagnosing selection issues. | `/scripts/check_sensors_config.py` | Yes (diagnostic) |
| `scripts/cleanup_repo.py` | Dry-run archiver for noisy scripts (moves to `/archive`). | `/scripts/cleanup_repo.py` | No (helper) |
| `archive/` | Location for archived files moved out of main tree. | `/archive/*` | No (archive) |
| `bridge_patch.py`, `clean_bridge_patch.py` | Patching utilities historically used to alter the bridge behavior. | `/bridge_patch.py` | No (archive/legacy) |
| `apply_dual_fix.py`, `finalize_multi_sensor.py`, `implement_per_sensor_calibration.py`, `implement_complete_per_sensor_calibration.py` | Calibration and sensor utility scripts. | `/*` | No (helper)
| `fix_*` files (many) | One-off fixes addressing specific bugs in sensors, DB, logging, etc. | `/*fix_*.py` | No (archive/patch)
| `sync_bridge_data.py` / `sync_bridge_data_fixed.py` | Data sync helpers for bridge/sensor mapping. | `/sync_bridge_data.py` | No (helper)
| `tools/` | Historical tools and helpers. Inspect before archiving. | `/tools/*` | Mostly No (see items) |

## Diagnostic logs and sample captures
| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `capture_120.log` / `capture_120_latest.log` | Raw capture logs / sample recordings (historical). | `/capture_*.log` | No (artifacts)
| `capture_short.log` | Short capture log. | `/capture_short.log` | No (artifact)
| `bt50_samples.db` (repo copy) | Sample capture DB present in repo root — verify that this is a snapshot. | `/bt50_samples.db` | Yes (but confirm whether it's a snapshot or live) |
| `logs/` | On-Pi logs directory (NDJSON, debug logs). On dev machine the logs directory may be present for testing. | `/logs/*` | Yes (runtime)

## Documentation, handoff, and notes
| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `docs/architecture.md` | Human-readable architecture overview. | `/docs/architecture.md` | Yes |
| `docs/architecture_model.md` | Detailed architecture model (this file references it). | `/docs/architecture_model.md` | Yes |
| `HANDOFF_*.md` | Handoff notes and operational history. | `/HANDOFF_*.md` | No (ancillary but useful)
| `PI_DEPLOYMENT.md`, `PI_AMG_TEST_COMMANDS.md` | Pi deployment instructions and AMG test helpers. | `/PI_DEPLOYMENT.md` | Yes (deployment)

## Tests
| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `tests/` | Unit and integration tests for code under `src/` (if present). | `/tests/*` | Yes (CI / dev)

## Small systemd / scheduled helpers
| Name | Function | Path | In model? |
|---|---|---:|:---:|
| `tmp_bt50-prune.service`, `tmp_bt50-prune.timer` | Example systemd service/timer pair used to prune old BT50 files — likely a local helper. | `/tmp_bt50-prune.*` | No (helper)

---

Notes & recommendations
- Many files with `fix_`, `patch`, `backup`, `old`, `*_backup` in the name are good candidates to move into `archive/` after review. I intentionally did not move files. Use `scripts/cleanup_repo.py` to preview moves before applying.
- Confirm whether `bt50_samples.db` at repo root is a snapshot copy — the authoritative capture DB is on the Pi at `/home/jrwest/projects/LeadVille/logs/bt50_samples.db`.
- If you want, I can produce a CSV or machine-readable inventory (JSON) for automated tooling or to populate a change-management ticket.

---

Next steps I can take on this task:
- Generate a CSV/JSON export of the inventory.
- Recursively enumerate `src/`, `scripts/`, and `tools/` to produce a more granular table including function-level summaries (per-file docstrings where available).
- Begin an archival pass using `scripts/cleanup_repo.py --apply` (dry-run before apply is recommended).