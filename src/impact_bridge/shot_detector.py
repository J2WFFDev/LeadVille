"""
Shot Detection System

Advanced shot detection with configurable thresholds, duration validation,
and interval enforcement for BT50 sensor data.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class DetectedShot:
    """Represents a detected shot event"""
    timestamp: datetime
    peak_magnitude: float
    duration_samples: int
    baseline_deviation: float
    sample_data: List[Dict]


class ShotDetector:
    """
    Advanced shot detection with baseline calibration and validation
    """
    
    def __init__(self, 
                 baseline_x: int = 0,
                 threshold: float = 150.0,
                 min_duration: int = 6,
                 max_duration: int = 11, 
                 min_interval_seconds: float = 1.0):
        """
        Initialize shot detector
        
        Args:
            baseline_x: Calibrated baseline for X-axis
            threshold: Minimum change from baseline to detect shot
            min_duration: Minimum samples for valid shot
            max_duration: Maximum samples for valid shot
            min_interval_seconds: Minimum time between shots
        """
        self.baseline_x = baseline_x
        self.threshold = threshold
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.min_interval_seconds = min_interval_seconds
        
        # Detection state
        self.last_shot_time = 0
        self.detection_active = False
        self.current_detection = []
        
        # Statistics
        self.total_samples = 0
        self.total_shots = 0
        self.recent_shots = []
        self.start_time = time.time()
        
        logger.info(f"Shot detector initialized: threshold={threshold}, "
                   f"duration={min_duration}-{max_duration}, interval={min_interval_seconds}s")
    
    def process_samples(self, samples: List[Dict]) -> List[DetectedShot]:
        """
        Process sensor samples and detect shots
        
        Args:
            samples: List of parsed sensor samples
            
        Returns:
            List of detected shots (usually 0 or 1)
        """
        detected_shots = []
        
        for sample in samples:
            self.total_samples += 1
            shot = self._process_single_sample(sample)
            if shot:
                detected_shots.append(shot)
                
        return detected_shots
    
    def _process_single_sample(self, sample: Dict) -> Optional[DetectedShot]:
        """Process a single sample for shot detection"""
        current_time = time.time()
        
        # Calculate deviation from baseline
        vx_raw = sample['vx_raw']
        deviation = abs(vx_raw - self.baseline_x)
        
        # Check if sample exceeds threshold
        exceeds_threshold = deviation >= self.threshold
        
        # State machine for detection
        if exceeds_threshold and not self.detection_active:
            # Start new detection if enough time has passed
            if current_time - self.last_shot_time >= self.min_interval_seconds:
                self.detection_active = True
                self.current_detection = [sample]
                logger.debug(f"Shot detection started: deviation={deviation}")
            else:
                logger.debug(f"Shot ignored due to interval: {current_time - self.last_shot_time:.3f}s")
                
        elif self.detection_active:
            self.current_detection.append(sample)
            
            # Check if we should end detection
            if not exceeds_threshold or len(self.current_detection) >= self.max_duration:
                return self._finalize_detection(current_time)
                
        return None
    
    def _finalize_detection(self, current_time: float) -> Optional[DetectedShot]:
        """Finalize current detection and determine if it's a valid shot"""
        try:
            duration = len(self.current_detection)
            
            # Validate duration
            if duration < self.min_duration:
                logger.debug(f"Shot rejected: too short ({duration} samples)")
                self.detection_active = False
                return None
            
            # Calculate shot characteristics
            peak_magnitude = 0
            total_deviation = 0
            
            for sample in self.current_detection:
                deviation = abs(sample['vx_raw'] - self.baseline_x)
                peak_magnitude = max(peak_magnitude, deviation)
                total_deviation += deviation
                
            avg_deviation = total_deviation / duration
            
            # Create detected shot
            shot = DetectedShot(
                timestamp=datetime.now(timezone.utc),
                peak_magnitude=peak_magnitude,
                duration_samples=duration,
                baseline_deviation=avg_deviation,
                sample_data=self.current_detection.copy()
            )
            
            # Update statistics
            self.total_shots += 1
            self.last_shot_time = current_time
            self.recent_shots.append(shot)
            
            # Keep only recent shots (last 10)
            if len(self.recent_shots) > 10:
                self.recent_shots.pop(0)
            
            logger.info(f"Shot #{self.total_shots} detected: "
                       f"peak={peak_magnitude:.1f}, duration={duration}, avg_dev={avg_deviation:.1f}")
            
            return shot
            
        finally:
            self.detection_active = False
            self.current_detection = []
    
    def get_stats(self) -> Dict:
        """Get detection statistics"""
        runtime = time.time() - self.start_time
        shots_per_minute = (self.total_shots / runtime * 60) if runtime > 0 else 0
        
        return {
            'total_shots': self.total_shots,
            'total_samples': self.total_samples,
            'runtime_seconds': runtime,
            'shots_per_minute': shots_per_minute,
            'baseline_x': self.baseline_x,
            'threshold': self.threshold
        }
    
    def get_recent_shots(self) -> List[DetectedShot]:
        """Get list of recently detected shots"""
        return self.recent_shots.copy()
    
    def reset_statistics(self):
        """Reset all statistics and recent shots"""
        self.total_samples = 0
        self.total_shots = 0
        self.recent_shots = []
        self.start_time = time.time()
        logger.info("Shot detector statistics reset")