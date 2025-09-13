#!/usr/bin/env python3
"""
LeadVille Frontend Demo

Starts both the WebSocket server simulation and demonstrates how to run
the React frontend with real-time WebSocket integration.

Run this to see the complete frontend stack working with the backend.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

# Import our test server
from test_websocket_server import MockWebSocketServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrontendDemo:
    def __init__(self):
        self.frontend_dir = Path(__file__).parent / "frontend"
        self.websocket_server = MockWebSocketServer()
        
    def check_frontend_setup(self):
        """Check if frontend dependencies are installed"""
        if not (self.frontend_dir / "node_modules").exists():
            logger.error("Frontend dependencies not found. Run: cd frontend && npm install")
            return False
        return True
        
    async def run_demo(self):
        """Run the complete demo"""
        logger.info("🚀 Starting LeadVille Frontend Demo")
        
        if not self.check_frontend_setup():
            return
            
        logger.info("📡 Starting WebSocket server on localhost:8765...")
        
        # Start WebSocket server in background
        server_task = asyncio.create_task(self.websocket_server.start())
        
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        logger.info("✅ WebSocket server started and broadcasting events")
        logger.info("")
        logger.info("🌐 To view the frontend:")
        logger.info("   1. Open a new terminal")
        logger.info("   2. cd frontend")
        logger.info("   3. npm run dev")
        logger.info("   4. Open http://localhost:5173")
        logger.info("")
        logger.info("📊 You should see real-time data updating in the dashboard!")
        logger.info("💡 The WebSocket client will automatically connect and display:")
        logger.info("   - Timer events with shot detection")
        logger.info("   - Health status with connection info")
        logger.info("   - Session updates with shot counts")
        logger.info("")
        logger.info("Press Ctrl+C to stop the demo")
        
        try:
            # Keep running until interrupted
            await server_task
        except KeyboardInterrupt:
            logger.info("🛑 Demo stopped")
        except Exception as e:
            logger.error(f"❌ Demo error: {e}")

def main():
    """Main entry point"""
    print("=" * 60)
    print("LeadVille Bridge - Frontend Foundation Demo")
    print("=" * 60)
    print()
    print("This demo shows the React frontend working with WebSocket integration.")
    print("Features demonstrated:")
    print("- React + Vite + TypeScript + Tailwind CSS")
    print("- Real-time WebSocket communication")
    print("- Kiosk-friendly responsive design")
    print("- Dashboard components with live data")
    print()
    
    demo = FrontendDemo()
    
    try:
        asyncio.run(demo.run_demo())
    except KeyboardInterrupt:
        print("\n👋 Demo finished")

if __name__ == "__main__":
    main()