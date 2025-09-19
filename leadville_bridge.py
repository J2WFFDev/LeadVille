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
    "CA:8B:D6:7F:76:5B",  # WTVB01-BT50-76:5B (Target 1)
    "C2:1B:DB:F0:55:50"   # WTVB01-BT50-55:50 (Target 2) 
]
BT50_SENSOR_MAC = BT50_SENSORS[0]  # Primary sensor for compatibility

# BLE UUIDs
AMG_TIMER_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
BT50_SENSOR_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"

# Impact threshold - Raw count changes (based on stationary variation analysis)
# Normal variation: ~57 counts, so threshold = 3x normal variation
IMPACT_THRESHOLD = 200  # Raw counts - Detect changes > 150 counts from baseline

# Calibration settings
CALIBRATION_SAMPLES = 250  # Number of samples to collect for baseline calibration

class FixedBridge:
    def __init__(self):
        # Use global dual logger
        self.logger = logger
        
        self.amg_client = None
        self.bt50_client = None
        self.running = False
        self.session_id = int(time.time())
        
        # Dynamic baseline values (set during startup calibration)
        self.baseline_x = None
        self.baseline_y = None  
        self.baseline_z = None
        self.calibration_complete = False
        
        # Calibration data collection
        self.calibration_samples = []
        self.collecting_calibration = False
        
        # AMG Timer start beep tracking for splits
        self.start_beep_time = None
        self.previous_shot_time = None
        self.impact_counter = 0
        self.shot_counter = 0
        self.last_projection = None
        self.current_string_number = 1  # Default string number
        
        # Shot detector (will be initialized after calibration)
        self.shot_detector = None
        
        # Timing calibrator for shot-impact correlation
        if TIMING_AVAILABLE:
            self.timing_calibrator = RealTimeTimingCalibrator(Path("latest_timing_calibration.json"))
            print("✓ Timing calibrator initialized with 526ms expected delay")
        else:
            self.timing_calibrator = None
            print("⚠ Timing calibrator not available")
        
        # Development configuration setup
        if DEV_CONFIG_AVAILABLE and dev_config:
            dev_config.print_config_summary()
            self.dev_config = dev_config
        else:
            self.dev_config = None
            self.logger.warning("Development configuration not available")
        
        # Sensor-to-target mapping for enhanced logging
        
        # Load Bridge-assigned sensors from database (replaces hardcoded sensors)
        print("🔄 Loading Bridge-assigned sensors from database...")
        bridge_devices = get_bridge_assigned_devices()
        
        if bridge_devices:
            # Build BT50_SENSORS list from database assignments
            self.bt50_sensors = []
            
            # Get all BT50 sensors assigned to this Bridge
            try:
                from src.impact_bridge.database.database import get_database_session, init_database
                from src.impact_bridge.database.models import Bridge, Sensor, TargetConfig
                from src.impact_bridge.config import DatabaseConfig
                
                db_config = DatabaseConfig()
                init_database(db_config)
                
                with get_database_session(db_config) as session:
                    # Get Bridge ID (assuming we're using Bridge MCU1)
                    bridge = session.query(Bridge).filter_by(bridge_id="MCU1").first()
                    if bridge:
                        # Get sensors assigned to this Bridge's targets
                        sensors = session.query(Sensor).filter_by(bridge_id=bridge.id).all()
                        
                        for sensor in sensors:
                            if "BT50" in sensor.label.upper():
                                self.bt50_sensors.append(sensor.hw_addr)
                                print(f"🎯 Loaded BT50 sensor: {sensor.hw_addr} ({sensor.label})")
                        
                        print(f"✅ Loaded {len(self.bt50_sensors)} BT50 sensors from database")
                    else:
                        print("⚠️ Bridge MCU1 not found in database, using hardcoded sensors")
                        self.bt50_sensors = BT50_SENSORS
                        
            except Exception as e:
                print(f"⚠️ Failed to load sensors from database: {e}")
                print("🔄 Falling back to hardcoded sensors")
                self.bt50_sensors = BT50_SENSORS
        else:
            print("⚠️ No Bridge-assigned devices found, using hardcoded sensors")
            self.bt50_sensors = BT50_SENSORS
        self.sensor_mappings = {}  # {sensor_mac: {"sensor_id": "55:50", "target_num": 2, "stage": "Go Fast"}}
        self.current_sensor_mac = None  # Track which sensor triggered the notification
        self.bt50_clients = []  # List of all connected BT50 clients
        
        # Per-sensor calibration system
        self.sensor_target_count = 100  # Samples required per sensor
        self.per_sensor_calibration = {}  # {sensor_mac: {"samples": [], "baseline": {}, "complete": False}}
        self.sensor_baselines = {}  # {sensor_mac: {"baseline_x": int, "noise_x": float, etc}}
        
        # Enhanced impact detector with onset timing
        if ENHANCED_DETECTION_AVAILABLE:
            # Use development configuration for thresholds if available
            if self.dev_config and self.dev_config.is_enhanced_impact_enabled():
                peak_threshold = self.dev_config.get_peak_threshold()
                onset_threshold = self.dev_config.get_onset_threshold()
                lookback_samples = self.dev_config.get_lookback_samples()
                print(f"✓ Using development config for enhanced impact detection")
            else:
                peak_threshold = 150.0
                onset_threshold = 30.0
                lookback_samples = 10
                
            self.enhanced_impact_detectors = {}  # Per-sensor detectors
            print("✓ Enhanced impact detector initialized (onset detection enabled)")
        else:
            self.enhanced_impact_detectors = {}
            print("⚠ Enhanced impact detector not available")
        
        # Ensure log directories exist
        Path("logs/main").mkdir(parents=True, exist_ok=True)
        Path("logs/debug").mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging - both console and debug file"""
        timestamp = datetime.now()
        debug_file = f"logs/debug/bridge_debug_{timestamp.strftime('%Y%m%d_%H%M%S')}.log"
        
        # Create formatters with millisecond precision
        class MillisecondFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                ct = self.converter(record.created)
                ms = int((record.created - int(record.created)) * 1000)
                s = time.strftime('%H:%M:%S', ct)
                return f"{s}.{ms:03d}"
        
        console_formatter = MillisecondFormatter('[%(asctime)s] %(levelname)s: %(message)s')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Setup root logger for debug level (console already configured)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # File handler for ALL debug info (don't add another console handler)
        file_handler = logging.FileHandler(debug_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        self.logger = logging.getLogger("FixedBridge")
        self.logger.info(f"Debug logging enabled: {debug_file}")
    
    async def calibration_notification_handler(self, characteristic, data):
        """Collect calibration samples during startup"""
        if not self.collecting_calibration:
            return
            
        # For calibration, parse data even if shot_detector import failed
        try:
            if PARSER_AVAILABLE:
                # Use the imported parser
                result = parse_5561(data)
                if result and result['samples']:
                    # Collect raw values from all samples in this notification
                    for sample in result['samples']:
                        vx_raw, vy_raw, vz_raw = sample['raw']
                        self.calibration_samples.append({
                            'vx_raw': vx_raw,
                            'vy_raw': vy_raw,
                            'vz_raw': vz_raw,
                            'timestamp': time.time()
                        })
                        
                        if len(self.calibration_samples) >= CALIBRATION_SAMPLES:
                            self.collecting_calibration = False
                            break
            else:
                # Fallback: manually parse WitMotion 5561 frames for calibration
                if len(data) >= 44 and data[0] == 0x55 and data[1] == 0x61:
                    # Extract first sample from 5561 frame
                    vx_raw = struct.unpack('<h', data[14:16])[0]
                    vy_raw = struct.unpack('<h', data[16:18])[0] 
                    vz_raw = struct.unpack('<h', data[18:20])[0]
                    
                    self.calibration_samples.append({
                        'vx_raw': vx_raw,
                        'vy_raw': vy_raw,
                        'vz_raw': vz_raw,
                        'timestamp': time.time()
                    })
                    
                    if len(self.calibration_samples) >= CALIBRATION_SAMPLES:
                        self.collecting_calibration = False
                        
        except Exception as e:
            self.logger.error(f"Calibration data collection failed: {e}")
    
    async def perform_startup_calibration(self):
        """Perform automatic startup calibration to establish fresh zero baseline"""
        self.logger.info("🎯 Starting automatic calibration...")
        print("🎯 Performing startup calibration...")
        print("📋 Please ensure sensor is STATIONARY during calibration")
        print("⏱️  Collecting 100+ samples for baseline establishment...")
        
        # Reset per-sensor calibration state
        self.per_sensor_calibration = {}
        self.sensor_baselines = {}
        self.collecting_calibration = True
        
        # Initialize storage for each connected sensor
        for sensor_mac in BT50_SENSORS:
            self.per_sensor_calibration[sensor_mac] = {
                "samples": [],
                "baseline": {},
                "complete": False,
                "target_samples": self.sensor_target_count
            }
        
        # Start calibration notifications on all sensors
        try:
            # Enable notifications for all connected BT50 sensors
            for client in self.bt50_clients:
                await client.start_notify(BT50_SENSOR_UUID, self.calibration_notification_handler)
            self.logger.debug(f"Calibration notifications enabled on {len(self.bt50_clients)} sensors")
            
            # Wait for calibration to complete
            start_time = time.time()
            timeout = 30  # 30 second timeout
            
            while self.collecting_calibration:
                await asyncio.sleep(0.1)
                print(f"\r📊 Collected {len(self.calibration_samples)}/{CALIBRATION_SAMPLES} samples...", end='', flush=True)
                
                if time.time() - start_time > timeout:
                    self.logger.error("Calibration timeout - insufficient data")
                    print(f"\n❌ Calibration timeout after {timeout}s")
                    return False
            
            print()  # New line after progress
            
            # Enhanced per-sensor calibration with individual sensor baselines
            self.logger.info("🎯 Calibration collection completed for all sensors!")
            self.logger.info(f"📊 Detailed Per-Sensor Calibration Analysis:")
            self.logger.info(f"📈 Total samples collected: {len(self.calibration_samples)}")
            
            # Store individual sensor baselines (this is the key change!)
            self.individual_sensor_baselines = {}
            
            # Analyze calibration data by clustering samples (sensors have different baselines)
            vx_values = [s['vx_raw'] for s in self.calibration_samples]
            vy_values = [s['vy_raw'] for s in self.calibration_samples]
            vz_values = [s['vz_raw'] for s in self.calibration_samples]
            
            import statistics
            from collections import defaultdict
            
            # Sort by X values to find natural sensor clusters
            vx_sorted = sorted(self.calibration_samples, key=lambda x: x['vx_raw'])
            vx_values_sorted = [s['vx_raw'] for s in vx_sorted]
            
            # Find the gap in X values to split into two sensor groups
            if len(vx_values_sorted) > 1:
                diffs = [vx_values_sorted[i+1] - vx_values_sorted[i] for i in range(len(vx_values_sorted)-1)]
                max_gap_idx = diffs.index(max(diffs))
                split_value = (vx_values_sorted[max_gap_idx] + vx_values_sorted[max_gap_idx + 1]) / 2
                
                # Split samples into two groups based on X value
                sensor_groups = defaultdict(list)
                for sample in self.calibration_samples:
                    if sample['vx_raw'] <= split_value:
                        sensor_groups[0].append(sample)
                    else:
                        sensor_groups[1].append(sample)
                        
                self.logger.info(f"📊 Sensor detection: Split at X={split_value:.0f}")
                self.logger.info(f"📊 Group sizes: {len(sensor_groups[0])} + {len(sensor_groups[1])}")
            else:
                sensor_groups = {0: self.calibration_samples}
            
            # Create individual baselines for each sensor
            sensor_names = ['BAE5', '5550']
            for i, (group_id, samples) in enumerate(sensor_groups.items()):
                if len(samples) < 10:  # Need minimum samples
                    continue
                    
                sensor_name = sensor_names[i] if i < len(sensor_names) else f"Sensor_{group_id+1}"
                    
                vx_group = [s['vx_raw'] for s in samples]
                vy_group = [s['vy_raw'] for s in samples]
                vz_group = [s['vz_raw'] for s in samples]
                
                # Calculate individual sensor baseline
                baseline_x = int(sum(vx_group) / len(vx_group))
                baseline_y = int(sum(vy_group) / len(vy_group))
                baseline_z = int(sum(vz_group) / len(vz_group))
                
                noise_x = statistics.stdev(vx_group) if len(set(vx_group)) > 1 else 0
                noise_y = statistics.stdev(vy_group) if len(set(vy_group)) > 1 else 0
                noise_z = statistics.stdev(vz_group) if len(set(vz_group)) > 1 else 0
                
                # Store individual sensor baseline
                self.individual_sensor_baselines[sensor_name] = {
                    'baseline_x': baseline_x,
                    'baseline_y': baseline_y,
                    'baseline_z': baseline_z,
                    'noise_x': noise_x,
                    'noise_y': noise_y,
                    'noise_z': noise_z,
                    'sample_count': len(samples)
                }
                
                # Log individual sensor analysis to console log
                self.logger.info(f"📊 {sensor_name} Individual Calibration:")
                self.logger.info(f"   📈 Samples collected: {len(samples)}")
                self.logger.info(f"   📍 Individual Baseline: X={baseline_x:+05d}, Y={baseline_y:+05d}, Z={baseline_z:+05d}")
                self.logger.info(f"   📏 Noise (±1σ): X=±{noise_x:.1f}, Y=±{noise_y:.1f}, Z=±{noise_z:.1f}")
                self.logger.info(f"   🔧 Zero adjustment: X={abs(baseline_x)}, Y={abs(baseline_y)}, Z={abs(baseline_z)} counts")
                self.logger.info(f"   📈 95% confidence (±2σ): X=±{2*noise_x:.1f}, Y=±{2*noise_y:.1f}, Z=±{2*noise_z:.1f}")

            # Set system baseline to first sensor for compatibility, but each sensor uses its own
            if self.individual_sensor_baselines:
                first_sensor = list(self.individual_sensor_baselines.keys())[0]
                self.baseline_x = self.individual_sensor_baselines[first_sensor]['baseline_x']
                self.baseline_y = self.individual_sensor_baselines[first_sensor]['baseline_y']
                self.baseline_z = self.individual_sensor_baselines[first_sensor]['baseline_z']
                
                self.logger.info(f"🎯 Individual Sensor Calibration Complete:")
                self.logger.info(f"   📊 {len(self.individual_sensor_baselines)} sensors individually calibrated")
                self.logger.info(f"   🎯 Each sensor will use its own baseline for impact detection")
            else:
                # Fallback to combined approach
                self.baseline_x = int(sum(vx_values) / len(vx_values))
                self.baseline_y = int(sum(vy_values) / len(vy_values))
                self.baseline_z = int(sum(vz_values) / len(vz_values))

            # Calculate noise characteristics for compatibility
            import statistics
            noise_x = statistics.stdev(vx_values) if len(set(vx_values)) > 1 else 0
            noise_y = statistics.stdev(vy_values) if len(set(vy_values)) > 1 else 0
            noise_z = statistics.stdev(vz_values) if len(set(vz_values)) > 1 else 0            # Initialize shot detector with calibrated baseline (if available)
            if PARSER_AVAILABLE:
                self.shot_detector = ShotDetector(
                    baseline_x=self.baseline_x,
                    threshold=IMPACT_THRESHOLD,
                    min_duration=6,
                    max_duration=11,
                    min_interval_seconds=1.0
                )
            else:
                self.logger.warning("Shot detector not available - impact detection disabled")
                self.shot_detector = None
            
            self.calibration_complete = True
            
            # Log calibration results - separate completion from details
            self.logger.info(f"Calibration complete: X={self.baseline_x}, Y={self.baseline_y}, Z={self.baseline_z}")
            self.logger.info("✅ Calibration completed successfully!")
            self.logger.info(f"📊 Baseline established: X={self.baseline_x}, Y={self.baseline_y}, Z={self.baseline_z}")
            self.logger.info(f"📈 Noise levels: X=±{noise_x:.1f}, Y=±{noise_y:.1f}, Z=±{noise_z:.1f}")
            self.logger.info(f"🎯 Impact threshold: {IMPACT_THRESHOLD} counts from baseline")
            
            # Log calibration event
            self.log_event("Calibration", "Sensor", "12:E3", "Plate 1", 
                         f"Baseline established: X={self.baseline_x}, Y={self.baseline_y}, Z={self.baseline_z} "
                         f"(noise: ±{noise_x:.1f}, ±{noise_y:.1f}, ±{noise_z:.1f})")
            
            # Switch back to normal notification handler
            # Switch all sensors to impact notification handler with individual sensor identification
            for i, client in enumerate(self.bt50_clients):
                await client.stop_notify(BT50_SENSOR_UUID)
                
                # Create a sensor-specific handler using closure to capture the sensor MAC
                sensor_mac = self.bt50_sensors[i]
                
                def create_sensor_handler(sensor_address):
                    async def sensor_specific_handler(characteristic, data):
                        await self.bt50_notification_handler(characteristic, data, sensor_address)
                    return sensor_specific_handler
                
                # Use the sensor-specific handler
                handler = create_sensor_handler(sensor_mac)
                await client.start_notify(BT50_SENSOR_UUID, handler)
                
                sensor_id = self.bt50_sensors[i][-5:].replace(":", "")
                self.logger.debug(f"Impact notifications enabled for sensor {sensor_id} ({sensor_mac})")

            # Show listening status for all sensors
            self.logger.info(f"📝 Status: All {len(self.bt50_clients)} sensors - Listening")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            print(f"❌ Calibration failed: {e}")
            return False
        
    def log_event(self, event_type, device, device_id, position, details, timestamp=None):
        """Log structured events"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # CSV format
        csv_line = f'{timestamp.strftime("%m/%d/%y %I:%M:%S.%f")[:-4]}{timestamp.strftime("%p").lower()},{event_type},{device},{device_id},{position},"{details}"\n'
        
        csv_file = f"logs/main/bridge_main_{timestamp.strftime('%Y%m%d')}.csv"
        with open(csv_file, 'a') as f:
            f.write(csv_line)
            
        # NDJSON format
        json_data = {
            "datetime": timestamp.strftime("%m/%d/%y %I:%M:%S.%f")[:-4] + timestamp.strftime("%p").lower(),
            "type": event_type,
            "device": device,
            "device_id": device_id,
            "device_position": position,
            "details": details,
            "timestamp_iso": timestamp.isoformat(),
            "seq": int(time.time())
        }
        
        ndjson_file = f"logs/main/bridge_main_{timestamp.strftime('%Y%m%d')}.ndjson"
        with open(ndjson_file, 'a') as f:
            f.write(json.dumps(json_data) + '\n')
            
        # Only print detailed log events to debug level (not console)
        self.logger.debug(f"Event logged: {event_type}: {device} {device_id} - {details}")

    async def amg_notification_handler(self, characteristic, data):
        """Handle AMG timer notifications with complete frame capture"""
        hex_data = data.hex()

        
        # Log raw hex to debug only
        self.logger.debug(f"AMG notification: {hex_data}")
        self.logger.debug(f"AMG raw bytes: {list(data)} (length: {len(data)} bytes)")
        
        # AMG frames are typically 14 bytes, not 32
        expected_frame_size = 14
        if len(data) != expected_frame_size:
            self.logger.debug(f"AMG frame size: {len(data)} bytes (expected: {expected_frame_size})")
        
        # Enhanced frame type analysis
        if len(data) >= 2:
            frame_header = data[0]
            frame_type = data[1]
            frame_type_names = {0x03: "SHOT", 0x05: "START", 0x08: "STOP"}
            frame_name = frame_type_names.get(frame_type, f"UNKNOWN({frame_type:02x})")
            
            # Log raw hex data to debug log only (not console)
            if len(data) >= 14:
                hex_row = ' '.join(f'{b:02x}' for b in data[:14])
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                self.logger.debug(f"AMG_HEX [{timestamp}] {frame_name:5s}: {hex_row}")
            
            self.logger.debug(f"AMG frame type: {frame_header:02x}{frame_type:02x} = {frame_name}")
            
            # Handle START beep (frame type 0x05)
            if frame_header == 0x01 and frame_type == 0x05:
                self.start_beep_time = datetime.now()
                
                # Use byte 13 as string number (per official AMG project documentation)
                if len(data) >= 14:
                    self.current_string_number = data[13]  # Bytes 12-13 = series/batch (string number)
                    
                    # Extract additional timing data per AMG protocol
                    time_cs = (data[4] << 8) | data[5]  # Bytes 4-5: main time (centiseconds)
                    split_cs = (data[6] << 8) | data[7]  # Bytes 6-7: split time (centiseconds) 
                    first_cs = (data[8] << 8) | data[9]  # Bytes 8-9: first shot time (centiseconds)
                    
                    self.logger.info(f"📝 Status: Timer DC:1A - -------Start Beep ------- String #{self.current_string_number} at {self.start_beep_time.strftime('%H:%M:%S.%f')[:-3]}")
                else:
                    self.current_string_number = 1
                    self.logger.info(f"📝 Status: Timer DC:1A - -------Start Beep ------- String #{self.current_string_number} at {self.start_beep_time.strftime('%H:%M:%S.%f')[:-3]}")
                
                # Reset counters for new string
                self.impact_counter = 0
                self.previous_shot_time = None
                # Initialize shot counter for new string
                self.shot_counter = 0
                # Reset impact peak tracking for new string
                self.recent_impact_peaks = []
                # Reset shot split times tracking for new string
                self.shot_split_times = []
            
            # Handle shots with split timing (frame type 0x03)
            elif frame_header == 0x01 and frame_type == 0x03 and len(data) >= 14:
                # Use byte 2 for shot number and byte 13 for string number (per AMG project)
                shot_number = data[2]
                string_number = data[13]  # Bytes 12-13 = series/batch (string number)
                reception_timestamp = datetime.now()
                
                # Extract timing data per AMG protocol
                time_cs = (data[4] << 8) | data[5]        # Bytes 4-5: main time (centiseconds)
                split_cs = (data[6] << 8) | data[7]       # Bytes 6-7: split time (centiseconds)
                first_cs = (data[8] << 8) | data[9]       # Bytes 8-9: first shot time (centiseconds)
                
                timer_split_seconds = time_cs / 100.0
                timer_split_ms = time_cs * 10
                split_seconds = split_cs / 100.0
                first_seconds = first_cs / 100.0
                
                # Calculate actual shot timestamp based on start beep + timer split
                actual_shot_timestamp = reception_timestamp
                if self.start_beep_time:
                    actual_shot_timestamp = self.start_beep_time + timedelta(milliseconds=timer_split_ms)
                
                # Calculate time from previous shot for split timing
                shot_split_seconds = 0.0
                if hasattr(self, 'previous_shot_time') and self.previous_shot_time:
                    shot_split_seconds = (actual_shot_timestamp - self.previous_shot_time).total_seconds()
                    # Track split times for average calculation (exclude shot #1's 0.0 split)
                    if not hasattr(self, 'shot_split_times'):
                        self.shot_split_times = []
                    self.shot_split_times.append(shot_split_seconds)
                
                self.logger.info(f"🔫 String {string_number}, Shot #{shot_number} - Time {timer_split_seconds:.2f}s, Split {shot_split_seconds:.2f}s, First {first_seconds:.2f}s")
                
                # Store for next split calculation
                self.previous_shot_time = actual_shot_timestamp
                self.shot_counter = shot_number  # Track shot number within string
                
                # Log with actual timer split values
                shot_details = f"Shot #{shot_number}, timer split: {timer_split_seconds:.2f}s ({timer_split_ms:.0f}ms)"
                
                # Add ACTUAL shot timestamp (not reception time) to timing calibrator
                if self.timing_calibrator:
                    self.timing_calibrator.add_shot_event(actual_shot_timestamp, shot_number, "DC:1A")
                    self.logger.debug(f"Shot #{shot_number} added to timing calibrator with timer split: {timer_split_seconds:.2f}s")
                
                # Generate statistical timing projection for impact
                if STATISTICAL_TIMING_AVAILABLE and statistical_calibrator:
                    projected_impact_time, timing_metadata = statistical_calibrator.project_impact_time(
                        actual_shot_timestamp, confidence_level="median"
                    )
                    
                    # Log projected impact timing with confidence intervals
                    confidence_range = timing_metadata["confidence_intervals"]["68_percent"]
                    # Store projection metadata for impact correlation
                    self.last_projection = {
                        'shot_number': shot_number,
                        'shot_time': actual_shot_timestamp,
                        'projected_time': projected_impact_time,
                        'metadata': timing_metadata
                    }
                    
                    # Log projection details to debug
                    self.logger.debug(f"Statistical projection metadata: {json.dumps(timing_metadata, indent=2)}")
                    
                    # Add projection event to logs
                    projection_details = (f"Impact projected at {projected_impact_time.strftime('%H:%M:%S.%f')[:-3]}, "
                                        f"offset: {timing_metadata['offset_used_ms']}ms, "
                                        f"uncertainty: ±{timing_metadata['uncertainty_ms']}ms")
                    self.log_event("Projection", "Statistical", "BT50", "Bay 1", projection_details, projected_impact_time)
            
            # Handle STOP frame (frame type 0x08) 
            elif frame_header == 0x01 and frame_type == 0x08:
                reception_timestamp = datetime.now()
                
                # Extract string number and timing data per AMG protocol
                if len(data) >= 14:
                    string_number = data[13]  # Bytes 12-13 = series/batch (string number)
                    time_cs = (data[4] << 8) | data[5]        # Bytes 4-5: main time (centiseconds)
                    split_cs = (data[6] << 8) | data[7]       # Bytes 6-7: split time (centiseconds)
                    first_cs = (data[8] << 8) | data[9]       # Bytes 8-9: first shot time (centiseconds)
                    
                    timer_seconds = time_cs / 100.0
                    split_seconds = split_cs / 100.0
                    first_seconds = first_cs / 100.0
                else:
                    string_number = getattr(self, 'current_string_number', 1)
                    timer_seconds = 0
                    split_seconds = 0
                    first_seconds = 0
                
                # Calculate total string time if start beep available
                total_info = ""
                if self.start_beep_time:
                    total_ms = (reception_timestamp - self.start_beep_time).total_seconds() * 1000
                    total_info = f" (total: {timer_seconds:.2f}s)"
                
                self.logger.info(f"📝 Status: Timer DC:1A - Stop Beep for String #{string_number} at {reception_timestamp.strftime('%H:%M:%S.%f')[:-3]}{total_info}")
                if len(data) >= 14:
                    # Calculate impact statistics
                    impact_count = getattr(self, 'impact_counter', 0)
                    shot_count = getattr(self, 'shot_counter', 0)
                    
                    # Calculate average peak magnitude from recent impacts
                    avg_peak = 0
                    if hasattr(self, 'recent_impact_peaks') and self.recent_impact_peaks:
                        avg_peak = int(sum(self.recent_impact_peaks) / len(self.recent_impact_peaks))
                    
                    # Calculate average split time from shot deltas
                    avg_split = 0.0
                    if hasattr(self, 'shot_split_times') and self.shot_split_times:
                        avg_split = sum(self.shot_split_times) / len(self.shot_split_times)
                    
                    self.logger.info(f"📊 String {string_number} Final - Time {timer_seconds:.2f}s, Avg Split {avg_split:.2f}s, First {first_seconds:.2f}s, Shots {shot_count}, Impacts {impact_count}, Avg Peak {avg_peak}g")
                
                stop_details = f"String #{string_number} Stop"
                if self.start_beep_time:
                    stop_details += f", total time: {total_ms:.0f}ms"
                
                # Use reception timestamp for STOP since no timer data available
                
                # Reset for next string
                self.start_beep_time = None
                self.impact_counter = 0
                self.shot_counter = 0
                self.previous_shot_time = None
                self.recent_impact_peaks = []
                self.shot_split_times = []
            else:
                self.logger.debug(f"AMG {frame_name} frame (not logged to console)")
        else:
            self.logger.warning(f"AMG frame too short for type analysis: {len(data)} bytes")



    def get_sensor_baseline(self, sensor_mac):
        """Get individual sensor baseline for accurate impact detection"""
        if sensor_mac in self.sensor_baselines:
            baseline = self.sensor_baselines[sensor_mac]
            return (baseline["baseline_x"], baseline["baseline_y"], baseline["baseline_z"])
        else:
            # Fallback to system baseline
            self.logger.warning(f"No individual baseline for sensor {sensor_mac[-5:]}, using system baseline")
            return (self.baseline_x, self.baseline_y, self.baseline_z)

    def get_current_sensor_info(self, sensor_mac=None):
        """Get sensor information for logging - database-aware version"""
        try:
            sensor_id = sensor_mac[-5:] if sensor_mac else "UNK"

            # Query database for current sensor-to-target assignments
            try:
                # Import database components
                from src.impact_bridge.database.models import Sensor, TargetConfig, StageConfig, Bridge
                from src.impact_bridge.database.database import get_database_session, init_database
                from src.impact_bridge.config import DatabaseConfig
                
                # Initialize database with proper config
                db_config = DatabaseConfig()
                init_database(db_config)
                
                with get_database_session() as session:
                    # Find the sensor by MAC address
                    sensor = session.query(Sensor).filter(Sensor.hw_addr == sensor_mac).first()
                    
                    if sensor and sensor.target_config_id:
                        # Get target configuration
                        target = session.query(TargetConfig).filter(TargetConfig.id == sensor.target_config_id).first()
                        if target:
                            target_id = f"Target {target.target_number}"
                            
                            # Get stage information
                            stage = session.query(StageConfig).filter(StageConfig.id == target.stage_config_id).first()
                            stage_name = stage.name if stage else "Unknown Stage"
                            
                            # Get bridge information
                            bridge = session.query(Bridge).filter(Bridge.id == sensor.bridge_id).first()
                            bridge_name = bridge.name if bridge else "Unknown Bridge"
                            
                            return {
                                "bridge_name": bridge_name,
                                "stage_name": stage_name,
                                "target_id": target_id,
                                "sensor_id": sensor_id
                            }
            
            except Exception as db_error:
                self.logger.debug(f"Database lookup failed: {db_error}")
            
            # Fallback: Use MAC-based mapping if database lookup fails
            target_id = "Unknown"
            if sensor_mac:
                if "55:50" in sensor_mac:
                    target_id = "Target 2"
                elif "76:5B" in sensor_mac:
                    target_id = "Target 3"
                else:
                    target_id = "Target 1"

            return {
                "bridge_name": "Orange-GoFast Bridge",
                "stage_name": "Go Fast",
                "target_id": target_id,
                "sensor_id": sensor_id
            }

        except Exception as e:
            self.logger.debug(f"Error in get_current_sensor_info: {e}")
            # Absolute fallback
            return {
                "bridge_name": "Default Bridge",
                "stage_name": "Default Stage", 
                "target_id": "Target 1",
                "sensor_id": sensor_mac[-5:] if sensor_mac else "UNK"
            }
    async def bt50_notification_handler(self, characteristic, data, sensor_mac=None):
        # DEBUG: Track which sensor is calling        sensor_short = sensor_mac[-5:] if sensor_mac else "UNK"        if not hasattr(self, "_handler_calls"):            self._handler_calls = {}        self._handler_calls[sensor_short] = self._handler_calls.get(sensor_short, 0) + 1        if self._handler_calls[sensor_short] % 50 == 0:            self.logger.info(f"🔍 Handler calls: {sensor_short} = {self._handler_calls[sensor_short]}")
        """Handle BT50 sensor notifications with RAW VALUES and shot detection"""
        hex_data = data.hex()

        # Use the sensor_mac parameter passed from the sensor-specific handler
        if sensor_mac is None:
            # Fallback: use first available sensor if no parameter provided
            if self.sensor_mappings:
                sensor_mac = list(self.sensor_mappings.keys())[0]
            else:
                sensor_mac = "UNKNOWN:SENSOR"

        
        # Log raw data to debug only
        # TEMP DEBUG: Show sensor activity every 100 notifications        if not hasattr(self, "_debug_counter"):            self._debug_counter = {}        sensor_short = sensor_mac[-5:] if sensor_mac else "UNK"        self._debug_counter[sensor_short] = self._debug_counter.get(sensor_short, 0) + 1        if self._debug_counter[sensor_short] % 100 == 0:            self.logger.info(f"📊 DEBUG: Sensor {sensor_short} active (notifications: {self._debug_counter[sensor_short]})")
        self.logger.debug(f"BT50 raw: {hex_data[:64]}...")
        
        if not PARSER_AVAILABLE:
            self.logger.warning("Parser not available, skipping impact detection")
            return
            
        if not self.calibration_complete:
            self.logger.warning("Calibration not complete, skipping detection")
            return
            
        # Use parser but extract raw integer values directly
        try:
            result = parse_5561(data)
            if result and result['samples']:
                # Get RAW INTEGER values directly (no scale factor applied)
                sample = result['samples'][0]  # First sample
                vx_raw, vy_raw, vz_raw = sample['raw']  # Raw int16 values
                
                # Apply dynamic baseline subtraction to raw values
                vx_corrected = vx_raw - self.baseline_x
                vy_corrected = vy_raw - self.baseline_y
                vz_corrected = vz_raw - self.baseline_z
                
                # Calculate corrected magnitude from raw values
                magnitude_corrected = (vx_corrected**2 + vy_corrected**2 + vz_corrected**2)**0.5
                magnitude_raw = (vx_raw**2 + vy_raw**2 + vz_raw**2)**0.5
                
                # Enhanced sample logging for impact analysis (development mode)
                current_time = datetime.now()
                
                # Development mode sample logging
                if self.dev_config and self.dev_config.is_sample_logging_enabled():
                    if self.dev_config.should_log_all_samples() or (self.dev_config.should_log_impact_samples() and magnitude_corrected > 25.0):
                        self.logger.debug(f"BT50 sample: {current_time.strftime('%H:%M:%S.%f')[:-3]} vx_raw={vx_raw}, vy_raw={vy_raw}, vz_raw={vz_raw}, magnitude={magnitude_corrected:.1f}")
                elif not self.dev_config:  # Fallback if no dev config
                    self.logger.debug(f"BT50 sample: {current_time.strftime('%H:%M:%S.%f')[:-3]} vx_raw={vx_raw}, vy_raw={vy_raw}, vz_raw={vz_raw}, magnitude={magnitude_corrected:.1f}")
                
                # Show processing status every 50 samples (debug)
                if hasattr(self, '_sample_count'):
                    self._sample_count += 1
                else:
                    self._sample_count = 1
                    
                if self._sample_count % 50 == 0:
                    self.logger.debug(f"BT50 processing: sample #{self._sample_count}, current magnitude: {magnitude_corrected:.1f}")
                
                # Run shot detection on X-axis raw values (if available)
                if self.shot_detector:
                    shot_event = self.shot_detector.process_sample(vx_raw)
                    if shot_event:
                        # Shot detected! Log detailed information
                        # Get sensor info for logging with specific sensor
                        sensor_info = self.get_current_sensor_info(sensor_mac)
                        bridge_name = sensor_info["bridge_name"]
                        stage_name = sensor_info["stage_name"]
                        target_id = sensor_info["target_id"]
                        sensor_id = sensor_info["sensor_id"]
                        
                        self.logger.info(f"🎯 SHOT DETECTED #{shot_event.shot_id}: Stage {stage_name}, Target {target_num}, Sensor {sensor_id} - Duration {shot_event.duration_ms:.0f}ms, Deviation {shot_event.max_deviation} counts")
                        
                        self.log_event("Shot", "Sensor", sensor_id, f"Target {target_num}", 
                                     f"Shot #{shot_event.shot_id}: duration {shot_event.duration_samples} samples ({shot_event.duration_ms:.0f}ms), "
                                     f"max deviation {shot_event.max_deviation} counts, X-range [{min(shot_event.x_values)}-{max(shot_event.x_values)}]")
                
                # Enhanced impact detection with onset timing
                # Get or create detector for this sensor
                sensor_short = sensor_mac[-5:] if sensor_mac else "UNK"
                if sensor_short not in self.enhanced_impact_detectors:
                    if ENHANCED_DETECTION_AVAILABLE:
                        if self.dev_config and hasattr(self.dev_config, 'enhanced_impact_detection'):
                            peak_threshold = self.dev_config.enhanced_impact_detection.peak_threshold
                            onset_threshold = self.dev_config.enhanced_impact_detection.onset_threshold  
                            lookback_samples = self.dev_config.enhanced_impact_detection.lookback_samples
                        else:
                            peak_threshold = 150.0
                            onset_threshold = 30.0
                            lookback_samples = 10
                        self.enhanced_impact_detectors[sensor_short] = EnhancedImpactDetector(
                            threshold=peak_threshold,
                            onset_threshold=onset_threshold,
                            lookback_samples=lookback_samples
                        )
                    else:
                        self.enhanced_impact_detectors[sensor_short] = None
                        
                if self.enhanced_impact_detectors.get(sensor_short):
                    # Debug: Log every 1000th sample to verify detector is active
                    if not hasattr(self, '_debug_sample_count'):
                        self._debug_sample_count = 0
                    self._debug_sample_count += 1
                    if self._debug_sample_count % 1000 == 0:
                        self.logger.debug(f"Enhanced impact detector active, processed {self._debug_sample_count} samples")
                    timestamp = datetime.now()
                    impact_event = self.enhanced_impact_detectors[sensor_short].process_sample(
                        timestamp=timestamp,
                        raw_values=[vx_raw, vy_raw, vz_raw],
                        corrected_values=[vx_corrected, vy_corrected, vz_corrected],
                        magnitude=magnitude_corrected
                    )
                    
                    if impact_event:
                        # Simple impact logging - calculate basic timing
                        impact_number = getattr(self, 'impact_counter', 0) + 1
                        setattr(self, 'impact_counter', impact_number)
                        
                        # Calculate time from string start
                        if self.start_beep_time:
                            time_from_start = (impact_event.onset_timestamp - self.start_beep_time).total_seconds()
                        else:
                            time_from_start = 0.0
                        
                        # Calculate time from shot if projection available
                        time_from_shot = 0.0
                        if hasattr(self, 'last_projection') and self.last_projection:
                            actual_shot_time = self.last_projection['shot_time']
                            time_from_shot = (impact_event.onset_timestamp - actual_shot_time).total_seconds()
                        
                        # Get current string number
                        current_string = getattr(self, 'current_string_number', 1)
                        
                        # Console impact logging  
                        # Get sensor info for enhanced logging with specific sensor
                        sensor_info = self.get_current_sensor_info(sensor_mac)
                        bridge_name = sensor_info["bridge_name"]
                        stage_name = sensor_info["stage_name"]
                        target_id = sensor_info["target_id"]
                        sensor_id = sensor_info["sensor_id"]
                        
                        # Enhanced console impact logging with Stage/Target/Sensor info
                        self.logger.info(f"💥 IMPACT #{impact_number}: {bridge_name} | {stage_name} | {target_id} | Sensor {sensor_id} - String {current_string}, Time {time_from_start:.2f}s, Shot→Impact {time_from_shot:.3f}s, Peak {impact_event.peak_magnitude:.0f}g")
                        
                        # Track impact peak magnitudes for final statistics
                        if not hasattr(self, 'recent_impact_peaks'):
                            self.recent_impact_peaks = []
                        self.recent_impact_peaks.append(impact_event.peak_magnitude)
                        
                        # Log structured event data
                        self.log_event("Impact", "Sensor", sensor_id, f"Target {target_num}", 
                                     f"Enhanced impact: onset {impact_event.onset_magnitude:.1f}g → peak {impact_event.peak_magnitude:.1f}g, "
                                     f"duration {impact_event.duration_ms:.1f}ms, confidence {impact_event.confidence:.2f}")

                
                
                
                # Fallback: Legacy impact detection (if enhanced detection not available)
                elif magnitude_corrected > IMPACT_THRESHOLD:
                    timestamp = datetime.now()
                    
                    # Log clean impact message with corrected values only
                    # Get sensor info for legacy logging with specific sensor
                    sensor_info = self.get_current_sensor_info(sensor_mac)
                    bridge_name = sensor_info["bridge_name"]
                    stage_name = sensor_info["stage_name"]
                    sensor_id = sensor_info["sensor_id"]
                    target_id = sensor_info["target_id"]
                    
                    self.logger.info(f"📝 LEGACY IMPACT: Stage {stage_name}, Target {target_num}, Sensor {sensor_id} - Mag {magnitude_corrected:.0f}g [{vx_corrected:.0f}, {vy_corrected:.0f}, {vz_corrected:.0f}] at {timestamp.strftime('%H:%M:%S.%f')[:-3]}")
                    self.log_event("Impact", "Sensor", sensor_id, f"Target {target_num}", 
                                 f"Legacy impact: Mag={magnitude_corrected:.1f} corrected[{vx_corrected:.1f},{vy_corrected:.1f},{vz_corrected:.1f}] (threshold: {IMPACT_THRESHOLD})")
                    
                    # Add to timing calibrator for correlation (using peak timestamp)
                    if self.timing_calibrator:
                        self.timing_calibrator.add_impact_event(timestamp, magnitude_corrected, "12:E3", vx_raw)
                        self.logger.debug(f"Legacy impact {magnitude_corrected:.1f}g added to timing calibrator")
                
        except Exception as e:
            self.logger.debug(f"BT50 parsing failed: {e}")

    async def reset_ble(self):
        """Reset BLE connections before starting"""
        self.logger.info("🔄 Starting BLE reset")
        
        try:
            import subprocess
            
            # Simple disconnect commands
            devices = [BT50_SENSOR_MAC, AMG_TIMER_MAC]
            for mac in devices:
                try:
                    subprocess.run(['bluetoothctl', 'disconnect', mac], 
                                  capture_output=True, text=True, timeout=3)
                    self.logger.debug(f"Attempted disconnect of {mac}")
                except Exception as e:
                    self.logger.debug(f"Disconnect {mac} failed: {e}")
            
            # Quick adapter cycle
            try:
                subprocess.run(['sudo', 'hciconfig', 'hci0', 'down'], 
                             capture_output=True, timeout=2)
                await asyncio.sleep(0.5)
                subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], 
                             capture_output=True, timeout=2)
                self.logger.info("🔧 Reset Bluetooth adapter")
            except Exception as e:
                self.logger.warning(f"Adapter reset failed: {e}")
            
            # Brief wait for stabilization
            await asyncio.sleep(1)
            self.logger.info("✓ BLE reset complete")
            
        except Exception as e:
            self.logger.error(f"BLE reset failed: {e}")
            print(f"⚠ BLE reset failed: {e}")

    async def connect_devices(self):
        """Connect to both devices"""
        # Perform automatic BLE reset first
        await self.reset_ble()
        
        self.logger.info("📝 Status: Bridge MCU1 - Bridge Initialized")
        self.log_event("Status", "Bridge", "MCU1", "Bay 1", "Bridge Initialized")
        
        try:
            # Connect AMG Timer
            self.logger.info("Connecting to AMG timer...")
            self.amg_client = BleakClient(AMG_TIMER_MAC)
            await self.amg_client.connect()
            self.logger.info("📝 Status: Timer DC:1A - Connected")
            self.log_event("Status", "Timer", "DC:1A", "Bay 1", "Connected")
            
            # Enable notifications
            await self.amg_client.start_notify(AMG_TIMER_UUID, self.amg_notification_handler)
            self.logger.info("AMG timer and shot notifications enabled")
            
        except Exception as e:
            self.logger.error(f"AMG timer connection failed: {e}")
            
        try:
            # Connect BT50 Sensor
            # Connect to multiple BT50 sensors
            self.bt50_clients = []  # Reset clients list
            connected_count = 0
            for i, sensor_mac in enumerate(BT50_SENSORS):
                target_num = i + 1
                sensor_id = sensor_mac[-5:].replace(":", "")
                
                try:
                    self.logger.info(f"Connecting to BT50 sensor - Target {target_num} ({sensor_id})...")
                    self.logger.info(f"Target {target_num} MAC: {sensor_mac}")
                    
                    client = BleakClient(sensor_mac)
                    await client.connect()
                    self.bt50_clients.append(client)
                    
                    # Use first sensor as primary for compatibility
                    if i == 0:
                        self.bt50_client = client
                    
                    self.logger.info(f"📝 Status: Sensor {sensor_id} - Connected (Target {target_num})")
                    self.log_event("Status", "Sensor", sensor_id, f"Target {target_num}", "Connected")
                    
                    # Store sensor mapping for impact logging
                    ble_id = sensor_mac[-5:]  # Last 5 chars (55:50 format)
                    self.sensor_mappings[sensor_mac] = {
                        "sensor_id": ble_id,
                        "target_num": target_num,
                        "stage": "Go Fast",  # TODO: Get from Bridge configuration
                        "full_mac": sensor_mac
                    }
                    self.logger.debug(f"Stored sensor mapping: {ble_id} -> Target {target_num}, Stage Go Fast")
                    connected_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Target {target_num} sensor connection failed: {e}")
            
            self.logger.info(f"✅ Connected to {connected_count}/{len(self.bt50_sensors)} BT50 sensors")
            
            # Wait for connection to stabilize before calibration
            await asyncio.sleep(1.0)
            
            # Perform startup calibration
            calibration_success = await self.perform_startup_calibration()
            if not calibration_success:
                self.logger.error("Startup calibration failed - cannot proceed")
                print("❌ Bridge startup failed due to calibration error")
                return
            
            # Calibration handles the listening status message
            self.logger.info(f"BT50 sensors ({len(self.bt50_clients)}) and impact notifications enabled")
            
        except Exception as e:
            self.logger.error(f"BT50 sensor connection failed: {e}")
        
        # Final ready status - only if both devices connected successfully
        if (self.amg_client and self.amg_client.is_connected and 
            self.bt50_client and self.bt50_client.is_connected and 
            self.calibration_complete):
            self.logger.info("-----------------------------🎯Bridge ready for String🎯-----------------------------")
            self.log_event("Status", "Bridge", "MCU1", "Bay 1", "Bridge ready for String - All systems operational")

    async def cleanup(self):
        """Proper cleanup of BLE connections"""
        self.logger.info("Cleaning up connections...")
        
        # Log shot detection statistics
        if self.shot_detector:
            stats = self.shot_detector.get_stats()
            self.logger.info(f"Shot detection summary: {stats['total_shots']} shots detected "
                            f"from {stats['total_samples']} samples ({stats['shots_per_minute']:.1f}/min)")
            
            recent_shots = self.shot_detector.get_recent_shots()
            if recent_shots:
                self.logger.info("Recent shots:")
                for shot in recent_shots:
                    self.logger.info(f"  Shot #{shot.shot_id}: {shot.timestamp_str}, "
                                   f"{shot.duration_samples} samples, {shot.max_deviation} counts")
        else:
            self.logger.info("Shot detector not initialized - no statistics available")
        
        # Report timing correlation statistics
        if self.timing_calibrator:
            timing_stats = self.timing_calibrator.get_correlation_stats()
            self.logger.info("=== TIMING CORRELATION STATISTICS ===")
            self.logger.info(f"Total correlated pairs: {timing_stats['total_pairs']}")
            self.logger.info(f"Correlation success rate: {timing_stats['success_rate']*100:.1f}%")
            self.logger.info(f"Average timing delay: {timing_stats['avg_delay_ms']}ms")
            self.logger.info(f"Expected timing delay: {timing_stats['expected_delay_ms']}ms")
            self.logger.info(f"Calibration status: {timing_stats['calibration_status']}")
            if timing_stats['pending_shots'] > 0 or timing_stats['pending_impacts'] > 0:
                self.logger.info(f"Pending events: {timing_stats['pending_shots']} shots, {timing_stats['pending_impacts']} impacts")
            self.logger.info("=====================================")
        else:
            self.logger.info("Timing calibrator not initialized - no correlation statistics")
        
        if self.amg_client and self.amg_client.is_connected:
            try:
                await self.amg_client.stop_notify(AMG_TIMER_UUID)
                await self.amg_client.disconnect()
                self.log_event("Status", "Timer", "DC:1A", "Bay 1", "Disconnected")
            except Exception as e:
                self.logger.error(f"AMG cleanup error: {e}")
                
        if self.bt50_client and self.bt50_client.is_connected:
            try:
                await self.bt50_client.stop_notify(BT50_SENSOR_UUID)
                await self.bt50_client.disconnect()
                self.log_event("Status", "Sensor", "12:E3", "Plate 1", "Disconnected")
            except Exception as e:
                self.logger.error(f"BT50 cleanup error: {e}")
                
        self.logger.info("Cleanup complete")

    async def run(self):
        """Main run loop with proper cleanup"""
        self.running = True
        
        # Announce startup and log file location
        self.logger.info("🎯 TinTown Bridge v2.0 - Starting...")
        self.logger.info(f"📋 Complete console log: {console_log_path}")
        self.logger.info("💡 Use 'tail -f' on this log file to see ALL events including AMG beeps")
        
        try:
            await self.connect_devices()
            
            print("\n=== AUTOMATIC CALIBRATION BRIDGE WITH SHOT DETECTION ===")
            print("✨ Dynamic baseline calibration - establishes fresh zero on every startup")
            print("🎯 Shot Detection: 150 count threshold, 6-11 sample duration, 1s interval")
            print(f"📊 Current baseline: X={self.baseline_x}, Y={self.baseline_y}, Z={self.baseline_z} (auto-calibrated)")
            print(f"⚡ Impact threshold: {IMPACT_THRESHOLD} counts from dynamic baseline")
            print("🔄 Baseline automatically corrects for any sensor orientation")
            print("Press CTRL+C to stop\n")
            
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping bridge...")
            self.running = False
        except Exception as e:
            self.logger.error(f"Bridge error: {e}")
            self.running = False
        finally:
            await self.cleanup()

async def main():
    bridge = FixedBridge()
    await bridge.run()

if __name__ == "__main__":
    asyncio.run(main())