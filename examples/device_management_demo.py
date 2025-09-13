#!/usr/bin/env python3
"""
Device Management API Demo

This example demonstrates how to use the LeadVille Impact Bridge device management API
to discover, pair, and assign BLE devices to targets.

Usage:
    python examples/device_management_demo.py

Note: This requires the API server to be running and BlueZ to be available for actual BLE operations.
"""

import asyncio
import json
import time
from typing import List, Dict, Any

import httpx


class DeviceManagementDemo:
    """Demo client for device management API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)
    
    def discover_devices(self, duration: float = 10.0) -> List[Dict[str, Any]]:
        """Discover nearby BLE devices."""
        print(f"🔍 Starting device discovery for {duration} seconds...")
        
        response = self.client.post(
            "/v1/admin/devices/discover",
            json={"duration": duration}
        )
        
        if response.status_code == 200:
            data = response.json()
            devices = data["devices"]
            print(f"✅ Discovery completed. Found {data['total_found']} devices:")
            
            for device in devices:
                print(f"  📱 {device['address']} ({device['name']}) - Type: {device['device_type']}, RSSI: {device['rssi']}dBm")
            
            return devices
        else:
            print(f"❌ Discovery failed: {response.text}")
            return []
    
    def pair_device(self, address: str, device_type: str = "unknown") -> bool:
        """Pair with a specific BLE device."""
        print(f"🤝 Attempting to pair with device {address}...")
        
        response = self.client.post(
            "/v1/admin/devices/pair",
            json={
                "address": address,
                "device_type": device_type
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                print(f"✅ Successfully paired with {address}")
                return True
            else:
                print(f"❌ Failed to pair with {address}: {data['message']}")
                return False
        else:
            print(f"❌ Pairing request failed: {response.text}")
            return False
    
    def assign_device(self, address: str, target_id: int) -> bool:
        """Assign a device to a target."""
        print(f"🎯 Assigning device {address} to target {target_id}...")
        
        response = self.client.post(
            "/v1/admin/devices/assign",
            json={
                "address": address,
                "target_id": target_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                print(f"✅ Successfully assigned {address} to target {target_id}")
                return True
            else:
                print(f"❌ Failed to assign device: {data['message']}")
                return False
        else:
            print(f"❌ Assignment request failed: {response.text}")
            return False
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List all known devices."""
        print("📋 Retrieving device list...")
        
        response = self.client.get("/v1/admin/devices/list")
        
        if response.status_code == 200:
            data = response.json()
            devices = data["devices"]
            print(f"📱 Found {data['total']} devices:")
            
            for device in devices:
                status = "🟢 Connected" if device["is_connected"] else "🔴 Disconnected"
                target = f"Target {device['target_id']}" if device['target_id'] else "Unassigned"
                battery = f"{device['battery']}%" if device['battery'] else "Unknown"
                
                print(f"  📱 {device['address']} ({device['label']})")
                print(f"     Status: {status}, Target: {target}, Battery: {battery}")
                if device['last_error']:
                    print(f"     ⚠️  Last Error: {device['last_error']}")
            
            return devices
        else:
            print(f"❌ Failed to retrieve device list: {response.text}")
            return []
    
    def start_health_monitoring(self, interval: float = 30.0) -> bool:
        """Start device health monitoring."""
        print(f"❤️  Starting health monitoring (interval: {interval}s)...")
        
        response = self.client.post(
            "/v1/admin/devices/monitoring",
            json={
                "enabled": True,
                "interval": interval
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                print(f"✅ Health monitoring started")
                return True
            else:
                print(f"❌ Failed to start monitoring: {data['message']}")
                return False
        else:
            print(f"❌ Monitoring request failed: {response.text}")
            return False
    
    def get_device_health(self, address: str) -> Dict[str, Any]:
        """Get health status for a specific device."""
        print(f"🩺 Checking health of device {address}...")
        
        response = self.client.get(f"/v1/admin/devices/health/{address}")
        
        if response.status_code == 200:
            health = response.json()
            status = "🟢 Healthy" if health["is_connected"] else "🔴 Unhealthy"
            print(f"  Status: {status}")
            print(f"  RSSI: {health['rssi']}dBm" if health['rssi'] else "  RSSI: Unknown")
            print(f"  Battery: {health['battery_level']}%" if health['battery_level'] else "  Battery: Unknown")
            print(f"  Last Seen: {health['last_seen']}")
            print(f"  Connection Attempts: {health['connection_attempts']}")
            if health['last_error']:
                print(f"  ⚠️  Last Error: {health['last_error']}")
            
            return health
        elif response.status_code == 404:
            print(f"❌ Device {address} not found or no health data available")
            return {}
        else:
            print(f"❌ Health check failed: {response.text}")
            return {}
    
    def unassign_device(self, address: str) -> bool:
        """Remove device assignment."""
        print(f"🔄 Unassigning device {address}...")
        
        response = self.client.post(
            "/v1/admin/devices/unassign",
            json={"address": address}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                print(f"✅ Successfully unassigned {address}")
                return True
            else:
                print(f"❌ Failed to unassign device: {data['message']}")
                return False
        else:
            print(f"❌ Unassignment request failed: {response.text}")
            return False
    
    def check_api_status(self) -> bool:
        """Check if the API server is running."""
        try:
            response = self.client.get("/v1/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ API server is {health['status']} (uptime: {health['uptime_seconds']}s)")
                return True
            else:
                print(f"❌ API server returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API server: {e}")
            return False


def main():
    """Main demo function."""
    print("🚀 LeadVille Impact Bridge Device Management Demo")
    print("=" * 50)
    
    demo = DeviceManagementDemo()
    
    # Check API status
    if not demo.check_api_status():
        print("Please start the API server first:")
        print("  python start_api.py --debug")
        return
    
    print()
    
    # List current devices
    current_devices = demo.list_devices()
    print()
    
    # Start health monitoring
    demo.start_health_monitoring(interval=60.0)
    print()
    
    # Discover new devices (short duration for demo)
    discovered_devices = demo.discover_devices(duration=3.0)
    print()
    
    if discovered_devices:
        # Try to pair with the first discovered device
        first_device = discovered_devices[0]
        success = demo.pair_device(first_device["address"], first_device["device_type"])
        print()
        
        if success:
            # For demo purposes, assume target ID 1 exists
            # In a real scenario, you'd first create targets
            demo.assign_device(first_device["address"], target_id=1)
            print()
            
            # Check device health
            demo.get_device_health(first_device["address"])
            print()
    
    # List devices again to see changes
    print("📋 Final device list:")
    demo.list_devices()
    
    print()
    print("✅ Demo completed!")
    print()
    print("💡 Tips:")
    print("  - Use the API documentation at http://localhost:8000/v1/docs")
    print("  - Check device health regularly for production use")
    print("  - Devices need to be physically present for actual BLE operations")


if __name__ == "__main__":
    main()