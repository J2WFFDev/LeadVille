#!/usr/bin/env python3
"""
Simple SpecialPie timer connection test without callbacks
"""
import sys
import asyncio
sys.path.append('/home/jrwest/projects/LeadVille')

from src.impact_bridge.specialpie_handler import SpecialPieHandler

async def simple_connection_test():
    mac_address = "50:54:7B:AD:4F:03"
    
    print(f"Creating SpecialPie handler for: {mac_address}")
    handler = SpecialPieHandler(mac_address)
    
    # Don't set any callbacks to avoid the callback error
    handler.on_connection_change = None
    handler.on_shot = None
    handler.on_string_start = None
    handler.on_string_stop = None
    
    print(f"Attempting BLE connection...")
    try:
        connected = await handler.connect()
        print(f"Connection result: {connected}")
        
        if connected:
            print("✅ SpecialPie timer connected!")
            print(f"  Device address: {handler.mac_address}")
            print(f"  Is connected: {handler.is_connected}")
            print(f"  Notification UUID: {handler.notification_uuid}")
            
            # Test status
            status = handler.get_status()
            print(f"Handler status: {status}")
            
        else:
            print("❌ Connection failed")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            await handler.disconnect()
            print("Disconnected")
        except:
            pass

if __name__ == '__main__':
    asyncio.run(simple_connection_test())