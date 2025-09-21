#!/usr/bin/env python3
"""Export the full bt50_samples table to CSV on the Pi.
Creates `projects/LeadVille/logs/bt50_samples_export.csv`.
"""
import sqlite3
import csv
import os

DB = "projects/LeadVille/logs/bt50_samples.db"
OUT = "projects/LeadVille/logs/bt50_samples_export.csv"

if not os.path.exists(DB):
    print(f"DB not found: {DB}")
    raise SystemExit(2)

con = sqlite3.connect(DB)
cur = con.cursor()

# Ensure table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bt50_samples'")
if cur.fetchone() is None:
    print('No bt50_samples table found')
    con.close()
    raise SystemExit(0)

# Get column names
cols = [c[1] for c in cur.execute("PRAGMA table_info(bt50_samples)")]

# Stream rows to CSV
with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(cols)
    for row in cur.execute('SELECT * FROM bt50_samples ORDER BY id'):
        w.writerow(row)

con.close()
print('Wrote', OUT)
