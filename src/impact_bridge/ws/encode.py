"""
WebSocket event encoding for timer events.

Normalizes timer events into JSON format for frontend consumption.
"""

import json
import time
from typing import Dict, Any, Optional
from dataclasses import asdict

from ..timers.types import (
    TimerEvent, TimerConnected, TimerDisconnected, TimerReady,
    Shot, StringStart, StringStop, Battery, ClockSync
)


def encode_timer_event(event: TimerEvent, source: str) -> Dict[str, Any]:
    """
    Encode a timer event for WebSocket transmission.
    
    Args:
        event: Timer event to encode
        source: Timer adapter name (e.g., "amg", "specialpie")
        
    Returns:
        Dictionary ready for JSON serialization
    """
    base_data = {
        "source": source,
        "t_ms": event.timestamp_ms,
        "raw": event.raw
    }
    
    if isinstance(event, TimerConnected):
        return {
            "type": "timer_connected",
            **base_data,
            "info": asdict(event.info)
        }
    
    elif isinstance(event, TimerDisconnected):
        return {
            "type": "timer_disconnected", 
            **base_data,
            "reason": event.reason
        }
    
    elif isinstance(event, TimerReady):
        return {
            "type": "timer_ready",
            **base_data
        }
    
    elif isinstance(event, Shot):
        return {
            "type": "shot",
            **base_data,
            "split_ms": event.split_ms,
            "shot_number": event.shot_number,
            "string_number": event.string_number
        }
    
    elif isinstance(event, StringStart):
        return {
            "type": "string_start",
            **base_data,
            "string_number": event.string_number
        }
    
    elif isinstance(event, StringStop):
        return {
            "type": "string_stop", 
            **base_data,
            "total_ms": event.total_ms,
            "shot_count": event.shot_count,
            "string_number": event.string_number
        }
    
    elif isinstance(event, Battery):
        return {
            "type": "battery",
            **base_data,
            "level_pct": event.level_pct
        }
    
    elif isinstance(event, ClockSync):
        return {
            "type": "clock_sync",
            **base_data, 
            "delta_ms": event.delta_ms,
            "device_time_ms": event.device_time_ms,
            "host_time_ms": event.host_time_ms
        }
    
    else:
        # Unknown event type
        return {
            "type": "unknown",
            **base_data,
            "event_class": event.__class__.__name__
        }


def encode_timer_event_json(event: TimerEvent, source: str) -> str:
    """
    Encode a timer event as JSON string for WebSocket transmission.
    
    Args:
        event: Timer event to encode
        source: Timer adapter name
        
    Returns:
        JSON string ready to send over WebSocket
    """
    data = encode_timer_event(event, source)
    return json.dumps(data, separators=(',', ':'))


class TimerEventEncoder:
    """
    Stateful encoder for timer events with additional context tracking.
    """
    
    def __init__(self, source: str):
        self.source = source
        self.connection_start_time: Optional[int] = None
        self.last_event_time: Optional[int] = None
        
    def encode(self, event: TimerEvent) -> Dict[str, Any]:
        """Encode event with additional context."""
        encoded = encode_timer_event(event, self.source)
        
        # Add connection context
        if isinstance(event, TimerConnected):
            self.connection_start_time = event.timestamp_ms
        
        if self.connection_start_time:
            encoded["connection_uptime_ms"] = event.timestamp_ms - self.connection_start_time
        
        # Add timing context
        if self.last_event_time:
            encoded["since_last_event_ms"] = event.timestamp_ms - self.last_event_time
        
        self.last_event_time = event.timestamp_ms
        
        return encoded
    
    def encode_json(self, event: TimerEvent) -> str:
        """Encode event as JSON with context."""
        data = self.encode(event)
        return json.dumps(data, separators=(',', ':'))