"""Scorekeeper interface API endpoints."""

import csv
import io
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, asc, func, case

from ..database.engine import get_db_session
from ..database.models import Run, Match, Stage, Shooter, TimerEvent, SensorEvent, Note
from ..database.crud import DatabaseCRUD
from .models import (
    RunInfo, RunsListRequest, RunsListResponse, TimerEventInfo,
    TimerAlignmentUpdateRequest, TimerAlignmentUpdateResponse,
    AuditTrailEntry, AuditTrailResponse, RunExportRequest, RunExportResponse,
    RunValidationResult, BulkValidationRequest, BulkValidationResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _create_audit_entry(session: Session, run_id: int, change_type: str, 
                       field_name: str, old_value: Any, new_value: Any,
                       reason: str, author_role: str) -> Dict[str, Any]:
    """Create an audit trail entry for a run change."""
    
    # Get the run and update its audit_json field
    run = session.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Initialize audit_json if it doesn't exist
    if not run.audit_json:
        run.audit_json = {"entries": []}
    
    # Create audit entry
    audit_entry = {
        "id": len(run.audit_json["entries"]) + 1,
        "change_type": change_type,
        "field_name": field_name,
        "old_value": str(old_value) if old_value is not None else None,
        "new_value": str(new_value) if new_value is not None else None,
        "reason": reason,
        "author_role": author_role,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {}
    }
    
    # Add to audit trail
    run.audit_json["entries"].append(audit_entry)
    run.updated_at = datetime.utcnow()
    
    session.flush()
    return audit_entry


@router.get("/runs", response_model=RunsListResponse)
async def list_runs(
    match_id: Optional[int] = Query(None, description="Filter by match ID"),
    stage_id: Optional[int] = Query(None, description="Filter by stage ID"),
    squad: Optional[str] = Query(None, description="Filter by squad"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    session: Session = Depends(get_db_session)
):
    """Get paginated list of runs with filtering options."""
    
    try:
        # Build query with joins for related data
        query = (session.query(Run)
                .join(Shooter, Run.shooter_id == Shooter.id)
                .join(Stage, Run.stage_id == Stage.id)
                .join(Match, Run.match_id == Match.id)
                .options(
                    joinedload(Run.shooter),
                    joinedload(Run.stage),
                    joinedload(Run.match),
                    joinedload(Run.timer_events),
                    joinedload(Run.sensor_events),
                    joinedload(Run.notes)
                ))
        
        # Apply filters
        if match_id:
            query = query.filter(Run.match_id == match_id)
        if stage_id:
            query = query.filter(Run.stage_id == stage_id)
        if squad:
            query = query.filter(Shooter.squad == squad)
        if status:
            query = query.filter(Run.status == status)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Run, sort_by, Run.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * page_size
        runs = query.offset(offset).limit(page_size).all()
        
        # Convert to response format
        run_infos = []
        for run in runs:
            run_info = RunInfo(
                id=run.id,
                match_id=run.match_id,
                stage_id=run.stage_id,
                shooter_id=run.shooter_id,
                shooter_name=run.shooter.name,
                squad=run.shooter.squad,
                stage_name=run.stage.name,
                stage_number=run.stage.number,
                match_name=run.match.name,
                status=run.status,
                started_ts=run.started_ts,
                ended_ts=run.ended_ts,
                timer_events_count=len(run.timer_events),
                sensor_events_count=len(run.sensor_events),
                has_notes=len(run.notes) > 0,
                created_at=run.created_at,
                updated_at=run.updated_at
            )
            run_infos.append(run_info)
        
        total_pages = (total + page_size - 1) // page_size
        
        return RunsListResponse(
            runs=run_infos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/runs/{run_id}/timer-events", response_model=List[TimerEventInfo])
async def get_run_timer_events(
    run_id: int,
    session: Session = Depends(get_db_session)
):
    """Get timer events for a specific run with alignment information."""
    
    try:
        # Verify run exists
        run = session.query(Run).filter(Run.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get timer events for the run
        timer_events = (session.query(TimerEvent)
                       .filter(TimerEvent.run_id == run_id)
                       .order_by(TimerEvent.ts_utc)
                       .all())
        
        event_infos = []
        for event in timer_events:
            # Basic alignment validation (could be enhanced with more sophisticated logic)
            is_aligned = True  # Placeholder - implement actual alignment logic
            alignment_offset_ms = None  # Placeholder
            
            event_info = TimerEventInfo(
                id=event.id,
                ts_utc=event.ts_utc,
                type=event.type,
                raw=event.raw,
                is_aligned=is_aligned,
                alignment_offset_ms=alignment_offset_ms
            )
            event_infos.append(event_info)
        
        return event_infos
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timer events for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/timer-events/{event_id}/align", response_model=TimerAlignmentUpdateResponse)
async def update_timer_alignment(
    event_id: int,
    request: TimerAlignmentUpdateRequest,
    session: Session = Depends(get_db_session)
):
    """Update timer event alignment with audit trail."""
    
    try:
        # Get the timer event
        event = session.query(TimerEvent).filter(TimerEvent.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Timer event not found")
        
        # Validate bounded edit (e.g., maximum 5 second adjustment)
        old_timestamp = event.ts_utc
        time_diff = abs((request.new_timestamp - old_timestamp).total_seconds())
        max_adjustment_seconds = 5.0
        
        if time_diff > max_adjustment_seconds:
            raise HTTPException(
                status_code=400, 
                detail=f"Alignment adjustment exceeds maximum allowed ({max_adjustment_seconds}s)"
            )
        
        # Update the timestamp
        event.ts_utc = request.new_timestamp
        
        # Create audit trail entry
        audit_entry = None
        if event.run_id:
            offset_ms = (request.new_timestamp - old_timestamp).total_seconds() * 1000
            audit_entry = _create_audit_entry(
                session=session,
                run_id=event.run_id,
                change_type="timer_alignment",
                field_name="ts_utc",
                old_value=old_timestamp.isoformat(),
                new_value=request.new_timestamp.isoformat(),
                reason=request.reason,
                author_role=request.author_role
            )
        
        session.commit()
        
        offset_ms = (request.new_timestamp - old_timestamp).total_seconds() * 1000
        
        return TimerAlignmentUpdateResponse(
            success=True,
            event_id=event_id,
            old_timestamp=old_timestamp,
            new_timestamp=request.new_timestamp,
            offset_ms=offset_ms,
            message="Timer alignment updated successfully",
            audit_entry_id=audit_entry["id"] if audit_entry else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating timer alignment for event {event_id}: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/runs/{run_id}/audit-trail", response_model=AuditTrailResponse)
async def get_run_audit_trail(
    run_id: int,
    session: Session = Depends(get_db_session)
):
    """Get audit trail for a specific run."""
    
    try:
        # Get the run
        run = session.query(Run).filter(Run.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get audit entries from the run's audit_json field
        audit_entries = []
        if run.audit_json and "entries" in run.audit_json:
            for entry_data in run.audit_json["entries"]:
                entry = AuditTrailEntry(
                    id=entry_data["id"],
                    run_id=run_id,
                    change_type=entry_data["change_type"],
                    field_name=entry_data["field_name"],
                    old_value=entry_data.get("old_value"),
                    new_value=entry_data.get("new_value"),
                    reason=entry_data["reason"],
                    author_role=entry_data["author_role"],
                    timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                    metadata=entry_data.get("metadata")
                )
                audit_entries.append(entry)
        
        return AuditTrailResponse(
            entries=audit_entries,
            total=len(audit_entries),
            run_id=run_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit trail for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/export/runs", response_model=RunExportResponse)
async def export_runs(
    request: RunExportRequest,
    session: Session = Depends(get_db_session)
):
    """Export runs data in CSV or NDJSON format."""
    
    try:
        # Build query with filters
        query = (session.query(Run)
                .join(Shooter, Run.shooter_id == Shooter.id)
                .join(Stage, Run.stage_id == Stage.id)
                .join(Match, Run.match_id == Match.id)
                .options(
                    joinedload(Run.shooter),
                    joinedload(Run.stage),
                    joinedload(Run.match)
                ))
        
        # Apply filters
        if request.match_id:
            query = query.filter(Run.match_id == request.match_id)
        if request.stage_id:
            query = query.filter(Run.stage_id == request.stage_id)
        if request.squad:
            query = query.filter(Shooter.squad == request.squad)
        if request.status:
            query = query.filter(Run.status == request.status)
        
        runs = query.all()
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"runs_export_{timestamp}.{request.format}"
        
        # Prepare data for export
        export_data = []
        for run in runs:
            run_data = {
                "run_id": run.id,
                "match_name": run.match.name,
                "stage_name": run.stage.name,
                "stage_number": run.stage.number,
                "shooter_name": run.shooter.name,
                "squad": run.shooter.squad,
                "status": run.status,
                "started_ts": run.started_ts.isoformat() if run.started_ts else None,
                "ended_ts": run.ended_ts.isoformat() if run.ended_ts else None,
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat()
            }
            
            # Include events if requested
            if request.include_events:
                timer_events = DatabaseCRUD.timer_events.list_by_run(session, run.id)
                sensor_events = DatabaseCRUD.sensor_events.list_by_run(session, run.id)
                
                run_data["timer_events_count"] = len(timer_events)
                run_data["sensor_events_count"] = len(sensor_events)
                
                if request.format == "ndjson":
                    run_data["timer_events"] = [
                        {
                            "ts_utc": event.ts_utc.isoformat(),
                            "type": event.type,
                            "raw": event.raw
                        } for event in timer_events
                    ]
                    run_data["sensor_events"] = [
                        {
                            "ts_utc": event.ts_utc.isoformat(),
                            "magnitude": event.magnitude,
                            "features": event.features_json
                        } for event in sensor_events
                    ]
            
            # Include audit trail if requested
            if request.include_audit and run.audit_json:
                run_data["audit_entries"] = run.audit_json.get("entries", [])
            
            export_data.append(run_data)
        
        # Generate export content
        if request.format == "csv":
            output = io.StringIO()
            if export_data:
                # Flatten data for CSV (only basic fields for CSV format)
                csv_data = []
                for run_data in export_data:
                    csv_row = {k: v for k, v in run_data.items() 
                              if not isinstance(v, (list, dict))}
                    csv_data.append(csv_row)
                
                writer = csv.DictWriter(output, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
            
            content = output.getvalue()
            file_size = len(content.encode('utf-8'))
            
        else:  # ndjson format
            lines = []
            for run_data in export_data:
                lines.append(json.dumps(run_data, default=str))
            content = "\n".join(lines)
            file_size = len(content.encode('utf-8'))
        
        # In a real implementation, you'd save this to a file or cloud storage
        # For now, we'll just return the metadata
        
        return RunExportResponse(
            success=True,
            format=request.format,
            filename=filename,
            download_url=None,  # Would be populated with actual download URL
            record_count=len(export_data),
            file_size_bytes=file_size,
            message=f"Successfully exported {len(export_data)} runs in {request.format.upper()} format"
        )
        
    except Exception as e:
        logger.error(f"Error exporting runs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate/runs", response_model=BulkValidationResponse)
async def validate_runs(
    request: BulkValidationRequest,
    session: Session = Depends(get_db_session)
):
    """Validate multiple runs for data integrity and timer alignment."""
    
    try:
        start_time = datetime.utcnow()
        results = []
        
        for run_id in request.run_ids:
            # Get run with related data
            run = (session.query(Run)
                  .options(
                      joinedload(Run.timer_events),
                      joinedload(Run.sensor_events)
                  )
                  .filter(Run.id == run_id)
                  .first())
            
            if not run:
                results.append(RunValidationResult(
                    run_id=run_id,
                    is_valid=False,
                    issues=[f"Run {run_id} not found"],
                    warnings=[],
                    timer_alignment_status="error"
                ))
                continue
            
            # Validate run data
            issues = []
            warnings = []
            timer_alignment_status = "ok"
            event_correlation_score = None
            
            # Basic validation checks
            if not run.started_ts and run.status not in ["pending"]:
                issues.append("Run marked as active/completed but has no start time")
            
            if run.ended_ts and run.started_ts and run.ended_ts < run.started_ts:
                issues.append("End time is before start time")
            
            # Timer alignment validation
            if request.check_timer_alignment and run.timer_events:
                timer_events = sorted(run.timer_events, key=lambda x: x.ts_utc)
                
                # Check for reasonable time gaps between events
                for i in range(1, len(timer_events)):
                    time_diff = (timer_events[i].ts_utc - timer_events[i-1].ts_utc).total_seconds()
                    if time_diff < 0.1:  # Events too close together
                        warnings.append(f"Timer events very close together ({time_diff:.3f}s)")
                    elif time_diff > 300:  # Events too far apart (5 minutes)
                        warnings.append(f"Large gap between timer events ({time_diff:.1f}s)")
                
                # Check for expected event sequence
                event_types = [event.type for event in timer_events]
                if "START" not in event_types and run.status != "pending":
                    timer_alignment_status = "missing_start"
                    issues.append("No START event found for active/completed run")
            
            # Event correlation validation
            if request.check_event_correlation and run.timer_events and run.sensor_events:
                # Simple correlation score based on timing alignment
                shot_events = [e for e in run.timer_events if e.type == "SHOT"]
                impact_events = run.sensor_events
                
                if shot_events and impact_events:
                    # Calculate correlation score (simplified)
                    correlation_count = 0
                    for shot_event in shot_events:
                        # Look for impact within 2 seconds of shot
                        for impact_event in impact_events:
                            time_diff = abs((impact_event.ts_utc - shot_event.ts_utc).total_seconds())
                            if time_diff <= 2.0:
                                correlation_count += 1
                                break
                    
                    event_correlation_score = correlation_count / len(shot_events)
                    if event_correlation_score < 0.8:
                        warnings.append(f"Low shot-to-impact correlation ({event_correlation_score:.2f})")
            
            is_valid = len(issues) == 0
            
            results.append(RunValidationResult(
                run_id=run_id,
                is_valid=is_valid,
                issues=issues,
                warnings=warnings,
                timer_alignment_status=timer_alignment_status,
                event_correlation_score=event_correlation_score
            ))
        
        # Calculate summary statistics
        summary = {
            "valid_runs": sum(1 for r in results if r.is_valid),
            "invalid_runs": sum(1 for r in results if not r.is_valid),
            "runs_with_warnings": sum(1 for r in results if r.warnings),
            "timer_alignment_issues": sum(1 for r in results if r.timer_alignment_status != "ok")
        }
        
        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return BulkValidationResponse(
            results=results,
            summary=summary,
            total_processed=len(results),
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error validating runs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")