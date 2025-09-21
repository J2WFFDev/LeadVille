#!/usr/bin/env python3
"""Inspect the bt50_samples SQLite DB and print tables, schema, counts by sensor_mac,
and the last 10 rows. Designed to run on the Raspberry Pi without extra packages.
"""
import sqlite3
import os
import sys

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'bt50_samples.db'))

if not os.path.exists(DB_PATH):
    print(f"DB not found: {DB_PATH}")
    sys.exit(2)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

print("Tables:")
for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(" ", r[0])

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bt50_samples'")
if cur.fetchone() is None:
    print("\nNo table named bt50_samples found")
    con.close()
    sys.exit(0)

print("\nSchema for bt50_samples:")
for r in cur.execute("PRAGMA table_info(bt50_samples)"):
    print(" ", r)

print("\nCounts by sensor_mac:")
for r in cur.execute("SELECT COALESCE(sensor_mac,'<null>') AS mac, COUNT(*) FROM bt50_samples GROUP BY mac ORDER BY COUNT(*) DESC LIMIT 20"):
    print(" ", r)

print("\nLast 10 rows:")
cols = [c[1] for c in cur.execute("PRAGMA table_info(bt50_samples)")]
for row in cur.execute("SELECT * FROM bt50_samples ORDER BY id DESC LIMIT 10"):
    print("\nROW:")
    for k, v in zip(cols, row):
        print(f"  {k}: {v}")

con.close()
