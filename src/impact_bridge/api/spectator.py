"""Spectator dashboard API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/spectator", tags=["spectator"])


class ImpactEvent(BaseModel):
    """Impact event data."""
    time: str
    target: str
    zone: str
    timestamp: datetime


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    position: int
    shooter_name: str
    shooter_number: Optional[int] = None
    time: float
    classification: str


class MatchStatus(BaseModel):
    """Current match status."""
    current_stage: str
    active_shooter: Optional[str] = None
    timer_status: str
    elapsed_time: str


class SpectatorData(BaseModel):
    """Complete spectator dashboard data."""
    match_status: MatchStatus
    recent_impacts: List[ImpactEvent]
    leaderboard: List[LeaderboardEntry]
    stage_info: dict
    system_status: dict
    last_update: datetime


# Mock data for demonstration
MOCK_IMPACTS = [
    ImpactEvent(
        time="02:15.23",
        target="Target A1",
        zone="Alpha",
        timestamp=datetime.now()
    ),
    ImpactEvent(
        time="01:42.17",
        target="Target B2",
        zone="Charlie",
        timestamp=datetime.now()
    ),
    ImpactEvent(
        time="01:18.05",
        target="Target A3",
        zone="Alpha",
        timestamp=datetime.now()
    )
]

MOCK_LEADERBOARD = [
    LeaderboardEntry(
        position=1,
        shooter_name="J. Smith",
        shooter_number=42,
        time=156.23,
        classification="A-Class"
    ),
    LeaderboardEntry(
        position=2,
        shooter_name="M. Johnson",
        shooter_number=15,
        time=162.45,
        classification="A-Class"
    ),
    LeaderboardEntry(
        position=3,
        shooter_name="K. Williams",
        shooter_number=23,
        time=168.89,
        classification="B-Class"
    )
]


@router.get("/data")
async def get_spectator_data(
    privacy_mode: bool = Query(default=True, description="Enable privacy mode to anonymize shooter names")
) -> SpectatorData:
    """Get complete spectator dashboard data."""
    
    # Apply privacy mode if enabled
    leaderboard = MOCK_LEADERBOARD.copy()
    active_shooter = "J. Smith (#42)"
    
    if privacy_mode:
        for entry in leaderboard:
            if entry.shooter_number:
                entry.shooter_name = f"Shooter {entry.shooter_number}"
            else:
                entry.shooter_name = "Shooter XX"
        active_shooter = "Shooter XX"
    
    return SpectatorData(
        match_status=MatchStatus(
            current_stage="Stage 1",
            active_shooter=active_shooter,
            timer_status="Running",
            elapsed_time="02:34.56"
        ),
        recent_impacts=MOCK_IMPACTS,
        leaderboard=leaderboard,
        stage_info={
            "name": "Speed Steel Challenge",
            "target_count": 6,
            "course_of_fire": "6 rounds minimum, freestyle"
        },
        system_status={
            "sensors": "connected",
            "timer": "connected",
            "data_quality": "excellent"
        },
        last_update=datetime.now()
    )


@router.get("/impacts")
async def get_recent_impacts(
    limit: int = Query(default=10, le=50, description="Maximum number of impacts to return")
) -> List[ImpactEvent]:
    """Get recent impact events."""
    return MOCK_IMPACTS[:limit]


@router.get("/leaderboard")
async def get_leaderboard(
    privacy_mode: bool = Query(default=True, description="Enable privacy mode to anonymize shooter names")
) -> List[LeaderboardEntry]:
    """Get current stage leaderboard."""
    
    leaderboard = MOCK_LEADERBOARD.copy()
    
    if privacy_mode:
        for entry in leaderboard:
            if entry.shooter_number:
                entry.shooter_name = f"Shooter {entry.shooter_number}"
            else:
                entry.shooter_name = "Shooter XX"
    
    return leaderboard


@router.get("/match-status")
async def get_match_status() -> MatchStatus:
    """Get current match status."""
    return MatchStatus(
        current_stage="Stage 1",
        active_shooter="J. Smith (#42)",
        timer_status="Running",
        elapsed_time="02:34.56"
    )