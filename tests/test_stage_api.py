#!/usr/bin/env python3
"""Test stage API response"""

import json
import subprocess

def test_stage_api():
    try:
        # Test from frontend perspective
        result = subprocess.run(['curl', '-s', 'http://localhost:5173/api/admin/leagues/1/stages'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Frontend API Error: {result.stderr}")
            return
            
        data = json.loads(result.stdout)
        
        go_fast = next((s for s in data['stages'] if s['name'] == 'Go Fast'), None)
        if go_fast:
            print("=== Go Fast Stage from Frontend API ===")
            for target in go_fast['targets'][:2]:  # Just first 2 targets
                print(f"Target {target['target_number']}:")
                print(f"  Has sensor key: {'sensor' in target}")
                if 'sensor' in target and target['sensor']:
                    sensor = target['sensor']
                    print(f"  Sensor: {sensor['label']} ({sensor['hw_addr']})")
                else:
                    print(f"  Sensor value: {target.get('sensor', 'KEY_MISSING')}")
                print()
        else:
            print("Go Fast stage not found")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stage_api()