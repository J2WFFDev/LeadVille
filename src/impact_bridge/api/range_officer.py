"""Range Officer API endpoints."""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from .models import (
    ROTarget,
    ROStageLayout,
    ROHit,
    ROString,
    ROStringRequest,
    ROStringResponse,
    ROSystemStatus,
    ROHitRequest,
    ROHitResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for demo purposes
# In production, this would be replaced with proper database storage
class RODataStore:
    def __init__(self):
        self.stages = {
            'stage1': ROStageLayout(
                stage_id='stage1',
                name='Pistol Bay',
                targets=[
                    ROTarget(id=1, label='T1', x=150, y=200, status='online'),
                    ROTarget(id=2, label='T2', x=300, y=200, status='online'),
                    ROTarget(id=3, label='T3', x=450, y=200, status='degraded'),
                    ROTarget(id=4, label='T4', x=600, y=200, status='online'),
                    ROTarget(id=5, label='T5', x=750, y=200, status='offline')
                ]
            ),
            'stage2': ROStageLayout(
                stage_id='stage2',
                name='Rifle Range',
                targets=[
                    ROTarget(id=1, label='R1', x=200, y=150, status='online'),
                    ROTarget(id=2, label='R2', x=400, y=150, status='online'),
                    ROTarget(id=3, label='R3', x=600, y=150, status='online'),
                    ROTarget(id=4, label='R4', x=200, y=250, status='degraded'),
                    ROTarget(id=5, label='R5', x=400, y=250, status='online'),
                    ROTarget(id=6, label='R6', x=600, y=250, status='offline')
                ]
            ),
            'stage3': ROStageLayout(
                stage_id='stage3',
                name='Mixed Course',
                targets=[
                    ROTarget(id=1, label='M1', x=120, y=100, status='online'),
                    ROTarget(id=2, label='M2', x=300, y=120, status='online'),
                    ROTarget(id=3, label='M3', x=500, y=140, status='degraded'),
                    ROTarget(id=4, label='M4', x=680, y=160, status='online'),
                    ROTarget(id=5, label='M5', x=200, y=280, status='online'),
                    ROTarget(id=6, label='M6', x=400, y=300, status='offline'),
                    ROTarget(id=7, label='M7', x=600, y=320, status='online')
                ]
            )
        }
        self.strings = []
        self.active_string = None
        self.string_counter = 1
        self.hits = []

    def get_stage(self, stage_id: str) -> Optional[ROStageLayout]:
        return self.stages.get(stage_id)

    def get_all_stages(self) -> List[ROStageLayout]:
        return list(self.stages.values())

    def create_string(self, shooter: str, stage_id: str) -> ROString:
        if self.active_string:
            raise ValueError("A string is already active")
        
        string = ROString(
            id=self.string_counter,
            shooter=shooter,
            start_time=datetime.now(),
            stage_id=stage_id,
            status='active'
        )
        
        self.active_string = string
        self.string_counter += 1
        return string

    def complete_string(self) -> Optional[ROString]:
        if not self.active_string:
            return None
        
        self.active_string.end_time = datetime.now()
        self.active_string.status = 'completed'
        
        # Add hits from current session
        string_hits = [hit for hit in self.hits if hit.string_id == self.active_string.id]
        self.active_string.hits = string_hits
        
        self.strings.append(self.active_string)
        completed_string = self.active_string
        self.active_string = None
        
        return completed_string

    def cancel_string(self) -> Optional[ROString]:
        if not self.active_string:
            return None
        
        self.active_string.status = 'cancelled'
        cancelled_string = self.active_string
        self.active_string = None
        
        # Remove hits from cancelled string
        self.hits = [hit for hit in self.hits if hit.string_id != cancelled_string.id]
        
        return cancelled_string

    def add_hit(self, target_id: int, timestamp: Optional[datetime] = None, 
                x: Optional[float] = None, y: Optional[float] = None) -> ROHit:
        hit = ROHit(
            id=str(uuid4()),
            target_id=target_id,
            timestamp=timestamp or datetime.now(),
            x=x,
            y=y,
            string_id=self.active_string.id if self.active_string else None
        )
        
        self.hits.append(hit)
        
        # Update target's last hit time
        for stage in self.stages.values():
            for target in stage.targets:
                if target.id == target_id:
                    target.last_hit = hit.timestamp
                    break
        
        return hit

    def get_system_status(self) -> ROSystemStatus:
        # Count target statuses across all stages
        total_targets = 0
        online_targets = 0
        degraded_targets = 0
        offline_targets = 0
        
        for stage in self.stages.values():
            for target in stage.targets:
                total_targets += 1
                if target.status == 'online':
                    online_targets += 1
                elif target.status == 'degraded':
                    degraded_targets += 1
                elif target.status == 'offline':
                    offline_targets += 1
        
        return ROSystemStatus(
            system_online=True,
            active_string=self.active_string,
            total_targets=total_targets,
            online_targets=online_targets,
            degraded_targets=degraded_targets,
            offline_targets=offline_targets,
            last_update=datetime.now()
        )

# Global data store instance
data_store = RODataStore()


@router.get("/status",
           response_model=ROSystemStatus,
           summary="Get Range Officer system status",
           description="Get overall system status including active string and target counts.")
async def get_ro_status() -> ROSystemStatus:
    """Get Range Officer system status."""
    try:
        logger.debug("Retrieving RO system status")
        return data_store.get_system_status()
    except Exception as e:
        logger.error(f"Error retrieving RO system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system status: {str(e)}"
        )


@router.get("/stages",
           response_model=List[ROStageLayout],
           summary="Get all stage layouts",
           description="Get list of all available stage layouts with target configurations.")
async def get_stages() -> List[ROStageLayout]:
    """Get all stage layouts."""
    try:
        logger.debug("Retrieving all stage layouts")
        return data_store.get_all_stages()
    except Exception as e:
        logger.error(f"Error retrieving stage layouts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stage layouts: {str(e)}"
        )


@router.get("/stages/{stage_id}",
           response_model=ROStageLayout,
           summary="Get specific stage layout",
           description="Get layout configuration for a specific stage.")
async def get_stage(stage_id: str) -> ROStageLayout:
    """Get specific stage layout."""
    try:
        logger.debug(f"Retrieving stage layout for {stage_id}")
        
        stage = data_store.get_stage(stage_id)
        if not stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stage {stage_id} not found"
            )
        
        return stage
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stage {stage_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stage: {str(e)}"
        )


