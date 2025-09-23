# Archived: leadville_bridge_backup.py

Reason: historic launcher variants and experiments moved to archive on 2025-09-23

Original path: `/leadville_bridge_backup.py`

Contents (original file included below for reference):

```python
#!/usr/bin/env python3
"""
Fixed Dev Bridge - Uses corrected BT50 parser with 1mg scale factor
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from bleak import BleakClient, BleakScanner
import struct
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup dual logging - both to systemd and console log file
def setup_dual_logging():
    """Setup logging to both systemd journal and a dedicated console log file"""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / 'logs' / 'console'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create console log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    console_log_file = log_dir / f'bridge_console_{timestamp}.log'
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler (for systemd journal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    # File handler (for complete console log)
    file_handler = logging.FileHandler(console_log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return console_log_file

# Initialize dual logging
console_log_path = setup_dual_logging()
logger = logging.getLogger(__name__)

# Import the corrected parser, shot detector, timing calibration, and enhanced impact detection
try:
    from impact_bridge.ble.wtvb_parse import parse_5561
    from impact_bridge.shot_detector import ShotDetector
    from impact_bridge.timing_calibration import RealTimeTimingCalibrator
    from impact_bridge.enhanced_impact_detection import EnhancedImpactDetector
    from impact_bridge.statistical_timing_calibration import statistical_calibrator
    from impact_bridge.dev_config import dev_config
    print("✓ Successfully imported corrected parse_5561 with 1mg scale factor")
    print("✓ Successfully imported ShotDetector")
    print("✓ Successfully imported RealTimeTimingCalibrator")
    print("✓ Successfully imported EnhancedImpactDetector")
    print("✓ Successfully imported Statistical Timing Calibrator")
    print("✓ Successfully imported development configuration")
    PARSER_AVAILABLE = True
    TIMING_AVAILABLE = True
    ENHANCED_DETECTION_AVAILABLE = True
    STATISTICAL_TIMING_AVAILABLE = True
    DEV_CONFIG_AVAILABLE = True
except Exception as e:
    print(f"⚠ Parser/Timing/Enhanced detection import failed: {e}")
    PARSER_AVAILABLE = False
    TIMING_AVAILABLE = False
    ENHANCED_DETECTION_AVAILABLE = False
    STATISTICAL_TIMING_AVAILABLE = False
    DEV_CONFIG_AVAILABLE = False
    dev_config = None
    statistical_calibrator = None

# Device MACs

# Bridge-assigned device lookup method
def get_bridge_assigned_devices():
    """Get devices assigned to this Bridge from database"""
    try:
        from src.impact_bridge.database.database import get_database_session, init_database
        from src.impact_bridge.database.models import Bridge, Sensor
        from src.impact_bridge.config import DatabaseConfig
        
        # Initialize database
        db_config = DatabaseConfig()
        init_database(db_config)
        
        with get_database_session() as session:
            bridge = session.query(Bridge).first()
            if not bridge:
                print("No Bridge found in database")
                return {}
                
            sensors = session.query(Sensor).filter_by(bridge_id=bridge.id).all()
            device_map = {}
            
            print(f"Found {len(sensors)} sensors assigned to Bridge {bridge.name}")
            
            for sensor in sensors:
                label = sensor.label.lower()
                if "timer" in label or "amg" in label:
                    device_map["amg_timer"] = sensor.hw_addr
                    print(f"🎯 Bridge-assigned AMG timer: {sensor.hw_addr} ({sensor.label})")
                elif "bt50" in label:
                    device_map["bt50_sensor"] = sensor.hw_addr  
                    print(f"🎯 Bridge-assigned BT50 sensor: {sensor.hw_addr} ({sensor.label})")
                    
            return device_map
            
    except Exception as e:
        print(f"Failed to get Bridge-assigned devices: {e}")
        return {}

# Your discovered device MAC addresses (Orange-GoFast Bridge - Go Fast Stage)
AMG_TIMER_MAC = "60:09:C3:1F:DC:1A"  # AMG Lab COMM DC1A

# Multiple BT50 sensors for Go Fast stage targets
BT50_SENSORS = [
    "EA:18:3D:6D:BA:E5",  # WTVB01-BT50-BA:E5 (Target 1)
    "C2:1B:DB:F0:55:50"   # WTVB01-BT50-55:50 (Target 2) 
]
BT50_SENSOR_MAC = BT50_SENSORS[0]  # Primary sensor for compatibility

# BLE UUIDs
AMG_TIMER_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
BT50_SENSOR_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"

# Impact threshold - Raw count changes (based on stationary variation analysis)
# Normal variation: ~57 counts, so threshold = 3x normal variation
IMPACT_THRESHOLD = 150  # Raw counts - Detect changes > 150 counts from baseline

# Calibration settings
CALIBRATION_SAMPLES = 100  # Number of samples to collect for baseline calibration

... (file truncated for brevity) ...

```
