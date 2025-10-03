"""Verbose parser for WTVB01 / WitMotion BT50 packets.

This module provides two main parsing helpers and a small SQLite logger for
investigation. It recognizes:

- Flag 0x61 frames (device default upload): 0x55 0x61 + 26 bytes (28 total)
- 32-byte WTVB frames (older/alternate framing where axes are at offsets)

The parser is intentionally verbose (logging debug information) and can
optionally persist parsed samples to `db/bt50_samples.db` for offline
inspection.
"""

from __future__ import annotations

import logging
import struct
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from impact_bridge.paths import SAMPLES_DB as DB_PATH

logger = logging.getLogger(__name__)


def _ensure_db(path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS bt50_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_ns INTEGER,
                frame_hex TEXT,
                parser TEXT,
                vx INTEGER,
                vy INTEGER,
                vz INTEGER,
                angle_x INTEGER,
                angle_y INTEGER,
                angle_z INTEGER,
                temp_raw INTEGER,
                disp_x INTEGER,
                disp_y INTEGER,
                disp_z INTEGER,
                freq_x INTEGER,
                freq_y INTEGER,
                freq_z INTEGER
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _write_db_row(data: Dict, frame_hex: str, parser: str = "flag61", path: Path = DB_PATH) -> None:
    _ensure_db(path)
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO bt50_samples (
                ts_ns, frame_hex, parser, vx, vy, vz, angle_x, angle_y, angle_z,
                temp_raw, disp_x, disp_y, disp_z, freq_x, freq_y, freq_z
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(time.time_ns()),
                frame_hex,
                parser,
                data.get("vx", 0),
                data.get("vy", 0),
                data.get("vz", 0),
                data.get("angle_x", 0),
                data.get("angle_y", 0),
                data.get("angle_z", 0),
                data.get("temp_raw", 0),
                data.get("disp_x", 0),
                data.get("disp_y", 0),
                data.get("disp_z", 0),
                data.get("freq_x", 0),
                data.get("freq_y", 0),
                data.get("freq_z", 0),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _i16_le_from_bytes(b: bytes) -> int:
    return struct.unpack('<h', b)[0]


def parse_bt50_frame(frame: bytes, write_db: bool = False) -> Optional[Dict]:
    """Parse a standard BT50 velocity frame (flag 0x61, 28 bytes total).

    Returns a dict with the parsed register values (integers) and derived
    human-readable values. If `write_db` is True the raw register values are
    written to `db/bt50_samples.db` for later inspection.
    """
    if not frame or len(frame) < 28:
        logger.debug("parse_bt50_frame: frame too short")
        return None
    if frame[0] != 0x55 or frame[1] != 0x61:
        logger.debug("parse_bt50_frame: invalid header")
        return None

    payload = frame[2:2 + 26]
    if len(payload) < 26:
        logger.debug("parse_bt50_frame: incomplete payload")
        return None

    regs = [ _i16_le_from_bytes(payload[i:i+2]) for i in range(0, 26, 2) ]
    # order from manual / example: VX, VY, VZ, AngleX, AngleY, AngleZ, TEMP,
    # DX, DY, DZ, FX, FY, FZ
    vx, vy, vz, ax, ay, az, temp_raw, dx, dy, dz, fx, fy, fz = regs

    parsed = {
        "vx": vx,  # mm/s
        "vy": vy,
        "vz": vz,
        "angle_x": ax,
        "angle_y": ay,
        "angle_z": az,
        "temp_raw": temp_raw,
        "temperature_c": temp_raw / 100.0,
        "disp_x": dx,  # um
        "disp_y": dy,
        "disp_z": dz,
        "freq_x": fx,  # Hz
        "freq_y": fy,
        "freq_z": fz,
    }

    logger.debug(f"parse_bt50_frame: parsed={parsed}")

    if write_db:
        _write_db_row(parsed, frame.hex(), parser="bt50")

    return parsed


def parse_wtvb32_frame(frame: bytes, write_db: bool = False) -> Optional[Dict]:
    """Parse a 32-byte WTVB frame variant where accelerations are at offsets
    observed in some device samples (e.g., X@14-15, Y@16-17, Z@26-27). This
    parser returns scaled g values (using historical calibration = 0.000902)
    and raw integer counts.
    """
    if not frame or len(frame) < 32:
        logger.debug("parse_wtvb32_frame: frame too short")
        return None
    if frame[0] != 0x55 or frame[1] != 0x61:
        logger.debug("parse_wtvb32_frame: invalid header")
        return None

    try:
        vx_raw = _i16_le_from_bytes(frame[14:16])
        vy_raw = _i16_le_from_bytes(frame[16:18])
        vz_raw = _i16_le_from_bytes(frame[26:28])
    except struct.error:
        logger.exception("parse_wtvb32_frame: struct error")
        return None

    # calibrated scale (vendor calibration observed): counts -> g
    scale = 0.000902
    vx = vx_raw * scale
    vy = vy_raw * scale
    vz = vz_raw * scale

    parsed = {
        "vx_raw": vx_raw,
        "vy_raw": vy_raw,
        "vz_raw": vz_raw,
        "vx_g": vx,
        "vy_g": vy,
        "vz_g": vz,
    }

    logger.debug(f"parse_wtvb32_frame: parsed={parsed}")

    if write_db:
        # write raw integer axis values (map into db fields for analysis)
        db_row = {
            "vx": vx_raw,
            "vy": vy_raw,
            "vz": vz_raw,
            "angle_x": 0,
            "angle_y": 0,
            "angle_z": 0,
            "temp_raw": 0,
            "disp_x": 0,
            "disp_y": 0,
            "disp_z": 0,
            "freq_x": 0,
            "freq_y": 0,
            "freq_z": 0,
        }
        _write_db_row(db_row, frame.hex(), parser="wtvb32")

    return parsed


def scan_and_parse(payload: bytes, write_db: bool = False) -> List[Dict]:
    """Scan a notification payload for known frame types and return a list of
    parsed records. This handles concatenated frames and partial notifications
    (caller should handle reassembly if needed).
    """
    results: List[Dict] = []
    i = 0
    L = len(payload)
    while i < L - 1:
        if payload[i] == 0x55 and payload[i + 1] == 0x61:
            # Try flag61 (28 bytes total)
            if i + 28 <= L:
                frame = payload[i:i+28]
                parsed = parse_bt50_frame(frame, write_db=write_db)
                if parsed:
                    results.append({"parser": "bt50", "offset": i, "parsed": parsed, "frame_hex": frame.hex()})
                    i += 28
                    continue
            # Try 32-byte WTVB frame
            if i + 32 <= L:
                frame32 = payload[i:i+32]
                parsed32 = parse_wtvb32_frame(frame32, write_db=write_db)
                if parsed32:
                    results.append({"parser": "wtvb32", "offset": i, "parsed": parsed32, "frame_hex": frame32.hex()})
                    i += 32
                    continue
            # Not enough bytes for a full frame yet: break and allow caller to wait
            break
        else:
            i += 1

    return results


# Backwards compatibility export until callers migrate off the old name
parse_flag61_frame = parse_bt50_frame