#!/usr/bin/env python3
"""
LeadVille Impact Bridge - Production BLE-based Impact Sensor System

A clean, production-ready implementation of the BT50 sensor bridge with AM            # Enhanced impact detector initialized silently (manual message below) timer integration.
Provides real-time shot detection, impact correlation, and comprehensive logging.
"""

import os
import sys
import time
import asyncio
import logging
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from bleak import BleakClient, BleakScanner

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Database imports for Bridge-assigned sensor lookup
from .database.database import get_database_session
from .database.models import Bridge, Sensor

# Setup dual logging - both to console and file
def setup_dual_logging():
    """Setup logging to both console and dedicated log files"""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / 'logs' / 'console'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create console log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    console_log_file = log_dir / f'bridge_console_{timestamp}.log'
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    # File handler for complete console log
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

# Import the impact bridge components
try:
    # Prefer the verbose BLE parser for diagnostics; keep the original simple
    # parse_5561 available to preserve existing behavior used throughout the
    # bridge. The verbose parser can persist parsed frames for analysis.
    try:
        from impact_bridge.ble.wtvb_parse import scan_and_parse, parse_flag61_frame, parse_wtvb32_frame  # type: ignore
    except Exception:
        # If the ble package import style isn't available, try the flat import
        from impact_bridge.wtvb_parse import scan_and_parse, parse_flag61_frame, parse_wtvb32_frame  # type: ignore

    # Import the simple parser under the expected name so existing code keeps working
    try:
        from impact_bridge.ble.wtvb_parse_simple import parse_5561
    except Exception:
        # Fallback if package paths differ
        from impact_bridge.wtvb_parse_simple import parse_5561
    from impact_bridge.shot_detector import ShotDetector
    from impact_bridge.timing_calibration import RealTimeTimingCalibrator
    from impact_bridge.enhanced_impact_detection import EnhancedImpactDetector
    from impact_bridge.statistical_timing_calibration import statistical_calibrator
    from impact_bridge.dev_config import dev_config
    print("✓ Successfully imported all impact bridge components")
    COMPONENTS_AVAILABLE = True
except Exception as e:
    print(f"⚠ Component import failed: {e}")
    COMPONENTS_AVAILABLE = False

<<<<<<< HEAD
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
=======
# Device Configuration - Now dynamically loaded from Bridge assignments
# AMG_TIMER_MAC = "60:09:C3:1F:DC:1A"  # Legacy - now loaded from Bridge assignments
# BT50_SENSOR_MAC = "F8:FE:92:31:12:E3"  # Legacy - now loaded from Bridge assignments
# Placeholder legacy names for backward-compatible reset logic. These will
# usually be None/empty because the bridge reads assignments from the DB.
BT50_SENSOR_MAC = ""
AMG_TIMER_MAC = ""
>>>>>>> origin/pi-snapshot-20250920-155656

# BLE UUIDs
AMG_TIMER_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
BT50_SENSOR_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"

<<<<<<< HEAD
# Impact threshold - Raw count changes (based on stationary variation analysis)
# Normal variation: ~57 counts, so threshold = 3x normal variation
IMPACT_THRESHOLD = 200  # Raw counts - Detect changes > 150 counts from baseline

# Calibration settings
CALIBRATION_SAMPLES = 250  # Number of samples to collect for baseline calibration
=======
# Default configuration values
DEFAULT_IMPACT_THRESHOLD = 150  # Raw counts for impact detection
DEFAULT_CALIBRATION_SAMPLES = 100  # Samples for baseline calibration

>>>>>>> origin/pi-snapshot-20250920-155656

