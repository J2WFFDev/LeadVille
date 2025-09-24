#!/usr/bin/env python3
"""Wrapper to run start_timer_dashboard from scripts/ for a cleaner repo root."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).parent.parent / 'start_timer_dashboard.py'), run_name='__main__')
