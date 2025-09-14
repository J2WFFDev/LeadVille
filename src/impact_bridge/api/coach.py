"""Coach interface API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/coach", tags=["coach"])


class CoachNoteCreate(BaseModel):
    """Coach note creation model."""
    shooter_id: Optional[int] = None
    content: str
    category: str = "general"
    is_bookmark: bool = False
    run_time: Optional[float] = None


class CoachNoteResponse(BaseModel):
    """Coach note response model."""
    id: int
    shooter_id: Optional[int]
    content: str
    category: str
    is_bookmark: bool
    run_time: Optional[float]
    timestamp: datetime
    author_role: str = "Coach"

    class Config:
        from_attributes = True


class BookmarkCreate(BaseModel):
    """Bookmark creation model."""
    shooter_id: Optional[int] = None
    content: Optional[str] = None
    run_time: float


class SessionSummary(BaseModel):
    """Session summary data."""
    total_notes: int
    total_bookmarks: int
    session_duration_minutes: int
    session_id: str


class ExportData(BaseModel):
    """Notes export data structure."""
    session_id: str
    export_time: datetime
    notes: List[CoachNoteResponse]
    summary: SessionSummary


# In-memory storage for demo purposes
# In production, this would use the database
session_notes = []
session_start_time = datetime.now()


@router.post("/notes", response_model=CoachNoteResponse)
async def create_note(note: CoachNoteCreate) -> CoachNoteResponse:
    """Create a new coach note."""
    
    # Create note object
    new_note = CoachNoteResponse(
        id=len(session_notes) + 1,
        shooter_id=note.shooter_id,
        content=note.content,
        category=note.category,
        is_bookmark=note.is_bookmark,
        run_time=note.run_time,
        timestamp=datetime.now(),
        author_role="Coach"
    )
    
    session_notes.append(new_note)
    return new_note


@router.get("/notes", response_model=List[CoachNoteResponse])
async def get_notes(
    category: Optional[str] = None,
    bookmarks_only: bool = False
) -> List[CoachNoteResponse]:
    """Get coach notes with optional filtering."""
    
    filtered_notes = session_notes
    
    if bookmarks_only:
        filtered_notes = [note for note in filtered_notes if note.is_bookmark]
    elif category and category != "all":
        filtered_notes = [note for note in filtered_notes if note.category == category]
    
    # Sort by timestamp descending
    return sorted(filtered_notes, key=lambda x: x.timestamp, reverse=True)


@router.put("/notes/{note_id}", response_model=CoachNoteResponse)
async def update_note(note_id: int, content: str) -> CoachNoteResponse:
    """Update a coach note."""
    
    for note in session_notes:
        if note.id == note_id:
            note.content = content
            return note
    
    raise HTTPException(status_code=404, detail="Note not found")


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int) -> dict:
    """Delete a coach note."""
    
    global session_notes
    original_count = len(session_notes)
    session_notes = [note for note in session_notes if note.id != note_id]
    
    if len(session_notes) == original_count:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"message": "Note deleted successfully"}


@router.post("/bookmarks", response_model=CoachNoteResponse)
async def create_bookmark(bookmark: BookmarkCreate) -> CoachNoteResponse:
    """Create a bookmark for a key moment."""
    
    # Format time for display
    minutes = int(bookmark.run_time // 60)
    seconds = bookmark.run_time % 60
    time_str = f"{minutes:02d}:{seconds:05.2f}"
    
    content = bookmark.content or f"Key moment at {time_str}"
    
    bookmark_note = CoachNoteResponse(
        id=len(session_notes) + 1,
        shooter_id=bookmark.shooter_id,
        content=content,
        category="general",
        is_bookmark=True,
        run_time=bookmark.run_time,
        timestamp=datetime.now(),
        author_role="Coach"
    )
    
    session_notes.append(bookmark_note)
    return bookmark_note


@router.get("/session-summary", response_model=SessionSummary)
async def get_session_summary() -> SessionSummary:
    """Get current session summary."""
    
    total_notes = len(session_notes)
    total_bookmarks = len([note for note in session_notes if note.is_bookmark])
    duration_minutes = int((datetime.now() - session_start_time).total_seconds() / 60)
    
    session_id = f"COACH-{datetime.now().strftime('%Y%m%d')}-{len(session_notes):03d}"
    
    return SessionSummary(
        total_notes=total_notes,
        total_bookmarks=total_bookmarks,
        session_duration_minutes=duration_minutes,
        session_id=session_id
    )


@router.get("/export", response_model=ExportData)
async def export_notes() -> ExportData:
    """Export all notes for sharing/backup."""
    
    summary = await get_session_summary()
    
    return ExportData(
        session_id=summary.session_id,
        export_time=datetime.now(),
        notes=sorted(session_notes, key=lambda x: x.timestamp),
        summary=summary
    )


@router.delete("/session")
async def clear_session() -> dict:
    """Clear all notes from current session."""
    
    global session_notes, session_start_time
    session_notes.clear()
    session_start_time = datetime.now()
    
    return {"message": "Session cleared successfully"}


@router.get("/shooters")
async def get_shooters() -> List[dict]:
    """Get available shooters for selection."""
    
    # Mock shooter data - in production this would come from database
    return [
        {"id": 1, "name": "J. Smith", "number": 42, "classification": "A-Class"},
        {"id": 2, "name": "M. Johnson", "number": 15, "classification": "A-Class"},
        {"id": 3, "name": "K. Williams", "number": 23, "classification": "B-Class"}
    ]


@router.get("/performance-stats")
async def get_performance_stats(shooter_id: Optional[int] = None) -> dict:
    """Get live performance statistics."""
    
    # Mock performance data - in production this would be calculated from real data
    return {
        "current_time": "02:34.56",
        "target_rate": "1.2",
        "accuracy": 85,
        "shots_fired": 6,
        "targets_hit": 5,
        "run_active": True
    }