#!/usr/bin/env python3
"""
Initialize SpecialPie timer for your device
"""
import sys
import asyncio
sys.path.append('/home/jrwest/projects/LeadVille')

from src.impact_bridge.specialpie_handler import specialpie_manager

async def setup_specialpie_timer():
    # Add your SpecialPie timer to the manager
    mac_address = "50:54:7B:AD:4F:03"
    
    print(f"Adding SpecialPie timer: {mac_address}")
    handler = specialpie_manager.add_timer(mac_address)
    
    print(f"Manager status before connection:")
    status = specialpie_manager.get_status()
    print(f"  Total timers: {status['total_timers']}")
    print(f"  Connected: {status['connected_timers']}")
    
    # Try to connect
    print(f"\nAttempting to connect to SpecialPie timer...")
    try:
        connected = await handler.connect()
        print(f"Connection result: {connected}")
        
        if connected:
            print("✅ SpecialPie timer connected successfully!")
            print("Starting shot monitoring...")
            await handler.start_monitoring()
            print("✅ Shot monitoring started - fire some shots!")
            
            # Wait for a few seconds to capture any shots
            print("Waiting 10 seconds for shot data...")
            await asyncio.sleep(10)
            
            # Get handler status
            handler_status = handler.get_status()
            print(f"\nHandler status after monitoring:")
            print(f"  Connected: {handler_status['connected']}")
            print(f"  Monitoring: {handler_status['monitoring']}")
            print(f"  Current shots: {handler_status['current_shots']}")
            
            if handler_status['last_shot']:
                print(f"  Last shot: {handler_status['last_shot']}")
        else:
            print("❌ Failed to connect to SpecialPie timer")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        
    # Final manager status
    print(f"\nFinal manager status:")
    final_status = specialpie_manager.get_status()
    print(f"  Total timers: {final_status['total_timers']}")
    print(f"  Connected: {final_status['connected_timers']}")
    print(f"  Monitoring: {final_status['monitoring_timers']}")

if __name__ == '__main__':
    asyncio.run(setup_specialpie_timer())