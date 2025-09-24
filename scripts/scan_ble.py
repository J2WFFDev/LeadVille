#!/usr/bin/env python3
"""Wrapper to run BLE scan utilities from the scripts/ folder.
This file was moved from repository root to keep the top-level clean.
"""
from pathlib import Path
import runpy

if __name__ == '__main__':
    # Original `scan_ble.py` was at repository root; import and run it explicitly.
    target = Path(__file__).parent.parent / 'scan_ble.py'
    if target.exists():
        runpy.run_path(str(target), run_name='__main__')
    else:
        print('scan_ble.py not found in repo root; please run scripts/scan_ble.py from repository root')
