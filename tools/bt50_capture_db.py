"""Multi-sensor BT50 capture and DB writer.

This script accepts one or more `--mac` arguments and connects to each device
concurrently. Parsed frames are enqueued to a single DB writer coroutine which
serializes writes into `logs/bt50_samples.db` and tags each row with the
source `sensor_mac`.

Usage (examples):
    # single sensor (backwards compatible)
    PYTHONPATH=projects/LeadVille/src python3 tools/bt50_capture_db.py --mac AA:BB:CC:DD:EE:FF --duration 30

    # multiple sensors
    PYTHONPATH=projects/LeadVille/src python3 tools/bt50_capture_db.py --mac AA:BB:CC:DD:EE:FF --mac 11:22:33:44:55:66 --duration 60
"""

import argparse
import asyncio
import logging
import os
import sqlite3
import sys
import time
from math import ceil
from typing import Dict, Any, List
from collections import deque
import math

from bleak import BleakClient, BleakScanner


class ImpactDetector:
    """Simple rolling-window detector: initial movement -> spike.

    - window_ms: total window to consider (ms)
    - pre_ms: how far before the start to compute pre_mag (ms)
    - start_thresh: magnitude threshold to designate initial movement
    - spike_thresh: magnitude threshold to confirm a spike

    feed_sample(ts_ns, mag) returns an event dict or None.
    """

    def __init__(self, window_ms: int = 100, pre_ms: int = 30, start_thresh: float = 0.05, spike_thresh: float = 0.25):
        self.window_ns = int(window_ms * 1e6)
        self.pre_ns = int(pre_ms * 1e6)
        self.start_thresh = float(start_thresh)
        self.spike_thresh = float(spike_thresh)
        self.buf = deque()

    def feed_sample(self, ts_ns: int, mag: float):
        # append and evict old
        self.buf.append((ts_ns, mag))
        cutoff = ts_ns - self.window_ns
        while self.buf and self.buf[0][0] < cutoff:
            self.buf.popleft()

        # find first sample >= start_thresh
        start_idx = None
        for i, (t, m) in enumerate(self.buf):
            if m >= self.start_thresh:
                start_idx = i
                break
        if start_idx is None:
            return None

        # convert to list for safe slicing and analysis
        buf_list = list(self.buf)
        start_t, start_m = buf_list[start_idx]

        # find peak after start
        post = buf_list[start_idx:]
        peak_t, peak_m = max(post, key=lambda x: x[1])
        if peak_m >= self.spike_thresh and (peak_t - start_t) <= self.window_ns:
            pre_samples = [m for (t, m) in buf_list if t < start_t and (start_t - t) <= self.pre_ns]
            pre_mag = max(pre_samples) if pre_samples else 0.0
            ev = {
                'impact_ts_ns': start_t,
                'detection_ts_ns': peak_t,
                'peak_mag': float(peak_m),
                'pre_mag': float(pre_mag),
                'post_mag': float(peak_m),
                'duration_ms': (peak_t - start_t) / 1e6,
            }
            # reset buffer to avoid duplicate detections
            self.buf.clear()
            return ev
        return None

# Make project package importable when running from tools/
# Prefer the project's `src/` directory (so `impact_bridge` resolves), but
# also keep the repo root as a fallback.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(repo_root, 'src')
if os.path.isdir(src_dir):
    sys.path.insert(0, src_dir)
else:
    # fallback to repo root (older setups)
    sys.path.insert(0, repo_root)

from impact_bridge.ble.wtvb_parse import scan_and_parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bt50_capture_db')


DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'bt50_samples.db')

# Samples with all motion values below this threshold are considered status-only
# (values are in raw register units; tune per your calibration)
NOISE_THRESHOLD = 5