class LeadVilleBridge:
    """
    LeadVille Impact Bridge - Production BLE sensor system
    """
    
    def __init__(self):
        self.logger = logger
        
        self.amg_client = None
        self.bt50_client = None
        self.running = False
        self.session_id = int(time.time())
        
        # Dynamic baseline values (set during calibration)
        self.baseline_x = None
        self.baseline_y = None  
        self.baseline_z = None
        self.calibration_complete = False
        
        # Calibration data collection
        self.calibration_samples = []
        self.collecting_calibration = False
        
        # Shot/Impact tracking
        self.start_beep_time = None
        self.previous_shot_time = None
        self.impact_counter = 0
        self.shot_counter = 0
        self.current_string_number = 1
        self.enhanced_impact_counter = 0
        
        # Initialize components if available
        if COMPONENTS_AVAILABLE:
            self._initialize_components()
        else:
            self.logger.error("Cannot initialize - components not available")
            
        # Setup comprehensive logging
        self._setup_detailed_logging()
        
    def _initialize_components(self):
        """Initialize all impact bridge components"""
        # Follow TinTown's exact initialization sequence
        
<<<<<<< HEAD
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
=======
        # 1. Statistical calibrator FIRST (like TinTown)
        self.statistical_calibrator = statistical_calibrator
        self.logger.info("Statistical calibrator initialized:")
        self.logger.info("  Primary offset: 83.0ms")
        self.logger.info("  Uncertainty: ±94.0ms")
        self.logger.info("  68% confidence: 9.2ms - 196.7ms")
        
        # 2. Development configuration
        self.dev_config = dev_config
        self.logger.info("📋 Loaded development config from config/development.yaml")
        
        # 3. Timing calibrator (before config display)
        self.timing_calibrator = RealTimeTimingCalibrator(
            Path("timing_calibration.json"),
            expected_delay_ms=dev_config.get_expected_delay()
        )
        self.logger.info("Timing calibrator initialized")
        self.logger.info(f"Expected delay: 1035ms")
        self.logger.info(f"Correlation window: 1520.0ms")
        self.logger.info(f"Delay tolerance: ±663ms")
        
        # 4. Development configuration display block
        self.logger.info("============================================================")
        self.logger.info("🔧 TINTOWN DEVELOPMENT CONFIGURATION")
        self.logger.info("============================================================")
        self.logger.info("Mode: 🔧 Development Mode (Enhanced logging and analysis enabled)")
        self.logger.info("Enhanced Logging: ✅")
        self.logger.info("Sample Logging: ✅")
        self.logger.info("Impact Analysis: ✅")
        self.logger.info("Timing Correlation: ✅")
        self.logger.info("Analysis Tools: ✅")
        self.logger.info("Enhanced Impact Detection: ✅")
        self.logger.info("Performance Monitoring: ✅")
        self.logger.info(f"  Onset Threshold: {dev_config.get_onset_threshold()}g")
        self.logger.info(f"  Peak Threshold: {dev_config.get_peak_threshold()}g")
        self.logger.info(f"  Lookback Samples: {dev_config.get_lookback_samples()}")
        self.logger.info("============================================================")
        
        # 5. Enhanced impact detector
        if dev_config.is_enhanced_impact_enabled():
            self.enhanced_impact_detector = EnhancedImpactDetector(
                threshold=dev_config.get_peak_threshold(),
                onset_threshold=dev_config.get_onset_threshold(),
                lookback_samples=dev_config.get_lookback_samples()
            )
            self.logger.info("Enhanced impact detector initialized:")
            self.logger.info(f"  Peak threshold: {dev_config.get_peak_threshold()}g")
            self.logger.info(f"  Onset threshold: {dev_config.get_onset_threshold()}g")
            self.logger.info(f"  Lookback samples: {dev_config.get_lookback_samples()}")
        else:
            self.enhanced_impact_detector = None
            self.logger.info("Enhanced impact detection disabled")
