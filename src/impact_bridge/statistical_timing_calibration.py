"""
Statistical Timing Calibration Module

Provides statistical analysis and calibration for timing correlation between
AMG timer events and BT50 sensor impacts.
"""

import json
import logging
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StatisticalTimingCalibrator:
    """
    Statistical analysis for timing calibration
    """
    
    def __init__(self, data_file: Optional[Path] = None):
        """
        Initialize statistical calibrator
        
        Args:
            data_file: Optional file to load/save statistical data
        """
        self.data_file = data_file or Path("statistical_timing_data.json")
        
        # Statistical data
        self.timing_samples = []
        self.correlation_history = []
        
        # Configuration
        self.max_samples = 1000  # Keep last 1000 samples
        self.outlier_threshold = 2.0  # Standard deviations for outlier detection
        
        # Load existing data
        self._load_data()
        
        logger.info(f"Statistical timing calibrator initialized")
    
    def add_timing_sample(self, delay_ms: float, confidence: float = 1.0):
        """
        Add a timing sample for statistical analysis
        
        Args:
            delay_ms: Measured delay between shot and impact
            confidence: Confidence score for this measurement (0.0-1.0)
        """
        sample = {
            'delay_ms': delay_ms,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        self.timing_samples.append(sample)
        
        # Maintain sample limit
        if len(self.timing_samples) > self.max_samples:
            self.timing_samples.pop(0)
        
        logger.debug(f"Added timing sample: {delay_ms:.1f}ms (confidence: {confidence:.2f})")
    
    def get_calibrated_delay(self) -> Tuple[float, float]:
        """
        Get statistically calibrated delay and confidence
        
        Returns:
            Tuple of (calibrated_delay_ms, confidence_score)
        """
        if len(self.timing_samples) < 3:
            return 526.0, 0.0  # Default delay, no confidence
        
        # Filter out outliers and low-confidence samples
        filtered_samples = self._filter_samples()
        
        if len(filtered_samples) < 2:
            return 526.0, 0.1  # Default delay, low confidence
        
        # Calculate weighted average
        delays = [s['delay_ms'] for s in filtered_samples]
        weights = [s['confidence'] for s in filtered_samples]
        
        weighted_avg = sum(d * w for d, w in zip(delays, weights)) / sum(weights)
        
        # Calculate confidence based on sample consistency
        std_dev = statistics.stdev(delays) if len(delays) > 1 else 0
        consistency = max(0.0, 1.0 - (std_dev / 100.0))  # Lower std dev = higher consistency
        sample_confidence = min(1.0, len(filtered_samples) / 20.0)  # More samples = higher confidence
        
        overall_confidence = (consistency * 0.7 + sample_confidence * 0.3)
        
        return weighted_avg, overall_confidence
    
    def _filter_samples(self) -> List[Dict]:
        """Filter samples to remove outliers and low-confidence data"""
        if len(self.timing_samples) < 3:
            return self.timing_samples
        
        # Calculate basic statistics
        delays = [s['delay_ms'] for s in self.timing_samples]
        mean_delay = statistics.mean(delays)
        std_delay = statistics.stdev(delays) if len(delays) > 1 else 0
        
        # Filter outliers and low confidence
        filtered = []
        for sample in self.timing_samples:
            # Check for outliers
            z_score = abs(sample['delay_ms'] - mean_delay) / max(std_delay, 1.0)
            
            # Keep samples that are not outliers and have reasonable confidence
            if (z_score <= self.outlier_threshold and 
                sample['confidence'] >= 0.3 and 
                100 <= sample['delay_ms'] <= 2000):  # Reasonable delay range
                filtered.append(sample)
        
        return filtered
    
    def get_statistics(self) -> Dict:
        """Get comprehensive timing statistics"""
        if not self.timing_samples:
            return {
                'total_samples': 0,
                'filtered_samples': 0,
                'mean_delay_ms': 0.0,
                'std_dev_ms': 0.0,
                'confidence': 0.0,
                'calibrated_delay_ms': 526.0
            }
        
        filtered = self._filter_samples()
        delays = [s['delay_ms'] for s in filtered]
        
        calibrated_delay, confidence = self.get_calibrated_delay()
        
        stats = {
            'total_samples': len(self.timing_samples),
            'filtered_samples': len(filtered),
            'mean_delay_ms': statistics.mean(delays) if delays else 0.0,
            'std_dev_ms': statistics.stdev(delays) if len(delays) > 1 else 0.0,
            'confidence': confidence,
            'calibrated_delay_ms': calibrated_delay
        }
        
        if delays:
            stats['min_delay_ms'] = min(delays)
            stats['max_delay_ms'] = max(delays)
            stats['median_delay_ms'] = statistics.median(delays)
        
        return stats
    
    def _load_data(self):
        """Load statistical data from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.timing_samples = data.get('timing_samples', [])
                    logger.info(f"Loaded {len(self.timing_samples)} timing samples")
        except Exception as e:
            logger.warning(f"Could not load statistical data: {e}")
    
    def save_data(self):
        """Save statistical data to file"""
        try:
            data = {
                'timing_samples': self.timing_samples,
                'last_updated': datetime.now().isoformat(),
                'statistics': self.get_statistics()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved statistical data: {len(self.timing_samples)} samples")
            
        except Exception as e:
            logger.error(f"Could not save statistical data: {e}")
    
    def reset_data(self):
        """Reset all statistical data"""
        self.timing_samples = []
        self.correlation_history = []
        logger.info("Statistical data reset")


# Global instance for easy access
statistical_calibrator = StatisticalTimingCalibrator()