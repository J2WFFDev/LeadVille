#!/usr/bin/env python3
"""
tools/bt50_prune.py

Safe pruning utility for bt50_samples.db
- Dry-run mode shows counts and bytes that would be removed
- Default retention: 30 days
- Options: --db, --days, --vacuum, --yes

Usage examples:
  python tools/bt50_prune.py --db logs/bt50_samples.db --days 30 --dry-run
  python tools/bt50_prune.py --db logs/bt50_samples.db --days 365 --yes --vacuum

"""
from __future__ import annotations
import argparse
import os
import sqlite3
import time
from datetime import datetime, timedelta


def human(n: int) -> str:
    for unit in ['','K','M','G','T']:
        if abs(n) < 1024.0:
            return "%3.1f%s" % (n, unit)
        n /= 1024.0
    return "%3.1fP" % (n)


def ensure_db(path: str) -> None:
    if not os.path.exists(path):
        raise SystemExit(f"DB not found: {path}")


def prune(db_path: str, days: int, dry_run: bool, vacuum: bool) -> None:
    ensure_db(db_path)
    cutoff_ns = int((time.time() - days * 24 * 3600) * 1e9)
    print(f"Pruning rows older than {days} days (ts_ns < {cutoff_ns}) from {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(1) as cnt, SUM(LENGTH(frame_hex)) as bytes FROM bt50_samples WHERE ts_ns < ?", (cutoff_ns,))
    row = cur.fetchone()
    cnt = row['cnt'] or 0
    b = row['bytes'] or 0
    print(f"Matched rows: {cnt}, approx bytes in frame_hex: {human(b)}")

    if cnt == 0:
        print("Nothing to prune.")
        conn.close()
        return

    if dry_run:
        print("Dry-run mode: no changes made.")
        conn.close()
        return

    print("Deleting rows...")
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("BEGIN")
    cur.execute("DELETE FROM bt50_samples WHERE ts_ns < ?", (cutoff_ns,))
    deleted = cur.rowcount
    conn.commit()
    print(f"Deleted rows: {deleted}")

    if vacuum:
        print("Running VACUUM (this can take time)...")
        conn.execute("VACUUM")
        print("VACUUM completed.")

    conn.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="logs/bt50_samples.db", help="Path to bt50 samples DB")
    p.add_argument("--days", type=int, default=30, help="Retention in days")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--vacuum", action="store_true")
    p.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    args = p.parse_args()

    if not args.yes and not args.dry_run:
        print("This will permanently delete rows from the DB. Use --dry-run to preview, or --yes to confirm.")
        resp = input("Proceed? [y/N]: ").strip().lower()
        if resp != 'y':
            print("Aborted by user.")
            raise SystemExit(1)

    prune(args.db, args.days, args.dry_run, args.vacuum)
