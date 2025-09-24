#!/usr/bin/env python3
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).parent.parent / 'debug_fastapi_session.py'), run_name='__main__')
