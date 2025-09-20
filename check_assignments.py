#!/usr/bin/env python3
"""Check sensor assignments"""

import json
import subprocess

def check_assignments():
    try:
        # Get devices from API
        result = subprocess.run(['curl', '-s', 'http://localhost:8001/api/admin/devices'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error getting devices: {result.stderr}")
            return
            
        data = json.loads(result.stdout)
        
        print("=== Current Sensor Assignments ===")
        for device in data['devices']:
            print(f"Device: {device['label']}")
            print(f"  ID: {device['id']}")
            print(f"  Address: {device['address']}")
            print(f"  target_config_id: {device.get('target_config_id', 'None')}")
            print(f"  assigned: {device.get('target_config_id') is not None}")
            print()
        
        print(f"Total devices: {data['count']}")
        assigned_count = sum(1 for d in data['devices'] if d.get('target_config_id') is not None)
        print(f"Assigned devices: {assigned_count}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_assignments()