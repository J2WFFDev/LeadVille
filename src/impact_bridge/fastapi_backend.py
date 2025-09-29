"""
LeadVille FastAPI Backend (initial scaffold)
Mirrors Flask API structure for health and logs endpoints, CORS, and log parsing.
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
import os
import json
import glob
import sys
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Database helper functions
def get_db_connection():
    """Get database connection with row factory"""
    import sqlite3
    from pathlib import Path
    
    db_path = Path("db/leadville.db")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

async def _update_json_config_from_db(bridge_id: int):
    """Update JSON config file from database (dual-write strategy)"""
    import json
    from pathlib import Path
    
    try:
        with get_db_connection() as conn:
            # Get bridge configuration including stage info
            cursor = conn.execute("""
                SELECT bc.timer_address, bc.stage_config_id, sc.name as stage_name
                FROM bridge_configurations bc
                LEFT JOIN stage_configs sc ON bc.stage_config_id = sc.id
                WHERE bc.bridge_id = ?
            """, (bridge_id,))
            bridge_config = cursor.fetchone()
            
            timer_address = bridge_config['timer_address'] if bridge_config else None
            stage_config_id = bridge_config['stage_config_id'] if bridge_config else None
            stage_name = bridge_config['stage_name'] if bridge_config else None
            
            # Get sensor assignments with target information
            cursor = conn.execute("""
                SELECT target_number, sensor_address, sensor_label
                FROM bridge_target_assignments 
                WHERE bridge_id = ?
                ORDER BY target_number
            """, (bridge_id,))
            assignments = cursor.fetchall()
        
        # Build sensor assignments dict for new unified format
        sensors_dict = {}
        for assignment in assignments:
            target_key = f"target_{assignment['target_number']}"
            sensors_dict[target_key] = {
                "address": assignment['sensor_address'],
                "label": assignment['sensor_label']
            }
        
        # Write JSON config for boot sequence (bridge-compatible format)
        # The bridge expects simple format with "timer" string and "sensors" array
        sensor_addresses = [assignment['sensor_address'] for assignment in assignments]
        
        config_data = {
            "timer": timer_address,
            "sensors": sensor_addresses
        }
        
        # Create config directory if it doesn't exist
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "bridge_device_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        logger.info(f"Updated JSON config from database: {config_data}")
        
    except Exception as e:
        logger.error(f"Failed to update JSON config from database: {e}")
        raise

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

app = FastAPI(title="LeadVille Impact Bridge API", version="2.0.0")

# Enable CORS for all domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include device pool management routes
try:
    from src.impact_bridge.pool_api import router as pool_router
    app.include_router(pool_router)
    logger.info("✅ Device Pool Management API routes included")
except Exception as e:
    logger.error(f"❌ Failed to include Device Pool API routes: {e}")
    # Continue without pool routes for now

# Include SpecialPie timer management routes
try:
    from src.impact_bridge.specialpie_api import router as specialpie_router
    app.include_router(specialpie_router)
    logger.info("✅ SpecialPie Timer API routes included")
except Exception as e:
    logger.error(f"❌ Failed to include SpecialPie API routes: {e}")
    # Continue without SpecialPie routes for now

# Include AMG Commander timer management routes
try:
    from src.impact_bridge.amg_api import router as amg_router
    app.include_router(amg_router)
    logger.info("✅ AMG Commander Timer API routes included")
except Exception as e:
    logger.error(f"❌ Failed to include AMG Commander API routes: {e}")
    # Continue without AMG routes for now

# Include SpecialPie demo routes (for testing without hardware)
try:
    from src.impact_bridge.specialpie_demo import router as specialpie_demo_router
    app.include_router(specialpie_demo_router)
    logger.info("✅ SpecialPie Demo API routes included")
except Exception as e:
    logger.error(f"❌ Failed to include SpecialPie Demo routes: {e}")
    # Continue without demo routes

# Mount static files for dashboard pages
try:
    docs_path = project_root / "docs"
    if docs_path.exists():
        app.mount("/docs", StaticFiles(directory=str(docs_path)), name="docs")
        logger.info(f"Mounted static files from {docs_path}")
    else:
        logger.warning(f"Docs directory not found at {docs_path}")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

# Log directories for original LeadVille structure
LOG_DIRS = [
    str(project_root / "logs/console"),
    str(project_root / "logs/debug"),
    str(project_root / "logs/main"),
]

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "project": "LeadVille Impact Bridge",
        "version": "2.0.0"
    }

@app.get("/api/logs")
def get_logs(limit: int = 100):
    logs = fetch_logs(limit)
    return JSONResponse(content=logs)

@app.get("/api/shot-log")
def get_shot_log(limit: int = 100):
    """Get combined timer events and sensor impacts from shot_log database view"""
    try:
        import sqlite3
        from pathlib import Path

        # Determine capture DB path candidates and prefer an explicit env var
        project_root = Path(__file__).parent.parent.parent
        candidates = []
        env_db = os.environ.get('CAPTURE_DB_PATH')
        if env_db:
            candidates.append(Path(env_db))
        # Preferred project location
            # Preferred canonical location inside the project and explicit override via env var.
            candidates.append(project_root / 'db' / 'leadville_runtime.db')
            # Also allow explicit override via CAPTURE_DB_PATH environment variable (checked above).
        
            # Legacy locations removed

        db_path = None
        # Try candidates in order and log what we check
        for candidate in candidates:
            try:
                exists = candidate.exists()
            except Exception as e:
                exists = False
                logger.debug(f"Error checking path {candidate}: {e}")
            logger.info(f"Checking capture DB candidate: {candidate} exists={exists}")
            if exists:
                db_path = candidate
                break

        if db_path is None:
            logger.warning(f"No capture DB found among candidates: {candidates}")
            return JSONResponse(content={"error": "Database not found", "logs": []}, status_code=404)

        # Log basic file info for diagnostics
        try:
            st = db_path.stat()
            logger.info(f"Using capture DB: {db_path} size={st.st_size} mtime={st.st_mtime}")
        except Exception:
            logger.info(f"Using capture DB: {db_path} (stat unavailable)")

        # Open database connection (read-only is fine for API reads)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                log_id,
                record_type,
                event_time,
                device_id,
                event_type,
                current_shot,
                split_seconds,
                string_total_time,
                sensor_mac,
                impact_magnitude
            FROM shot_log 
            ORDER BY ts_ns DESC 
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        # Convert to list of dictionaries
        logs = []
        for row in rows:
            logs.append({
                "log_id": row[0],
                "record_type": row[1],
                "timestamp": row[2],  # event_time is already formatted
                "level": get_log_level_for_event(row[4]),  # event_type
                "source": get_source_for_record(row[1], row[3], row[8]),  # record_type, device_id, sensor_mac
                "message": format_shot_log_message(row),
                "event_type": row[4],
                "shot_number": row[5],
                "split_time": row[6],
                "total_time": row[7],
                "sensor_mac": row[8],
                "impact_magnitude": row[9]
            })

        return JSONResponse(content={"logs": logs, "count": len(logs)})

    except Exception as e:
        logger.error(f"Error fetching shot_log data: {e}")
        return JSONResponse(
            content={"error": f"Failed to fetch shot log: {str(e)}", "logs": []},
            status_code=500
        )

def get_log_level_for_event(event_type: str) -> str:
    """Map event types to log levels for consistent display"""
    if event_type == "START":
        return "INFO"
    elif event_type == "SHOT":
        return "SUCCESS"
    elif event_type == "STOP":
        return "INFO"
    elif event_type == "IMPACT":
        return "WARNING"
    else:
        return "INFO"

def get_source_for_record(record_type: str, device_id: str, sensor_mac: str) -> str:
    """Generate source name for different record types"""
    if record_type == "shot":
        return "📊 shot_log"
    elif record_type == "timer_control":
        return "📊 shot_log"
    elif record_type == "impact":
        return "� shot_log"
    else:
        return "📊 shot_log"

def format_shot_log_message(row) -> str:
    """Format shot log row into readable message"""
    log_id, record_type, event_time, device_id, event_type, current_shot, split_seconds, string_total_time, sensor_mac, impact_magnitude = row
    
    if record_type == "shot":
        split_time = f"{split_seconds:.2f}" if split_seconds is not None else "0.00"
        total_time = f"{string_total_time:.2f}" if string_total_time is not None else "0.00"
        return f"Shot #{current_shot} - Split: {split_time}s, Total: {total_time}s"
    elif record_type == "timer_control":
        if event_type == "START":
            return "🔫 Timer started"
        elif event_type == "STOP":
            total_time = f"{string_total_time:.2f}" if string_total_time is not None else "0.00"
            return f"🏁 Timer stopped - Final time: {total_time}s"
    elif record_type == "impact":
        magnitude = f"{impact_magnitude:.1f}" if impact_magnitude is not None else "0.0"
        return f"💥 Impact detected - Magnitude: {magnitude}"
    
    return f"{event_type}: {record_type}"

@app.get("/api/admin/network")
def get_network_status():
    """Get current network status and configuration"""
    try:
        from src.impact_bridge.network_manager import NetworkManager
        nm = NetworkManager()
        status = nm.get_network_status()
        return JSONResponse(content=status)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to get network status: {str(e)}"},
            status_code=500
        )

from pydantic import BaseModel

class NetworkRequest(BaseModel):
    mode: str
    ssid: str = None
    password: str = None

@app.post("/api/admin/network")
def switch_network_mode(request: NetworkRequest):
    """Switch network mode between online and offline"""
    try:
        from src.impact_bridge.network_manager import NetworkManager
        nm = NetworkManager()
        
        mode = request.mode
        if mode == "online":
            ssid = request.ssid
            password = request.password
            if not ssid or not password:
                return JSONResponse(
                    content={"error": "SSID and password required for online mode"},
                    status_code=400
                )
            success = nm.switch_to_online_mode(ssid, password)
        elif mode == "offline":
            success = nm.switch_to_offline_mode()
        else:
            return JSONResponse(
                content={"error": "Invalid mode. Use 'online' or 'offline'"},
                status_code=400
            )
        
        if success:
            return JSONResponse(content={"status": "success", "mode": mode})
        else:
            return JSONResponse(
                content={"error": f"Failed to switch to {mode} mode"},
                status_code=500
            )
            
    except Exception as e:
            return JSONResponse(
                content={"error": f"Network switch failed: {str(e)}"},
                status_code=500
            )

@app.get("/api/admin/system")
def get_system_stats():
    """Get system monitoring statistics"""
    try:
        from src.impact_bridge.system_monitor import SystemMonitor
        monitor = SystemMonitor()
        stats = monitor.get_system_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to get system stats: {str(e)}"},
            status_code=500
        )

@app.get("/api/admin/services")
def get_service_health():
    """Get service health status"""
    try:
        from src.impact_bridge.system_monitor import SystemMonitor
        monitor = SystemMonitor()
        services = monitor.get_service_health()
        return JSONResponse(content=services)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to get service health: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/services/restart")
async def restart_bridge_service():
    """Restart the leadville-bridge service (core BLE bridge, not the API)"""
    try:
        import subprocess
        import asyncio
        from datetime import datetime
        
        # Schedule restart with a small delay to allow response to be sent
        async def delayed_restart():
            await asyncio.sleep(2)  # Give time for response to be sent
            try:
                result = subprocess.run(['/usr/bin/sudo', '/usr/bin/systemctl', 'restart', 'leadville-bridge'], 
                                      check=True, capture_output=True, text=True)
                logger.info("Bridge service restart initiated successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to restart bridge service: {e.returncode} - stdout: {e.stdout} - stderr: {e.stderr}")
        
        # Schedule the restart
        asyncio.create_task(delayed_restart())
        
        return JSONResponse(content={
            "status": "restart_initiated",
            "message": "Bridge service restart initiated. Service will restart in 2 seconds.",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to restart service: {str(e)}"},
            status_code=500
        )

@app.get("/api/admin/ble")
def get_ble_quality():
    """Get BLE connection quality and status"""
    try:
        from src.impact_bridge.system_monitor import SystemMonitor
        monitor = SystemMonitor()
        ble_status = monitor.get_ble_quality()
        return JSONResponse(content=ble_status)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to get BLE status: {str(e)}"},
            status_code=500
        )

# =============================================================================
# Device Management API Endpoints
# =============================================================================

@app.get("/api/admin/devices")
async def get_devices():
    """Get all paired devices"""
    try:
        from src.impact_bridge.device_manager import device_manager
        devices = device_manager.get_paired_devices()
        return JSONResponse(content={
            "devices": devices,
            "count": len(devices)
        })
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return JSONResponse(
            content={"error": f"Failed to get devices: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/devices/discover")
async def discover_devices(duration: int = 10):
    """Discover available BLE devices"""
    try:
        from src.impact_bridge.device_manager import device_manager
        devices = await device_manager.discover_devices(duration)
        return JSONResponse(content={
            "discovered_devices": devices,
            "count": len(devices),
            "scan_duration": duration
        })
    except ValueError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error discovering devices: {e}")
        return JSONResponse(
            content={"error": f"Device discovery failed: {str(e)}"},
            status_code=500
        )

@app.websocket("/ws/admin/devices/discover")
async def websocket_discover_devices(websocket: WebSocket, duration: int = 10):
    """Discover BLE devices with real-time WebSocket streaming"""
    await websocket.accept()
    
    try:
        from src.impact_bridge.device_manager import device_manager
        import asyncio
        import time
        
        # Send start message
        await websocket.send_json({
            "type": "start",
            "duration": duration,
            "message": "Starting BLE device discovery..."
        })
        
        if device_manager.scanning:
            await websocket.send_json({
                "type": "error",
                "message": "Discovery already in progress"
            })
            return
            
        device_manager.scanning = True
        device_manager.discovered_devices.clear()
        discovered_devices = []
        
        try:
            from bleak import BleakScanner
            
            # Start scanning with periodic discovery (compatible with Bleak 1.1.0)
            start_time = time.time()
            last_discovery_check = 0
            check_interval = 3  # Check for new devices every 3 seconds
            scan_timeout = 2.0  # Each scan takes 2 seconds
            
            # Send initial progress
            await websocket.send_json({
                "type": "progress",
                "elapsed": 0,
                "remaining": duration,
                "progress": 0,
                "devices_found": len(discovered_devices),
                "scan_status": "Starting discovery..."
            })
            
            # Main discovery loop
            while time.time() - start_time < duration:
                current_time = time.time()
                elapsed = round(current_time - start_time, 1)
                remaining = max(0, duration - elapsed)
                overall_progress = (elapsed / duration) * 100
                
                # Discover devices periodically 
                if current_time - last_discovery_check >= check_interval:
                    # Send scanning status
                    await websocket.send_json({
                        "type": "progress",
                        "elapsed": elapsed,
                        "remaining": remaining,
                        "progress": overall_progress,
                        "devices_found": len(discovered_devices),
                        "scan_status": f"Scanning for devices... ({scan_timeout:.1f}s)"
                    })
                    
                    try:
                        # Start scan with progress tracking
                        scan_start = time.time()
                        devices = await BleakScanner.discover(timeout=scan_timeout)
                        scan_duration = time.time() - scan_start
                        
                        new_devices_found = 0
                        for device in devices:
                            try:
                                # Analyze device to see if it's relevant
                                device_info = await device_manager._analyze_device(device)
                                if device_info and device_manager._is_relevant_device(device_info):
                                    # Check if we already found this device
                                    if device.address not in [d["address"] for d in discovered_devices]:
                                        discovered_devices.append(device_info)
                                        device_manager.discovered_devices[device.address] = device_info
                                        new_devices_found += 1
                                        
                                        # Send device found message immediately
                                        await websocket.send_json({
                                            "type": "device_found",
                                            "device": device_info,
                                            "count": len(discovered_devices),
                                            "elapsed": round(time.time() - start_time, 1)
                                        })
                            except Exception as e:
                                logger.debug(f"Error analyzing device {device.address}: {e}")
                                
                        last_discovery_check = current_time
                        
                        # Send scan complete status
                        updated_elapsed = round(time.time() - start_time, 1)
                        await websocket.send_json({
                            "type": "progress",
                            "elapsed": updated_elapsed,
                            "remaining": max(0, duration - updated_elapsed),
                            "progress": (updated_elapsed / duration) * 100,
                            "devices_found": len(discovered_devices),
                            "scan_status": f"Scan complete - Found {new_devices_found} new devices ({scan_duration:.1f}s)"
                        })
                        
                        logger.debug(f"Discovery scan completed in {scan_duration:.1f}s, found {new_devices_found} new devices, total: {len(discovered_devices)}")
                        
                    except Exception as e:
                        logger.error(f"Error during device scan: {e}")
                        await websocket.send_json({
                            "type": "progress",
                            "elapsed": elapsed,
                            "remaining": remaining,
                            "progress": overall_progress,
                            "devices_found": len(discovered_devices),
                            "scan_status": f"Scan error: {str(e)}"
                        })
                else:
                    # Send waiting status between scans
                    time_until_next_scan = check_interval - (current_time - last_discovery_check)
                    await websocket.send_json({
                        "type": "progress",
                        "elapsed": elapsed,
                        "remaining": remaining,
                        "progress": overall_progress,
                        "devices_found": len(discovered_devices),
                        "scan_status": f"Waiting {time_until_next_scan:.1f}s until next scan..."
                    })
                
                # Short sleep to prevent busy waiting
                await asyncio.sleep(0.5)
            
            # Send completion message
            await websocket.send_json({
                "type": "complete",
                "devices": discovered_devices,
                "count": len(discovered_devices),
                "duration": duration,
                "message": f"Discovery complete - Found {len(discovered_devices)} devices"
            })
            
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Discovery failed: {str(e)}"
            })
        finally:
            device_manager.scanning = False
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during device discovery")
        if 'device_manager' in locals():
            device_manager.scanning = False
    except Exception as e:
        logger.error(f"WebSocket discovery error: {e}")
        await websocket.send_json({
            "type": "error", 
            "message": f"WebSocket error: {str(e)}"
        })

@app.post("/api/admin/devices/pair")
async def pair_device(request: Request):
    """Pair a discovered device"""
    try:
        data = await request.json()
        mac_address = data.get("mac_address")
        label = data.get("label")
        
        if not mac_address or not label:
            return JSONResponse(
                content={"error": "mac_address and label are required"},
                status_code=400
            )
        
        from src.impact_bridge.device_manager import device_manager
        result = await device_manager.pair_device(mac_address, label)
        return JSONResponse(content=result)
        
    except ValueError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error pairing device: {e}")
        return JSONResponse(
            content={"error": f"Device pairing failed: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/devices/{sensor_id}/assign")
async def assign_device_to_target(sensor_id: int, request: Request):
    """
    [DEPRECATED] Assign a device to a target
    
    This endpoint is deprecated. Use the Device Pool system instead:
    - POST /api/admin/pool/sessions/{session_id}/lease
    """
    logger.warning("DEPRECATED: /api/admin/devices/{sensor_id}/assign endpoint called. Use Device Pool system instead.")
    try:
        data = await request.json()
        target_id = data.get("target_id")
        
        if target_id is None:
            return JSONResponse(
                content={"error": "target_id is required"},
                status_code=400
            )
        
        from src.impact_bridge.device_manager import device_manager
        result = await device_manager.assign_device_to_target(sensor_id, target_id)
        return JSONResponse(content=result)
        
    except ValueError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error assigning device: {e}")
        return JSONResponse(
            content={"error": f"Device assignment failed: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/devices/{sensor_id}/unassign")
async def unassign_device(sensor_id: int):
    """
    [DEPRECATED] Remove device assignment from target
    
    This endpoint is deprecated. Use the Device Pool system instead:
    - POST /api/admin/pool/sessions/{session_id}/release/{device_id}
    """
    logger.warning("DEPRECATED: /api/admin/devices/{sensor_id}/unassign endpoint called. Use Device Pool system instead.")
    try:
        from src.impact_bridge.device_manager import device_manager
        result = await device_manager.unassign_device(sensor_id)
        return JSONResponse(content=result)
        
    except ValueError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error unassigning device: {e}")
        return JSONResponse(
            content={"error": f"Device unassignment failed: {str(e)}"},
            status_code=500
        )

@app.put("/api/admin/devices/{mac_address}/health")
async def update_device_health(mac_address: str, request: Request):
    """Update device health status (battery, RSSI)"""
    try:
        data = await request.json()
        battery = data.get("battery")
        rssi = data.get("rssi")
        
        from src.impact_bridge.device_manager import device_manager
        result = await device_manager.update_device_health(mac_address, battery, rssi)
        return JSONResponse(content=result)
        
    except ValueError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error updating device health: {e}")
        return JSONResponse(
            content={"error": f"Device health update failed: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/devices/{mac_address}/refresh_battery")
async def refresh_device_battery(mac_address: str):
    """Refresh battery status for a specific device by connecting and reading current level"""
    try:
        from src.impact_bridge.device_manager import device_manager
        battery_level = await device_manager.refresh_device_battery(mac_address)
        
        if battery_level is not None:
            # Update the device health with new battery reading
            await device_manager.update_device_health(mac_address, battery=battery_level)
            return JSONResponse(content={
                "status": "success",
                "battery": battery_level,
                "message": f"Battery level refreshed: {battery_level}%"
            })
        else:
            return JSONResponse(content={
                "status": "failed",
                "battery": None,
                "message": "Could not read battery level"
            }, status_code=422)
            
    except ValueError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=404
        )
    except Exception as e:
        logger.error(f"Error refreshing battery for {mac_address}: {e}")
        return JSONResponse(
            content={"error": f"Battery refresh failed: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/devices/refresh_all_batteries")
async def refresh_all_device_batteries():
    """Refresh battery status for all paired BT50 devices using external service"""
    try:
        import subprocess
        import os
        
        # Run the battery refresh service
        script_path = "/home/jrwest/projects/LeadVille/tools/battery_refresh_service.py"
        if not os.path.exists(script_path):
            return JSONResponse(
                content={"error": "Battery refresh service not found"},
                status_code=500
            )
        
        result = subprocess.run([
            'python3', script_path
        ], cwd='/home/jrwest/projects/LeadVille/tools',
           capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Parse the output to extract success count
            output_lines = result.stdout.strip().split('\n')
            summary_line = [line for line in output_lines if 'Batch complete:' in line]
            
            if summary_line:
                # Extract numbers from "✅ Batch complete: 1/3 devices updated"
                summary = summary_line[0]
                try:
                    numbers = summary.split(':')[1].strip().split('/')[0].strip().split()[0]
                    successful = int(numbers)
                except:
                    successful = 0
            else:
                successful = 0
                
            return JSONResponse(content={
                "status": "completed",
                "successful_updates": successful,
                "output": result.stdout,
                "message": "Battery refresh completed"
            })
        else:
            return JSONResponse(
                content={
                    "status": "error", 
                    "error": result.stderr,
                    "output": result.stdout
                },
                status_code=500
            )
        
    except subprocess.TimeoutExpired:
        return JSONResponse(
            content={"error": "Battery refresh timed out"},
            status_code=408
        )
    except Exception as e:
        logger.error(f"Error running battery refresh: {e}")
        return JSONResponse(
            content={"error": f"Battery refresh failed: {str(e)}"},
            status_code=500
        )

@app.delete("/api/admin/devices/{sensor_id}")
async def remove_device(sensor_id: int):
    """Remove a paired device"""
    try:
        from src.impact_bridge.device_manager import device_manager
        result = await device_manager.remove_device(sensor_id)
        return JSONResponse(content=result)
        
    except ValueError as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error removing device: {e}")
        return JSONResponse(
            content={"error": f"Device removal failed: {str(e)}"},
            status_code=500
        )

@app.get("/api/admin/devices/assignments")
def get_device_assignments():
    """
    [DEPRECATED] Get current device-to-target assignments
    
    This endpoint is deprecated. Use the Device Pool system instead:
    - GET /api/admin/pool/sessions/{session_id}/devices
    """
    logger.warning("DEPRECATED: /api/admin/devices/assignments endpoint called. Use Device Pool system instead.")
    try:
        from src.impact_bridge.device_manager import device_manager
        assignments = device_manager.get_device_assignments()
        return JSONResponse(content=assignments)
    except Exception as e:
        logger.error(f"Error getting device assignments: {e}")
        return JSONResponse(
            content={"error": f"Failed to get assignments: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/devices/discovery/reset")
async def reset_device_discovery():
    """Reset device discovery state and Bluetooth adapter"""
    try:
        from src.impact_bridge.device_manager import device_manager
        import subprocess
        
        # Reset device manager state
        device_manager.scanning = False
        device_manager.discovered_devices.clear()
        
        # Reset Bluetooth adapter
        try:
            logger.info("Resetting Bluetooth adapter for discovery...")
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'reset'], 
                         capture_output=True, timeout=3)
            await asyncio.sleep(0.5)
            subprocess.run(['sudo', 'bluetoothctl', 'pairable', 'on'], 
                         capture_output=True, timeout=3)
        except Exception as bt_reset_e:
            logger.warning(f"Bluetooth reset during discovery reset failed: {bt_reset_e}")
        
        logger.info("Device discovery state and Bluetooth adapter reset")
        return JSONResponse(content={
            "status": "reset",
            "message": "Device discovery state and Bluetooth adapter reset"
        })
    except Exception as e:
        logger.error(f"Error resetting device discovery: {e}")
        return JSONResponse(
            content={"error": f"Failed to reset discovery: {str(e)}"},
            status_code=500
        )

@app.get("/api/admin/node")
def get_node_info():
    """Get current node information"""
    try:
        import socket
        import platform
        from datetime import datetime
        
        # Get basic node info
        node_info = {
            'name': socket.gethostname(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0],
            'timestamp': datetime.now().isoformat(),
        }
        
        # Add network info
        from src.impact_bridge.network_manager import NetworkManager
        nm = NetworkManager()
        network_status = nm.get_network_status()
        node_info['network'] = network_status
        
        return JSONResponse(content=node_info)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to get node info: {str(e)}"},
            status_code=500
        )

@app.get("/api/admin/bridge/config")
async def get_bridge_config():
    """Get the current bridge device configuration from database"""
    try:
        # Get bridge configuration from database
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT bc.bridge_id, bc.stage_config_id, bc.timer_address,
                       sc.name as stage_name
                FROM bridge_configurations bc
                LEFT JOIN stage_configs sc ON bc.stage_config_id = sc.id
                WHERE bc.bridge_id = 1
            """)
            bridge_config = cursor.fetchone()
            
            if not bridge_config:
                return JSONResponse(
                    content={"error": "Bridge configuration not found"},
                    status_code=404
                )
            
            # Get target assignments
            cursor = conn.execute("""
                SELECT target_number, sensor_address, sensor_label
                FROM bridge_target_assignments
                WHERE bridge_id = 1
                ORDER BY target_number
            """)
            target_assignments = cursor.fetchall()
        
        # Get paired device information for status
        from src.impact_bridge.device_manager import device_manager
        paired_devices = device_manager.get_paired_devices()
        device_lookup = {device['address']: device for device in paired_devices}
        
        # Build timer response
        timer_address = bridge_config['timer_address']
        timer_info = {
            "address": timer_address,
            "status": "configured" if timer_address else "not_configured",
            "device_info": device_lookup.get(timer_address) if timer_address else None
        }
        
        # Build sensors response with target assignments
        sensors = []
        targets = {}
        
        for assignment in target_assignments:
            sensor_addr = assignment['sensor_address']
            target_num = assignment['target_number']
            
            sensor_info = {
                "address": sensor_addr,
                "label": assignment['sensor_label'],
                "target_number": target_num,
                "device_info": device_lookup.get(sensor_addr),
                "status": "paired" if sensor_addr in device_lookup else "not_paired"
            }
            sensors.append(sensor_info)
            targets[f"target_{target_num}"] = sensor_info
        
        response = {
            "bridge_id": bridge_config['bridge_id'],
            "stage_config_id": bridge_config['stage_config_id'],
            "stage_name": bridge_config['stage_name'],
            "timer": timer_info,
            "sensors": sensors,
            "targets": targets,
            "summary": {
                "timer_configured": bool(timer_address),
                "sensors_count": len(sensors),
                "sensors_paired": len([s for s in sensors if s['status'] == 'paired']),
                "targets_assigned": len(targets)
            }
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Failed to get bridge config: {e}")
        return JSONResponse(
            content={"error": f"Failed to get bridge config: {str(e)}"},
            status_code=500
        )
        
    except Exception as e:
        logger.error(f"Failed to get bridge config: {e}")
        return JSONResponse(
            content={"error": f"Failed to get bridge config: {str(e)}"},
            status_code=500
        )

@app.put("/api/admin/bridge/config")
async def update_bridge_config(request: dict):
    """Update the bridge device configuration in database and JSON file"""
    try:
        import json
        from pathlib import Path
        
        # Validate request structure
        timer = request.get("timer")
        sensors = request.get("sensors", [])
        targets = request.get("targets", {})  # New: target assignments {"1": "EA:18...", "2": "DB:10..."}
        
        if not isinstance(sensors, list):
            return JSONResponse(
                content={"error": "sensors must be a list"},
                status_code=400
            )
        
        bridge_id = 1  # Default bridge ID
        
        # Update database with transaction
        with get_db_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # Update bridge configuration (timer)
                conn.execute("""
                    INSERT OR REPLACE INTO bridge_configurations 
                    (bridge_id, stage_config_id, timer_address)
                    VALUES (?, COALESCE((SELECT stage_config_id FROM bridge_configurations WHERE bridge_id = ?), 1), ?)
                """, (bridge_id, bridge_id, timer))
                
                # Clear existing target assignments
                conn.execute("DELETE FROM bridge_target_assignments WHERE bridge_id = ?", (bridge_id,))
                
                # Insert new target assignments
                if targets:
                    # Using targets dictionary (new format)
                    for target_num_str, sensor_addr in targets.items():
                        if sensor_addr:  # Only assign if not null/empty
                            target_num = int(target_num_str)
                            
                            # Get sensor label from device pool
                            cursor = conn.execute(
                                "SELECT label FROM device_pool WHERE hw_addr = ?",
                                (sensor_addr,)
                            )
                            device_row = cursor.fetchone()
                            sensor_label = device_row['label'] if device_row else f"Sensor {sensor_addr[-4:]}"
                            
                            conn.execute("""
                                INSERT INTO bridge_target_assignments 
                                (bridge_id, target_number, sensor_address, sensor_label)
                                VALUES (?, ?, ?, ?)
                            """, (bridge_id, target_num, sensor_addr, sensor_label))
                            
                elif sensors:
                    # Using sensors list (legacy format) - assign to targets sequentially
                    for i, sensor_addr in enumerate(sensors):
                        target_num = i + 1
                        
                        # Get sensor label from device pool
                        cursor = conn.execute(
                            "SELECT label FROM device_pool WHERE hw_addr = ?",
                            (sensor_addr,)
                        )
                        device_row = cursor.fetchone()
                        sensor_label = device_row['label'] if device_row else f"Sensor {sensor_addr[-4:]}"
                        
                        conn.execute("""
                            INSERT INTO bridge_target_assignments 
                            (bridge_id, target_number, sensor_address, sensor_label)
                            VALUES (?, ?, ?, ?)
                        """, (bridge_id, target_num, sensor_addr, sensor_label))
                
                conn.execute("COMMIT")
                
            except Exception as e:
                conn.execute("ROLLBACK")
                raise e
        
        # Dual-write: Update JSON file for boot sequence
        await _update_json_config_from_db(bridge_id)
        
        logger.info(f"Updated bridge config: timer={timer}, targets={len(targets) if targets else len(sensors)} assignments")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Bridge configuration updated",
            "config": {
                "timer": timer,
                "sensors": sensors,
                "targets": targets
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to update bridge config: {e}")
        return JSONResponse(
            content={"error": f"Failed to update bridge config: {str(e)}"},
            status_code=500
        )

@app.put("/api/admin/bridge/target/{target_number}/assign")
async def assign_device_to_target(target_number: str, request: dict):
    """Assign a device to a specific target (for drag-and-drop)"""
    try:
        device_address = request.get("device_address")
        bridge_id = request.get("bridge_id", 1)  # Default to bridge 1
        
        if not device_address:
            return JSONResponse(
                content={"error": "device_address is required"},
                status_code=400
            )
        
        # Handle timer assignment special case
        if target_number == "timer":
            is_timer_assignment = True
            target_num = None
        else:
            try:
                target_num = int(target_number)
                if target_num < 1 or target_num > 10:  # Reasonable limit
                    return JSONResponse(
                        content={"error": "target_number must be between 1 and 10"},
                        status_code=400
                    )
                is_timer_assignment = False
            except ValueError:
                return JSONResponse(
                    content={"error": "target_number must be an integer or 'timer'"},
                    status_code=400
                )
        
        with get_db_connection() as conn:
            # Get device label from device pool
            cursor = conn.execute(
                "SELECT label, device_type FROM device_pool WHERE hw_addr = ?",
                (device_address,)
            )
            device_row = cursor.fetchone()
            
            if not device_row:
                return JSONResponse(
                    content={"error": f"Device {device_address} not found in device pool"},
                    status_code=404
                )
            
            device_label = device_row['label']
            device_type = device_row['device_type']
            
            # Handle timer assignment (special case)
            if is_timer_assignment or device_type == 'timer':
                # Update bridge configuration with timer
                conn.execute("""
                    INSERT OR REPLACE INTO bridge_configurations 
                    (bridge_id, stage_config_id, timer_address)
                    VALUES (?, COALESCE((SELECT stage_config_id FROM bridge_configurations WHERE bridge_id = ?), 1), ?)
                """, (bridge_id, bridge_id, device_address))
                
                conn.commit()
                await _update_json_config_from_db(bridge_id)
                
                return JSONResponse({
                    "status": "success",
                    "message": f"{device_label} assigned as bridge timer",
                    "assignment": {
                        "device_address": device_address,
                        "device_label": device_label,
                        "target": "timer",
                        "bridge_id": bridge_id
                    }
                })
            else:
                # Handle sensor assignment to target
                if target_num is None:
                    return JSONResponse(
                        content={"error": "target_number required for sensor assignment"},
                        status_code=400
                    )
                
                # Remove any existing assignment for this sensor (ensure 1:1 mapping)
                conn.execute(
                    "DELETE FROM bridge_target_assignments WHERE bridge_id = ? AND sensor_address = ?",
                    (bridge_id, device_address)
                )
                
                # Remove any existing sensor from this target
                conn.execute(
                    "DELETE FROM bridge_target_assignments WHERE bridge_id = ? AND target_number = ?",
                    (bridge_id, target_num)
                )
                
                # Add new assignment
                conn.execute("""
                    INSERT INTO bridge_target_assignments 
                    (bridge_id, target_number, sensor_address, sensor_label)
                    VALUES (?, ?, ?, ?)
                """, (bridge_id, target_num, device_address, device_label))
            
                conn.commit()
                await _update_json_config_from_db(bridge_id)
                
                return JSONResponse(content={
                    "status": "success",
                    "message": f"{device_label} assigned to Target {target_num}",
                    "assignment": {
                        "device_address": device_address,
                        "device_label": device_label,
                        "device_type": device_type,
                        "target_number": target_num,
                        "bridge_id": bridge_id
                    }
                })
        
    except Exception as e:
        logger.error(f"Failed to assign device: {e}")
        return JSONResponse(
            content={"error": f"Failed to assign device: {str(e)}"},
            status_code=500
        )

@app.delete("/api/admin/bridge/target/{target_number}/unassign")
async def unassign_target(target_number: int, bridge_id: int = 1):
    """Remove sensor assignment from a target"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT sensor_address, sensor_label FROM bridge_target_assignments WHERE bridge_id = ? AND target_number = ?",
                (bridge_id, target_number)
            )
            assignment = cursor.fetchone()
            
            if not assignment:
                return JSONResponse(
                    content={"error": f"No assignment found for Target {target_number}"},
                    status_code=404
                )
            
            # Remove the assignment
            conn.execute(
                "DELETE FROM bridge_target_assignments WHERE bridge_id = ? AND target_number = ?",
                (bridge_id, target_number)
            )
            conn.commit()
        
        # Update JSON config
        await _update_json_config_from_db(bridge_id)
        
        logger.info(f"Unassigned {assignment['sensor_label']} from Target {target_number}")
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Target {target_number} unassigned",
            "unassigned": {
                "device_address": assignment['sensor_address'],
                "device_label": assignment['sensor_label'],
                "target_number": target_number
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to unassign target: {e}")
        return JSONResponse(
            content={"error": f"Failed to unassign target: {str(e)}"},
            status_code=500
        )

@app.delete("/api/admin/bridge/timer/unassign")
async def unassign_timer(request: dict):
    """Remove timer assignment from bridge"""
    try:
        bridge_id = request.get("bridge_id", 1)
        
        with get_db_connection() as conn:
            # Get current timer assignment
            cursor = conn.execute(
                "SELECT timer_address FROM bridge_configurations WHERE bridge_id = ?",
                (bridge_id,)
            )
            config = cursor.fetchone()
            
            if not config or not config['timer_address']:
                return JSONResponse(
                    content={"message": "No timer currently assigned"},
                    status_code=200
                )
            
            timer_address = config['timer_address']
            
            # Clear timer assignment
            conn.execute(
                "UPDATE bridge_configurations SET timer_address = NULL WHERE bridge_id = ?",
                (bridge_id,)
            )
            conn.commit()
        
        # Update JSON config
        await _update_json_config_from_db(bridge_id)
        
        logger.info(f"Unassigned timer {timer_address} from bridge {bridge_id}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Timer unassigned from bridge",
            "unassigned_timer": timer_address
        })
        
    except Exception as e:
        logger.error(f"Failed to unassign timer: {e}")
        return JSONResponse(
            content={"error": f"Failed to unassign timer: {str(e)}"},
            status_code=500
        )

@app.delete("/api/admin/bridge/sensors/unassign_all")
async def unassign_all_sensors(request: dict):
    """Remove all sensor assignments from bridge"""
    try:
        bridge_id = request.get("bridge_id", 1)
        
        with get_db_connection() as conn:
            # Get current sensor assignments
            cursor = conn.execute(
                "SELECT sensor_address, sensor_label, target_number FROM bridge_target_assignments WHERE bridge_id = ?",
                (bridge_id,)
            )
            assignments = cursor.fetchall()
            
            if not assignments:
                return JSONResponse(
                    content={"message": "No sensors currently assigned"},
                    status_code=200
                )
            
            # Clear all sensor assignments
            conn.execute(
                "DELETE FROM bridge_target_assignments WHERE bridge_id = ?",
                (bridge_id,)
            )
            conn.commit()
        
        # Update JSON config
        await _update_json_config_from_db(bridge_id)
        
        unassigned_list = [
            {"address": a['sensor_address'], "label": a['sensor_label'], "target": a['target_number']} 
            for a in assignments
        ]
        
        logger.info(f"Unassigned {len(assignments)} sensors from bridge {bridge_id}")
        
        return JSONResponse(content={
            "status": "success",
            "message": f"All {len(assignments)} sensors unassigned from bridge",
            "unassigned_sensors": unassigned_list
        })
        
    except Exception as e:
        logger.error(f"Failed to unassign all sensors: {e}")
        return JSONResponse(
            content={"error": f"Failed to unassign all sensors: {str(e)}"},
            status_code=500
        )

@app.put("/api/admin/bridge/stage")
async def change_bridge_stage(request: dict):
    """Change bridge stage with optional assignment preservation"""
    try:
        stage_config_id = request.get("stage_config_id")
        bridge_id = request.get("bridge_id", 1)
        preserve_assignments = request.get("preserve_assignments", False)  # New parameter
        
        if not stage_config_id:
            return JSONResponse(
                content={"error": "stage_config_id is required"},
                status_code=400
            )
        
        with get_db_connection() as conn:
            # Verify stage exists
            cursor = conn.execute(
                "SELECT name FROM stage_configs WHERE id = ?",
                (stage_config_id,)
            )
            stage = cursor.fetchone()
            
            if not stage:
                return JSONResponse(
                    content={"error": f"Stage config {stage_config_id} not found"},
                    status_code=404
                )
            
            # Conditionally clear assignments based on parameter
            if not preserve_assignments:
                conn.execute("DELETE FROM bridge_target_assignments WHERE bridge_id = ?", (bridge_id,))
                # Update bridge configuration with new stage and clear timer
                conn.execute("""
                    INSERT OR REPLACE INTO bridge_configurations 
                    (bridge_id, stage_config_id, timer_address)
                    VALUES (?, ?, NULL)
                """, (bridge_id, stage_config_id))
                log_msg = f"Changed bridge {bridge_id} to stage {stage_config_id} ({stage['name']}) and cleared all assignments"
            else:
                # Just update the stage, keep existing timer and assignments
                conn.execute("""
                    UPDATE bridge_configurations 
                    SET stage_config_id = ?
                    WHERE bridge_id = ?
                """, (stage_config_id, bridge_id))
                log_msg = f"Changed bridge {bridge_id} to stage {stage_config_id} ({stage['name']}) and preserved assignments"
            
            conn.commit()
        
        # Update JSON config 
        await _update_json_config_from_db(bridge_id)
        
        logger.info(log_msg)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Bridge stage changed to {stage['name']}" + ("" if preserve_assignments else " - all assignments cleared"),
            "stage": {
                "stage_config_id": stage_config_id,
                "stage_name": stage['name']
            },
            "assignments_preserved": preserve_assignments
        })
        
    except Exception as e:
        logger.error(f"Failed to change bridge stage: {e}")
        return JSONResponse(
            content={"error": f"Failed to change bridge stage: {str(e)}"},
            status_code=500
        )

@app.put("/api/admin/node")
def update_node_info(request: dict):
    """Update node configuration"""
    try:
        # For now, just return success
        # In full implementation, this would update hostname, timezone, etc.
        return JSONResponse(content={"status": "success", "message": "Node update not yet implemented"})
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to update node: {str(e)}"},
            status_code=500
        )

# ===== STAGE MANAGEMENT ENDPOINTS =====

@app.get("/api/admin/leagues")
def get_leagues():
    """Get all available leagues"""
    try:
        from .database.models import League
        from .database.session import get_db_session
        
        session = get_db_session()
        leagues = session.query(League).all()
        session.close()
        
        return JSONResponse(content={
            "leagues": [
                {
                    "id": league.id,
                    "name": league.name,
                    "abbreviation": league.abbreviation,
                    "description": league.description
                }
                for league in leagues
            ]
        })
    except Exception as e:
        logger.error(f"Failed to get leagues: {e}")
        return JSONResponse(
            content={"error": f"Failed to get leagues: {str(e)}"},
            status_code=500
        )

@app.get("/api/admin/leagues/{league_id}/stages")
def get_league_stages(league_id: int):
    """Get all stage configurations for a league"""
    try:
        from .database.models import League, StageConfig, TargetConfig, Sensor
        from .database.database import get_database_session
        from sqlalchemy.orm import joinedload
        
        with get_database_session() as session:
            league = session.query(League).filter_by(id=league_id).first()
            
            if not league:
                return JSONResponse(
                    content={"error": "League not found"},
                    status_code=404
                )
            
            stages = session.query(StageConfig).options(
                joinedload(StageConfig.target_configs)
            ).filter_by(league_id=league_id).all()
            
            # Get all sensors assigned to target configs
            assigned_sensors = session.query(Sensor).filter(
                Sensor.target_config_id.isnot(None)
            ).all()
            sensor_by_target_config = {sensor.target_config_id: sensor for sensor in assigned_sensors}
            
            return JSONResponse(content={
                "league": {
                    "id": league.id,
                    "name": league.name,
                    "abbreviation": league.abbreviation
                },
                "stages": [
                    {
                        "id": stage.id,
                        "name": stage.name,
                        "description": stage.description,
                        "target_count": len(stage.target_configs),
                        "targets": [
                            {
                                "id": target.id,
                                "target_number": target.target_number,
                                "shape": target.shape,
                                "type": target.type,
                                "category": target.category,
                                "distance_feet": target.distance_feet,
                                "offset_feet": target.offset_feet,
                                "height_feet": target.height_feet,
                                "sensor": {
                                    "id": sensor_by_target_config[target.id].id,
                                    "hw_addr": sensor_by_target_config[target.id].hw_addr,
                                    "label": sensor_by_target_config[target.id].label,
                                    "last_seen": sensor_by_target_config[target.id].last_seen.isoformat() if sensor_by_target_config[target.id].last_seen else None,
                                    "battery": sensor_by_target_config[target.id].battery,
                                    "rssi": sensor_by_target_config[target.id].rssi
                                } if target.id in sensor_by_target_config else None
                            }
                            for target in sorted(stage.target_configs, key=lambda t: t.target_number)
                        ]
                    }
                    for stage in stages
                ]
            })
    except Exception as e:
        logger.error(f"Failed to get league stages: {e}")
        return JSONResponse(
            content={"error": f"Failed to get league stages: {str(e)}"},
            status_code=500
        )

@app.get("/api/admin/stages/{stage_id}")
def get_stage_details(stage_id: int):
    """Get detailed stage configuration including target layout"""
    try:
        from .database.models import StageConfig, TargetConfig, Sensor
        from .database.database import get_database_session
        from sqlalchemy.orm import joinedload
        
        with get_database_session() as session:
            stage = session.query(StageConfig).options(
                joinedload(StageConfig.target_configs),
                joinedload(StageConfig.league)
            ).filter_by(id=stage_id).first()
            
            if not stage:
                return JSONResponse(
                    content={"error": "Stage not found"},
                    status_code=404
                )
            
            # Get target config IDs for this stage
            target_config_ids = [target.id for target in stage.target_configs]
            
            # Get sensors assigned to any target in this stage
            assigned_sensors = session.query(Sensor).filter(
                Sensor.target_config_id.in_(target_config_ids)
            ).all()
            sensor_assignments = {sensor.target_config_id: sensor for sensor in assigned_sensors}
            
            return JSONResponse(content={
            "stage": {
                "id": stage.id,
                "name": stage.name,
                "description": stage.description,
                "league": {
                    "id": stage.league.id,
                    "name": stage.league.name,
                    "abbreviation": stage.league.abbreviation
                },
                "targets": [
                    {
                        "id": target.id,
                        "target_number": target.target_number,
                        "shape": target.shape,
                        "type": target.type,
                        "category": target.category,
                        "distance_feet": target.distance_feet,
                        "offset_feet": target.offset_feet,
                        "height_feet": target.height_feet,
                        "sensor": {
                            "id": sensor_assignments[target.id].id,
                            "hw_addr": sensor_assignments[target.id].hw_addr,
                            "label": sensor_assignments[target.id].label,
                            "last_seen": sensor_assignments[target.id].last_seen.isoformat() if sensor_assignments[target.id].last_seen else None,
                            "battery": sensor_assignments[target.id].battery,
                            "rssi": sensor_assignments[target.id].rssi
                        } if target.id in sensor_assignments else None
                    }
                    for target in sorted(stage.target_configs, key=lambda t: t.target_number)
                ]
            }
        })
    except Exception as e:
        logger.error(f"Failed to get stage details: {e}")
        return JSONResponse(
            content={"error": f"Failed to get stage details: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/stages/{stage_id}/assign_sensor")
def assign_sensor_to_target(stage_id: int, request: dict):
    """
    [DEPRECATED] Assign a sensor to a target within a stage
    
    This endpoint is deprecated. Use the Device Pool system instead:
    - POST /api/admin/pool/sessions to create a session
    - POST /api/admin/pool/sessions/{session_id}/lease to lease devices
    """
    logger.warning("DEPRECATED: /api/admin/stages/{stage_id}/assign_sensor endpoint called. Use Device Pool system instead.")
    """Assign a sensor to a specific target in a stage"""
    try:
        from .database.models import StageConfig, TargetConfig, Sensor
        from .database.database import get_database_session
        
        sensor_id = request.get("sensor_id")
        target_number = request.get("target_number")
        
        if not sensor_id or not target_number:
            return JSONResponse(
                content={"error": "sensor_id and target_number are required"},
                status_code=400
            )
        
        with get_database_session() as session:
            # Verify stage exists
            stage = session.query(StageConfig).filter_by(id=stage_id).first()
            if not stage:
                return JSONResponse(
                    content={"error": "Stage not found"},
                    status_code=404
                )
            
            # Find the target config
            target_config = session.query(TargetConfig).filter_by(
                stage_config_id=stage_id,
                target_number=target_number
            ).first()
            
            if not target_config:
                return JSONResponse(
                    content={"error": f"Target {target_number} not found in stage"},
                    status_code=404
                )
            
            # Find the sensor
            sensor = session.query(Sensor).filter_by(id=sensor_id).first()
            if not sensor:
                return JSONResponse(
                    content={"error": "Sensor not found"},
                    status_code=404
                )
            
            # Clear any existing assignment for this sensor
            sensor.target_config_id = None
            
            # Assign sensor to target
            sensor.target_config_id = target_config.id
            
            # Store data we need for response before session closes
            sensor_label = sensor.label
            stage_name = stage.name
            target_type = target_config.type
            target_category = target_config.category
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Sensor {sensor_label} assigned to {stage_name} Target {target_number}",
            "assignment": {
                "sensor_id": sensor_id,
                "sensor_label": sensor_label,
                "stage_name": stage_name,
                "target_number": target_number,
                "target_type": target_type,
                "target_category": target_category
            }
        })
    except Exception as e:
        logger.error(f"Failed to assign sensor: {e}")
        return JSONResponse(
            content={"error": f"Failed to assign sensor: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/stages/{stage_id}/unassign_sensor")
def unassign_sensor_from_target(stage_id: int, request: dict):
    """
    [DEPRECATED] Remove sensor assignment from a target within a stage
    
    This endpoint is deprecated. Use the Device Pool system instead:
    - POST /api/admin/pool/sessions/{session_id}/release/{device_id}
    """
    logger.warning("DEPRECATED: /api/admin/stages/{stage_id}/unassign_sensor endpoint called. Use Device Pool system instead.")
    """Remove sensor assignment from a target"""
    try:
        from .database.models import TargetConfig, Sensor
        from .database.database import get_database_session
        
        target_number = request.get("target_number")
        
        if not target_number:
            return JSONResponse(
                content={"error": "target_number is required"},
                status_code=400
            )
        
        with get_database_session() as session:
            # Find the target config
            target_config = session.query(TargetConfig).filter_by(
                stage_config_id=stage_id,
                target_number=target_number
            ).first()
            
            if not target_config:
                return JSONResponse(
                    content={"error": f"Target {target_number} not found in stage"},
                    status_code=404
                )
            
            # Find assigned sensor
            sensor = session.query(Sensor).filter_by(target_config_id=target_config.id).first()
            
            if sensor:
                sensor.target_config_id = None
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Sensor unassigned from Target {target_number}",
            "target_number": target_number
        })
    except Exception as e:
        logger.error(f"Failed to unassign sensor: {e}")
        return JSONResponse(
            content={"error": f"Failed to unassign sensor: {str(e)}"},
            status_code=500
        )

# ============================================================================
# Bridge Configuration Endpoints
# ============================================================================

@app.get("/api/admin/bridge")
def get_bridge_config():
    """Get current Bridge configuration"""
    try:
        from .database.models import Bridge
        from .database.database import get_database_session
        
        with get_database_session() as session:
            # Get the current Bridge (assume single Bridge per instance for now)
            bridge = session.query(Bridge).first()
            
            if not bridge:
                # Create default Bridge if none exists
                bridge = Bridge(
                    name="Default Bridge",
                    bridge_id="bridge-001",
                    match_id=None,
                    match_name=None
                )
                session.add(bridge)
                session.commit()
                session.refresh(bridge)
            
            return JSONResponse(content={
                "bridge": {
                    "id": bridge.id,
                    "name": bridge.name,
                    "bridge_id": bridge.bridge_id,
                    "current_stage_id": bridge.current_stage_id,
                    "current_stage_name": bridge.current_stage.name if bridge.current_stage else None,
                    "match_id": bridge.match_id,
                    "match_name": bridge.match_name,
                    "created_at": bridge.created_at.isoformat(),
                    "updated_at": bridge.updated_at.isoformat()
                }
            })
    except Exception as e:
        logger.error(f"Failed to get Bridge config: {e}")
        return JSONResponse(
            content={"error": f"Failed to get Bridge config: {str(e)}"},
            status_code=500
        )

@app.put("/api/admin/bridge")
def update_bridge_config(request: dict):
    """Update Bridge configuration"""
    try:
        from .database.models import Bridge
        from .database.database import get_database_session
        
        name = request.get("name")
        bridge_id = request.get("bridge_id")
        match_id = request.get("match_id")
        match_name = request.get("match_name")
        
        if not name or not bridge_id:
            return JSONResponse(
                content={"error": "name and bridge_id are required"},
                status_code=400
            )
        
        with get_database_session() as session:
            # Get the current Bridge
            bridge = session.query(Bridge).first()
            
            if not bridge:
                # Create new Bridge
                bridge = Bridge(
                    name=name,
                    bridge_id=bridge_id,
                    match_id=match_id,
                    match_name=match_name
                )
                session.add(bridge)
            else:
                # Update existing Bridge
                bridge.name = name
                bridge.bridge_id = bridge_id
                bridge.match_id = match_id
                bridge.match_name = match_name
            
            session.commit()
            session.refresh(bridge)
            
            return JSONResponse(content={
                "status": "success",
                "message": "Bridge configuration updated",
                "bridge": {
                    "id": bridge.id,
                    "name": bridge.name,
                    "bridge_id": bridge.bridge_id,
                    "current_stage_id": bridge.current_stage_id,
                    "match_id": bridge.match_id,
                    "match_name": bridge.match_name
                }
            })
    except Exception as e:
        logger.error(f"Failed to update Bridge config: {e}")
        return JSONResponse(
            content={"error": f"Failed to update Bridge config: {str(e)}"},
            status_code=500
        )

@app.post("/api/admin/bridge/assign_stage")
def assign_bridge_to_stage(request: dict):
    """Assign this Bridge to a specific stage"""
    try:
        from .database.models import Bridge, StageConfig, Sensor
        from .database.database import get_database_session
        
        stage_id = request.get("stage_id")
        
        if not stage_id:
            return JSONResponse(
                content={"error": "stage_id is required"},
                status_code=400
            )
        
        with get_database_session() as session:
            # Get the current Bridge
            bridge = session.query(Bridge).first()
            if not bridge:
                return JSONResponse(
                    content={"error": "Bridge not configured"},
                    status_code=404
                )
            
            # Verify stage exists
            stage = session.query(StageConfig).filter_by(id=stage_id).first()
            if not stage:
                return JSONResponse(
                    content={"error": "Stage not found"},
                    status_code=404
                )
            
            # Update Bridge assignment
            bridge.current_stage_id = stage_id
            
            # Update all sensors assigned to targets in this stage to belong to this Bridge
            target_ids = [target.id for target in stage.target_configs]
            if target_ids:
                session.query(Sensor).filter(
                    Sensor.target_config_id.in_(target_ids)
                ).update({"bridge_id": bridge.id}, synchronize_session=False)
            
            session.commit()
            
            return JSONResponse(content={
                "status": "success",
                "message": f"Bridge '{bridge.name}' assigned to stage '{stage.name}'",
                "assignment": {
                    "bridge_id": bridge.id,
                    "bridge_name": bridge.name,
                    "stage_id": stage.id,
                    "stage_name": stage.name,
                    "sensors_updated": len(target_ids) if target_ids else 0
                }
            })
    except Exception as e:
        logger.error(f"Failed to assign Bridge to stage: {e}")
        return JSONResponse(
            content={"error": f"Failed to assign Bridge to stage: {str(e)}"},
            status_code=500
        )

@app.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial log batch
        logs = fetch_logs(50)
        await websocket.send_json({"type": "log_batch", "logs": logs})
        
        while True:
            # Wait for client messages
            data = await websocket.receive_json()
            if data.get("type") == "request_logs":
                limit = data.get("limit", 50)
                logs = fetch_logs(limit)
                await websocket.send_json({"type": "log_batch", "logs": logs})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint for real-time event streaming"""
    from src.impact_bridge.event_streamer import event_streamer
    
    try:
        await event_streamer.connect(websocket)
        
        # Auto-subscribe to common channels
        await event_streamer.subscribe_client(websocket, [
            'status', 'sensor_events', 'timer_events', 'health_status'
        ])
        
        # Send initial status
        await event_streamer.send_status_update(websocket)
        
        while True:
            # Wait for client messages
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                await event_streamer.handle_client_message(websocket, data)
            except json.JSONDecodeError:
                await event_streamer.send_to_client(websocket, {
                    'type': 'error',
                    'message': 'Invalid JSON message'
                })
                
    except WebSocketDisconnect:
        event_streamer.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket live endpoint error: {e}")
        event_streamer.disconnect(websocket)

def fetch_logs(limit: int = 100) -> List[Dict[str, Any]]:
    all_logs = []
    for log_dir in LOG_DIRS:
        if not os.path.exists(log_dir):
            continue
        log_patterns = [
            os.path.join(log_dir, '*.log'),
            os.path.join(log_dir, '*.ndjson'),
            os.path.join(log_dir, '*.csv')
        ]
        for pattern in log_patterns:
            log_files = glob.glob(pattern)
            log_files.sort(key=os.path.getmtime, reverse=True)
            for log_file in log_files[:5]:
                try:
                    entries = parse_log_file(log_file, limit)
                    all_logs.extend(entries)
                    if len(all_logs) >= limit:
                        break
                except Exception as e:
                    print(f"⚠️ Error parsing {log_file}: {e}")
                    continue
            if len(all_logs) >= limit:
                break
        if len(all_logs) >= limit:
            break
    all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return all_logs[:limit]

def parse_log_file(file_path: str, max_entries: int = 100) -> List[Dict[str, Any]]:
    entries = []
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in reversed(lines[-max_entries:]):
            line = line.strip()
            if not line:
                continue
            entry = parse_log_entry(line, file_name)
            if entry:
                entries.append(entry)
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
    return entries

def parse_log_entry(line: str, source_file: str) -> Dict[str, Any]:
    try:
        if line.startswith('{'):
            try:
                data = json.loads(line)
                return {
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'level': data.get('level', 'INFO'),
                    'source': data.get('source', source_file),
                    'message': data.get('message', line),
                    'raw': line
                }
            except json.JSONDecodeError:
                pass
        if line.startswith('[') and ']' in line:
            try:
                end_bracket = line.find(']')
                timestamp_str = line[1:end_bracket]
                remainder = line[end_bracket + 1:].strip()
                if ':' in remainder:
                    level_part, message = remainder.split(':', 1)
                    level = level_part.strip()
                    message = message.strip()
                else:
                    level = 'INFO'
                    message = remainder
                source = source_file
                if 'FixedBridge' in message:
                    source = 'FixedBridge'
                elif 'bleak' in message:
                    source = 'bleak.backends.bluezdbus.manager'
                elif 'BT50' in message:
                    source = 'BT50Sensor'
                return {
                    'timestamp': timestamp_str,
                    'level': level,
                    'source': source,
                    'message': message,
                    'raw': line
                }
            except (ValueError, IndexError):
                pass
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'source': source_file,
            'message': line,
            'raw': line
        }
    except Exception as e:
        print(f"⚠️ Error parsing log line: {e}")
        return None

@app.get("/api/health/detailed")
def get_detailed_health():
    """Get comprehensive health status including system monitoring"""
    try:
        from src.impact_bridge.system_monitor import SystemMonitor
        monitor = SystemMonitor()
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'version': '2.0.0',
            'system': monitor.get_system_stats(),
            'services': monitor.get_service_health(),
            'ble': monitor.get_ble_quality(),
            'network_interfaces': monitor.get_network_interfaces()
        }
        
        # Determine overall health status
        cpu_usage = health_data['system']['cpu']['usage_percent']
        memory_usage = health_data['system']['memory']['percent']
        disk_usage = health_data['system']['disk']['percent']
        
        if cpu_usage > 90 or memory_usage > 95 or disk_usage > 95:
            health_data['status'] = 'critical'
        elif cpu_usage > 70 or memory_usage > 85 or disk_usage > 85:
            health_data['status'] = 'warning'
        
        return JSONResponse(content=health_data)
    except Exception as e:
        return JSONResponse(
            content={
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': f'Health check failed: {str(e)}'
            },
            status_code=500
        )

