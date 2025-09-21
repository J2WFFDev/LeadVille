#!/usr/bin/env python3
"""
Wrapper for bt50_prune.py which runs prune every run but only VACUUMs at most once per week.
Stores last vacuum timestamp in `logs/last_vacuum_ts` (POSIX seconds).

Usage: same args as bt50_prune.py, wrapper accepts --vacuum-weekly flag to enable weekly vacuuming.

"""
from __future__ import annotations
import argparse
import os
import time
import subprocess
from datetime import datetime, timedelta

LAST_VAC_FILE = "logs/last_vacuum_ts"
WEEK_SECONDS = 7 * 24 * 3600


def need_vacuum() -> bool:
    try:
        m = os.path.getmtime(LAST_VAC_FILE)
        return (time.time() - m) >= WEEK_SECONDS
    except FileNotFoundError:
        return True


def touch_last_vac():
    os.makedirs(os.path.dirname(LAST_VAC_FILE), exist_ok=True)
    with open(LAST_VAC_FILE, "w") as f:
        f.write(str(int(time.time())))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="logs/bt50_samples.db")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--vacuum-weekly", action="store_true")
    p.add_argument("--yes", action="store_true")
    args = p.parse_args()

    base_cmd = ["/usr/bin/env", "python3", "tools/bt50_prune.py", "--db", args.db, "--days", str(args.days)]

    do_vac = False
    if args.vacuum_weekly and need_vacuum():
        do_vac = True

    if do_vac:
        cmd = base_cmd + ["--vacuum", "--yes"]
    else:
        if args.yes:
            cmd = base_cmd + ["--yes"]
        else:
            cmd = base_cmd

    print("Running: ", " ".join(cmd))
    res = subprocess.run(cmd, cwd="/home/jrwest/projects/LeadVille")
    if res.returncode == 0 and do_vac:
        touch_last_vac()

    raise SystemExit(res.returncode)


if __name__ == '__main__':
    main()
