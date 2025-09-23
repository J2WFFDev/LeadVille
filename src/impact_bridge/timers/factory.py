"""
Timer adapter factory for creating timer instances.
"""

from typing import Literal, Dict, Any

from .base import ITimerAdapter
from .amg_commander import AMGCommanderAdapter
from .specialpie import SpecialPieAdapter

TimerType = Literal["amg", "specialpie"]


def create_timer(kind: TimerType, **kwargs) -> ITimerAdapter:
    """
    Create a timer adapter instance.
    
    Args:
        kind: Timer type ("amg" or "specialpie")
        **kwargs: Configuration arguments passed to the adapter
        
    Returns:
        ITimerAdapter instance
        
    Raises:
        ValueError: If timer type is not supported
    """
    if kind == "amg":
        return AMGCommanderAdapter(**kwargs)
    elif kind == "specialpie":
        return SpecialPieAdapter(**kwargs)
    else:
        raise ValueError(f"Unsupported timer type: {kind}. Supported types: amg, specialpie")


def get_supported_timers() -> list[str]:
    """Get list of supported timer types."""
    return ["amg", "specialpie"]


def get_timer_info(kind: TimerType) -> Dict[str, Any]:
    """
    Get information about a timer type.
    
    Args:
        kind: Timer type
        
    Returns:
        Dictionary with timer information
    """
    info = {
        "amg": {
            "name": "AMG Commander",
            "connection_types": ["ble"],
            "description": "AMG Labs Commander shot timer with BLE connectivity",
            "protocols": ["AMG BLE Protocol"],
            "features": ["shot_timing", "string_timing", "battery_status"]
        },
        "specialpie": {
            "name": "SpecialPie Timer",
            "connection_types": ["serial", "ble", "udp"],
            "description": "SpecialPie shot timer with multiple connectivity options",
            "protocols": ["SpecialPie Protocol"],
            "features": ["shot_timing", "string_timing", "battery_status", "clock_sync", "simulator"]
        }
    }
    
    return info.get(kind, {})