>>>>>>> origin/pi-snapshot-20250920-155656
        
        # Shot detector (initialized after calibration)
        self.shot_detector = None
        
    def _setup_detailed_logging(self):
        """Setup comprehensive debug and main event logging"""
        timestamp = datetime.now()
        
        # Debug log file
        debug_file = f"logs/debug/bridge_debug_{timestamp.strftime('%Y%m%d_%H%M%S')}.log"
        
        # Create debug file handler
        debug_handler = logging.FileHandler(debug_file)
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        debug_handler.setFormatter(debug_formatter)
        
        # Add debug handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(debug_handler)
        root_logger.setLevel(logging.DEBUG)
        
        self.logger.info(f"Debug logging enabled: {debug_file}")
    
    def get_bridge_assigned_devices(self):
        """Get MAC addresses of devices assigned to this Bridge"""
        try:
            with get_database_session() as session:
                bridge = session.query(Bridge).first()
                if not bridge or not bridge.current_stage_id:
                    self.logger.warning("No Bridge or stage assignment found - using default devices")
                    return {
                        'timer': "60:09:C3:1F:DC:1A",  # Default AMG timer
                        'sensors': ["EA:18:3D:6D:BA:E5", "C2:1B:DB:F0:55:50"]  # Default BT50 sensors
                    }
                
                # Get sensors assigned to this Bridge's stage
                target_config_ids = [target.id for target in bridge.current_stage.target_configs]
                if not target_config_ids:
                    self.logger.warning(f"No targets found for stage {bridge.current_stage.name}")
                    return {'timer': None, 'sensors': []}
                
                assigned_sensors = session.query(Sensor).filter(
                    Sensor.target_config_id.in_(target_config_ids),
                    Sensor.bridge_id == bridge.id
                ).all()
                
                # Separate timer and impact sensors
                timer_mac = None
                sensor_macs = []
                
                for sensor in assigned_sensors:
                    # AMG timers have "AMG" or "COMM" in their label
                    if any(keyword in sensor.label.upper() for keyword in ['AMG', 'COMM', 'TIMER']):
                        timer_mac = sensor.hw_addr
                    elif any(keyword in sensor.label.upper() for keyword in ['BT50', 'WTVB']):
                        sensor_macs.append(sensor.hw_addr)
                
                self.logger.info(f"Bridge '{bridge.name}' assigned to stage '{bridge.current_stage.name}'")
                self.logger.info(f"Timer: {timer_mac}")
                self.logger.info(f"Impact Sensors: {sensor_macs}")
                
                return {
                    'timer': timer_mac,
                    'sensors': sensor_macs
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get Bridge assignments: {e}")
            # Fallback to default devices
            return {
                'timer': "60:09:C3:1F:DC:1A",
                'sensors': ["EA:18:3D:6D:BA:E5", "C2:1B:DB:F0:55:50"]
            }
        
    async def calibration_notification_handler(self, characteristic, data):
        """Handle calibration sample collection"""
        if not self.collecting_calibration:
            return
            
        try:
            if COMPONENTS_AVAILABLE:
                result = parse_5561(data)
                if result and result['samples']:
                    for sample in result['samples']:
                        self.calibration_samples.append(sample)
                        # Progress reporting every 10 samples
                        if len(self.calibration_samples) % 10 == 0:
                            print(f"📊 Collected {len(self.calibration_samples)}/{DEFAULT_CALIBRATION_SAMPLES} samples...")
                        if len(self.calibration_samples) >= DEFAULT_CALIBRATION_SAMPLES:
                            self.collecting_calibration = False
                            break
        except Exception as e:
            self.logger.error(f"Calibration data collection failed: {e}")
            
    async def perform_startup_calibration(self):
        """Perform automatic startup calibration"""
        self.logger.info("🎯 Starting automatic calibration...")
        self.logger.info(f"Calibration: {DEFAULT_CALIBRATION_SAMPLES} samples, auto=True")
        self.logger.info("================================")
        print("🎯 Performing startup calibration...")
        print("📋 Please ensure sensor is STATIONARY during calibration")
        print("⏱️  Collecting samples for baseline establishment...")
        
        # Reset per-sensor calibration state
        self.per_sensor_calibration = {}
        self.sensor_baselines = {}
        self.collecting_calibration = True
        
<<<<<<< HEAD
        # Initialize storage for each connected sensor
        for sensor_mac in BT50_SENSORS:
            self.per_sensor_calibration[sensor_mac] = {
                "samples": [],
                "baseline": {},
                "complete": False,
                "target_samples": self.sensor_target_count
            }
        
        # Start calibration notifications on all sensors
=======
>>>>>>> origin/pi-snapshot-20250920-155656
        try:
            # Enable notifications for all connected BT50 sensors
            for client in self.bt50_clients:
                await client.start_notify(BT50_SENSOR_UUID, self.calibration_notification_handler)
            self.logger.debug(f"Calibration notifications enabled on {len(self.bt50_clients)} sensors")
            
            # Wait for calibration to complete
            start_time = time.time()
            timeout = dev_config.get_calibration_timeout() if COMPONENTS_AVAILABLE else 30
            
            while self.collecting_calibration and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.1)
                if len(self.calibration_samples) >= DEFAULT_CALIBRATION_SAMPLES:
                    break
            
