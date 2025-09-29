"""
Device Pool Management Models
Implements temporary device assignment system for shared BLE device resources.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, CheckConstraint, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class DevicePoolStatus(enum.Enum):
    """Device availability status in the pool"""
    available = "available"      # Device is in pool and can be leased
    leased = "leased"           # Device is currently leased to a session
    offline = "offline"         # Device is not responding/unavailable
    maintenance = "maintenance"  # Device is removed for maintenance

class SessionStatus(enum.Enum):
    """Active session status"""
    active = "active"           # Session is running with devices connected
    idle = "idle"              # Session exists but devices not connected
    ended = "ended"            # Session completed, devices should be released

class DevicePool(Base):
    """Shared pool of BLE devices available for temporary assignment"""
    __tablename__ = 'device_pool'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hw_addr = Column(String(17), nullable=False, unique=True)  # MAC address
    device_type = Column(String(20), nullable=False)  # 'timer', 'sensor', 'other'
    label = Column(String(100), nullable=False)
    vendor = Column(String(50), nullable=True)  # 'WitMotion', 'AMG', etc.
    model = Column(String(50), nullable=True)   # 'BT50', 'AMGTimer', etc.
    status = Column(String(20), nullable=False, default="available")  # Use string instead of enum temporarily
    last_seen = Column(DateTime, nullable=True)
    battery = Column(Integer, nullable=True)  # Battery percentage
    rssi = Column(Integer, nullable=True)     # Signal strength
    notes = Column(Text, nullable=True)       # Administrative notes
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    device_leases = relationship("DeviceLease", back_populates="device", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("battery >= 0 AND battery <= 100", name='check_pool_device_battery'),
        CheckConstraint("rssi >= -100 AND rssi <= 0", name='check_pool_device_rssi'),
        CheckConstraint("device_type IN ('timer', 'sensor', 'shot_timer', 'other')", name='check_device_type'),
        Index('idx_pool_hw_addr', 'hw_addr'),
        Index('idx_pool_status', 'status'),
        Index('idx_pool_device_type', 'device_type'),
        Index('idx_pool_last_seen', 'last_seen'),
    )

class ActiveSession(Base):
    """Active bridge sessions managing temporary device assignments"""
    __tablename__ = 'active_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_name = Column(String(100), nullable=False)  # Human-readable session name
    bridge_id = Column(Integer, nullable=False)  # Removed FK constraint temporarily
    stage_id = Column(Integer, nullable=True)   # Removed FK constraint temporarily
    status = Column(String(20), nullable=False, default="idle")  # Use string instead of enum temporarily
    started_at = Column(DateTime, nullable=False, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=False, default=func.now())
    notes = Column(Text, nullable=True)
    
    # Relationships  
    device_leases = relationship("DeviceLease", back_populates="session", cascade="all, delete-orphan")
    # Use string references for models in other modules to avoid circular imports
    # bridge = relationship("Bridge", foreign_keys=[bridge_id])
    # stage = relationship("Stage", foreign_keys=[stage_id])
    
    __table_args__ = (
        Index('idx_session_bridge', 'bridge_id'),
        Index('idx_session_status', 'status'),
        Index('idx_session_started', 'started_at'),
        Index('idx_session_stage', 'stage_id'),
    )

class DeviceLease(Base):
    """Temporary assignment of pool devices to active sessions"""
    __tablename__ = 'device_leases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('device_pool.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('active_sessions.id'), nullable=False)
    target_assignment = Column(String(50), nullable=True)  # "Target 1", "Timer", etc.
    leased_at = Column(DateTime, nullable=False, default=func.now())
    released_at = Column(DateTime, nullable=True)
    is_connected = Column(Boolean, nullable=False, default=False)  # Bridge connection status
    connection_attempts = Column(Integer, nullable=False, default=0)
    last_connection_attempt = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    device = relationship("DevicePool", back_populates="device_leases")
    session = relationship("ActiveSession", back_populates="device_leases")
    
    __table_args__ = (
        # Ensure a device can only be leased to one active session
        CheckConstraint("released_at IS NULL OR released_at >= leased_at", name='check_lease_dates'),
        Index('idx_lease_device', 'device_id'),
        Index('idx_lease_session', 'session_id'),
        Index('idx_lease_active', 'device_id', 'released_at'),  # For finding active leases
        Index('idx_lease_leased_at', 'leased_at'),
    )

class DevicePoolEvent(Base):
    """Event log for device pool operations (leasing, releasing, status changes)"""
    __tablename__ = 'device_pool_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('device_pool.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('active_sessions.id'), nullable=True)
    event_type = Column(String(20), nullable=False)  # 'lease', 'release', 'connect', 'disconnect', 'status_change'
    event_data = Column(Text, nullable=True)  # JSON data for event details
    timestamp = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    device = relationship("DevicePool", foreign_keys=[device_id])
    session = relationship("ActiveSession", foreign_keys=[session_id])
    
    __table_args__ = (
        CheckConstraint("event_type IN ('lease', 'release', 'connect', 'disconnect', 'status_change', 'discovered', 'error')", 
                       name='check_event_type'),
        Index('idx_pool_event_device', 'device_id'),
        Index('idx_pool_event_session', 'session_id'), 
        Index('idx_pool_event_timestamp', 'timestamp'),
        Index('idx_pool_event_type', 'event_type'),
    )