"""Parser for WTVB01 / WitMotion BT50 structured packets (0x55 0x61 frames).

Provides a small helper `parse_5561(payload: bytes) -> Optional[Dict]` that scans a
notification payload for 0x55 0x61 framed records and extracts VX/VY/VZ samples.

Return value (when frames found):
  {
    'samples': [{'vx': float, 'vy': float, 'vz': float, 'raw': (vx_raw, vy_raw, vz_raw)}, ...],
    'VX': avg_vx, 'VY': avg_vy, 'VZ': avg_vz
  }

CALIBRATED: Scale factor 0.000425 based on gravity reference calibration 20250909_165201.
Frame structure: 32-byte frames, acceleration at offsets 14, 16, 26 (X, Y, Z).
"""

from __future__ import annotations

import struct
from typing import Optional, List, Dict


def _int16_le(b: bytes) -> int:
    return struct.unpack('<h', b)[0]


def parse_5561(payload: bytes) -> Optional[Dict]:
    """Scan `payload` for 0x55 0x61 frames and extract VX/VY/VZ samples.

    BT50 notifications contain multiple 0x55 0x61 frames concatenated.
    Each frame is 32 bytes with acceleration data at offsets 22-27.
    This function finds each frame, parses the three axis int16 values, applies
    a default scale and returns a summary dict.
    """
    if not payload or len(payload) < 32:
        return None

    frames: List[Dict] = []
    i = 0
    L = len(payload)

    # BT50 frame length is 32 bytes
    while i + 32 <= L:
        # look for header 0x55 0x61
        if payload[i] == 0x55 and payload[i + 1] == 0x61:
            # ensure enough bytes for full frame
            if i + 28 <= L:
                try:
                    # BT50 frame structure: acceleration data at offsets 14, 16, 26
                    # Analysis showed X at bytes 14-15, Y at 16-17, Z at 26-27
                    vx_raw = _int16_le(payload[i + 14:i + 16])
                    vy_raw = _int16_le(payload[i + 16:i + 18])
                    vz_raw = _int16_le(payload[i + 26:i + 28])
                except struct.error:
                    break

                # BT50 scale factor: Calibrated based on gravity reference
                # Calibration 20250909_170626 showed scale = 0.000902 for realistic 1g gravity
                scale = 0.000902
                vx = vx_raw * scale
                vy = vy_raw * scale
                vz = vz_raw * scale

                sample = {
                    'vx': vx,
                    'vy': vy,
                    'vz': vz,
                    'vx_raw': vx_raw,   # Keep raw for debugging
                    'vy_raw': vy_raw,
                    'vz_raw': vz_raw,
                    'raw': (vx_raw, vy_raw, vz_raw),  # TinTown format
                }
                frames.append(sample)

                # advance by 32 bytes (full BT50 frame)
                i += 32
                continue
            else:
                break
        else:
            i += 1

    if not frames:
        return None

    return {
        'frame_type': '5561',
        'samples': frames,
        'sample_count': len(frames)
    }


def calculate_magnitude(vx_raw: int, vy_raw: int, vz_raw: int) -> float:
    """Calculate 3D magnitude from raw acceleration values"""
    return (vx_raw**2 + vy_raw**2 + vz_raw**2)**0.5


def detect_impact_simple(samples: List[Dict], threshold: float = 150.0) -> bool:
    """Simple impact detection based on raw value changes"""
    if not samples:
        return False
    
    # Check if any sample exceeds threshold from baseline
    for sample in samples:
        magnitude = calculate_magnitude(
            sample['vx_raw'], 
            sample['vy_raw'], 
            sample['vz_raw']
        )
        if magnitude > threshold:
            return True
            
    return False
