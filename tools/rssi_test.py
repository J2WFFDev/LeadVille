#!/usr/bin/env python3
"""
Simple RSSI Test Script
Tests BLE signal strength measurement
"""

import asyncio
from bleak import BleakScanner

async def scan_with_rssi():
    print('🔍 Scanning for devices with RSSI...')
    
    # Use return_adv=True to get advertisement data with RSSI
    discovered = await BleakScanner.discover(timeout=8.0, return_adv=True)
    
    target_devices = []
    for device, adv_data in discovered.values():
        if device.name and ('BT50' in device.name or 'AMG' in device.name):
            rssi = adv_data.rssi if hasattr(adv_data, 'rssi') else getattr(device, 'rssi', None)
            target_devices.append({
                'address': device.address,
                'name': device.name,
                'rssi': rssi
            })
    
    print(f'\n📡 Found {len(target_devices)} target devices:')
    for device in sorted(target_devices, key=lambda x: x['rssi'] or -999, reverse=True):
        rssi_text = f"{device['rssi']} dBm" if device['rssi'] else "N/A"
        signal_quality = ""
        if device['rssi']:
            if device['rssi'] >= -60:
                signal_quality = " (🟢 Excellent)"
            elif device['rssi'] >= -70:
                signal_quality = " (🟡 Good)"
            elif device['rssi'] >= -80:
                signal_quality = " (🟠 Fair)"
            else:
                signal_quality = " (🔴 Poor)"
        
        print(f"  {device['address']}: {device['name']}")
        print(f"    Signal: {rssi_text}{signal_quality}")

if __name__ == "__main__":
    asyncio.run(scan_with_rssi())