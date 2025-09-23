Scripts README

This folder is intended to contain small, reusable scripts that are part of normal development and operations (e.g., `setup_service_bridge.py`, `create_bridge_table.py`).

Guidelines:
- Keep scripts small and idempotent.
- Provide a short usage snippet at the top of each script.
- Scripts that are one-off or experimental belong in `archive/` with an entry in `archive/ARCHIVE_LIST.md`.

Files to consider moving into `scripts/` (or updating at their current location):
- `create_bridge_table.py`
- `init_database_views.py`
- `manage_db.py`
- `setup_service_bridge.py`

If you want, I can move these into `scripts/` and create small wrapper README snippets for each.