<<<<<<< HEAD
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
=======
            if len(self.calibration_samples) < DEFAULT_CALIBRATION_SAMPLES:
                self.logger.error(f"Calibration timeout - only {len(self.calibration_samples)} samples collected")
                return False
                
            # Calculate baseline using outlier-filtered median (more robust)
            # Use scaled values like TinTown  
            vx_values = [s['vx'] for s in self.calibration_samples]
            vy_values = [s['vy'] for s in self.calibration_samples]
            vz_values = [s['vz'] for s in self.calibration_samples]
            
            # Filter outliers using interquartile range method
            def filter_outliers(values):
                if len(values) < 10:
                    return values
                q1 = statistics.quantiles(values, n=4)[0]
                q3 = statistics.quantiles(values, n=4)[2]
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                return [v for v in values if lower_bound <= v <= upper_bound]
            
            vx_filtered = filter_outliers(vx_values)
            vy_filtered = filter_outliers(vy_values)  
            vz_filtered = filter_outliers(vz_values)
            
            self.baseline_x = statistics.median(vx_filtered) if vx_filtered else statistics.median(vx_values)
            self.baseline_y = statistics.median(vy_filtered) if vy_filtered else statistics.median(vy_values)
            self.baseline_z = statistics.median(vz_filtered) if vz_filtered else statistics.median(vz_values)
            
            # Calculate noise characteristics using filtered values
            noise_x = statistics.stdev(vx_filtered) if len(set(vx_filtered)) > 1 else 0
            noise_y = statistics.stdev(vy_filtered) if len(set(vy_filtered)) > 1 else 0
            noise_z = statistics.stdev(vz_filtered) if len(set(vz_filtered)) > 1 else 0
            
            # Initialize shot detector with calibrated baseline
            if COMPONENTS_AVAILABLE:
                min_dur, max_dur = dev_config.get_shot_duration_range()
>>>>>>> origin/pi-snapshot-20250920-155656
                self.shot_detector = ShotDetector(
                    baseline_x=0,  # Using pre-corrected samples, so baseline is 0
                    threshold=dev_config.get_shot_threshold(),
                    min_duration=min_dur,
                    max_duration=max_dur,
                    min_interval_seconds=dev_config.get_shot_interval()
                )
                self.logger.info("✓ Shot detector initialized with calibrated baseline")
            
            self.calibration_complete = True
            
            # Log calibration results in TinTown format with appropriate precision
            self.logger.info(f"Calibration complete: X={self.baseline_x:.1f}, Y={self.baseline_y:.1f}, Z={self.baseline_z:.1f}")
            self.logger.info("✅ Calibration completed successfully!")
            self.logger.info(f"📊 Baseline established: X={self.baseline_x:.1f}, Y={self.baseline_y:.1f}, Z={self.baseline_z:.1f}")
            self.logger.info(f"📈 Noise levels: X=±{noise_x:.3f}, Y=±{noise_y:.3f}, Z=±{noise_z:.3f}")
            self.logger.info(f"🎯 Impact threshold: 150 counts from baseline")
            
            # Reset enhanced impact detector to clear any residual state
            if self.enhanced_impact_detector:
                self.enhanced_impact_detector.reset()
            
<<<<<<< HEAD
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
            
=======
            # Switch to normal notification handler
            await self.bt50_client.stop_notify(BT50_SENSOR_UUID)
            await self.bt50_client.start_notify(BT50_SENSOR_UUID, self.bt50_notification_handler)
            
            self.logger.info("📝 Status: Sensor 12:E3 - Listening")
            self.logger.info("BT50 sensor and impact notifications enabled")
            self.logger.info("-----------------------------🎯Bridge ready for String🎯-----------------------------")
