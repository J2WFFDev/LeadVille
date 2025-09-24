#!/usr/bin/env python3
"""Test individual stage details API"""

import json
import subprocess

def test_stage_details():
    try:
        # Test stage 3 (Go Fast)
        result = subprocess.run(['curl', '-s', 'http://localhost:8001/api/admin/stages/3'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"API Error: {result.stderr}")
            return
            
        data = json.loads(result.stdout)
        
        if 'stage' in data:
            stage = data['stage']
            print(f"=== Stage Details API Test ===")
            print(f"Stage: {stage['name']}")
            print(f"Targets found: {len(stage['targets'])}")
            print()
            
            for target in stage['targets'][:2]:  # Just first 2 targets
                print(f"Target {target['target_number']}:")
                if target.get('sensor'):
                    sensor = target['sensor'] 
                    print(f"  ✓ ASSIGNED: {sensor['label']} ({sensor['hw_addr']})")
                else:
                    print(f"  ✗ UNASSIGNED")
                print()
        else:
            print("Error in response:")
            print(data)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stage_details()