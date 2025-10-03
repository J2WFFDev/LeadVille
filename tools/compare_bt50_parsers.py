#!/usr/bin/env python3
"""Export recent BT50 parser outputs to CSV.

The legacy `parse_5561` data is no longer produced; compatibility columns are
retained but populated with null values so downstream tooling can transition
gradually.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from impact_bridge.ble.parsers import parse_bt50_frame  # type: ignore  # noqa: E402

DEFAULT_DB = REPO_ROOT / "db" / "bt50_samples.db"
DEFAULT_OUTPUT = REPO_ROOT / "analysis" / "parser_comparison.csv"
MAX_SIMPLE_SAMPLES = 4


def fetch_frames(db_path: Path, limit: int) -> Iterable[Dict[str, str]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ts_ns, frame_hex FROM bt50_samples ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        for row in cur.fetchall():
            yield dict(row)
    finally:
        conn.close()


def parse_frame(frame_hex: str) -> Dict[str, Optional[object]]:
    frame_bytes = bytes.fromhex(frame_hex)
    record: Dict[str, Optional[object]] = {}

    bt50 = parse_bt50_frame(frame_bytes, write_db=False)
    if bt50:
        record.update(
            {
                "bt50_vx": bt50.get("vx"),
                "bt50_vy": bt50.get("vy"),
                "bt50_vz": bt50.get("vz"),
                "bt50_temp_raw": bt50.get("temp_raw"),
                "bt50_temperature_c": bt50.get("temperature_c"),
                "bt50_disp_x": bt50.get("disp_x"),
                "bt50_disp_y": bt50.get("disp_y"),
                "bt50_disp_z": bt50.get("disp_z"),
                "bt50_freq_x": bt50.get("freq_x"),
                "bt50_freq_y": bt50.get("freq_y"),
                "bt50_freq_z": bt50.get("freq_z"),
            }
        )
    else:
        record.update(
            {
                "bt50_vx": None,
                "bt50_vy": None,
                "bt50_vz": None,
                "bt50_temp_raw": None,
                "bt50_temperature_c": None,
                "bt50_disp_x": None,
                "bt50_disp_y": None,
                "bt50_disp_z": None,
                "bt50_freq_x": None,
                "bt50_freq_y": None,
                "bt50_freq_z": None,
            }
        )

    # Legacy parser retired: populate compatibility columns with null data
    record["simple_sample_count"] = 0
    for idx in range(MAX_SIMPLE_SAMPLES):
        record[f"simple_s{idx}_vx"] = None
        record[f"simple_s{idx}_vy"] = None
        record[f"simple_s{idx}_vz"] = None

    return record


def write_csv(rows: Iterable[Dict[str, Optional[object]]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_list = list(rows)
    if not rows_list:
        raise RuntimeError("No rows to write; check source data")

    fieldnames = ["frame_id", "frame_ts_ns", "bt50_vx", "bt50_vy", "bt50_vz",
                  "bt50_temp_raw", "bt50_temperature_c", "bt50_disp_x", "bt50_disp_y",
                  "bt50_disp_z", "bt50_freq_x", "bt50_freq_y", "bt50_freq_z",
                  "simple_sample_count"]
    for idx in range(MAX_SIMPLE_SAMPLES):
        fieldnames.extend(
            [f"simple_s{idx}_vx", f"simple_s{idx}_vy", f"simple_s{idx}_vz"]
        )

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_list:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare BT50 parser outputs")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to bt50_samples.db")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="CSV output path")
    parser.add_argument("--limit", type=int, default=50, help="Number of frames to export")
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"Database not found: {args.db}")

    rows: List[Dict[str, Optional[object]]] = []
    for frame in fetch_frames(args.db, args.limit):
        parsed = parse_frame(frame["frame_hex"])
        parsed.update(
            {
                "frame_id": frame.get("id"),
                "frame_ts_ns": frame.get("ts_ns"),
            }
        )
        rows.append(parsed)

    if not rows:
        raise SystemExit("No frames parsed; check database content")

    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
