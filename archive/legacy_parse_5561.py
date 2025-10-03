"""Legacy WitMotion BT50 multi-sample parser.

This module preserves the retired `parse_5561` implementation for reference in
archived tooling. Active bridge code should rely on
`impact_bridge.ble.parsers.parse_bt50_frame` instead.
"""

import logging
import struct
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def parse_5561(data: bytes) -> Optional[Dict[str, Any]]:
    try:
        if len(data) < 8:
            logger.debug("Frame too short: %s bytes", len(data))
            return None
        if data[0] != 0x55 or data[1] != 0x61:
            logger.debug("Invalid header: %02x %02x", data[0], data[1])
            return None

        samples: List[Dict[str, Any]] = []
        for i in range(2, min(len(data) - 5, 42), 6):
            if i + 6 <= len(data):
                ax_raw = struct.unpack('<h', data[i : i + 2])[0]
                ay_raw = struct.unpack('<h', data[i + 2 : i + 4])[0]
                az_raw = struct.unpack('<h', data[i + 4 : i + 6])[0]
                samples.append(
                    {
                        "vx": ax_raw,
                        "vy": ay_raw,
                        "vz": az_raw,
                        "vx_raw": ax_raw,
                        "vy_raw": ay_raw,
                        "vz_raw": az_raw,
                        "raw": (ax_raw, ay_raw, az_raw),
                    }
                )

        if not samples:
            logger.debug("No samples parsed from frame")
            return None

        return {"frame_type": "5561", "samples": samples, "sample_count": len(samples)}
    except Exception as exc:
        logger.error("Parse error: %s", exc)
        return None

def calculate_magnitude(vx_raw: int, vy_raw: int, vz_raw: int) -> float:
    return (vx_raw ** 2 + vy_raw ** 2 + vz_raw ** 2) ** 0.5

def detect_impact_simple(samples: List[Dict[str, Any]], threshold: float = 150.0) -> bool:
    if not samples:
        return False
    for sample in samples:
        if calculate_magnitude(sample['vx_raw'], sample['vy_raw'], sample['vz_raw']) > threshold:
            return True
    return False
