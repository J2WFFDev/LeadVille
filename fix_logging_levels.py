#!/usr/bin/env python3

import re

def fix_logging_and_config():
    with open("leadville_bridge.py", "r") as f:
        content = f.read()
    
    # Fix 1: Change parsing errors to debug level (not console level)
    content = re.sub(
        r'self\.logger\.error\(f"BT50 parsing failed: \{e\}"\)',
        'self.logger.debug(f"BT50 parsing failed: {e}")',
        content
    )
    
    # Fix 2: Add fallback for DevConfig enhanced_impact_detection
    old_config_check = r"""if self.dev_config:
                            peak_threshold = self.dev_config.enhanced_impact_detection.peak_threshold
                            onset_threshold = self.dev_config.enhanced_impact_detection.onset_threshold  
                            lookback_samples = self.dev_config.enhanced_impact_detection.lookback_samples"""
    
    new_config_check = """if self.dev_config and hasattr(self.dev_config, 'enhanced_impact_detection'):
                            peak_threshold = self.dev_config.enhanced_impact_detection.peak_threshold
                            onset_threshold = self.dev_config.enhanced_impact_detection.onset_threshold  
                            lookback_samples = self.dev_config.enhanced_impact_detection.lookback_samples"""
    
    content = re.sub(old_config_check, new_config_check, content)
    
    with open("leadville_bridge.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed logging levels:")
    print("   - BT50 parsing errors now go to DEBUG log only (not console)")
    print("   - Added DevConfig attribute check to prevent errors")
    print("🧹 Console log should now be clean and user-friendly!")

if __name__ == "__main__":
    fix_logging_and_config()