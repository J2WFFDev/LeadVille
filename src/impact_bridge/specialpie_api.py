"""
SpecialPie Timer API Endpoints
Provides REST API for managing SpecialPie shot timers
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .database.session import get_db_session
from .database.models import Sensor
from .specialpie_handler import specialpie_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/specialpie", tags=["SpecialPie Timers"])

@router.get("/timers")
async def get_specialpie_timers(db: Session = Depends(get_db_session)):
    """Get all paired SpecialPie timers"""
    try:
        # Get SpecialPie timers from database
        timers = db.query(Sensor).filter(
            Sensor.calib.contains({"device_type": "shot_timer"})
        ).all()
        
        # Get handler status for each timer
        timer_data = []
        for timer in timers:
            handler = specialpie_manager.get_handler(timer.hw_addr)
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
                "current_shots": handler_status['current_shots'] if handler_status else 0,
                "last_shot": handler_status['last_shot'] if handler_status else None
            })
        
        return {
            "timers": timer_data,
            "total_count": len(timer_data),
            "connected_count": sum(1 for t in timer_data if t['connected'])
        }
        
    except Exception as e:
        logger.error(f"Error getting SpecialPie timers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/connect")
async def connect_timer(hw_addr: str):
    """Connect to a SpecialPie timer"""
    try:
        handler = specialpie_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found in manager")
        
        success = await handler.connect()
        
        return {
            "hw_addr": hw_addr,
            "connected": success,
            "message": "Connected successfully" if success else "Connection failed"
        }
        
    except Exception as e:
        logger.error(f"Error connecting to SpecialPie timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/disconnect")
async def disconnect_timer(hw_addr: str):
    """Disconnect from a SpecialPie timer"""
    try:
        handler = specialpie_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found in manager")
        
        await handler.disconnect()
        
        return {
            "hw_addr": hw_addr,
            "connected": False,
            "message": "Disconnected successfully"
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting SpecialPie timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/start_monitoring")
async def start_monitoring(hw_addr: str):
    """Start monitoring shots from a SpecialPie timer"""
    try:
        handler = specialpie_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found in manager")
        
        if not handler.is_connected:
            raise HTTPException(status_code=400, detail=f"Timer {hw_addr} is not connected")
        
        await handler.start_monitoring()
        
        return {
            "hw_addr": hw_addr,
            "monitoring": True,
            "message": "Shot monitoring started"
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring for SpecialPie timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timers/{hw_addr}/stop_monitoring")
async def stop_monitoring(hw_addr: str):
    """Stop monitoring shots from a SpecialPie timer"""
    try:
        handler = specialpie_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found in manager")
        
        await handler.stop_monitoring()
        
        return {
            "hw_addr": hw_addr,
            "monitoring": False,
            "message": "Shot monitoring stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping monitoring for SpecialPie timer {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timers/{hw_addr}/status")
async def get_timer_status(hw_addr: str):
    """Get detailed status of a SpecialPie timer"""
    try:
        handler = specialpie_manager.get_handler(hw_addr)
        if not handler:
            raise HTTPException(status_code=404, detail=f"Timer {hw_addr} not found in manager")
        
        status = handler.get_status()
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting SpecialPie timer status {hw_addr}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_manager_status():
    """Get overall SpecialPie manager status"""
    try:
        status = specialpie_manager.get_status()
        return {
            "manager_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting SpecialPie manager status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Shot event callback for database logging
async def log_shot_event(shot_event: Dict[str, Any]):
    """Callback to log shot events to database"""
    try:
        # This would typically log to TimerEvent table
        logger.info(f"Shot Event: {shot_event}")
        
        # TODO: Implement database logging to TimerEvent table
        # with get_database_session() as session:
        #     timer_event = TimerEvent(
        #         ts_utc=shot_event['timestamp'],
        #         type='SHOT',
        #         raw=str(shot_event['raw_data'])
        #     )
        #     session.add(timer_event)
        #     session.commit()
        
    except Exception as e:
        logger.error(f"Error logging shot event: {e}")

# String event callback for database logging
async def log_string_event(event_type: str, string_event: Dict[str, Any]):
    """Callback to log string start/stop events to database"""
    try:
        logger.info(f"String Event ({event_type}): {string_event}")
        
        # TODO: Implement database logging to TimerEvent table
        # with get_database_session() as session:
        #     timer_event = TimerEvent(
        #         ts_utc=string_event['timestamp'],
        #         type=event_type.upper(),
        #         raw=str(string_event['raw_data'])
        #     )
        #     session.add(timer_event)
        #     session.commit()
        
    except Exception as e:
        logger.error(f"Error logging string event: {e}")

# Register callbacks on module import
specialpie_manager.add_shot_callback(log_shot_event)
specialpie_manager.add_string_callback(log_string_event)