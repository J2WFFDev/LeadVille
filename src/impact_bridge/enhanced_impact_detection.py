"""
Enhanced Impact Detection with Onset Timing

Advanced impact detection that identifies the precise onset of impact events
using dual threshold analysis and lookback processing.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class ImpactEvent:
    """Represents a detected impact with onset timing"""
    onset_timestamp: datetime
    peak_timestamp: datetime
    peak_magnitude: float
    onset_magnitude: float
    duration_samples: int
    onset_sample_index: int


class EnhancedImpactDetector:
    """
    Enhanced impact detection with precise onset timing detection
    """
    
    def __init__(self, 
                 threshold: float = 150.0,
                 onset_threshold: float = 30.0,
                 lookback_samples: int = 10):
        """
        Initialize enhanced impact detector
        
        Args:
            threshold: Primary detection threshold (peak detection)
            onset_threshold: Secondary threshold for onset detection
            lookback_samples: Number of samples to look back for onset
        """
        self.threshold = threshold
        self.onset_threshold = onset_threshold
        self.lookback_samples = lookback_samples
        
        # Detection state
        self.sample_buffer = []
        self.detection_active = False
        self.current_detection_start = 0
        
        # Statistics
        self.total_impacts = 0
        self.total_samples_processed = 0
        
        logger.info(f"Enhanced impact detector initialized: "
                   f"threshold={threshold}, onset={onset_threshold}, "
                   f"lookback={lookback_samples}")
    
    def process_samples(self, samples: List[Dict], baseline_x: int = 0) -> List[ImpactEvent]:
        """
        Process samples for enhanced impact detection
        
        Args:
            samples: List of sensor samples
            baseline_x: Baseline value for deviation calculation
            
        Returns:
            List of detected impact events
        """
        impacts = []
        
        for sample in samples:
            self.total_samples_processed += 1
            
            # Add sample to buffer
            sample_with_deviation = sample.copy()
            sample_with_deviation['deviation'] = abs(sample['vx_raw'] - baseline_x)
            sample_with_deviation['sample_index'] = self.total_samples_processed
            
            self.sample_buffer.append(sample_with_deviation)
            
            # Maintain buffer size
            max_buffer_size = self.lookback_samples + 20  # Extra room for detection
            if len(self.sample_buffer) > max_buffer_size:
                self.sample_buffer.pop(0)
            
            # Check for impact
            impact = self._check_for_impact()
            if impact:
                impacts.append(impact)
        
        return impacts
    
    def _check_for_impact(self) -> Optional[ImpactEvent]:
        """Check current sample buffer for impact events"""
        if len(self.sample_buffer) < 2:
            return None
            
        current_sample = self.sample_buffer[-1]
        current_deviation = current_sample['deviation']
        
        # Primary threshold detection
        if current_deviation >= self.threshold and not self.detection_active:
            # Impact detected - now find the onset
            return self._analyze_impact_onset()
        
        return None
    
    def _analyze_impact_onset(self) -> Optional[ImpactEvent]:
        """Analyze the sample buffer to find precise impact onset"""
        try:
            # Find the peak (current sample should be the peak or close to it)
            peak_index = len(self.sample_buffer) - 1
            peak_sample = self.sample_buffer[peak_index]
            peak_magnitude = peak_sample['deviation']
            
            # Look back to find onset
            onset_index = self._find_onset_index(peak_index)
            
            if onset_index is None:
                logger.debug("Could not find onset for impact")
                return None
            
            onset_sample = self.sample_buffer[onset_index]
            onset_magnitude = onset_sample['deviation']
            
            # Create impact event
            self.total_impacts += 1
            
            impact = ImpactEvent(
                onset_timestamp=datetime.now(timezone.utc),  # Could be more precise with sample timing
                peak_timestamp=datetime.now(timezone.utc),
                peak_magnitude=peak_magnitude,
                onset_magnitude=onset_magnitude,
                duration_samples=peak_index - onset_index + 1,
                onset_sample_index=onset_sample['sample_index']
            )
            
            logger.info(f"Enhanced impact #{self.total_impacts}: "
                       f"onset={onset_magnitude:.1f}, peak={peak_magnitude:.1f}, "
                       f"duration={impact.duration_samples}")
            
            # Prevent immediate re-detection
            self.detection_active = True
            
            # Clear buffer to prevent re-detection
            self.sample_buffer = self.sample_buffer[-5:]  # Keep only recent samples
            self.detection_active = False
            
            return impact
            
        except Exception as e:
            logger.error(f"Impact onset analysis failed: {e}")
            return None
    
    def _find_onset_index(self, peak_index: int) -> Optional[int]:
        """
        Find the onset index by looking back from peak
        
        Args:
            peak_index: Index of the peak sample in buffer
            
        Returns:
            Index of onset sample or None if not found
        """
        # Start looking back from peak
        lookback_start = max(0, peak_index - self.lookback_samples)
        
        # Find where signal first crosses onset threshold
        for i in range(peak_index - 1, lookback_start - 1, -1):
            if i >= 0 and i < len(self.sample_buffer):
                if self.sample_buffer[i]['deviation'] < self.onset_threshold:
                    # Found where signal drops below onset threshold
                    # The onset is the next sample (first to cross threshold)
                    onset_idx = min(i + 1, peak_index)
                    return onset_idx
        
        # If no clear onset found, use the start of lookback window
        return lookback_start
    
    def get_stats(self) -> Dict:
        """Get detection statistics"""
        return {
            'total_impacts': self.total_impacts,
            'total_samples': self.total_samples_processed,
            'threshold': self.threshold,
            'onset_threshold': self.onset_threshold,
            'lookback_samples': self.lookback_samples,
            'buffer_size': len(self.sample_buffer)
        }
    
    def reset(self):
        """Reset detector state"""
        self.sample_buffer = []
        self.detection_active = False
        self.total_impacts = 0
        self.total_samples_processed = 0
        logger.info("Enhanced impact detector reset")
    
    def is_enabled(self) -> bool:
        """Check if enhanced detection is enabled"""
        return True  # Always enabled in this implementation
    
    def configure_thresholds(self, threshold: float, onset_threshold: float):
        """Update detection thresholds"""
        self.threshold = threshold
        self.onset_threshold = onset_threshold
        logger.info(f"Thresholds updated: threshold={threshold}, onset={onset_threshold}")