@app.get("/api/health/detailed")
def get_detailed_health():
    """Get comprehensive health status including system monitoring"""
    try:
        from src.impact_bridge.system_monitor import SystemMonitor
        monitor = SystemMonitor()
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'version': '2.0.0',
            'system': monitor.get_system_stats(),
            'services': monitor.get_service_health(),
            'ble': monitor.get_ble_quality(),
            'network_interfaces': monitor.get_network_interfaces()
        }
        
        # Determine overall health status
        cpu_usage = health_data['system']['cpu']['usage_percent']
        memory_usage = health_data['system']['memory']['percent']
        disk_usage = health_data['system']['disk']['percent']
        
        if cpu_usage > 90 or memory_usage > 95 or disk_usage > 95:
            health_data['status'] = 'critical'
        elif cpu_usage > 70 or memory_usage > 85 or disk_usage > 85:
            health_data['status'] = 'warning'
        
        return JSONResponse(content=health_data)
    except Exception as e:
        return JSONResponse(
            content={
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': f'Health check failed: {str(e)}'
            },
            status_code=500
        )

# Setup authentication routes
try:
    from src.impact_bridge.auth.api import create_auth_routes
    # Note: FastAPI auth integration will need adaptation from Flask routes
    print("✅ Authentication routes available (adaptation needed)")