def _ensure_db(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    cur = con.cursor()
    # Use WAL for better concurrency and performance on inserts
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bt50_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_ns INTEGER DEFAULT (strftime('%s','now') || '000000000'),
            sensor_mac TEXT,
            frame_hex TEXT,
            parser TEXT,
            vx INTEGER, vy INTEGER, vz INTEGER,
            angle_x INTEGER, angle_y INTEGER, angle_z INTEGER,
            temp_raw INTEGER, temperature_c REAL,
            disp_x INTEGER, disp_y INTEGER, disp_z INTEGER,
            freq_x INTEGER, freq_y INTEGER, freq_z INTEGER
        )
        """
    )
    con.commit()
    # Create a compact device_status table for low-rate status updates
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS device_status (
            sensor_mac TEXT PRIMARY KEY,
            last_seen_ns INTEGER,
            temperature_c REAL,
            temp_raw INTEGER,
            battery_pct INTEGER,
            battery_mv INTEGER
        )
        """
    )
    con.commit()
    # Ensure we have a column to persist the last history timestamp per device
    cur.execute("PRAGMA table_info(device_status)")
    cols = [r[1] for r in cur.fetchall()]
    if 'last_history_ns' not in cols:
        # ALTER TABLE to add the column; safe if it doesn't exist
        cur.execute("ALTER TABLE device_status ADD COLUMN last_history_ns INTEGER")
        con.commit()
    # History table for occasional status snapshots
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS device_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_mac TEXT,
            ts_ns INTEGER,
            temperature_c REAL,
            temp_raw INTEGER,
            battery_pct INTEGER,
            battery_mv INTEGER
        )
        """
    )
    con.commit()
    # Impacts summary table for compact event recording
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS impacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_mac TEXT,
            impact_ts_ns INTEGER,
            detection_ts_ns INTEGER,
            peak_mag REAL,
            pre_mag REAL,
            post_mag REAL,
            duration_ms REAL
        )
        """
    )
    con.commit()
    # Timer events table for AMG timer (shot/start/stop)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS timer_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_ns INTEGER,
            device_id TEXT,
            event_type TEXT,
            split_seconds REAL,
            split_cs INTEGER,
            raw_hex TEXT
        )
        """
    )
    con.commit()
    con.close()


# simple global metrics collector for writer
writer_metrics = {
    'inserts': 0,
    'status_updates': 0,
    'history_inserts': 0,
    'batches_committed': 0,
}


async def db_writer(queue: asyncio.Queue, db_path: str, batch_size: int = 50):
    """Consume parsed records from the queue and write them to SQLite."""
    _ensure_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        pending = 0
        while True:
            item = await queue.get()
            if item is None:
                break

            # Support two item types:
            # 1) full sample item: {'sensor_mac','frame_hex','parser','parsed'} -> insert into bt50_samples
            # 2) status update: {'sensor_mac','status':{'temperature_c', 'temp_raw', 'battery_pct', ...}, 'last_seen_ns'}
            if 'status' in item:
                status = item['status'] or {}
                sensor_mac = item.get('sensor_mac')
                last_seen_ns = item.get('last_seen_ns')
                # Upsert device_status (simple replace semantics)
                cur.execute(
                    "REPLACE INTO device_status (sensor_mac, last_seen_ns, temperature_c, temp_raw, battery_pct, battery_mv, last_history_ns) VALUES (?,?,?,?,?,?,?)",
                    (
                        sensor_mac,
                        last_seen_ns,
                        status.get('temperature_c'),
                        status.get('temp_raw'),
                        status.get('battery_pct'),
                        status.get('battery_mv'),
                        item.get('last_history_ns'),
                    ),
                )
                pending += 1
                writer_metrics['status_updates'] += 1
                # Optionally insert into history table when requested
                if item.get('history'):
                    ts_ns = item.get('ts_ns') or last_seen_ns
                    cur.execute(
                        "INSERT INTO device_status_history (sensor_mac, ts_ns, temperature_c, temp_raw, battery_pct, battery_mv) VALUES (?,?,?,?,?,?)",
                        (
                            sensor_mac,
                            ts_ns,
                            status.get('temperature_c'),
                            status.get('temp_raw'),
                            status.get('battery_pct'),
                            status.get('battery_mv'),
                        ),
                    )
                    pending += 1
                    writer_metrics['history_inserts'] += 1
            elif 'impact' in item:
                # compact impact summary
                impact = item['impact'] or {}
                cur.execute(
                    "INSERT INTO impacts (sensor_mac, impact_ts_ns, detection_ts_ns, peak_mag, pre_mag, post_mag, duration_ms) VALUES (?,?,?,?,?,?,?)",
                    (
                        item.get('sensor_mac'),
                        impact.get('impact_ts_ns'),
                        impact.get('detection_ts_ns'),
                        impact.get('peak_mag'),
                        impact.get('pre_mag'),
                        impact.get('post_mag'),
                        impact.get('duration_ms'),
                    ),
                )
                pending += 1
                writer_metrics.setdefault('impacts', 0)
                writer_metrics['impacts'] += 1
            elif 'timer' in item:
                te = item['timer'] or {}
                # ts_ns may be provided; otherwise use current time
                ts_ns = te.get('ts_ns') or int(time.time() * 1e9)
                cur.execute(
                    "INSERT INTO timer_events (ts_ns, device_id, event_type, split_seconds, split_cs, raw_hex) VALUES (?,?,?,?,?,?)",
                    (
                        ts_ns,
                        item.get('device_id') or te.get('device_id'),
                        te.get('event_type'),
                        te.get('split_seconds'),
                        te.get('split_cs'),
                        te.get('raw_hex'),
                    ),
                )
                pending += 1
                writer_metrics.setdefault('timer_events', 0)
                writer_metrics['timer_events'] += 1
            else:
                sensor_mac = item.get('sensor_mac')
                frame_hex = item.get('frame_hex')
                parser = item.get('parser')
                parsed: Dict[str, Any] = item.get('parsed', {})

                cur.execute(
                    """
                    INSERT INTO bt50_samples (
                        sensor_mac, frame_hex, parser,
                        vx, vy, vz, angle_x, angle_y, angle_z,
                        temp_raw, temperature_c, disp_x, disp_y, disp_z,
                        freq_x, freq_y, freq_z
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        sensor_mac,
                        frame_hex,
                        parser,
                        parsed.get('vx'),
                        parsed.get('vy'),
                        parsed.get('vz'),
                        parsed.get('angle_x'),
                        parsed.get('angle_y'),
                        parsed.get('angle_z'),
                        parsed.get('temp_raw'),
                        parsed.get('temperature_c'),
                        parsed.get('disp_x'),
                        parsed.get('disp_y'),
                        parsed.get('disp_z'),
                        parsed.get('freq_x'),
                        parsed.get('freq_y'),
                        parsed.get('freq_z'),
                    ),
                )
                pending += 1
                writer_metrics['inserts'] += 1

            # Commit in batches for performance
            if pending >= batch_size:
                con.commit()
                pending = 0
                writer_metrics['batches_committed'] += 1

            queue.task_done()

        # final commit for any remaining
        if pending:
            con.commit()
            writer_metrics['batches_committed'] += 1
    finally:
        con.close()


