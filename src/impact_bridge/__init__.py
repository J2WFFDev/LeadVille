"""
Impact Bridge Library - Core BLE-based impact sensor system

This package provides the core components for a BLE-based impact detection system
that interfaces with AMG timers and BT50 sensors for shooting sports applications.
"""

__version__ = "2.0.0"
__author__ = "LeadVille Impact Bridge Team"

# Core modules
from .wtvb_parse import parse_5561
from .shot_detector import ShotDetector
from .timing_calibration import RealTimeTimingCalibrator
from .enhanced_impact_detection import EnhancedImpactDetector
from .statistical_timing_calibration import statistical_calibrator
from .dev_config import dev_config

__all__ = [
    'parse_5561',
    'ShotDetector', 
    'RealTimeTimingCalibrator',
    'EnhancedImpactDetector',
    'statistical_calibrator',
    'dev_config'
]