"""
Timer adapter system for LeadVille Impact Bridge.

Provides standardized interfaces for shot timer integration with support for:
- AMG Commander (BLE)
- SpecialPie Timer (Serial, BLE, UDP simulator)
- Extensible adapter system for additional timers
"""

from .base import ITimerAdapter, BaseTimerAdapter
from .types import (
    TimerEvent, TimerInfo, ConnectionType,
    TimerConnected, TimerDisconnected, TimerReady,
    Shot, StringStart, StringStop, Battery, ClockSync
)
from .factory import create_timer, get_supported_timers, get_timer_info, TimerType
from .amg_commander import AMGCommanderAdapter
from .specialpie import SpecialPieAdapter

__all__ = [
    # Interfaces
    'ITimerAdapter',
    'BaseTimerAdapter',
    
    # Event types
    'TimerEvent',
    'TimerInfo',
    'ConnectionType',
    'TimerConnected',
    'TimerDisconnected', 
    'TimerReady',
    'Shot',
    'StringStart',
    'StringStop',
    'Battery',
    'ClockSync',
    
    # Factory
    'create_timer',
    'get_supported_timers',
    'get_timer_info',
    'TimerType',
    
    # Adapters
    'AMGCommanderAdapter',
    'SpecialPieAdapter',
]