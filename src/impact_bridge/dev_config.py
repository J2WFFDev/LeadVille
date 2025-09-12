"""
Development Configuration Module

Centralized configuration system for development and testing parameters.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DevelopmentConfig:
    """
    Centralized configuration for development parameters
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize development configuration
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file or Path("dev_config.json")
        
        # Default configuration
        self.config = {
            # Enhanced Impact Detection
            'enhanced_impact': {
                'enabled': True,
                'peak_threshold': 150.0,
                'onset_threshold': 30.0,
                'lookback_samples': 10
            },
            
            # Shot Detection
            'shot_detection': {
                'threshold': 150.0,
                'min_duration': 6,
                'max_duration': 11,
                'min_interval_seconds': 1.0
            },
            
            # Timing Calibration
            'timing': {
                'expected_delay_ms': 526.0,
                'correlation_window_ms': 2000,
                'enable_statistical_calibration': True
            },
            
            # Logging
            'logging': {
                'console_level': 'INFO',
                'file_level': 'DEBUG',
                'enable_raw_data_logging': False
            },
            
            # BLE Configuration
            'ble': {
                'connection_timeout_seconds': 10,
                'auto_reconnect': True,
                'reset_on_startup': True
            },
            
            # Sensor Configuration
            'sensor': {
                'calibration_samples': 100,
                'calibration_timeout_seconds': 30,
                'auto_calibrate_on_startup': True
            }
        }
        
        # Load configuration file if it exists
        self._load_config()
        
        logger.info("Development configuration initialized")
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    
                # Merge with defaults (file config takes precedence)
                self._merge_config(self.config, file_config)
                
                logger.info(f"Configuration loaded from {self.config_file}")
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")
    
    def _merge_config(self, default: Dict, override: Dict):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Could not save config: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'enhanced_impact.peak_threshold')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set final value
        config[keys[-1]] = value
        logger.debug(f"Config updated: {key_path} = {value}")
    
    # Enhanced Impact Detection methods
    def is_enhanced_impact_enabled(self) -> bool:
        return self.get('enhanced_impact.enabled', True)
    
    def get_peak_threshold(self) -> float:
        return self.get('enhanced_impact.peak_threshold', 150.0)
    
    def get_onset_threshold(self) -> float:
        return self.get('enhanced_impact.onset_threshold', 30.0)
    
    def get_lookback_samples(self) -> int:
        return self.get('enhanced_impact.lookback_samples', 10)
    
    # Shot Detection methods
    def get_shot_threshold(self) -> float:
        return self.get('shot_detection.threshold', 150.0)
    
    def get_shot_duration_range(self) -> tuple:
        min_dur = self.get('shot_detection.min_duration', 6)
        max_dur = self.get('shot_detection.max_duration', 11)
        return (min_dur, max_dur)
    
    def get_shot_interval(self) -> float:
        return self.get('shot_detection.min_interval_seconds', 1.0)
    
    # Timing methods
    def get_expected_delay(self) -> float:
        return self.get('timing.expected_delay_ms', 526.0)
    
    def get_correlation_window(self) -> float:
        return self.get('timing.correlation_window_ms', 2000)
    
    # Sensor methods
    def get_calibration_samples(self) -> int:
        return self.get('sensor.calibration_samples', 100)
    
    def get_calibration_timeout(self) -> int:
        return self.get('sensor.calibration_timeout_seconds', 30)
    
    def is_auto_calibrate_enabled(self) -> bool:
        return self.get('sensor.auto_calibrate_on_startup', True)
    
    def print_config_summary(self):
        """Print a summary of current configuration"""
        logger.info("=== DEVELOPMENT CONFIGURATION ===")
        logger.info(f"Enhanced Impact: {self.is_enhanced_impact_enabled()} "
                   f"(peak={self.get_peak_threshold()}, onset={self.get_onset_threshold()})")
        logger.info(f"Shot Detection: threshold={self.get_shot_threshold()}, "
                   f"duration={self.get_shot_duration_range()}, interval={self.get_shot_interval()}s")
        logger.info(f"Timing: delay={self.get_expected_delay()}ms, "
                   f"window={self.get_correlation_window()}ms")
        logger.info(f"Calibration: {self.get_calibration_samples()} samples, "
                   f"auto={self.is_auto_calibrate_enabled()}")
        logger.info("================================")


# Global configuration instance
dev_config = DevelopmentConfig()