>>>>>>> origin/pi-snapshot-20250920-155656
            return True
            
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            return False
            
    async def amg_notification_handler(self, characteristic, data):
        """Handle AMG timer notifications"""
        hex_data = data.hex()
<<<<<<< HEAD

        
        # Log raw hex to debug only
=======
>>>>>>> origin/pi-snapshot-20250920-155656
        self.logger.debug(f"AMG notification: {hex_data}")
        
        # Process AMG timer frames (shots, start/stop beeps)
        if len(data) >= 2:
            frame_header = data[0]
            frame_type = data[1]
            
            # Handle START beep (0x0105)
            if frame_header == 0x01 and frame_type == 0x05:
                self.start_beep_time = datetime.now()
                # Extract string number if available
                string_number = data[13] if len(data) >= 14 else self.current_string_number
                self.current_string_number = string_number
                self.logger.info(f"📝 Status: Timer DC:1A - -------Start Beep ------- String #{string_number} at {self.start_beep_time.strftime('%H:%M:%S.%f')[:-3]}")
                
            # Handle SHOT event (0x0103)
            elif frame_header == 0x01 and frame_type == 0x03 and len(data) >= 14:
                shot_time = datetime.now()
                self.shot_counter += 1
                
                # Extract timer data
                time_cs = (data[4] << 8) | data[5]
                split_cs = (data[6] << 8) | data[7]  
                first_cs = (data[8] << 8) | data[9]
                
                timer_split_seconds = split_cs / 100.0
                first_seconds = first_cs / 100.0
                
                # Calculate split time from previous shot
                shot_split_seconds = 0.0
                if hasattr(self, 'previous_shot_time') and self.previous_shot_time:
                    shot_split_seconds = (shot_time - self.previous_shot_time).total_seconds()
                
                self.logger.info(f"🔫 String {self.current_string_number}, Shot #{self.shot_counter} - Time {timer_split_seconds:.2f}s, Split {shot_split_seconds:.2f}s, First {first_seconds:.2f}s")
                
                self.previous_shot_time = shot_time
                
                # Record shot for timing correlation
                if self.timing_calibrator:
                    self.timing_calibrator.record_shot(shot_time, self.shot_counter, self.current_string_number)
                    
            # Handle STOP beep (0x0108)
            elif frame_header == 0x01 and frame_type == 0x08:
                reception_timestamp = datetime.now()
                
                # Extract string data
                if len(data) >= 14:
                    string_number = data[13]
                    time_cs = (data[4] << 8) | data[5]
                    timer_seconds = time_cs / 100.0
                else:
                    string_number = self.current_string_number
                    timer_seconds = 0
                    
                # Calculate total info
                total_info = ""
                if self.start_beep_time:
                    total_ms = (reception_timestamp - self.start_beep_time).total_seconds() * 1000
                    total_info = f" (total: {timer_seconds:.2f}s)"
                    
                self.logger.info(f"� Status: Timer DC:1A - Stop Beep for String #{string_number} at {reception_timestamp.strftime('%H:%M:%S.%f')[:-3]}{total_info}")
                
                # Reset for next string  
                self.start_beep_time = None
                self.impact_counter = 0
                self.shot_counter = 0
                self.previous_shot_time = None
<<<<<<< HEAD
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
=======
                
    async def bt50_notification_handler(self, characteristic, data):
        """Handle BT50 sensor notifications with impact detection"""
        if not COMPONENTS_AVAILABLE or not self.calibration_complete:
>>>>>>> origin/pi-snapshot-20250920-155656
            return
            
        try:
            # Persist verbose parsed frames for offline analysis if sample logging
            # is enabled (this writes to logs/bt50_samples.db)
            try:
                write_db = False
                if hasattr(self, 'dev_config') and self.dev_config:
                    # dev_config may expose a sample logging toggle
                    if hasattr(self.dev_config, 'is_sample_logging_enabled'):
                        write_db = self.dev_config.is_sample_logging_enabled()
                    elif hasattr(self.dev_config, 'should_log_all_samples'):
                        write_db = self.dev_config.should_log_all_samples()

                # scan_and_parse is non-blocking and quick; it will write rows when
                # enabled. Wrap in its own try to avoid breaking detection on DB errors.
                try:
                    scan_and_parse(data, write_db=write_db)
                except Exception as e:
                    self.logger.debug(f"Verbose parser DB write failed: {e}")
            except Exception:
                # If verbose parser not available, ignore and continue
                pass

            # Parse sensor data using the simple parser (returns scaled vx/vy/vz)
            result = parse_5561(data)
            if not result or not result['samples']:
                return
            
            # Apply baseline correction to samples using scaled values like TinTown
            corrected_samples = []
            for sample in result['samples']:
                corrected_sample = sample.copy()
                corrected_sample['vx_corrected'] = sample['vx'] - self.baseline_x
                corrected_sample['vy_corrected'] = sample['vy'] - self.baseline_y  
                corrected_sample['vz_corrected'] = sample['vz'] - self.baseline_z
                corrected_samples.append(corrected_sample)
                
            # Process samples for shot detection
            if self.shot_detector:
                detected_shots = self.shot_detector.process_samples(corrected_samples)
                
                for shot in detected_shots:
                    self.impact_counter += 1
                    
<<<<<<< HEAD
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
=======
                    # Calculate time from string start
                    time_from_start = 0.0
                    if self.start_beep_time:
                        time_from_start = (shot.timestamp - self.start_beep_time).total_seconds()
                    
                    # Calculate time from last shot
                    time_from_shot = 0.0
                    if self.previous_shot_time:
                        time_from_shot = (shot.timestamp - self.previous_shot_time).total_seconds()
                    
                    self.logger.info(f"💥 String {self.current_string_number}, Impact #{self.impact_counter} - Time {time_from_start:.2f}s, Shot->Impact {time_from_shot:.3f}s, Peak {shot.peak_magnitude:.0f}g")
>>>>>>> origin/pi-snapshot-20250920-155656
                    
                    # Record impact for timing correlation
                    if self.timing_calibrator:
                        self.timing_calibrator.record_impact(shot.timestamp, shot.peak_magnitude)
            
            # Enhanced impact detection (if enabled)
            if self.enhanced_impact_detector:
                enhanced_impacts = self.enhanced_impact_detector.process_samples(
                    corrected_samples, 0  # baseline_x = 0 since we already corrected
                )
                
                for impact in enhanced_impacts:
                    # Calculate time from string start
                    time_from_start = 0.0
                    if self.start_beep_time:
                        time_from_start = (impact.onset_timestamp - self.start_beep_time).total_seconds()
                    
                    # Calculate time from last shot
                    time_from_shot = 0.0
                    if self.previous_shot_time:
                        time_from_shot = (impact.onset_timestamp - self.previous_shot_time).total_seconds()
                    
                    impact_number = getattr(self, 'enhanced_impact_counter', 0) + 1
                    setattr(self, 'enhanced_impact_counter', impact_number)
                    
                    self.logger.info(f"💥 String {self.current_string_number}, Enhanced Impact #{impact_number} - Time {time_from_start:.2f}s, Shot->Impact {time_from_shot:.3f}s, Peak {impact.peak_magnitude:.0f}g")
                    
        except Exception as e:
<<<<<<< HEAD
            self.logger.debug(f"BT50 parsing failed: {e}")

=======
            self.logger.error(f"BT50 processing failed: {e}")
            
>>>>>>> origin/pi-snapshot-20250920-155656
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
    
    async def connect_devices(self):
        """Connect to Bridge-assigned AMG timer and BT50 sensors"""
        # Perform automatic BLE reset first
        await self.reset_ble()
        
        self.logger.info("📝 Status: Bridge MCU1 - Bridge Initialized")
        
<<<<<<< HEAD
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
=======
        # Get Bridge-assigned devices
        assigned_devices = self.get_bridge_assigned_devices()
        timer_mac = assigned_devices.get('timer')
        sensor_macs = assigned_devices.get('sensors', [])
