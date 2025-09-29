#!/usr/bin/env python3
"""
Test SpecialPie device detection patterns
"""

import sys
import os
sys.path.append('/home/jrwest/projects/LeadVille')

from src.impact_bridge.device_manager import DeviceManager

def test_device_patterns():
    dm = DeviceManager()
    
    # Test various device patterns
    test_devices = [
        {'name': 'SpecialPie Timer', 'type': 'timer', 'vendor': 'SpecialPie'},
        {'name': 'SP M1A2 Timer', 'type': 'timer', 'vendor': 'SpecialPie'},  
        {'name': 'SPECIAL PIE', 'type': 'timer', 'vendor': 'SpecialPie'},
        {'name': 'BT50 Sensor', 'type': 'accelerometer', 'vendor': 'WitMotion'},
        {'name': 'AMG Timer', 'type': 'timer', 'vendor': 'AMG Labs'},
        {'name': 'Unknown Device', 'type': 'unknown', 'vendor': 'Unknown'}
    ]

    print("Testing SpecialPie device pattern matching:")
    print("=" * 50)
    
    for device in test_devices:
        try:
            is_relevant = dm._is_relevant_device(device)
            status = "✅ DETECTED" if is_relevant else "❌ FILTERED"
            print(f"{device['name']:20} | {status} | Type: {device['type']} | Vendor: {device['vendor']}")
        except Exception as e:
            print(f"{device['name']:20} | ERROR: {e}")

    print("=" * 50)
    print("Known device patterns:")
    for device_type, config in dm.known_devices.items():
        print(f"{device_type}: {config['name_patterns']} -> {config['type']} ({config['vendor']})")

if __name__ == '__main__':
    test_device_patterns()