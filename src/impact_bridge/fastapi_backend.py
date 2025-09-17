"""
LeadVille FastAPI Backend (initial scaffold)
Mirrors Flask API structure for health and logs endpoints, CORS, and log parsing.
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    """Assign a device to a target"""
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
    """Remove device assignment from target"""
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
    """Get current device-to-target assignments"""
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
def reset_device_discovery():
    """Reset device discovery state (clear stuck scanning flag)"""
    try:
        from src.impact_bridge.device_manager import device_manager
        device_manager.scanning = False
        device_manager.discovered_devices.clear()
        logger.info("Device discovery state reset")
        return JSONResponse(content={
            "status": "reset",
            "message": "Device discovery state cleared"
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
            
            # Use absolute path to database relative to project root
            project_root = Path(__file__).parent.parent.parent
            db_dir = project_root / "db"
            db_dir.mkdir(exist_ok=True)  # Ensure db directory exists
            
            config = DatabaseConfig()
            config.dir = str(db_dir)
            config.file = "bridge.db"
            
            init_database(config)
            logger.info(f"Database initialized at {db_dir / config.file}")
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
