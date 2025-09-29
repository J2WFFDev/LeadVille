"""
WitMotion BT50 Sensor Data Parser (simple 5561)
Scaled with 0.000902 factor for TinTown compatibility.
"""
import struct
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

def parse_5561(data: bytes) -> Optional[Dict[str, Any]]:
    try:
        if len(data) < 44:
            logger.debug(f"Frame too short: {len(data)} bytes")
            return None
        if data[0] != 0x55 or data[1] != 0x61:
            logger.debug(f"Invalid header: {data[0]:02x} {data[1]:02x}")
            return None

        samples = []
        for i in range(2, min(len(data) - 5, 42), 6):
            if i + 6 <= len(data):
                ax_raw = struct.unpack('<h', data[i:i+2])[0]
                ay_raw = struct.unpack('<h', data[i+2:i+4])[0]
                az_raw = struct.unpack('<h', data[i+4:i+6])[0]
                scale = 0.000902
                vx = ax_raw * scale
                vy = ay_raw * scale
                vz = az_raw * scale
                samples.append({
                    'vx': vx, 'vy': vy, 'vz': vz,
                    'vx_raw': ax_raw, 'vy_raw': ay_raw, 'vz_raw': az_raw,
                    'raw': (ax_raw, ay_raw, az_raw),
                })

        if not samples:
            logger.debug("No samples parsed from frame")
            return None

        return {'frame_type': '5561', 'samples': samples, 'sample_count': len(samples)}
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return None

def calculate_magnitude(vx_raw: int, vy_raw: int, vz_raw: int) -> float:
    return (vx_raw**2 + vy_raw**2 + vz_raw**2)**0.5

def detect_impact_simple(samples: List[Dict], threshold: float = 150.0) -> bool:
    if not samples:
        return False
    for s in samples:
        if calculate_magnitude(s['vx_raw'], s['vy_raw'], s['vz_raw']) > threshold:
            return True
    return False