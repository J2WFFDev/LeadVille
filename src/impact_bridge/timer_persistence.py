"""
Timer Event Database Persistence
Simple file-based database for AMG timer events with JSON storage
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TimerEvent:
    """Timer event data structure"""
    timestamp: str
    device_id: str
    event_type: str
    shot_state: str
    current_shot: int
    total_shots: int
    current_time: float
    split_time: float
    event_detail: str
    raw_hex: str
    session_id: Optional[str] = None


class TimerEventDatabase:
    """SQLite database for timer events"""
    
    def __init__(self, db_path: Path = Path("timer_events.db")):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with timer events table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS timer_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        shot_state TEXT,
                        current_shot INTEGER,
                        total_shots INTEGER,
                        current_time REAL,
                        split_time REAL,
                        event_detail TEXT,
                        raw_hex TEXT,
                        session_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for faster queries
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON timer_events(timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_event_type 
                    ON timer_events(event_type)
                """)
                
                conn.commit()
                logger.info(f"Timer events database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def store_event(self, event: TimerEvent) -> bool:
        """Store timer event in database"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._store_event_sync, event)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store timer event: {e}")
            return False
    
    def _store_event_sync(self, event: TimerEvent):
        """Synchronous event storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO timer_events (
                    timestamp, device_id, event_type, shot_state,
                    current_shot, total_shots, current_time, split_time,
                    event_detail, raw_hex, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                event.device_id,
                event.event_type,
                event.shot_state,
                event.current_shot,
                event.total_shots,
                event.current_time,
                event.split_time,
                event.event_detail,
                event.raw_hex,
                event.session_id
            ))
            conn.commit()
    
    async def get_recent_events(self, limit: int = 100) -> List[TimerEvent]:
        """Get recent timer events from database"""
        try:
            loop = asyncio.get_event_loop()
            events = await loop.run_in_executor(None, self._get_recent_events_sync, limit)
            return events
            
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []
    
    def _get_recent_events_sync(self, limit: int) -> List[TimerEvent]:
        """Synchronous recent events retrieval"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM timer_events 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            events = []
            for row in cursor.fetchall():
                event = TimerEvent(
                    timestamp=row["timestamp"],
                    device_id=row["device_id"],
                    event_type=row["event_type"],
                    shot_state=row["shot_state"],
                    current_shot=row["current_shot"],
                    total_shots=row["total_shots"],
                    current_time=row["current_time"],
                    split_time=row["split_time"],
                    event_detail=row["event_detail"],
                    raw_hex=row["raw_hex"],
                    session_id=row["session_id"]
                )
                events.append(event)
            
            return events
    
    async def get_session_events(self, session_id: str) -> List[TimerEvent]:
        """Get events for specific session"""
        try:
            loop = asyncio.get_event_loop()
            events = await loop.run_in_executor(None, self._get_session_events_sync, session_id)
            return events
            
        except Exception as e:
            logger.error(f"Failed to get session events: {e}")
            return []
    
    def _get_session_events_sync(self, session_id: str) -> List[TimerEvent]:
        """Synchronous session events retrieval"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM timer_events 
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            
            events = []
            for row in cursor.fetchall():
                event = TimerEvent(
                    timestamp=row["timestamp"],
                    device_id=row["device_id"],
                    event_type=row["event_type"],
                    shot_state=row["shot_state"],
                    current_shot=row["current_shot"],
                    total_shots=row["total_shots"],
                    current_time=row["current_time"],
                    split_time=row["split_time"],
                    event_detail=row["event_detail"],
                    raw_hex=row["raw_hex"],
                    session_id=row["session_id"]
                )
                events.append(event)
            
            return events


class TimerPersistenceManager:
    """Manager for timer event persistence with multiple backends"""
    
    def __init__(
        self, 
        db_path: Path = Path("timer_events.db"),
        json_backup_path: Path = Path("logs/timer_events_backup.jsonl"),
        session_id: Optional[str] = None
    ):
        self.database = TimerEventDatabase(db_path)
        self.json_backup_path = json_backup_path
        self.session_id = session_id or self._generate_session_id()
        
        # Ensure backup directory exists
        self.json_backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def store_timer_event(self, parsed_data: Dict[str, Any]) -> bool:
        """Store timer event with multiple backends"""
        try:
            # Create TimerEvent object
            event = TimerEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                device_id="60:09:C3:1F:DC:1A",  # AMG MAC address
                event_type=self._determine_event_type(parsed_data),
                shot_state=parsed_data.get("shot_state", ""),
                current_shot=parsed_data.get("current_shot", 0),
                total_shots=parsed_data.get("total_shots", 0),
                current_time=parsed_data.get("current_time", 0.0),
                split_time=parsed_data.get("split_time", 0.0),
                event_detail=parsed_data.get("event_detail", ""),
                raw_hex=parsed_data.get("raw_hex", ""),
                session_id=self.session_id
            )
            
            # Store in database
            db_success = await self.database.store_event(event)
            
            # Backup to JSON file
            json_success = await self._backup_to_json(event)
            
            if db_success:
                logger.debug(f"Timer event stored: {event.event_type}")
            
            return db_success or json_success
            
        except Exception as e:
            logger.error(f"Error storing timer event: {e}")
            return False
    
    async def _backup_to_json(self, event: TimerEvent) -> bool:
        """Backup event to JSONL file"""
        try:
            # Convert to dict and write as JSON line
            event_data = asdict(event)
            
            with open(self.json_backup_path, 'a') as f:
                f.write(json.dumps(event_data) + '\n')
            
            return True
            
        except Exception as e:
            logger.error(f"JSON backup failed: {e}")
            return False
    
    def _determine_event_type(self, parsed_data: Dict[str, Any]) -> str:
        """Determine event type from parsed AMG data"""
        shot_state = parsed_data.get("shot_state", "")
        
        if shot_state == "START":
            return "timer_start"
        elif shot_state == "STOPPED":
            return "timer_stop"
        elif shot_state == "ACTIVE":
            current_shot = parsed_data.get("current_shot", 0)
            if current_shot > 0:
                return "shot_detected"
            else:
                return "timer_active"
        
        return "unknown"
    
    async def get_recent_events(self, limit: int = 50) -> List[TimerEvent]:
        """Get recent timer events"""
        return await self.database.get_recent_events(limit)
    
    async def get_current_session_events(self) -> List[TimerEvent]:
        """Get events from current session"""
        return await self.database.get_session_events(self.session_id)