>>>>>>> origin/pi-snapshot-20250920-155656
        
        # Connect AMG Timer if assigned
        if timer_mac:
            try:
                self.logger.info(f"Connecting to assigned timer: {timer_mac}")
                self.amg_client = BleakClient(timer_mac)
                await self.amg_client.connect()
                await self.amg_client.start_notify(AMG_TIMER_UUID, self.amg_notification_handler)
                self.logger.info(f"📝 Status: Timer {timer_mac[-5:]} - Connected")
                self.logger.info("AMG timer and shot notifications enabled")
                
            except Exception as e:
                self.logger.error(f"AMG timer connection failed: {e}")
        else:
            self.logger.warning("No timer assigned to this Bridge")
            
        # Connect BT50 Sensors if assigned
        if sensor_macs:
            # For now, connect to the first assigned sensor (can be expanded for multiple sensors)
            primary_sensor_mac = sensor_macs[0]
            try:
                self.logger.info(f"Connecting to assigned BT50 sensor: {primary_sensor_mac}")
                self.bt50_client = BleakClient(primary_sensor_mac)
                await self.bt50_client.connect()
                self.logger.info(f"📝 Status: Sensor {primary_sensor_mac[-5:]} - Connected")
                
                # Perform calibration
                await asyncio.sleep(1.0)  # Let connection stabilize
                calibration_success = await self.perform_startup_calibration()
                
                if not calibration_success:
                    self.logger.error("❌ Calibration failed - bridge not ready")
                    
            except Exception as e:
                self.logger.error(f"BT50 sensor connection failed: {e}")
        else:
            self.logger.warning("No BT50 sensors assigned to this Bridge")
            
    async def cleanup(self):
        """Clean up connections and save data"""
        self.logger.info("Cleaning up connections...")
        
        # Save calibration data
        if self.timing_calibrator:
            self.timing_calibrator.save_calibration()
            
        if self.statistical_calibrator:
            self.statistical_calibrator.save_data()
            
        # Log shot detection statistics
        if self.shot_detector:
            stats = self.shot_detector.get_stats()
            self.logger.info(f"Shot detection summary: {stats['total_shots']} shots detected "
                           f"from {stats['total_samples']} samples ({stats.get('shots_per_minute', 0):.1f}/min)")
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
            
        # Disconnect devices
        if self.amg_client and self.amg_client.is_connected:
            await self.amg_client.disconnect()
            
        if self.bt50_client and self.bt50_client.is_connected:
            await self.bt50_client.disconnect()
            
        self.logger.info("Cleanup complete")
        
    async def run(self):
        """Main run loop"""
        self.running = True
        
        # Startup message
        self.logger.info("🎯 TinTown Bridge v2.0 - Starting...")
        self.logger.info(f"📋 Complete console log: {console_log_path}")
        self.logger.info("💡 Use 'tail -f' on this log file to see ALL events including AMG beeps")
        
        try:
            await self.connect_devices()
            
            if COMPONENTS_AVAILABLE and self.calibration_complete:
                print("\n=== AUTOMATIC CALIBRATION BRIDGE WITH SHOT DETECTION ===")
                print("✨ Dynamic baseline calibration - establishes fresh zero on every startup")
                print("🎯 Shot Detection: 150 count threshold, 6-11 sample duration, 1s interval")
                print(f"📊 Current baseline: X={self.baseline_x}, Y={self.baseline_y}, Z={self.baseline_z} (auto-calibrated)")
                print(f"⚡ Impact threshold: {DEFAULT_IMPACT_THRESHOLD} counts from dynamic baseline")
                print("🔄 Baseline automatically corrects for any sensor orientation")
                print("Press CTRL+C to stop\n")
            
            # Main operation loop
            while self.running:
                await asyncio.sleep(1.0)
                
        except KeyboardInterrupt:
            print("\nStopping LeadVille Bridge...")
            self.running = False
        except Exception as e:
            self.logger.error(f"Bridge error: {e}")
            self.running = False
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    bridge = LeadVilleBridge()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())