async def metrics_logger(queue: asyncio.Queue, interval: int = 10):
    """Periodically log queue size and writer metrics."""
    try:
        while True:
            qsize = queue.qsize()
            metrics_snapshot = writer_metrics.copy()
            logger.info(f"metrics: queue_size={qsize} inserts={metrics_snapshot['inserts']} status_updates={metrics_snapshot['status_updates']} history_inserts={metrics_snapshot['history_inserts']} batches={metrics_snapshot['batches_committed']}")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.debug("metrics_logger cancelled")
        return


async def sensor_task(mac: str, char_uuid: str, duration: int, queue: asyncio.Queue, status_interval: int = 60,
                      max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 30.0,
                      initial_last_history: Dict[str, int] | None = None,
                      detect_enabled: bool = False,
                      detect_window_ms: int = 100,
                      detect_pre_ms: int = 30,
                      detect_threshold_start: float = 0.05,
                      detect_threshold_spike: float = 0.25,
                      status_temp_delta: float = 0.5):
    """Connect to one sensor, subscribe, parse payloads and enqueue parsed records."""
    buf = bytearray()
    # mac may be a BleakDevice or a string address. Derive a stable sensor_id
    raw_id = getattr(mac, 'address', mac)
    # normalize to uppercase to match DB keys and initial_last_history mapping
    sensor_id = raw_id.upper() if isinstance(raw_id, str) else getattr(raw_id, 'address', str(raw_id)).upper()

    def handler(sender, data: bytes):
        nonlocal buf
        logger.debug(f"[{sensor_id}] raw: {data.hex()}")
        buf.extend(data)
        try:
            # Do not let scan_and_parse write directly to DB; receive parsed results
            results = scan_and_parse(bytes(buf), write_db=False)
            if results:
                for r in results:
                    parsed = r.get('parsed')
                    parser = r.get('parser')
                    frame_hex = r.get('frame_hex') if 'frame_hex' in r else bytes(buf).hex()
                    # Determine whether this is a motion sample or a status-only
                    vx = parsed.get('vx') or 0
                    vy = parsed.get('vy') or 0
                    vz = parsed.get('vz') or 0

                    is_motion = any(abs(int(v)) > NOISE_THRESHOLD for v in (vx, vy, vz))

                    if is_motion:
                        # compute magnitude scaled to g units if available
                        try:
                            sx = float(parsed.get('vx', 0))
                            sy = float(parsed.get('vy', 0))
                            sz = float(parsed.get('vz', 0))
                            mag = math.sqrt(sx*sx + sy*sy + sz*sz)
                        except Exception:
                            mag = None
                        # run detector if enabled
                        if detect_enabled and mag is not None:
                            now_ns = int(time.time() * 1e9)
                            det = handler._detector
                            ev = det.feed_sample(now_ns, mag)
                            if ev:
                                # enqueue compact impact event
                                impact_item = {
                                    'sensor_mac': sensor_id,
                                    'impact': ev,
                                }
                                queue.put_nowait(impact_item)
                                logger.info(f"[{sensor_id}] impact detected: {ev}")
                        item = {
                            'sensor_mac': sensor_id,
                            'frame_hex': frame_hex,
                            'parser': parser,
                            'parsed': parsed,
                        }
                        # Enqueue full motion sample for DB writer
                        queue.put_nowait(item)
                        logger.info(f"[{sensor_id}] parsed [{parser}] @ offset {r.get('offset')}: {parsed}")
                    else:
                        # Status-only: create a compact status update item
                        status = {
                            'temperature_c': parsed.get('temperature_c'),
                            'temp_raw': parsed.get('temp_raw'),
                            # battery fields may be present under different keys; include when available
                            'battery_pct': parsed.get('battery_pct'),
                            'battery_mv': parsed.get('battery_mv'),
                        }
                        now_ns = int(time.time() * 1e9)

                        # Decide whether to record a history sample. Use per-task in-memory
                        # tracking to avoid frequent writes. This is non-persistent and resets
                        # when the process restarts; that's acceptable for lightweight history.
                        history_flag = False
                        try:
                            last_hist = handler._last_history_ns.get(sensor_id)
                        except Exception:
                            last_hist = None

                        # If no per-task map, initialize it and seed from provided initial mapping
                        if not hasattr(handler, '_last_history_ns'):
                            handler._last_history_ns = {}
                        if not hasattr(handler, '_last_status_values'):
                            handler._last_status_values = {}
                        # seed from global initial mapping if available (keys are uppercased)
                        if initial_last_history:
                            for k, v in initial_last_history.items():
                                if k and v:
                                    handler._last_history_ns.setdefault(k.upper(), v)

                        status_changed = False
                        prev_status = handler._last_status_values.get(sensor_id)
                        # Consider 'changed' if temp or battery differs by a small delta
                        if prev_status is None:
                            status_changed = True
                        else:
                            prev_temp = prev_status.get('temperature_c')
                            if prev_temp is None and status.get('temperature_c') is not None:
                                status_changed = True
                            elif prev_temp is not None and status.get('temperature_c') is not None:
                                if abs(prev_temp - status.get('temperature_c')) >= getattr(handler, '_status_temp_delta', 0.5):
                                    status_changed = True

                        # History interval will be supplied by outer scope via handler._status_interval
                        interval_s = getattr(handler, '_status_interval', 60)
                        if last_hist is None or (now_ns - last_hist) >= interval_s * 1e9:
                            history_flag = True
                        if status_changed:
                            history_flag = True

                        # Update per-task caches
                        handler._last_history_ns[sensor_id] = now_ns
                        handler._last_status_values[sensor_id] = status

                        status_item = {
                            'sensor_mac': sensor_id,
                            'status': status,
                            'last_seen_ns': now_ns,
                            # persist last history timestamp so it survives restarts
                            'last_history_ns': handler._last_history_ns.get(sensor_id),
                            'history': history_flag,
                            'ts_ns': now_ns,
                        }
                        queue.put_nowait(status_item)
                        logger.debug(f"[{sensor_id}] status update: {status} history={history_flag}")
                # Clear buffer after consuming frames
                buf.clear()
        except Exception:
            logger.exception(f"[{mac}] parse error")

    # Reconnect loop with exponential backoff
    attempt = 0
    while True:
        try:
            async with BleakClient(mac) as client:
                logger.info(f"[{mac}] Connected")
                # Attach status interval to handler closure so it can decide when to
                # persist history samples
                setattr(handler, '_status_interval', status_interval)
                # attach detector instance to handler if enabled
                if detect_enabled:
                    # create detector and attach
                    handler._detector = ImpactDetector(window_ms=detect_window_ms, pre_ms=detect_pre_ms, start_thresh=detect_threshold_start, spike_thresh=detect_threshold_spike)
                else:
                    handler._detector = None
                # attach status_temp_delta value so handler can use it
                setattr(handler, '_status_temp_delta', float(status_temp_delta))
                await client.start_notify(char_uuid, handler)
                # Run for the duration or until disconnected
                await asyncio.sleep(duration)
                await client.stop_notify(char_uuid)
                # Clean exit after successful duration
                break
        except Exception:
            attempt += 1
            logger.exception(f"[{mac}] connection error (attempt {attempt})")
            if max_retries >= 0 and attempt > max_retries:
                logger.error(f"[{mac}] exceeded max_retries={max_retries}; giving up")
                break
            # exponential backoff
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            # add jitter
            jitter = delay * 0.1
            delay = delay + (jitter * (2 * (os.urandom(1)[0] / 255.0) - 1))
            delay = max(0.1, delay)
            logger.info(f"[{mac}] reconnecting in {delay:.1f}s (attempt {attempt}/{max_retries})")
            await asyncio.sleep(delay)


