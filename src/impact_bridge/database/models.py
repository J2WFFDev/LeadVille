"""SQLAlchemy models for LeadVille Impact Bridge."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Float,
    JSON,
    Boolean,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Node(Base):
    """System nodes (Raspberry Pi units)."""
    
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    mode = Column(String(50), nullable=False)  # online, offline, simulation
    ssid = Column(String(100))
    ip_addr = Column(String(45))  # IPv6 compatible
    versions = Column(JSON)  # Software version information
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    sensors = relationship("Sensor", back_populates="node")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("mode IN ('online', 'offline', 'simulation')", name="check_node_mode"),
        Index("idx_node_name", "name"),
        Index("idx_node_mode", "mode"),
    )


class Sensor(Base):
    """BT50 sensor devices."""
    
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True)
    hw_addr = Column(String(17), nullable=False, unique=True)  # MAC address
    label = Column(String(100), nullable=False)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    calib = Column(JSON)  # Calibration data
    last_seen = Column(DateTime)
    battery = Column(Float)  # Battery percentage
    rssi = Column(Integer)  # Signal strength
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    target = relationship("Target", back_populates="sensors")
    node = relationship("Node", back_populates="sensors")
    sensor_events = relationship("SensorEvent", back_populates="sensor")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("battery >= 0 AND battery <= 100", name="check_sensor_battery"),
        CheckConstraint("rssi >= -100 AND rssi <= 0", name="check_sensor_rssi"),
        Index("idx_sensor_hw_addr", "hw_addr"),
        Index("idx_sensor_target", "target_id"),
        Index("idx_sensor_last_seen", "last_seen"),
    )


class Target(Base):
    """Shooting targets."""
    
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False)
    name = Column(String(100), nullable=False)
    geometry = Column(JSON)  # Target geometry and scoring zones
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    stage = relationship("Stage", back_populates="targets")
    sensors = relationship("Sensor", back_populates="target")
    
    # Constraints
    __table_args__ = (
        Index("idx_target_stage", "stage_id"),
        Index("idx_target_name", "name"),
    )


class Stage(Base):
    """Match stages."""
    
    __tablename__ = "stages"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    name = Column(String(100), nullable=False)
    number = Column(Integer, nullable=False)
    layout_json = Column(JSON)  # Stage layout and configuration
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="stages")
    targets = relationship("Target", back_populates="stage")
    runs = relationship("Run", back_populates="stage")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("number > 0", name="check_stage_number_positive"),
        Index("idx_stage_match", "match_id"),
        Index("idx_stage_number", "match_id", "number"),
    )


class Match(Base):
    """Shooting matches/competitions."""
    
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False)
    location = Column(String(200))
    metadata_json = Column(JSON)  # Match-specific metadata
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    stages = relationship("Stage", back_populates="match")
    runs = relationship("Run", back_populates="match")
    
    # Constraints
    __table_args__ = (
        Index("idx_match_date", "date"),
        Index("idx_match_name", "name"),
    )


class TimerEvent(Base):
    """AMG timer events."""
    
    __tablename__ = "timer_events"
    
    id = Column(Integer, primary_key=True)
    ts_utc = Column(DateTime, nullable=False)
    type = Column(String(50), nullable=False)  # START, SHOT, STOP
    raw = Column(String(500))  # Raw timer data
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    run = relationship("Run", back_populates="timer_events")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("type IN ('START', 'SHOT', 'STOP', 'READY')", name="check_timer_event_type"),
        Index("idx_timer_event_ts", "ts_utc"),
        Index("idx_timer_event_run", "run_id"),
        Index("idx_timer_event_type", "type"),
    )


class SensorEvent(Base):
    """BT50 sensor impact events."""
    
    __tablename__ = "sensor_events"
    
    id = Column(Integer, primary_key=True)
    ts_utc = Column(DateTime, nullable=False)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    magnitude = Column(Float, nullable=False)
    features_json = Column(JSON)  # Impact features and analysis
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    sensor = relationship("Sensor", back_populates="sensor_events")
    run = relationship("Run", back_populates="sensor_events")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("magnitude >= 0", name="check_sensor_magnitude_positive"),
        Index("idx_sensor_event_ts", "ts_utc"),
        Index("idx_sensor_event_sensor", "sensor_id"),
        Index("idx_sensor_event_run", "run_id"),
        Index("idx_sensor_event_magnitude", "magnitude"),
    )


class Run(Base):
    """Individual shooter runs through stages."""
    
    __tablename__ = "runs"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False)
    shooter_id = Column(Integer, ForeignKey("shooters.id"), nullable=False)
    started_ts = Column(DateTime)
    ended_ts = Column(DateTime)
    status = Column(String(50), nullable=False, default="pending")
    annotations_json = Column(JSON)  # RO annotations and penalties
    audit_json = Column(JSON)  # Audit trail for the run
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="runs")
    stage = relationship("Stage", back_populates="runs")
    shooter = relationship("Shooter", back_populates="runs")
    timer_events = relationship("TimerEvent", back_populates="run")
    sensor_events = relationship("SensorEvent", back_populates="run")
    notes = relationship("Note", back_populates="run")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'completed', 'dnf', 'dq')", 
            name="check_run_status"
        ),
        CheckConstraint(
            "ended_ts IS NULL OR started_ts IS NULL OR ended_ts >= started_ts",
            name="check_run_time_order"
        ),
        Index("idx_run_match", "match_id"),
        Index("idx_run_stage", "stage_id"),
        Index("idx_run_shooter", "shooter_id"),
        Index("idx_run_status", "status"),
        Index("idx_run_started", "started_ts"),
    )


class Shooter(Base):
    """Shooters/competitors."""
    
    __tablename__ = "shooters"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    squad = Column(String(100))
    metadata_json = Column(JSON)  # Additional shooter info (division, class, etc.)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    runs = relationship("Run", back_populates="shooter")
    notes = relationship("Note", back_populates="shooter", foreign_keys="Note.shooter_id")
    
    # Constraints
    __table_args__ = (
        Index("idx_shooter_name", "name"),
        Index("idx_shooter_squad", "squad"),
    )


class Note(Base):
    """Notes and annotations for runs."""
    
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    author_role = Column(String(50), nullable=False)  # RO, CRO, Stats Officer, etc.
    content = Column(Text, nullable=False)
    shooter_id = Column(Integer, ForeignKey("shooters.id"), nullable=True)  # For shooter-specific notes
    ts_utc = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    run = relationship("Run", back_populates="notes")
    shooter = relationship("Shooter", foreign_keys=[shooter_id])
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "author_role IN ('RO', 'CRO', 'MD', 'Stats', 'Scorekeeper', 'System')",
            name="check_note_author_role"
        ),
        Index("idx_note_run", "run_id"),
        Index("idx_note_ts", "ts_utc"),
        Index("idx_note_author", "author_role"),
    )