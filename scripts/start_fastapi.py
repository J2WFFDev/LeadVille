#!/usr/bin/env python3
"""
LeadVille FastAPI Backend Launcher
Start the FastAPI server with proper configuration
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    try:
        from src.impact_bridge.fastapi_backend import app
        import uvicorn
        
        print("🚀 Starting LeadVille FastAPI Backend...")
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Install with: pip install fastapi uvicorn websockets")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)