async def main(macs: List[str], char_uuid: str, duration: int, status_interval: int = 60, reconnect_args: dict | None = None, detect_args: dict | None = None):
    queue: asyncio.Queue = asyncio.Queue()
    writer = asyncio.create_task(db_writer(queue, DB_PATH))
    metrics_task = asyncio.create_task(metrics_logger(queue, interval=10))

    handler_reconnect = reconnect_args or {'max_retries': 5, 'base_delay': 1.0, 'max_delay': 30.0}
    detect_args = detect_args or {'detect_enabled': False, 'detect_window_ms': 100, 'detect_pre_ms': 30, 'detect_threshold_start': 0.05, 'detect_threshold_spike': 0.25}

    # Try to discover devices first with a single scanner to avoid multiple
    # concurrent active_scan calls on BlueZ which raise "Operation already in progress".
    async def discover_devices(target_macs: List[str], timeout: int = 5, attempts: int = 3):
        found = {}
        targets = {m.upper(): m for m in target_macs}
        for attempt in range(attempts):
            logger.info(f"discovery attempt {attempt+1}/{attempts} timeout={timeout}s")
            devices = await BleakScanner.discover(timeout=timeout)
            for d in devices:
                if d.address and d.address.upper() in targets:
                    found[d.address.upper()] = d
            # stop early if all found
            if all(m.upper() in found for m in target_macs):
                break
        return found

    device_map = await discover_devices(macs, timeout=4, attempts=3)

    # Load persisted last_history_ns values from DB so we don't repeat history writes
    initial_last_history: Dict[str, int] = {}
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT sensor_mac, last_history_ns FROM device_status")
        for row in cur.fetchall():
            mac_addr, last_hist = row[0], row[1]
            if mac_addr and last_hist:
                initial_last_history[mac_addr.upper()] = int(last_hist)
    except Exception:
        logger.exception("failed to read initial last_history_ns from DB")
    finally:
        try:
            con.close()
        except Exception:
            pass

    tasks = []
    for i, m in enumerate(macs):
        key = m.upper()
        device = device_map.get(key)
        if device:
            # pass the BleakDevice object to sensor_task. sensor_task will extract
            # the `.address` for DB records and use the device directly to avoid
            # triggering a new active scan inside BleakClient.
            logger.info(f"Using discovered device object for {m}")
            tasks.append(asyncio.create_task(sensor_task(
                device,
                char_uuid,
                duration,
                queue,
                status_interval=status_interval,
                max_retries=handler_reconnect.get('max_retries', 5),
                base_delay=handler_reconnect.get('base_delay', 1.0),
                max_delay=handler_reconnect.get('max_delay', 30.0),
                initial_last_history=initial_last_history,
                detect_enabled=detect_args.get('detect_enabled', False),
                detect_window_ms=detect_args.get('detect_window_ms', 100),
                detect_pre_ms=detect_args.get('detect_pre_ms', 30),
                detect_threshold_start=detect_args.get('detect_threshold_start', 0.05),
                detect_threshold_spike=detect_args.get('detect_threshold_spike', 0.25),
            )))
        else:
            # Not discovered — stagger start times to reduce concurrent scanner calls
            delay = i * 1.5
            logger.warning(f"Device {m} not discovered during scan; will attempt connect (staggered) with {delay}s delay")
            async def delayed_start(addr, dly):
                await asyncio.sleep(dly)
                await sensor_task(
                    addr,
                    char_uuid,
                    duration,
                    queue,
                    status_interval=status_interval,
                    max_retries=handler_reconnect.get('max_retries', 5),
                    base_delay=handler_reconnect.get('base_delay', 1.0),
                    max_delay=handler_reconnect.get('max_delay', 30.0),
                    initial_last_history=initial_last_history,
                    detect_enabled=detect_args.get('detect_enabled', False),
                    detect_window_ms=detect_args.get('detect_window_ms', 100),
                    detect_pre_ms=detect_args.get('detect_pre_ms', 30),
                    detect_threshold_start=detect_args.get('detect_threshold_start', 0.05),
                    detect_threshold_spike=detect_args.get('detect_threshold_spike', 0.25),
                )
            tasks.append(asyncio.create_task(delayed_start(m, delay)))

    # Wait for all sensor tasks to complete
    await asyncio.gather(*tasks)

    # signal writer to finish
    await queue.put(None)
    await writer
    # stop metrics task
    metrics_task.cancel()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mac', action='append', required=True, help='BT50 device MAC address (can specify multiple)')
    parser.add_argument('--char', default='0000ffe4-0000-1000-8000-00805f9a34fb', help='Notify characteristic UUID')
    parser.add_argument('--duration', type=int, default=30, help='Seconds to capture')
    parser.add_argument('--status-interval', type=int, default=60, help='Seconds between status history samples (per sensor)')
    parser.add_argument('--reconnect-max-retries', type=int, default=5, help='Max reconnect attempts per sensor (-1 for infinite)')
    parser.add_argument('--reconnect-base-delay', type=float, default=1.0, help='Base delay (s) for reconnect backoff')
    parser.add_argument('--reconnect-max-delay', type=float, default=30.0, help='Max delay (s) for reconnect backoff')
    parser.add_argument('--detect-enabled', action='store_true', help='Enable impact detection')
    parser.add_argument('--detect-window-ms', type=int, default=100, help='Detection window in ms')
    parser.add_argument('--detect-pre-ms', type=int, default=30, help='Pre-window size in ms for pre_mag')
    parser.add_argument('--detect-threshold-start', type=float, default=0.05, help='Start threshold (magnitude units)')
    parser.add_argument('--detect-threshold-spike', type=float, default=0.25, help='Spike threshold (magnitude units)')
    args = parser.parse_args()

    # Normalize MACs
    macs = args.mac
    asyncio.run(main(macs, args.char, args.duration, status_interval=args.status_interval,
                     reconnect_args={
                         'max_retries': args.reconnect_max_retries,
                         'base_delay': args.reconnect_base_delay,
                         'max_delay': args.reconnect_max_delay,
                     },
                     detect_args={
                         'detect_enabled': args.detect_enabled,
                         'detect_window_ms': args.detect_window_ms,
                         'detect_pre_ms': args.detect_pre_ms,
                         'detect_threshold_start': args.detect_threshold_start,
                         'detect_threshold_spike': args.detect_threshold_spike,
                     }))
