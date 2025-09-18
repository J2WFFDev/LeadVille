#!/usr/bin/env python3
"""Check Go Fast stage assignments"""

import json
import subprocess

def check_stage_assignments():
    try:
        # Get SASP stages
        result = subprocess.run(['curl', '-s', 'http://localhost:8001/api/admin/leagues/1/stages'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error getting stages: {result.stderr}")
            return
            
        data = json.loads(result.stdout)
        
        # Find Go Fast stage
        go_fast = next((s for s in data['stages'] if s['name'] == 'Go Fast'), None)
        
        if go_fast:
            print("=== Go Fast Stage Target Assignments ===")
            print(f"Stage ID: {go_fast['id']}")
            print(f"Target count: {go_fast['target_count']}")
            print()
            
            for target in go_fast['targets']:
                print(f"Target {target['target_number']} ({target['type']}):")
                print(f"  Target Config ID: {target['id']}")
                if 'sensor' in target and target['sensor']:
                    sensor = target['sensor']
                    print(f"  Assigned Sensor: {sensor['label']} ({sensor['hw_addr']})")
                    print(f"  Sensor ID: {sensor['id']}")
                else:
                    print(f"  Assigned Sensor: None")
                print()
        else:
            print("Go Fast stage not found")
            print("Available stages:")
            for stage in data['stages']:
                print(f"  - {stage['name']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_stage_assignments()