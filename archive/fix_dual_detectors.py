#!/usr/bin/env python3

import re

def fix_dual_detectors():
    with open("leadville_bridge.py", "r") as f:
        content = f.read()
    
    # Replace single detector initialization with per-sensor detectors dict
    old_init = r"self\.enhanced_impact_detector = EnhancedImpactDetector\([^)]*\)"
    new_init = "self.enhanced_impact_detectors = {}  # Per-sensor detectors"
    content = re.sub(old_init, new_init, content)
    
    # Replace None assignment  
    content = re.sub(r"self\.enhanced_impact_detector = None", "self.enhanced_impact_detectors = {}", content)
    
    # Replace the detector usage with per-sensor logic
    old_usage = r"if self\.enhanced_impact_detector:"
    new_usage = """# Get or create detector for this sensor
                sensor_short = sensor_mac[-5:] if sensor_mac else "UNK"
                if sensor_short not in self.enhanced_impact_detectors:
                    if ENHANCED_DETECTION_AVAILABLE:
                        if self.dev_config:
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
                        
                if self.enhanced_impact_detectors.get(sensor_short):"""
    
    content = re.sub(old_usage, new_usage, content)
    
    # Replace the detector method call
    old_call = r"impact_event = self\.enhanced_impact_detector\.process_sample\("
    new_call = "impact_event = self.enhanced_impact_detectors[sensor_short].process_sample("
    content = re.sub(old_call, new_call, content)
    
    with open("leadville_bridge.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed: Created per-sensor enhanced impact detectors")
    print("🎯 Each sensor now has its own impact detector to prevent interference")

if __name__ == "__main__":
    fix_dual_detectors()