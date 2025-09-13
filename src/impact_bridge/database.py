"""Database persistence for sensor events and data."""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading
import time

logger = logging.getLogger(__name__)


class SensorDatabase:
    """SQLite database for persisting sensor events and data."""
    
    def __init__(
        self,
        db_path: str = "leadville_sensors.db",
        batch_size: int = 100,
        flush_interval: float = 5.0,
        enabled: bool = True,
    ):
        self.db_path = Path(db_path)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enabled = enabled
        
        self._connection: Optional[sqlite3.Connection] = None
        self._write_queue = asyncio.Queue()
        self._writer_task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
        
        if self.enabled:
            self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
                conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
                
                # Sensor samples table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sensor_samples (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp_ns INTEGER NOT NULL,
                        sensor_id TEXT NOT NULL,
                        vx REAL NOT NULL,
                        vy REAL NOT NULL,
                        vz REAL NOT NULL,
                        amplitude REAL NOT NULL,
                        rssi REAL,
                        battery_level INTEGER,
                        calibrated BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX(timestamp_ns),
                        INDEX(sensor_id),
                        INDEX(created_at)
                    )
                """)
                
                # Sensor events table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sensor_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp_ns INTEGER NOT NULL,
                        sensor_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT,  -- JSON
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX(timestamp_ns),
                        INDEX(sensor_id),
                        INDEX(event_type),
                        INDEX(created_at)
                    )
                """)
                
                # Impact detections table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS impact_detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp_ns INTEGER NOT NULL,
                        sensor_id TEXT NOT NULL,
                        onset_timestamp_ns INTEGER,
                        peak_timestamp_ns INTEGER,
                        onset_magnitude REAL,
                        peak_magnitude REAL,
                        duration_ms REAL,
                        confidence REAL,
                        impact_data TEXT,  -- JSON with full impact details
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX(timestamp_ns),
                        INDEX(sensor_id),
                        INDEX(peak_magnitude),
                        INDEX(created_at)
                    )
                """)
                
                # Sensor status table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sensor_status (
                        sensor_id TEXT PRIMARY KEY,
                        last_seen_ns INTEGER,
                        connection_count INTEGER DEFAULT 0,
                        total_samples INTEGER DEFAULT 0,
                        calibrated BOOLEAN DEFAULT FALSE,
                        calibration_timestamp DATETIME,
                        battery_level INTEGER,
                        avg_rssi REAL,
                        status_data TEXT,  -- JSON
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # System events table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp_ns INTEGER NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT,  -- JSON
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX(timestamp_ns),
                        INDEX(event_type),
                        INDEX(created_at)
                    )
                """)
                
                conn.commit()
                conn.close()
                
            logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.enabled = False
    
    async def start(self) -> None:
        """Start database writer task."""
        if not self.enabled:
            logger.info("Database persistence disabled")
            return
            
        logger.info("Starting database writer")
        self._writer_task = asyncio.create_task(self._writer_loop())
    
    async def stop(self) -> None:
        """Stop database writer and flush pending data."""
        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining data
        await self._flush_queue()
    
    async def store_sensor_sample(self, sensor_id: str, sample_data: Dict[str, Any]) -> None:
        """Store a sensor sample."""
        if not self.enabled:
            return
            
        record = {
            "table": "sensor_samples",
            "data": {
                "timestamp_ns": sample_data.get("ts", time.monotonic_ns()),
                "sensor_id": sensor_id,
                "vx": sample_data.get("vx", 0.0),
                "vy": sample_data.get("vy", 0.0),
                "vz": sample_data.get("vz", 0.0),
                "amplitude": sample_data.get("amp", 0.0),
                "rssi": sample_data.get("rssi"),
                "battery_level": sample_data.get("battery"),
                "calibrated": sample_data.get("calibrated", False),
            }
        }
        
        await self._queue_write(record)
    
    async def store_sensor_event(self, sensor_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Store a sensor event."""
        if not self.enabled:
            return
            
        record = {
            "table": "sensor_events",
            "data": {
                "timestamp_ns": event_data.get("timestamp_ns", time.monotonic_ns()),
                "sensor_id": sensor_id,
                "event_type": event_type,
                "event_data": json.dumps(event_data),
            }
        }
        
        await self._queue_write(record)
    
    async def store_impact_detection(self, sensor_id: str, impact_data: Dict[str, Any]) -> None:
        """Store an impact detection event."""
        if not self.enabled:
            return
            
        record = {
            "table": "impact_detections",
            "data": {
                "timestamp_ns": impact_data.get("timestamp_ns", time.monotonic_ns()),
                "sensor_id": sensor_id,
                "onset_timestamp_ns": impact_data.get("onset_timestamp_ns"),
                "peak_timestamp_ns": impact_data.get("peak_timestamp_ns"),
                "onset_magnitude": impact_data.get("onset_magnitude"),
                "peak_magnitude": impact_data.get("peak_magnitude"),
                "duration_ms": impact_data.get("duration_ms"),
                "confidence": impact_data.get("confidence"),
                "impact_data": json.dumps(impact_data),
            }
        }
        
        await self._queue_write(record)
    
    async def update_sensor_status(self, sensor_id: str, status_data: Dict[str, Any]) -> None:
        """Update sensor status information."""
        if not self.enabled:
            return
            
        record = {
            "table": "sensor_status",
            "operation": "upsert",
            "data": {
                "sensor_id": sensor_id,
                "last_seen_ns": status_data.get("last_sample_ns"),
                "connection_count": status_data.get("connection_count", 0),
                "total_samples": status_data.get("total_samples", 0),
                "calibrated": status_data.get("calibrated", False),
                "calibration_timestamp": status_data.get("calibration_timestamp"),
                "battery_level": status_data.get("battery_level"),
                "avg_rssi": status_data.get("avg_rssi"),
                "status_data": json.dumps(status_data),
            }
        }
        
        await self._queue_write(record)
    
    async def store_system_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Store a system-level event."""
        if not self.enabled:
            return
            
        record = {
            "table": "system_events",
            "data": {
                "timestamp_ns": event_data.get("timestamp_ns", time.monotonic_ns()),
                "event_type": event_type,
                "event_data": json.dumps(event_data),
            }
        }
        
        await self._queue_write(record)
    
    async def get_sensor_stats(self, sensor_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get sensor statistics for the past N hours."""
        if not self.enabled:
            return {}
            
        try:
            cutoff_ns = time.monotonic_ns() - (hours * 3600 * 1_000_000_000)
            
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                
                # Sample count and timing
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as sample_count,
                        MIN(timestamp_ns) as first_sample,
                        MAX(timestamp_ns) as last_sample,
                        AVG(amplitude) as avg_amplitude,
                        MAX(amplitude) as max_amplitude
                    FROM sensor_samples 
                    WHERE sensor_id = ? AND timestamp_ns > ?
                """, (sensor_id, cutoff_ns))
                
                stats = dict(cursor.fetchone())
                
                # Impact count
                cursor = conn.execute("""
                    SELECT COUNT(*) as impact_count
                    FROM impact_detections
                    WHERE sensor_id = ? AND timestamp_ns > ?
                """, (sensor_id, cutoff_ns))
                
                stats.update(dict(cursor.fetchone()))
                
                # Latest status
                cursor = conn.execute("""
                    SELECT * FROM sensor_status WHERE sensor_id = ?
                """, (sensor_id,))
                
                status_row = cursor.fetchone()
                if status_row:
                    stats["status"] = dict(status_row)
                
                conn.close()
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get sensor stats: {e}")
            return {}
    
    async def _queue_write(self, record: Dict[str, Any]) -> None:
        """Queue a write operation."""
        try:
            await self._write_queue.put(record)
        except Exception as e:
            logger.error(f"Failed to queue database write: {e}")
    
    async def _writer_loop(self) -> None:
        """Main writer loop with batching."""
        batch = []
        last_flush = time.monotonic()
        
        while True:
            try:
                # Wait for record or timeout
                try:
                    record = await asyncio.wait_for(
                        self._write_queue.get(),
                        timeout=self.flush_interval
                    )
                    batch.append(record)
                    
                except asyncio.TimeoutError:
                    # Flush on timeout even if batch not full
                    pass
                
                # Flush if batch is full or enough time has passed
                now = time.monotonic()
                if (len(batch) >= self.batch_size or 
                    (batch and now - last_flush >= self.flush_interval)):
                    
                    await self._write_batch(batch)
                    batch.clear()
                    last_flush = now
                    
            except asyncio.CancelledError:
                # Flush remaining records before exit
                if batch:
                    await self._write_batch(batch)
                break
                
            except Exception as e:
                logger.error(f"Database writer error: {e}")
                await asyncio.sleep(1.0)
    
    async def _write_batch(self, batch: List[Dict[str, Any]]) -> None:
        """Write a batch of records to database."""
        if not batch:
            return
            
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                
                for record in batch:
                    table = record["table"]
                    data = record["data"]
                    operation = record.get("operation", "insert")
                    
                    if operation == "upsert" and table == "sensor_status":
                        # Special handling for sensor status updates
                        placeholders = ", ".join([f"{k}=?" for k in data.keys()])
                        values = list(data.values())
                        
                        conn.execute(f"""
                            INSERT OR REPLACE INTO {table} 
                            ({", ".join(data.keys())})
                            VALUES ({", ".join(["?" for _ in data.keys()])})
                        """, values)
                        
                    else:
                        # Regular insert
                        placeholders = ", ".join(["?" for _ in data.keys()])
                        values = list(data.values())
                        
                        conn.execute(f"""
                            INSERT INTO {table} 
                            ({", ".join(data.keys())})
                            VALUES ({placeholders})
                        """, values)
                
                conn.commit()
                conn.close()
                
            logger.debug(f"Database batch written: {len(batch)} records")
            
        except Exception as e:
            logger.error(f"Database batch write failed: {e}")
    
    async def _flush_queue(self) -> None:
        """Flush any remaining queued records."""
        batch = []
        
        # Drain the queue
        while not self._write_queue.empty():
            try:
                record = self._write_queue.get_nowait()
                batch.append(record)
            except asyncio.QueueEmpty:
                break
        
        if batch:
            await self._write_batch(batch)