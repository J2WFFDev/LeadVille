"""
AMG Commander Timer API Endpoints
Enhanced API for managing AMG Commander timers with sensitivity control,
battery monitoring, and remote start capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .database.session import get_db_session
from .database.models import Sensor
from .amg_commander_handler import amg_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/amg", tags=["AMG Commander Timers"])

@router.get("/timers")
async def get_amg_timers(db: Session = Depends(get_db_session)):
    """Get all paired AMG Commander timers"""
    try:
        # Get AMG timers from database (those with AMG vendor or type timer)
        timers = db.query(Sensor).filter(
            (Sensor.label.ilike('%AMG%')) | 
            (Sensor.label.ilike('%COMMANDER%')) |
            (Sensor.calib.contains({"vendor": "AMG Labs"}))
        ).all()
        
        timer_data = []
        for timer in timers:
            handler = amg_manager.get_handler(timer.hw_addr)
            handler_status = handler.get_status() if handler else None
            
            timer_data.append({
                "id": timer.id,
                "hw_addr": timer.hw_addr,
                "label": timer.label,
                "battery": timer.battery,
                "rssi": timer.rssi,
                "last_seen": timer.last_seen.isoformat() if timer.last_seen else None,
                "connected": handler_status['connected'] if handler_status else False,
                "monitoring": handler_status['monitoring'] if handler_status else False,
                "sensitivity": handler_status['sensitivity'] if handler_status else 5,
                "battery_level": handler_status['battery_level'] if handler_status else None,
                "signal_strength": handler_status['signal_strength'] if handler_status else None,
                "current_shots": handler_status['current_shots'] if handler_status else 0,
                "last_time": handler_status['last_time'] if handler_status else None,
                "shot_sequence": handler_status['shot_sequence'] if handler_status else []
            })
        
        return {
            "timers": timer_data,
            "total_count": len(timer_data),
            "connected_count": sum(1 for t in timer_data if t['connected'])
        }
        
    except Exception as e:
        logger.error(f"Error getting AMG timers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/connect")
async def connect_timer(hw_addr: str):
    """Connect to an AMG Commander timer"""
    try:
        handler = amg_manager.get_handler(hw_addr)
        if not handler:
            # Auto-add timer to manager if not present
            handler = amg_manager.add_timer(hw_addr)
        
        success = await handler.connect()
        
        return {
            "hw_addr": hw_addr,
            "connected": success,
            "message": "Connected successfully" if success else "Connection failed",
            "battery_level": handler.battery_level,
            "sensitivity": handler.sensitivity
        }
        
    except Exception as e:
        logger.error(f"Error connecting to AMG timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/disconnect")
async def disconnect_timer(hw_addr: str):
    """Disconnect from an AMG Commander timer"""
    try:
        handler = amg_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found in manager")
        
        await handler.disconnect()
        
        return {
            "hw_addr": hw_addr,
            "connected": False,
            "message": "Disconnected successfully"
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting AMG timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/start_monitoring")
async def start_monitoring(hw_addr: str):
    """Start monitoring shots from AMG Commander timer"""
    try:
        handler = amg_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found")
        
        if not handler.is_connected:
            raise HTTPException(status_code=400, detail=f"Timer {hw_addr} is not connected")
        
        await handler.start_monitoring()
        
        return {
            "hw_addr": hw_addr,
            "monitoring": True,
            "message": "Shot monitoring started"
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring for AMG timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/stop_monitoring")
async def stop_monitoring(hw_addr: str):
    """Stop monitoring shots from AMG Commander timer"""
    try:
        handler = amg_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found")
        
        await handler.stop_monitoring()
        
        return {
            "hw_addr": hw_addr,
            "monitoring": False,
            "message": "Shot monitoring stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping monitoring for AMG timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/remote_start")
async def remote_start_timer(hw_addr: str):
    """Remotely start the AMG Commander timer (trigger beep)"""
    try:
        handler = amg_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found")
        
        if not handler.is_connected:
            raise HTTPException(status_code=400, detail=f"Timer {hw_addr} is not connected")
        
        success = await handler.remote_start_timer()
        
        return {
            "hw_addr": hw_addr,
            "command_sent": success,
            "message": "Remote start command sent" if success else "Failed to send command"
        }
        
    except Exception as e:
        logger.error(f"Error remote starting AMG timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/sensitivity/{sensitivity}")
async def set_sensitivity(hw_addr: str, sensitivity: int):
    """Set AMG Commander timer sensitivity (1-10)"""
    try:
        if not 1 <= sensitivity <= 10:
            raise HTTPException(status_code=400, detail="Sensitivity must be between 1 and 10")
        
        handler = amg_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found")
        
        if not handler.is_connected:
            raise HTTPException(status_code=400, detail=f"Timer {hw_addr} is not connected")
        
        success = await handler.set_sensitivity(sensitivity)
        
        return {
            "hw_addr": hw_addr,
            "sensitivity": sensitivity if success else handler.sensitivity,
            "success": success,
            "message": f"Sensitivity set to {sensitivity}" if success else "Failed to set sensitivity"
        }
        
    except Exception as e:
        logger.error(f"Error setting sensitivity for AMG timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/request_data")
async def request_shot_data(hw_addr: str, data_type: str = "shots"):
    """Request data from AMG Commander timer"""
    try:
        handler = amg_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found")
        
        if not handler.is_connected:
            raise HTTPException(status_code=400, detail=f"Timer {hw_addr} is not connected")
        
        if data_type == "shots":
            success = await handler.request_shot_data()
            message = "Shot data requested"
        elif data_type == "screen":
            success = await handler.request_screen_data()
            message = "Screen data requested"
        else:
            raise HTTPException(status_code=400, detail="data_type must be 'shots' or 'screen'")
        
        return {
            "hw_addr": hw_addr,
            "data_type": data_type,
            "success": success,
            "message": message if success else "Failed to request data"
        }
        
    except Exception as e:
        logger.error(f"Error requesting data from AMG timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timers/{hw_addr}/status")
async def get_timer_status(hw_addr: str):
    """Get detailed status of an AMG Commander timer"""
    try:
        handler = amg_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found")
        
        status = handler.get_status()
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting AMG timer status {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_manager_status():
    """Get overall AMG Commander manager status"""
    try:
        status = amg_manager.get_status()
        return {
            "manager_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting AMG manager status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/protocol")
async def get_protocol_info():
    """Get AMG Commander protocol information"""
    return {
        "protocol": "AMG Commander BLE Timer",
        "implementation": {
            "service_uuid": "6e400001-b5a3-f393-e0a9-e50e24dcca9e",
            "write_characteristic": "6e400002-b5a3-f393-e0a9-e50e24dcca9e",
            "notification_characteristic": "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
            "descriptor_uuid": "00002902-0000-1000-8000-00805f9b34fb"
        },
        "commands": {
            "remote_start": "COM START",
            "request_shots": "REQ STRING HEX", 
            "request_screen": "REQ SCREEN HEX",
            "set_sensitivity": "SET SENSITIVITY XX (01-10)"
        },
        "data_format": {
            "shot_timing": "2-byte pairs in centiseconds",
            "command_responses": "Binary protocol with command type identifiers",
            "real_time_shots": "Live shot data with splits and timing"
        },
        "features": [
            "Remote timer start (beep)",
            "Adjustable sensitivity (1-10)",
            "Real-time shot notifications",
            "Shot sequence retrieval",
            "Battery level monitoring",
            "Signal strength monitoring"
        ],
        "source": "Based on Denis Zhadan's AMG Lab Commander Android app analysis",
        "status": "✅ Enhanced implementation ready"
    }