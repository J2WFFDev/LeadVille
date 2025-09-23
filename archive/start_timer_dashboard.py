#!/usr/bin/env python3
"""
Timer Dashboard Backend Launcher

Simple script to launch the timer dashboard backend server.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from impact_bridge.timer_dashboard_backend import app
    import uvicorn
    
    if __name__ == "__main__":
        print("🚀 Starting LeadVille Timer Dashboard Backend...")
        print("📊 Database: logs/bt50_samples.db")
        print("🌐 Server: http://0.0.0.0:8001")
        print("📡 WebSocket: ws://0.0.0.0:8001/ws")
        print("🔗 API Docs: http://0.0.0.0:8001/docs")
        print("⏹️  Press Ctrl+C to stop")
        
        uvicorn.run(
            "impact_bridge.timer_dashboard_backend:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the LeadVille project directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)