@router.post("/strings/start",
            response_model=ROStringResponse,
            summary="Start a new string",
            description="Start a new shooting string for a competitor.")
async def start_string(request: ROStringRequest) -> ROStringResponse:
    """Start a new shooting string."""
    try:
        logger.info(f"Starting string for shooter {request.shooter} on stage {request.stage_id}")
        
        # Validate stage exists
        if not data_store.get_stage(request.stage_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stage {request.stage_id} not found"
            )
        
        string = data_store.create_string(request.shooter, request.stage_id)
        
        return ROStringResponse(
            success=True,
            string=string,
            message=f"String {string.id} started successfully"
        )
        
    except ValueError as e:
        logger.warning(f"String start failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting string: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start string: {str(e)}"
        )


@router.post("/strings/complete",
            response_model=ROStringResponse,
            summary="Complete current string",
            description="Complete the currently active shooting string.")
async def complete_string() -> ROStringResponse:
    """Complete the currently active string."""
    try:
        logger.info("Completing current string")
        
        completed_string = data_store.complete_string()
        
        if not completed_string:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active string to complete"
            )
        
        return ROStringResponse(
            success=True,
            string=completed_string,
            message=f"String {completed_string.id} completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing string: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete string: {str(e)}"
        )


@router.post("/strings/cancel",
            response_model=ROStringResponse,
            summary="Cancel current string",
            description="Cancel the currently active shooting string.")
async def cancel_string() -> ROStringResponse:
    """Cancel the currently active string."""
    try:
        logger.info("Cancelling current string")
        
        cancelled_string = data_store.cancel_string()
        
        if not cancelled_string:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active string to cancel"
            )
        
        return ROStringResponse(
            success=True,
            string=cancelled_string,
            message=f"String {cancelled_string.id} cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling string: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel string: {str(e)}"
        )


@router.get("/strings",
           response_model=List[ROString],
           summary="Get string history",
           description="Get list of all completed strings.")
async def get_strings() -> List[ROString]:
    """Get string history."""
    try:
        logger.debug("Retrieving string history")
        return data_store.strings
    except Exception as e:
        logger.error(f"Error retrieving string history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve string history: {str(e)}"
        )


@router.get("/strings/active",
           response_model=Optional[ROString],
           summary="Get active string",
           description="Get the currently active string if any.")
async def get_active_string() -> Optional[ROString]:
    """Get the currently active string."""
    try:
        logger.debug("Retrieving active string")
        return data_store.active_string
    except Exception as e:
        logger.error(f"Error retrieving active string: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active string: {str(e)}"
        )


@router.post("/hits",
            response_model=ROHitResponse,
            summary="Register a hit",
            description="Register a hit on a target.")
async def register_hit(request: ROHitRequest) -> ROHitResponse:
    """Register a hit on a target."""
    try:
        logger.info(f"Registering hit on target {request.target_id}")
        
        if not data_store.active_string:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No active string to register hit for"
            )
        
        hit = data_store.add_hit(
            target_id=request.target_id,
            timestamp=request.timestamp,
            x=request.x,
            y=request.y
        )
        
        return ROHitResponse(
            success=True,
            hit=hit,
            message=f"Hit registered on target {request.target_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering hit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register hit: {str(e)}"
        )


@router.get("/hits",
           response_model=List[ROHit],
           summary="Get all hits",
           description="Get list of all registered hits.")
async def get_hits() -> List[ROHit]:
    """Get all registered hits."""
    try:
        logger.debug("Retrieving all hits")
        return data_store.hits
    except Exception as e:
        logger.error(f"Error retrieving hits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hits: {str(e)}"
        )


@router.get("/hits/string/{string_id}",
           response_model=List[ROHit],
           summary="Get hits for string",
           description="Get all hits for a specific string.")
async def get_hits_for_string(string_id: int) -> List[ROHit]:
    """Get hits for a specific string."""
    try:
        logger.debug(f"Retrieving hits for string {string_id}")
        string_hits = [hit for hit in data_store.hits if hit.string_id == string_id]
        return string_hits
    except Exception as e:
        logger.error(f"Error retrieving hits for string {string_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hits for string: {str(e)}"
        )


@router.delete("/data/clear",
              summary="Clear all data",
              description="Clear all strings and hits (for testing/demo purposes).")
async def clear_all_data():
    """Clear all string and hit data."""
    try:
        logger.warning("Clearing all RO data")
        
        data_store.strings = []
        data_store.hits = []
        data_store.active_string = None
        data_store.string_counter = 1
        
        # Reset target last hit times
        for stage in data_store.stages.values():
            for target in stage.targets:
                target.last_hit = None
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "All data cleared successfully"}
        )
        
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear data: {str(e)}"
        )