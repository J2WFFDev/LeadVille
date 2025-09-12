#!/usr/bin/env python3
"""
LeadVille Impact Bridge - Production BLE-based Impact Sensor System

A clean, production-ready implementation of the BT50 sensor bridge with AMG timer integration.
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
    from impact_bridge.wtvb_parse import parse_5561
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

# Device Configuration
AMG_TIMER_MAC = "60:09:C3:1F:DC:1A"
BT50_SENSOR_MAC = "F8:FE:92:31:12:E3"

# BLE UUIDs
AMG_TIMER_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
BT50_SENSOR_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"

# Default configuration values
DEFAULT_IMPACT_THRESHOLD = 150  # Raw counts for impact detection
DEFAULT_CALIBRATION_SAMPLES = 100  # Samples for baseline calibration


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
                        if len(self.calibration_samples) >= DEFAULT_CALIBRATION_SAMPLES:
                            self.collecting_calibration = False
                            break
        except Exception as e:
            self.logger.error(f"Calibration data collection failed: {e}")
            
    async def perform_startup_calibration(self):
        """Perform automatic startup calibration"""
        self.logger.info("🎯 Starting automatic calibration...")
        print("🎯 Performing startup calibration...")
        print("📋 Please ensure sensor is STATIONARY during calibration")
        print("⏱️  Collecting samples for baseline establishment...")
        
        # Reset calibration state
        self.calibration_samples = []
        self.collecting_calibration = True
        
        try:
            await self.bt50_client.start_notify(BT50_SENSOR_UUID, self.calibration_notification_handler)
            
            # Wait for calibration to complete
            start_time = time.time()
            timeout = dev_config.get_calibration_timeout() if COMPONENTS_AVAILABLE else 30
            
            while self.collecting_calibration and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.1)
                if len(self.calibration_samples) >= DEFAULT_CALIBRATION_SAMPLES:
                    break
            
            if len(self.calibration_samples) < DEFAULT_CALIBRATION_SAMPLES:
                self.logger.error(f"Calibration timeout - only {len(self.calibration_samples)} samples collected")
                return False
                
            # Calculate baseline averages
            vx_values = [s['vx_raw'] for s in self.calibration_samples]
            vy_values = [s['vy_raw'] for s in self.calibration_samples]
            vz_values = [s['vz_raw'] for s in self.calibration_samples]
            
            self.baseline_x = int(sum(vx_values) / len(vx_values))
            self.baseline_y = int(sum(vy_values) / len(vy_values))
            self.baseline_z = int(sum(vz_values) / len(vz_values))
            
            # Calculate noise characteristics
            noise_x = statistics.stdev(vx_values) if len(set(vx_values)) > 1 else 0
            noise_y = statistics.stdev(vy_values) if len(set(vy_values)) > 1 else 0
            noise_z = statistics.stdev(vz_values) if len(set(vz_values)) > 1 else 0
            
            # Initialize shot detector with calibrated baseline
            if COMPONENTS_AVAILABLE:
                min_dur, max_dur = dev_config.get_shot_duration_range()
                self.shot_detector = ShotDetector(
                    baseline_x=self.baseline_x,
                    threshold=dev_config.get_shot_threshold(),
                    min_duration=min_dur,
                    max_duration=max_dur,
                    min_interval_seconds=dev_config.get_shot_interval()
                )
                self.logger.info("✓ Shot detector initialized with calibrated baseline")
            
            self.calibration_complete = True
            
            # Log calibration results
            self.logger.info("✅ Calibration completed successfully!")
            self.logger.info(f"📊 Baseline: X={self.baseline_x}, Y={self.baseline_y}, Z={self.baseline_z}")
            self.logger.info(f"📈 Noise levels: X=±{noise_x:.1f}, Y=±{noise_y:.1f}, Z=±{noise_z:.1f}")
            
            # Switch to normal notification handler
            await self.bt50_client.stop_notify(BT50_SENSOR_UUID)
            await self.bt50_client.start_notify(BT50_SENSOR_UUID, self.bt50_notification_handler)
            
            self.logger.info("📝 Status: Sensor 12:E3 - Listening")
            self.logger.info("BT50 sensor and impact notifications enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            return False
            
    async def amg_notification_handler(self, characteristic, data):
        """Handle AMG timer notifications"""
        hex_data = data.hex()
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
                
    async def bt50_notification_handler(self, characteristic, data):
        """Handle BT50 sensor notifications with impact detection"""
        if not COMPONENTS_AVAILABLE or not self.calibration_complete:
            return
            
        try:
            # Parse sensor data
            result = parse_5561(data)
            if not result or not result['samples']:
                return
                
            # Process samples for shot detection
            if self.shot_detector:
                detected_shots = self.shot_detector.process_samples(result['samples'])
                
                for shot in detected_shots:
                    self.impact_counter += 1
                    
                    # Calculate time from string start
                    time_from_start = 0.0
                    if self.start_beep_time:
                        time_from_start = (shot.timestamp - self.start_beep_time).total_seconds()
                    
                    # Calculate time from last shot
                    time_from_shot = 0.0
                    if self.previous_shot_time:
                        time_from_shot = (shot.timestamp - self.previous_shot_time).total_seconds()
                    
                    self.logger.info(f"💥 String {self.current_string_number}, Impact #{self.impact_counter} - Time {time_from_start:.2f}s, Shot->Impact {time_from_shot:.3f}s, Peak {shot.peak_magnitude:.0f}g")
                    
                    # Record impact for timing correlation
                    if self.timing_calibrator:
                        self.timing_calibrator.record_impact(shot.timestamp, shot.peak_magnitude)
            
            # Enhanced impact detection (if enabled)
            if self.enhanced_impact_detector:
                enhanced_impacts = self.enhanced_impact_detector.process_samples(
                    result['samples'], self.baseline_x
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
            self.logger.error(f"BT50 processing failed: {e}")
            
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
        """Connect to both AMG timer and BT50 sensor"""
        # Perform automatic BLE reset first
        await self.reset_ble()
        
        self.logger.info("📝 Status: Bridge MCU1 - Bridge Initialized")
        
        try:
            # Connect AMG Timer
            self.logger.info("Connecting to AMG timer...")
            self.amg_client = BleakClient(AMG_TIMER_MAC)
            await self.amg_client.connect()
            await self.amg_client.start_notify(AMG_TIMER_UUID, self.amg_notification_handler)
            self.logger.info("📝 Status: Timer DC:1A - Connected")
            self.logger.info("AMG timer and shot notifications enabled")
            
        except Exception as e:
            self.logger.error(f"AMG timer connection failed: {e}")
            
        try:
            # Connect BT50 Sensor
            self.logger.info("Connecting to BT50 sensor...")
            self.bt50_client = BleakClient(BT50_SENSOR_MAC)
            await self.bt50_client.connect()
            self.logger.info("📝 Status: Sensor 12:E3 - Connected")
            
            # Perform calibration
            await asyncio.sleep(1.0)  # Let connection stabilize
            calibration_success = await self.perform_startup_calibration()
            
            if calibration_success:
                # Final ready status - only if both devices connected successfully
                if (self.amg_client and self.amg_client.is_connected and 
                    self.bt50_client and self.bt50_client.is_connected and
                    self.calibration_complete):
                    self.logger.info("-----------------------------🎯Bridge ready for String🎯-----------------------------")
            else:
                self.logger.error("❌ Calibration failed - bridge not ready")
                
        except Exception as e:
            self.logger.error(f"BT50 sensor connection failed: {e}")
            
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