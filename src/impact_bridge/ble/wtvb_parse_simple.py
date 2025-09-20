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

from typing import Optional, List, Dict

# Use the canonical verbose parser to avoid duplicate/incorrect offset math.
# This keeps the simple API but delegates frame extraction to the tested
# `scan_and_parse` implementation which is the source of truth for offsets.
try:
    from impact_bridge.ble.wtvb_parse import scan_and_parse
except Exception:  # pragma: no cover - import guarded for tooling contexts
    scan_and_parse = None  # type: ignore

# Calibrated per-project scale used by the simple parser to present values
# in 'g' or similar units. Keep here for backwards compatibility tests.
DEFAULT_SCALE = 0.000902


def parse_5561(payload: bytes) -> Optional[Dict]:
    """Scan `payload` for 0x55 0x61 frames and extract VX/VY/VZ samples.

    This wrapper delegates frame boundary detection to `scan_and_parse` (if
    available) to avoid offset mismatches. It returns the simple dictionary
    shape previously used by callers:

      {
        'frame_type': '5561',
        'samples': [ { 'vx', 'vy', 'vz', 'vx_raw','vy_raw','vz_raw','raw' }, ... ],
        'sample_count': N
      }

    If `scan_and_parse` is not importable, this function will return None.
    """
    if not payload:
        return None

    if not scan_and_parse:
        # Defensive: if the verbose parser isn't available in this runtime,
        # do not attempt fragile manual offset parsing.
        return None

    results = scan_and_parse(payload, write_db=False)
    if not results:
        return None

    frames: List[Dict] = []
    for r in results:
        parser_name = r.get('parser')
        parsed = r.get('parsed', {}) or {}

        # Prefer raw register values when present; the verbose parser exposes
        # integer registers typically under 'vx','vy','vz'. The simple parser
        # historically exposed scaled floats under 'vx','vy','vz' and kept raw
        # values in vx_raw/..; normalize to provide both.
        vx_raw = parsed.get('vx')
        vy_raw = parsed.get('vy')
        vz_raw = parsed.get('vz')

        # If the verbose parser uses a different naming convention (e.g.
        # 'vx_raw') fall back to those keys.
        if vx_raw is None and 'vx_raw' in parsed:
            vx_raw = parsed.get('vx_raw')
        if vy_raw is None and 'vy_raw' in parsed:
            vy_raw = parsed.get('vy_raw')
        if vz_raw is None and 'vz_raw' in parsed:
            vz_raw = parsed.get('vz_raw')

        # Default missing raw values to 0 for safety in downstream code.
        vx_raw = 0 if vx_raw is None else int(vx_raw)
        vy_raw = 0 if vy_raw is None else int(vy_raw)
        vz_raw = 0 if vz_raw is None else int(vz_raw)

        # Provide scaled float values for quick usage in detection
        vx = vx_raw * DEFAULT_SCALE
        vy = vy_raw * DEFAULT_SCALE
        vz = vz_raw * DEFAULT_SCALE

        sample = {
            'vx': vx,
            'vy': vy,
            'vz': vz,
            'vx_raw': vx_raw,
            'vy_raw': vy_raw,
            'vz_raw': vz_raw,
            'raw': (vx_raw, vy_raw, vz_raw),
            'parser': parser_name,
        }
        frames.append(sample)

    if not frames:
        return None

    return {
        'frame_type': '5561',
        'samples': frames,
        'sample_count': len(frames),
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
