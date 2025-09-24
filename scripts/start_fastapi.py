#!/usr/bin/env python3
"""
Start script for LeadVille FastAPI used by systemd unit.

This script ensures the project `src/` path is on `sys.path` and starts
uvicorn with the FastAPI application module.
"""
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).parent.parent
    # Ensure project root is on sys.path so 'src' is importable as a top-level package
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    # Also add src directory for direct imports if needed
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Import and run uvicorn programmatically
    try:
        import uvicorn
        # Use module path to the FastAPI app
        app_location = "src.impact_bridge.fastapi_backend:app"
        uvicorn.run(app_location, host="0.0.0.0", port=8001, log_level="info")
    except Exception as e:
        print(f"Failed to start uvicorn: {e}")
        raise


if __name__ == "__main__":
    main()
