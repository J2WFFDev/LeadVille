"""
SQLAlchemy Database Models for LeadVille Impact Bridge

Based on InterfaceLayer.md specification and GitHub issue #4 implementation.
Includes authentication models for JWT-based role-based access control.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Float, Text, Boolean,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, JSON, Enum as SqlEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

Base = declarative_base()


class Role(str, Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"          # Full system access
    RO = "ro"               # Range Officer - stage management  
    SCOREKEEPER = "scorekeeper"  # Results management
    VIEWER = "viewer"       # Read-only access
    COACH = "coach"         # Coach notes and observations


class Node(Base):
    """Bridge Host (Raspberry Pi) node information"""
    __tablename__ = 'nodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    mode = Column(String(20), nullable=False)  # 'online' or 'offline'
    ssid = Column(String(100), nullable=True)
    ip_addr = Column(String(45), nullable=True)  # IPv4 or IPv6
    versions = Column(JSON, nullable=True)  # Software/firmware versions
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    sensors = relationship("Sensor", back_populates="node", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("mode IN ('online', 'offline')", name='check_node_mode'),
        Index('idx_node_name', 'name'),
    )


class Sensor(Base):
    """BLE sensor device information"""
    __tablename__ = 'sensors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hw_addr = Column(String(17), nullable=False, unique=True)  # MAC address
    label = Column(String(100), nullable=False)
    node_id = Column(Integer, ForeignKey('nodes.id'), nullable=True)
    target_id = Column(Integer, ForeignKey('targets.id'), nullable=True)
    calib = Column(JSON, nullable=True)  # Calibration data
    last_seen = Column(DateTime, nullable=True)
    battery = Column(Integer, nullable=True)  # Battery percentage
    rssi = Column(Integer, nullable=True)  # Signal strength
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    node = relationship("Node", back_populates="sensors")
    target = relationship("Target", back_populates="sensor")
    sensor_events = relationship("SensorEvent", back_populates="sensor", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("battery >= 0 AND battery <= 100", name='check_sensor_battery'),
        CheckConstraint("rssi >= -100 AND rssi <= 0", name='check_sensor_rssi'),
        Index('idx_sensor_hw_addr', 'hw_addr'),
        Index('idx_sensor_target', 'target_id'),
        Index('idx_sensor_last_seen', 'last_seen'),
    )


class Target(Base):
    """Physical target (steel plate) information"""
    __tablename__ = 'targets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_id = Column(Integer, ForeignKey('stages.id'), nullable=False)
    name = Column(String(100), nullable=False)
    geometry = Column(JSON, nullable=True)  # Shape, size, position data
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    stage = relationship("Stage", back_populates="targets")
    sensor = relationship("Sensor", back_populates="target", uselist=False)
    
    __table_args__ = (
        Index('idx_target_stage', 'stage_id'),
        UniqueConstraint('stage_id', 'name', name='uq_target_stage_name'),
    )


class Stage(Base):
    """Competition stage information"""
    __tablename__ = 'stages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    name = Column(String(100), nullable=False)
    number = Column(Integer, nullable=False)
    layout_json = Column(JSON, nullable=True)  # Stage layout configuration
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="stages")
    targets = relationship("Target", back_populates="stage", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="stage", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_stage_match', 'match_id'),
        Index('idx_stage_number', 'number'),
        UniqueConstraint('match_id', 'number', name='uq_stage_match_number'),
    )


class Match(Base):
    """Competition match information"""
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=True)
    metadata_json = Column(JSON, nullable=True)  # Additional match data
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    stages = relationship("Stage", back_populates="match", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="match", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_match_date', 'date'),
        Index('idx_match_name', 'name'),
    )


class TimerEvent(Base):
    """Timer events (START/SHOT/STOP)"""
    __tablename__ = 'timer_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime, nullable=False)
    type = Column(String(20), nullable=False)  # 'START', 'SHOT', 'STOP'
    raw = Column(Text, nullable=True)  # Raw timer data
    run_id = Column(Integer, ForeignKey('runs.id'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    run = relationship("Run", back_populates="timer_events")
    
    __table_args__ = (
        CheckConstraint("type IN ('START', 'SHOT', 'STOP')", name='check_timer_event_type'),
        Index('idx_timer_event_ts', 'ts_utc'),
        Index('idx_timer_event_run', 'run_id'),
        Index('idx_timer_event_type', 'type'),
    )


class SensorEvent(Base):
    """Sensor impact events"""
    __tablename__ = 'sensor_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_utc = Column(DateTime, nullable=False)
    sensor_id = Column(Integer, ForeignKey('sensors.id'), nullable=False)
    magnitude = Column(Float, nullable=False)
    features_json = Column(JSON, nullable=True)  # Additional sensor data
    run_id = Column(Integer, ForeignKey('runs.id'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    sensor = relationship("Sensor", back_populates="sensor_events")
    run = relationship("Run", back_populates="sensor_events")
    
    __table_args__ = (
        CheckConstraint("magnitude >= 0", name='check_sensor_event_magnitude'),
        Index('idx_sensor_event_ts', 'ts_utc'),
        Index('idx_sensor_event_sensor', 'sensor_id'),
        Index('idx_sensor_event_run', 'run_id'),
        Index('idx_sensor_event_magnitude', 'magnitude'),
    )


class Run(Base):
    """Individual shooter run"""
    __tablename__ = 'runs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    stage_id = Column(Integer, ForeignKey('stages.id'), nullable=False)
    shooter_id = Column(Integer, ForeignKey('shooters.id'), nullable=False)
    started_ts = Column(DateTime, nullable=True)
    ended_ts = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    annotations_json = Column(JSON, nullable=True)  # Run annotations
    audit_json = Column(JSON, nullable=True)  # Audit trail
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    match = relationship("Match", back_populates="runs")
    stage = relationship("Stage", back_populates="runs")
    shooter = relationship("Shooter", back_populates="runs")
    timer_events = relationship("TimerEvent", back_populates="run", cascade="all, delete-orphan")
    sensor_events = relationship("SensorEvent", back_populates="run", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="run", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'active', 'completed', 'cancelled')", name='check_run_status'),
        Index('idx_run_match', 'match_id'),
        Index('idx_run_stage', 'stage_id'),
        Index('idx_run_shooter', 'shooter_id'),
        Index('idx_run_status', 'status'),
        Index('idx_run_started', 'started_ts'),
    )


class Shooter(Base):
    """Shooter/competitor information"""
    __tablename__ = 'shooters'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    squad = Column(String(100), nullable=True)
    metadata_json = Column(JSON, nullable=True)  # Additional shooter data
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    runs = relationship("Run", back_populates="shooter", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_shooter_name', 'name'),
        Index('idx_shooter_squad', 'squad'),
    )


class Note(Base):
    """Notes and annotations for runs"""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey('runs.id'), nullable=False)
    author_role = Column(String(50), nullable=False)  # 'ro', 'scorekeeper', 'coach', etc.
    content = Column(Text, nullable=False)
    ts_utc = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    run = relationship("Run", back_populates="notes")
    
    __table_args__ = (
        CheckConstraint("author_role IN ('admin', 'ro', 'scorekeeper', 'viewer', 'coach')", name='check_note_author_role'),
        Index('idx_note_run', 'run_id'),
        Index('idx_note_author', 'author_role'),
        Index('idx_note_ts', 'ts_utc'),
    )


class User(Base):
    """User account with role-based access control"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(SqlEnum(Role), nullable=False, default=Role.VIEWER)
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)  # Default accounts created on first boot
    
    # Security fields
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=False, default=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    created_users = relationship("User", remote_side=[id])
    
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
        CheckConstraint('failed_login_attempts >= 0', name='check_failed_attempts_positive'),
    )
    
    def set_password(self, password: str) -> None:
        """Set user password with secure hashing"""
        from ..auth.utils import hash_password
        self.password_hash = hash_password(password)
        self.password_changed_at = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        from ..auth.utils import verify_password
        return verify_password(password, self.password_hash)
    
    def is_locked(self) -> bool:
        """Check if account is locked due to failed attempts"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def increment_failed_attempts(self) -> None:
        """Increment failed login attempts and lock if needed"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 15 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
    
    def clear_failed_attempts(self) -> None:
        """Clear failed attempts on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()
    
    def has_permission(self, required_role: 'Role') -> bool:
        """Check if user has required role permissions (hierarchical)"""
        if not self.is_active or self.is_locked():
            return False
            
        role_hierarchy = {
            Role.ADMIN: 5,
            Role.RO: 4,
            Role.SCOREKEEPER: 3, 
            Role.COACH: 2,
            Role.VIEWER: 1
        }
        
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level


class UserSession(Base):
    """User session management for JWT tokens"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token_jti = Column(String(36), nullable=False, unique=True)  # JWT ID
    refresh_token_hash = Column(String(255), nullable=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    login_method = Column(String(20), nullable=False, default='password')
    
    # Session lifecycle
    created_at = Column(DateTime, nullable=False, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, nullable=False, default=func.now())
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_session_token', 'token_jti'),
        Index('idx_session_user', 'user_id'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_revoked', 'revoked_at'),
    )
    
    def is_active(self) -> bool:
        """Check if session is still active"""
        now = datetime.utcnow()
        return (
            self.revoked_at is None and
            self.expires_at > now
        )
    
    def revoke(self) -> None:
        """Revoke the session"""
        self.revoked_at = datetime.utcnow()
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
    
    def generate_refresh_token(self) -> str:
        """Generate and store refresh token"""
        refresh_token_hash = secrets.token_urlsafe(32)
        from ..auth.utils import hash_password
        self.refresh_token_hash = hash_password(refresh_token_hash)
        return refresh_token_hash
    
    def verify_refresh_token(self, token: str) -> bool:
        """Verify refresh token"""
        if self.refresh_token_hash is None:
            return False
        from ..auth.utils import verify_password
        return verify_password(token, self.refresh_token_hash)