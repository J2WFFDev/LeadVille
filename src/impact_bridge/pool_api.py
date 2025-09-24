"""
Device Pool Management API Endpoints
Handles shared device pool operations, session management, and temporary assignments.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..database.session import get_db_session
from ..database.pool_models import (
    DevicePool, ActiveSession, DeviceLease, DevicePoolEvent,
    DevicePoolStatus, SessionStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/pool", tags=["Device Pool Management"])

@router.get("/devices")
async def get_pool_devices(
    status: Optional[str] = None,
    device_type: Optional[str] = None,
    include_leased: bool = False,
    db: Session = Depends(get_db_session)
):
    """Get all devices in the pool with optional filtering"""
    try:
        query = db.query(DevicePool)
        
        # Filter by status
        if status:
            try:
                status_enum = DevicePoolStatus(status)
                query = query.filter(DevicePool.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Filter by device type
        if device_type:
            query = query.filter(DevicePool.device_type == device_type)
        
        # Filter out leased devices unless specifically requested
        if not include_leased:
            query = query.filter(DevicePool.status != DevicePoolStatus.LEASED)
        
        devices = query.order_by(DevicePool.device_type, DevicePool.label).all()
        
        return {
            "devices": [
                {
                    "id": device.id,
                    "hw_addr": device.hw_addr,
                    "device_type": device.device_type,
                    "label": device.label,
                    "vendor": device.vendor,
                    "model": device.model,
                    "status": device.status.value,
                    "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                    "battery": device.battery,
                    "rssi": device.rssi,
                    "notes": device.notes,
                    "is_available": device.status == DevicePoolStatus.AVAILABLE
                }
                for device in devices
            ],
            "total_count": len(devices),
            "available_count": len([d for d in devices if d.status == DevicePoolStatus.AVAILABLE])
        }
    except Exception as e:
        logger.error(f"Error getting pool devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/devices")
async def add_device_to_pool(request: Request, db: Session = Depends(get_db_session)):
    """Add a discovered device to the shared pool"""
    try:
        data = await request.json()
        hw_addr = data.get("hw_addr")
        device_type = data.get("device_type", "sensor")
        label = data.get("label", f"Device {hw_addr}")
        vendor = data.get("vendor")
        model = data.get("model")
        
        if not hw_addr:
            raise HTTPException(status_code=400, detail="hw_addr is required")
        
        # Check if device already exists
        existing = db.query(DevicePool).filter(DevicePool.hw_addr == hw_addr).first()
        if existing:
            raise HTTPException(status_code=409, detail="Device already exists in pool")
        
        # Create new pool device
        device = DevicePool(
            hw_addr=hw_addr,
            device_type=device_type,
            label=label,
            vendor=vendor,
            model=model,
            status=DevicePoolStatus.AVAILABLE
        )
        
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Log the event
        event = DevicePoolEvent(
            device_id=device.id,
            event_type="discovered",
            event_data=f"Added to pool: {label}"
        )
        db.add(event)
        db.commit()
        
        return {
            "message": "Device added to pool",
            "device": {
                "id": device.id,
                "hw_addr": device.hw_addr,
                "label": device.label,
                "status": device.status.value
            }
        }
    except Exception as e:
        logger.error(f"Error adding device to pool: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def get_active_sessions(
    status: Optional[str] = None,
    bridge_id: Optional[int] = None,
    db: Session = Depends(get_db_session)
):
    """Get active sessions with their device assignments"""
    try:
        query = db.query(ActiveSession)
        
        if status:
            try:
                status_enum = SessionStatus(status)
                query = query.filter(ActiveSession.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if bridge_id:
            query = query.filter(ActiveSession.bridge_id == bridge_id)
        
        sessions = query.order_by(ActiveSession.started_at.desc()).all()
        
        return {
            "sessions": [
                {
                    "id": session.id,
                    "session_name": session.session_name,
                    "bridge_id": session.bridge_id,
                    "stage_id": session.stage_id,
                    "status": session.status.value,
                    "started_at": session.started_at.isoformat(),
                    "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                    "last_activity": session.last_activity.isoformat(),
                    "device_count": len([lease for lease in session.device_leases if lease.released_at is None]),
                    "connected_count": len([lease for lease in session.device_leases 
                                          if lease.released_at is None and lease.is_connected])
                }
                for session in sessions
            ]
        }
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions")
async def create_session(request: Request, db: Session = Depends(get_db_session)):
    """Create a new active session for device management"""
    try:
        data = await request.json()
        session_name = data.get("session_name")
        bridge_id = data.get("bridge_id")
        stage_id = data.get("stage_id")
        
        if not session_name or not bridge_id:
            raise HTTPException(status_code=400, detail="session_name and bridge_id are required")
        
        # Create new session
        session = ActiveSession(
            session_name=session_name,
            bridge_id=bridge_id,
            stage_id=stage_id,
            status=SessionStatus.IDLE
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return {
            "message": "Session created",
            "session": {
                "id": session.id,
                "session_name": session.session_name,
                "status": session.status.value
            }
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/lease")
async def lease_device(session_id: int, request: Request, db: Session = Depends(get_db_session)):
    """Lease a device from the pool to an active session"""
    try:
        data = await request.json()
        device_id = data.get("device_id")
        target_assignment = data.get("target_assignment", "")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="device_id is required")
        
        # Verify session exists and is active
        session = db.query(ActiveSession).filter(ActiveSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.status == SessionStatus.ENDED:
            raise HTTPException(status_code=400, detail="Cannot lease devices to ended session")
        
        # Verify device exists and is available
        device = db.query(DevicePool).filter(DevicePool.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        if device.status != DevicePoolStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=f"Device is not available (status: {device.status.value})")
        
        # Check if device is already leased to another session
        existing_lease = db.query(DeviceLease).filter(
            and_(DeviceLease.device_id == device_id, DeviceLease.released_at.is_(None))
        ).first()
        
        if existing_lease:
            raise HTTPException(status_code=409, detail="Device is already leased to another session")
        
        # Create lease
        lease = DeviceLease(
            device_id=device_id,
            session_id=session_id,
            target_assignment=target_assignment
        )
        
        # Update device status
        device.status = DevicePoolStatus.LEASED
        
        # Update session activity
        session.last_activity = func.now()
        
        db.add(lease)
        db.commit()
        db.refresh(lease)
        
        # Log the event
        event = DevicePoolEvent(
            device_id=device_id,
            session_id=session_id,
            event_type="lease",
            event_data=f"Leased to session '{session.session_name}' as '{target_assignment}'"
        )
        db.add(event)
        db.commit()
        
        return {
            "message": "Device leased successfully",
            "lease": {
                "id": lease.id,
                "device_hw_addr": device.hw_addr,
                "target_assignment": target_assignment,
                "leased_at": lease.leased_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error leasing device: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/release/{device_id}")
async def release_device(session_id: int, device_id: int, db: Session = Depends(get_db_session)):
    """Release a device from a session back to the pool"""
    try:
        # Find active lease
        lease = db.query(DeviceLease).filter(
            and_(
                DeviceLease.session_id == session_id,
                DeviceLease.device_id == device_id,
                DeviceLease.released_at.is_(None)
            )
        ).first()
        
        if not lease:
            raise HTTPException(status_code=404, detail="Active lease not found")
        
        # Release the lease
        lease.released_at = func.now()
        
        # Update device status back to available
        device = lease.device
        device.status = DevicePoolStatus.AVAILABLE
        
        # Update session activity
        session = lease.session
        session.last_activity = func.now()
        
        db.commit()
        
        # Log the event
        event = DevicePoolEvent(
            device_id=device_id,
            session_id=session_id,
            event_type="release",
            event_data=f"Released from session '{session.session_name}'"
        )
        db.add(event)
        db.commit()
        
        return {
            "message": "Device released successfully",
            "device_hw_addr": device.hw_addr
        }
    except Exception as e:
        logger.error(f"Error releasing device: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/end")
async def end_session(session_id: int, db: Session = Depends(get_db_session)):
    """End a session and release all its devices"""
    try:
        session = db.query(ActiveSession).filter(ActiveSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.status == SessionStatus.ENDED:
            raise HTTPException(status_code=400, detail="Session already ended")
        
        # Release all active leases
        active_leases = db.query(DeviceLease).filter(
            and_(DeviceLease.session_id == session_id, DeviceLease.released_at.is_(None))
        ).all()
        
        released_count = 0
        for lease in active_leases:
            lease.released_at = func.now()
            lease.device.status = DevicePoolStatus.AVAILABLE
            released_count += 1
            
            # Log release event
            event = DevicePoolEvent(
                device_id=lease.device_id,
                session_id=session_id,
                event_type="release",
                event_data=f"Auto-released when session ended"
            )
            db.add(event)
        
        # End session
        session.status = SessionStatus.ENDED
        session.ended_at = func.now()
        
        db.commit()
        
        return {
            "message": "Session ended successfully",
            "devices_released": released_count
        }
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/devices")
async def get_session_devices(session_id: int, db: Session = Depends(get_db_session)):
    """Get all devices currently leased to a session"""
    try:
        session = db.query(ActiveSession).filter(ActiveSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get active leases
        leases = db.query(DeviceLease).filter(
            and_(DeviceLease.session_id == session_id, DeviceLease.released_at.is_(None))
        ).all()
        
        return {
            "session_id": session_id,
            "session_name": session.session_name,
            "session_status": session.status.value,
            "devices": [
                {
                    "lease_id": lease.id,
                    "device_id": lease.device.id,
                    "hw_addr": lease.device.hw_addr,
                    "device_type": lease.device.device_type,
                    "label": lease.device.label,
                    "target_assignment": lease.target_assignment,
                    "is_connected": lease.is_connected,
                    "leased_at": lease.leased_at.isoformat(),
                    "connection_attempts": lease.connection_attempts,
                    "last_connection_attempt": lease.last_connection_attempt.isoformat() if lease.last_connection_attempt else None
                }
                for lease in leases
            ]
        }
    except Exception as e:
        logger.error(f"Error getting session devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))