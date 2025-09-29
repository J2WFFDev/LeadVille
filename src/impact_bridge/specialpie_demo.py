"""
SpecialPie Timer Demo/Simulator
Simulates SpecialPie timer discovery and shot data for testing purposes
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/demo/specialpie", tags=["SpecialPie Demo"])

# Demo SpecialPie timer data
DEMO_SPECIALPIE_TIMERS = [
    {
        "address": "AA:BB:CC:DD:EE:01",
        "name": "SpecialPie M1A2",
        "type": "shot_timer",
        "vendor": "SpecialPie",
        "battery": 85,
        "rssi": -45,
        "pairable": True,
        "connected": False,
        "monitoring": False
    },
    {
        "address": "AA:BB:CC:DD:EE:02", 
        "name": "SP-M1A2 Timer",
        "type": "shot_timer",
        "vendor": "SpecialPie",
        "battery": 72,
        "rssi": -52,
        "pairable": True,
        "connected": False,
        "monitoring": False
    }
]

# Demo shot data
DEMO_SHOT_DATA = [
    {"shot": 1, "time": "0.00", "split": "0.00"},
    {"shot": 2, "time": "1.33", "split": "1.33"},
    {"shot": 3, "time": "1.65", "split": "0.32"},
    {"shot": 4, "time": "1.94", "split": "0.29"},
    {"shot": 5, "time": "2.23", "split": "0.29"},
    {"shot": 6, "time": "2.84", "split": "0.61"}
]

@router.get("/discover")
async def demo_discover_specialpie():
    """Demo endpoint showing SpecialPie timer discovery"""
    return {
        "discovered_devices": DEMO_SPECIALPIE_TIMERS,
        "count": len(DEMO_SPECIALPIE_TIMERS),
        "scan_duration": 5,
        "note": "This is demo data - actual discovery requires Bluetooth adapter"
    }

@router.get("/timers")
async def demo_get_timers():
    """Demo endpoint showing SpecialPie timer management"""
    return {
        "timers": DEMO_SPECIALPIE_TIMERS,
        "total_count": len(DEMO_SPECIALPIE_TIMERS),
        "connected_count": sum(1 for t in DEMO_SPECIALPIE_TIMERS if t.get('connected')),
        "note": "Demo data - shows how SpecialPie timers would appear in the system"
    }

@router.post("/timers/{address}/connect")
async def demo_connect_timer(address: str):
    """Demo timer connection"""
    timer = next((t for t in DEMO_SPECIALPIE_TIMERS if t["address"] == address), None)
    if not timer:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    timer["connected"] = True
    return {
        "address": address,
        "connected": True,
        "message": "Demo connection successful - SpecialPie timer ready",
        "characteristic": "0000fff1-0000-1000-8000-00805f9b34fb"
    }

@router.post("/timers/{address}/start_monitoring")
async def demo_start_monitoring(address: str):
    """Demo shot monitoring"""
    timer = next((t for t in DEMO_SPECIALPIE_TIMERS if t["address"] == address), None)
    if not timer:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    timer["monitoring"] = True
    return {
        "address": address,
        "monitoring": True,
        "message": "Demo monitoring started - ready to capture shots",
        "protocol_notes": {
            "shot_command": "0x36 (54) - Contains shot timing data",
            "start_command": "0x34 (52) - String start event", 
            "stop_command": "0x18 (24) - String stop event",
            "data_format": "hex bytes -> int array -> timing extraction"
        }
    }

@router.get("/timers/{address}/shots")
async def demo_get_shots(address: str):
    """Demo shot data retrieval"""
    timer = next((t for t in DEMO_SPECIALPIE_TIMERS if t["address"] == address), None)
    if not timer:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    return {
        "address": address,
        "timer_name": timer["name"],
        "shots": DEMO_SHOT_DATA,
        "total_shots": len(DEMO_SHOT_DATA),
        "string_time": "2.84s",
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Demo shot data based on SpecialPie protocol examples"
    }

@router.get("/protocol")
async def demo_protocol_info():
    """Show SpecialPie protocol implementation details"""
    return {
        "protocol": "SpecialPie SP M1A2 BLE Shot Timer",
        "implementation": {
            "ble_service": "0000fff0-0000-1000-8000-00805f9b34fb",
            "notification_characteristic": "0000fff1-0000-1000-8000-00805f9b34fb",
            "data_processing": {
                "raw_data": "bytearray -> hex string -> int array",
                "shot_detection": "int_values[2] == 54 (0x36)",
                "timing_extraction": "seconds: int_values[4], ms: int_values[5]",
                "shot_number": "int_values[6]",
                "split_calculation": "current_time - previous_time"
            },
            "event_types": {
                "shot": "54 (0x36) - Shot with timing data",
                "start": "52 (0x34) - String start",  
                "stop": "24 (0x18) - String stop"
            }
        },
        "features": [
            "Real-time shot detection",
            "Millisecond precision timing", 
            "Automatic split calculation",
            "String start/stop events",
            "Multi-shot sequence tracking"
        ],
        "status": "✅ Implementation complete - awaiting hardware testing"
    }