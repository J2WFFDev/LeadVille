#!/usr/bin/env python3
"""
SpecialPie shot monitoring test - Connect and capture shots
"""
import sys
import asyncio
sys.path.append('/home/jrwest/projects/LeadVille')

from src.impact_bridge.specialpie_handler import SpecialPieHandler

# Global variables to capture shot data
shots_captured = []

def shot_callback(shot_event):
    """Callback for shot events"""
    shots_captured.append(shot_event)
    print(f"🎯 SHOT {shot_event['shot_number']}: {shot_event['total_time_formatted']}s (split: {shot_event['split_time_formatted']}s)")

def string_callback(event_type, string_event):
    """Callback for string start/stop events"""
    if event_type == 'start':
        print(f"🟢 STRING STARTED")
        shots_captured.clear()  # Clear previous shots
    elif event_type == 'stop':
        print(f"🔴 STRING STOPPED - Total shots: {string_event['total_shots']}")

async def shot_monitoring_test():
    mac_address = "50:54:7B:AD:4F:03"
    
    print(f"🔗 Connecting to SpecialPie timer: {mac_address}")
    handler = SpecialPieHandler(mac_address)
    
    # Set up shot capture callbacks
    handler.on_shot = shot_callback
    handler.on_string_start = lambda event: string_callback('start', event)
    handler.on_string_stop = lambda event: string_callback('stop', event)
    handler.on_connection_change = None
    
    try:
        # Connect to timer
        connected = await handler.connect()
        if not connected:
            print("❌ Failed to connect to SpecialPie timer")
            return
            
        print("✅ Connected successfully!")
        print(f"📡 BLE Notification UUID: {handler.notification_uuid}")
        
        # Start monitoring
        await handler.start_monitoring()
        print("🎯 Shot monitoring active - fire some shots or start a string!")
        print("⏰ Waiting 30 seconds for shot data...")
        print("   (Use your SpecialPie timer start button and fire shots)")
        
        # Monitor for 30 seconds
        for i in range(30):
            await asyncio.sleep(1)
            if i % 5 == 0:  # Print status every 5 seconds
                status = handler.get_status()
                print(f"   Status: {status['current_shots']} shots captured, monitoring: {status['monitoring']}")
        
        print(f"\n📊 Final Results:")
        print(f"   Total shots captured: {len(shots_captured)}")
        
        if shots_captured:
            print("🎯 Shot Details:")
            for shot in shots_captured:
                print(f"     Shot {shot['shot_number']}: {shot['total_time_formatted']}s (split: {shot['split_time_formatted']}s)")
        else:
            print("   No shots detected - make sure to:")
            print("     1. Press START on your SpecialPie timer")  
            print("     2. Fire some shots")
            print("     3. Press STOP on your timer")
        
        # Stop monitoring  
        await handler.stop_monitoring()
        print("⏹️ Monitoring stopped")
        
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await handler.disconnect()
        print("🔌 Disconnected from SpecialPie timer")

if __name__ == '__main__':
    print("🏁 SpecialPie Shot Timer Test")
    print("=" * 50)
    asyncio.run(shot_monitoring_test())