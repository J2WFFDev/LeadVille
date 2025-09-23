#!/usr/bin/env python3
"""Launcher: run the package module from `src` so imports resolve under systemd.

This minimal launcher ensures `src/` is on `sys.path` and then runs
`impact_bridge.leadville_bridge:main()`. Keeping the launcher tiny avoids
relative-import issues when systemd executes the script directly.
"""

import os
import sys
import asyncio


def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(repo_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Import and run package entrypoint
    from impact_bridge.leadville_bridge import main as package_main

    if asyncio.iscoroutinefunction(package_main):
        asyncio.run(package_main())
    else:
        package_main()


if __name__ == '__main__':
    main()