except ImportError as e:
    print(f"⚠️  Authentication not available: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize database
        try:
            from pathlib import Path
            from src.impact_bridge.config import DatabaseConfig
            from src.impact_bridge.database import init_database
            
            # Use absolute path to database in project db/ directory
            project_root = Path(__file__).parent.parent.parent
            
            config = DatabaseConfig()
            config.dir = str(project_root / "db")
            config.file = "leadville.db"
            
            init_database(config)
            logger.info(f"Database initialized at {config.path}")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
        
        from src.impact_bridge.event_streamer import event_streamer
        await event_streamer.start_periodic_tasks()
        
        # Try to setup MQTT integration
        try:
            from src.impact_bridge.mqtt_client import LeadVilleMQTT
            mqtt_client = LeadVilleMQTT()
            if await mqtt_client.connect():
                event_streamer.setup_mqtt_integration(mqtt_client)
                logger.info("MQTT integration enabled for event streaming")
            else:
                logger.warning("MQTT connection failed, event streaming will work without MQTT")
        except Exception as e:
            logger.warning(f"MQTT setup failed: {e}. Event streaming will work without MQTT")
            
        logger.info("FastAPI startup complete with database and event streaming")
    except Exception as e:
        logger.error(f"Startup error: {e}")

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 LeadVille FastAPI Server Starting")
    print("=" * 60)
    print(f"📊 Project: LeadVille Impact Bridge (FastAPI)")
    print(f"🌐 Host: 0.0.0.0:8001")
    print(f"📁 Log directories:")
    for log_dir in LOG_DIRS:
        exists = "✅" if os.path.exists(log_dir) else "❌"
        print(f"   {exists} {log_dir}")
    print()
    print("🌐 API Endpoints:")
    print(f"   📊 Health: http://0.0.0.0:8001/api/health")
    print(f"   📝 Logs: http://0.0.0.0:8001/api/logs")
    print(f"   🔌 WebSocket Logs: ws://0.0.0.0:8001/ws/logs")
    print(f"   ⚡ WebSocket Live: ws://0.0.0.0:8001/ws/live")
    print(f"   📚 Docs: http://0.0.0.0:8001/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
