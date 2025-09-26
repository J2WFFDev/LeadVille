#!/bin/bash
# Battery Checker Tool Usage Examples

echo "🔋 BT50 Battery Status Checker"
echo "================================"
echo
echo "Usage examples:"
echo
echo "1. Test all known BT50 devices:"
echo "   python3 battery_checker.py"
echo
echo "2. Test specific device:"
echo "   python3 battery_checker.py EA:18:3D:6D:BA:E5"
echo
echo "3. Test with verbose logging:"
echo "   PYTHONPATH=../src python3 battery_checker.py"
echo
echo "Known BT50 device addresses:"
echo "  - EA:18:3D:6D:BA:E5 (BT50 Device 1)"
echo "  - DB:10:38:B6:13:6B (BT50 Device 2)"
echo "  - C2:1B:DB:F0:55:50 (BT50 Device 3)"
echo
echo "Requirements:"
echo "  - pip install bleak"
echo "  - Bluetooth adapter enabled"
echo "  - BT50 devices powered on and in range"