#!/usr/bin/env python3
"""
Standalone test script for the kiosk API endpoint.
This runs only the kiosk functionality without requiring the full bridge.
"""

import uvicorn
from fastapi import FastAPI
from src.impact_bridge.api.kiosk import router as kiosk_router
from fastapi.responses import FileResponse

# Create a minimal app just for testing kiosk functionality
app = FastAPI(title="LeadVille Kiosk Test")

# Add kiosk router
app.include_router(kiosk_router, prefix="/v1/kiosk", tags=["Kiosk"])

# Serve kiosk HTML page
@app.get("/kiosk")
async def serve_kiosk():
    """Serve the kiosk boot status page."""
    return FileResponse("kiosk.html")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "LeadVille Kiosk Test API", "kiosk_url": "/kiosk"}

if __name__ == "__main__":
    print("🎯 Starting LeadVille Kiosk Test Server...")
    print("📡 Server: http://localhost:8003")
    print("🖥️  Kiosk: http://localhost:8003/kiosk")
    print("📊 Status API: http://localhost:8003/v1/kiosk/status")
    
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")