"""
Live Timer Dashboard Backend - FastAPI Server

Provides REST API and WebSocket endpoints for real-time timer data display.
Integrates with shot_log_simple database view for live shooting data.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import sqlite3
from pydantic import BaseModel


class TimerEvent(BaseModel):
    """Timer event data model"""
    log_id: int
    event_time: str
    event_type: str
    shot_number: Optional[int]
    total_shots: Optional[int]
    shot_time: Optional[float]
    string_total_time: Optional[float]
    timer_device: Optional[str]
    shot_rating: Optional[str]


class StringSummary(BaseModel):
    """String summary data model"""
    timer_device: str
    total_events: int
    shot_events: int
    max_string_time: Optional[float]
    avg_split_time: Optional[float]
    status: str


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_event_id = 0
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📡 WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"📡 WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️  WebSocket send failed: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


class DatabaseManager:
    """Manages database connections and queries"""
    
    def __init__(self, db_path: str = "db/bt50_samples.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_latest_events(self, limit: int = 20) -> List[Dict]:
        """Get latest timer events"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    log_id,
                    event_time,
                    event_type,
                    shot_number,
                    total_shots,
                    shot_time,
                    string_total_time,
                    timer_device,
                    CASE 
                        WHEN shot_time <= 0.30 THEN 'excellent'
                        WHEN shot_time <= 0.50 THEN 'good' 
                        WHEN shot_time <= 0.70 THEN 'fair'
                        ELSE 'slow'
                    END as shot_rating
                FROM shot_log_simple 
                ORDER BY log_id DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_current_string(self) -> List[Dict]:
        """Get shots from current/most recent string"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    log_id,
                    shot_number,
                    shot_time,
                    string_total_time,
                    event_time,
                    CASE 
                        WHEN shot_time <= 0.30 THEN 'excellent'
                        WHEN shot_time <= 0.50 THEN 'good' 
                        WHEN shot_time <= 0.70 THEN 'fair'
                        ELSE 'slow'
                    END as shot_rating
                FROM shot_log_simple 
                WHERE event_type = 'SHOT' 
                    AND log_id >= (
                        SELECT MAX(log_id) 
                        FROM shot_log_simple 
                        WHERE event_type = 'START'
                    )
                ORDER BY shot_number
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_timer_status(self) -> List[Dict]:
        """Get timer device status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    timer_device,
                    total_events,
                    shot_events,
                    max_string_time,
                    ROUND(avg_split_time, 3) as avg_split_time,
                    last_event,
                    CASE 
                        WHEN datetime(last_event) >= datetime('now', '-1 hour') THEN 'active'
                        WHEN datetime(last_event) >= datetime('now', '-1 day') THEN 'recent'
                        ELSE 'idle'
                    END as status
                FROM timer_summary
                ORDER BY last_event DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_new_events(self, since_id: int) -> List[Dict]:
        """Get events newer than specified ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    log_id,
                    event_time,
                    event_type,
                    shot_number,
                    total_shots,
                    shot_time,
                    string_total_time,
                    timer_device,
                    CASE 
                        WHEN shot_time <= 0.30 THEN 'excellent'
                        WHEN shot_time <= 0.50 THEN 'good' 
                        WHEN shot_time <= 0.70 THEN 'fair'
                        ELSE 'slow'
                    END as shot_rating
                FROM shot_log_simple 
                WHERE log_id > ?
                ORDER BY log_id ASC
                LIMIT 50
            """, (since_id,))
            
            return [dict(row) for row in cursor.fetchall()]


# Global instances
websocket_manager = WebSocketManager()
db_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_manager
    
    # Startup
    try:
        db_manager = DatabaseManager()
        print("🚀 Timer Dashboard Backend starting...")
        print(f"📊 Database: {db_manager.db_path}")
        
        # Start background task for polling new events
        polling_task = asyncio.create_task(poll_for_new_events())
        print("📡 WebSocket polling started")
        
        yield
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        raise
    finally:
        # Shutdown
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
        print("🛑 Timer Dashboard Backend stopped")


app = FastAPI(
    title="LeadVille Timer Dashboard",
    description="Real-time shooting timer dashboard with live data",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def poll_for_new_events():
    """Background task to poll for new events and broadcast via WebSocket"""
    last_seen_id = 0
    
    while True:
        try:
            # Get the highest ID we've seen
            if db_manager:
                latest_events = db_manager.get_latest_events(1)
                if latest_events:
                    current_max_id = latest_events[0]['log_id']
                    
                    # Check for new events
                    if current_max_id > last_seen_id:
                        new_events = db_manager.get_new_events(last_seen_id)
                        
                        for event in new_events:
                            await websocket_manager.broadcast({
                                "type": "timer_event",
                                "data": event
                            })
                        
                        last_seen_id = current_max_id
            
            await asyncio.sleep(1)  # Poll every second
            
        except Exception as e:
            print(f"⚠️  Polling error: {e}")
            await asyncio.sleep(5)  # Wait longer on error


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    
    try:
        # Send initial data
        current_string = db_manager.get_current_string()
        timer_status = db_manager.get_timer_status()
        
        await websocket.send_json({
            "type": "initial_data",
            "data": {
                "current_string": current_string,
                "timer_status": timer_status
            }
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"⚠️  WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


@app.get("/api/events/latest")
async def get_latest_events(limit: int = Query(20, ge=1, le=100)):
    """Get latest timer events"""
    try:
        if db_manager is None:
            raise HTTPException(status_code=503, detail="Database manager not initialized")
        events = db_manager.get_latest_events(limit)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/string/current")
async def get_current_string():
    """Get current string progress"""
    try:
        shots = db_manager.get_current_string()
        return {
            "shots": shots,
            "total_shots": len(shots),
            "string_time": shots[-1]["string_total_time"] if shots else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/timer/status")
async def get_timer_status():
    """Get timer device status"""
    try:
        if db_manager is None:
            raise HTTPException(status_code=503, detail="Database manager not initialized")
        status = db_manager.get_timer_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboard")
async def get_leaderboard():
    """Get today's best times"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    timer_device,
                    MIN(string_total_time) as best_time,
                    COUNT(*) as strings_completed,
                    MAX(event_time) as last_string
                FROM shot_log_simple
                WHERE event_type = 'STOP' 
                    AND date(event_time) = date('now')
                    AND string_total_time IS NOT NULL
                GROUP BY timer_device
                ORDER BY best_time ASC
            """)
            
            results = [dict(row) for row in cursor.fetchall()]
            return {"leaderboard": results}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        if db_manager is None:
            return {
                "status": "unhealthy",
                "error": "Database manager not initialized",
                "timestamp": datetime.now().isoformat()
            }
        
        # Test database connection
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shot_log_simple")
            count = cursor.fetchone()[0]
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_events": count,
            "websocket_connections": len(websocket_manager.active_connections),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    uvicorn.run(
        "timer_dashboard_backend:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )