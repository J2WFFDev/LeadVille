import time
import os
import sys
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from tools.bt50_capture_db import ImpactDetector


def test_impact_detector_simple():
    # small window; simulate quiet -> small movement -> spike
    det = ImpactDetector(window_ms=200, pre_ms=50, start_thresh=0.05, spike_thresh=0.2)
    base = int(time.time() * 1e9)
    samples = [
        (base + 0, 0.01),
        (base + 10_000_000, 0.02),
        (base + 20_000_000, 0.06),  # start
        (base + 30_000_000, 0.08),
        (base + 40_000_000, 0.25),  # spike
    ]

    ev = None
    for ts, m in samples:
        ev = det.feed_sample(ts, m)
        if ev:
            break

    assert ev is not None, 'expected an impact event'
    assert ev['peak_mag'] >= 0.25
    assert ev['impact_ts_ns'] == samples[2][0]
