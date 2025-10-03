#!/usr/bin/env python3
"""Split combined parser CSV into individual datasets.

Legacy `simple_*` columns may be empty because the multi-sample parser has been
retired; the splitter still emits the file so downstream consumers can migrate
at their own pace.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List


def split_csv(source: Path, bt50_dest: Path, simple_dest: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source CSV not found: {source}")

    with source.open(newline="") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)

    if not rows:
        raise ValueError("No rows found in source CSV")

    all_fields: List[str] = list(rows[0].keys())

    frame_columns = [col for col in ("frame_id", "frame_ts_ns") if col in all_fields]
    bt50_columns = frame_columns + [col for col in all_fields if col.startswith("bt50_")]
    simple_columns = frame_columns + [col for col in all_fields if col.startswith("simple_")]

    bt50_dest.parent.mkdir(parents=True, exist_ok=True)
    with bt50_dest.open("w", newline="") as bt50_file:
        writer = csv.DictWriter(bt50_file, fieldnames=bt50_columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col) for col in bt50_columns})

    simple_dest.parent.mkdir(parents=True, exist_ok=True)
    with simple_dest.open("w", newline="") as simple_file:
        writer = csv.DictWriter(simple_file, fieldnames=simple_columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col) for col in simple_columns})


def main() -> None:
    parser = argparse.ArgumentParser(description="Split parser comparison CSV")
    parser.add_argument("source", type=Path, help="Combined CSV with both parser outputs")
    parser.add_argument("bt50_output", type=Path, help="Output CSV for BT50 parser data")
    parser.add_argument("simple_output", type=Path, help="Output CSV for simple parser data")
    args = parser.parse_args()

    split_csv(args.source, args.bt50_output, args.simple_output)


if __name__ == "__main__":
    main()
