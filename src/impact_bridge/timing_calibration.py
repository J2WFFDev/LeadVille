"""
Real-Time Timing Calibration System

Correlates AMG timer shots with BT50 sensor impacts to maintain accurate timing.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class TimingPair:
    """Represents a correlated shot-impact timing pair"""
    shot_timestamp: datetime
    impact_timestamp: datetime
    delay_ms: float
    shot_number: int
    string_number: int


class RealTimeTimingCalibrator:
    """
    Real-time timing calibration between AMG timer and BT50 sensor
    """
    
    def __init__(self, calibration_file: Path, expected_delay_ms: float = 526.0):
        """
        Initialize timing calibrator
        
        Args:
            calibration_file: Path to save/load calibration data
            expected_delay_ms: Expected delay between shot and impact
        """
        self.calibration_file = calibration_file
        self.expected_delay_ms = expected_delay_ms
        
        # Correlation tracking
        self.pending_shots = []  # Shots waiting for impact correlation
        self.pending_impacts = []  # Impacts waiting for shot correlation
        self.correlated_pairs = []
        
        # Configuration
        self.max_correlation_window_ms = 2000  # 2 second window
        self.max_pending_items = 50  # Prevent memory buildup
        
        # Statistics
        self.total_correlations = 0
        self.successful_correlations = 0
        
        # Load existing calibration
        self._load_calibration()
        
        # Suppress automatic logging - manual message in main bridge
    
    def record_shot(self, timestamp: datetime, shot_number: int, string_number: int):
        """Record a shot event for correlation"""
        shot_event = {
            'timestamp': timestamp,
            'shot_number': shot_number,
            'string_number': string_number,
            'recorded_at': time.time()
        }
        
        self.pending_shots.append(shot_event)
        self._cleanup_pending()
        
        # Try to correlate with existing impacts
        self._attempt_correlation()
        
        logger.debug(f"Shot recorded: #{shot_number} string {string_number}")
    
    def record_impact(self, timestamp: datetime, magnitude: float):
        """Record an impact event for correlation"""
        impact_event = {
            'timestamp': timestamp,
            'magnitude': magnitude,
            'recorded_at': time.time()
        }
        
        self.pending_impacts.append(impact_event)
        self._cleanup_pending()
        
        # Try to correlate with existing shots
        self._attempt_correlation()
        
        logger.debug(f"Impact recorded: magnitude={magnitude:.1f}")
    
    def _attempt_correlation(self):
        """Attempt to correlate pending shots and impacts"""
        correlated_shots = []
        correlated_impacts = []
        
        for shot in self.pending_shots:
            best_match = None
            best_delay = float('inf')
            
            for impact in self.pending_impacts:
                # Calculate delay (impact should come after shot)
                delay_ms = (impact['timestamp'] - shot['timestamp']).total_seconds() * 1000
                
                # Check if delay is reasonable
                if 0 <= delay_ms <= self.max_correlation_window_ms:
                    # Prefer delays close to expected
                    delay_error = abs(delay_ms - self.expected_delay_ms)
                    if delay_error < abs(best_delay - self.expected_delay_ms):
                        best_match = impact
                        best_delay = delay_ms
            
            # If we found a good match, correlate them
            if best_match and abs(best_delay - self.expected_delay_ms) < 1000:  # Within 1 second
                pair = TimingPair(
                    shot_timestamp=shot['timestamp'],
                    impact_timestamp=best_match['timestamp'],
                    delay_ms=best_delay,
                    shot_number=shot['shot_number'],
                    string_number=shot['string_number']
                )
                
                self.correlated_pairs.append(pair)
                correlated_shots.append(shot)
                correlated_impacts.append(best_match)
                
                self.total_correlations += 1
                self.successful_correlations += 1
                
                logger.info(f"Timing correlation: Shot #{shot['shot_number']} -> "
                           f"Impact (delay={best_delay:.1f}ms)")
        
        # Remove correlated items from pending lists
        for shot in correlated_shots:
            self.pending_shots.remove(shot)
        for impact in correlated_impacts:
            self.pending_impacts.remove(impact)
    
    def _cleanup_pending(self):
        """Remove old pending items to prevent memory buildup"""
        current_time = time.time()
        timeout_seconds = self.max_correlation_window_ms / 1000
        
        # Remove old shots
        self.pending_shots = [
            shot for shot in self.pending_shots
            if current_time - shot['recorded_at'] < timeout_seconds
        ]
        
        # Remove old impacts
        self.pending_impacts = [
            impact for impact in self.pending_impacts 
            if current_time - impact['recorded_at'] < timeout_seconds
        ]
        
        # Limit list sizes
        if len(self.pending_shots) > self.max_pending_items:
            self.pending_shots = self.pending_shots[-self.max_pending_items:]
        if len(self.pending_impacts) > self.max_pending_items:
            self.pending_impacts = self.pending_impacts[-self.max_pending_items:]
    
    def get_correlation_stats(self) -> Dict:
        """Get timing correlation statistics"""
        success_rate = (self.successful_correlations / max(1, self.total_correlations))
        
        # Calculate average delay from recent correlations
        recent_pairs = self.correlated_pairs[-20:] if self.correlated_pairs else []
        avg_delay = sum(pair.delay_ms for pair in recent_pairs) / max(1, len(recent_pairs))
        
        return {
            'total_pairs': len(self.correlated_pairs),
            'success_rate': success_rate,
            'avg_delay_ms': round(avg_delay, 1) if recent_pairs else 0,
            'expected_delay_ms': self.expected_delay_ms,
            'pending_shots': len(self.pending_shots),
            'pending_impacts': len(self.pending_impacts),
            'calibration_status': 'Active' if recent_pairs else 'No Data'
        }
    
    def _load_calibration(self):
        """Load calibration data from file"""
        try:
            if self.calibration_file.exists():
                with open(self.calibration_file, 'r') as f:
                    data = json.load(f)
                    self.expected_delay_ms = data.get('expected_delay_ms', self.expected_delay_ms)
                    logger.info(f"Loaded calibration: delay={self.expected_delay_ms}ms")
        except Exception as e:
            logger.warning(f"Could not load calibration: {e}")
    
    def save_calibration(self):
        """Save current calibration data"""
        try:
            # Calculate current average delay
            if self.correlated_pairs:
                recent_delays = [pair.delay_ms for pair in self.correlated_pairs[-50:]]
                avg_delay = sum(recent_delays) / len(recent_delays)
            else:
                avg_delay = self.expected_delay_ms
            
            calibration_data = {
                'expected_delay_ms': round(avg_delay, 1),
                'total_correlations': len(self.correlated_pairs),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.calibration_file, 'w') as f:
                json.dump(calibration_data, f, indent=2)
                
            logger.info(f"Calibration saved: delay={avg_delay:.1f}ms")
            
        except Exception as e:
            logger.error(f"Could not save calibration: {e}")