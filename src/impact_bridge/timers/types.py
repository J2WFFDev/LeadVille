"""
Timer event types and data structures for the timer adapter system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class ConnectionType(Enum):
    """Timer connection transport types."""
    SERIAL = "serial"
    BLE = "ble"
    UDP = "udp"


@dataclass
class TimerInfo:
    """Timer device information."""
    model: str
    firmware_version: str
    connection_type: ConnectionType
    serial_number: Optional[str] = None
    battery_level: Optional[int] = None


# Base timer event
@dataclass
class TimerEvent:
    """Base class for all timer events."""
    timestamp_ms: int  # Host-adjusted milliseconds since epoch
    raw: Dict[str, Any]  # Raw frame data for debugging


@dataclass
class TimerConnected(TimerEvent):
    """Timer connected successfully."""
    info: TimerInfo


@dataclass
class TimerDisconnected(TimerEvent):
    """Timer disconnected."""
    reason: str


@dataclass
class TimerReady(TimerEvent):
    """Timer is ready to start timing."""
    pass


@dataclass
class Shot(TimerEvent):
    """Shot detected event."""
    split_ms: Optional[int]  # Split time in milliseconds
    shot_number: Optional[int] = None
    string_number: Optional[int] = None


@dataclass
class StringStart(TimerEvent):
    """String/sequence started."""
    string_number: Optional[int] = None


@dataclass
class StringStop(TimerEvent):
    """String/sequence stopped."""
    total_ms: int  # Total string time in milliseconds
    shot_count: int
    string_number: Optional[int] = None


@dataclass
class Battery(TimerEvent):
    """Battery level update."""
    level_pct: int


@dataclass
class ClockSync(TimerEvent):
    """Clock synchronization event."""
    delta_ms: int  # device_time - host_time in milliseconds
    device_time_ms: int
    host_time_ms: int