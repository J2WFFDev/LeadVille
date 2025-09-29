from __future__ import annotations
import os
from pathlib import Path

# Project root = .../LeadVille
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Allow deployment overrides
DB_DIR = Path(os.getenv("LEADVILLE_DB_DIR", PROJECT_ROOT / "db"))
LOG_DIR = Path(os.getenv("LEADVILLE_LOG_DIR", PROJECT_ROOT / "logs"))

CONFIG_DB  = DB_DIR / "leadville.db"          # read-only for bridge assignments
RUNTIME_DB = DB_DIR / "leadville_runtime.db"  # runtime writes (timer + impacts)
SAMPLES_DB = DB_DIR / "bt50_samples.db"       # optional verbose sample logger

DB_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)