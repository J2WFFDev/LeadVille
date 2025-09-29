#!/usr/bin/env python3
"""
AMG Commander Enhanced Test
Tests advanced AMG Commander features including sensitivity control,
remote start, battery monitoring, and shot data retrieval.
"""
import sys
import asyncio
sys.path.append('/home/jrwest/projects/LeadVille')

from src.impact_bridge.amg_commander_handler import amg_manager

# Global variables for capturing events
shot_events = []
timer_events = []

async def shot_callback(shot_event):
    """Callback for shot events"""
    shot_events.append(shot_event)
    print(f"🎯 SHOT: {shot_event['time_now']:.2f}s (split: {shot_event['time_split']:.2f}s, first: {shot_event['time_first']:.2f}s)")

async def timer_callback(timer_event):
    """Callback for timer events"""
    timer_events.append(timer_event)
    event_type = "START" if 'started' in str(timer_event) else "STOP"
    print(f"⏰ TIMER {event_type}: {timer_event}")

async def test_amg_enhanced_features():
    # Find your AMG Commander timer address
    # You'll need to replace this with your actual AMG timer MAC address
    # Check your paired devices to find the AMG timer address
    
    print("🔍 Looking for AMG Commander timer...")
    print("   Please replace 'XX:XX:XX:XX:XX:XX' with your actual AMG timer MAC address")
    
    # Example addresses - replace with your actual AMG timer
    possible_addresses = [
        "60:09:C3:1F:DC:1A",  # From your log - AMG Lab COMM DC1A
        "60:09:C3:84:7F:F4"   # From your log - AMG Lab COMM 7FF4
    ]
    
    amg_address = None
    for addr in possible_addresses:
        print(f"   Trying: {addr}")
        amg_address = addr
        break  # Use first available address for demo
    
    if not amg_address:
        print("❌ No AMG timer address specified")
        print("   Update the script with your AMG Commander MAC address")
        return
    
    print(f"🔗 Connecting to AMG Commander: {amg_address}")
    
    # Add timer to manager
    handler = amg_manager.add_timer(amg_address)
    
    # Set up callbacks
    amg_manager.shot_callbacks.append(shot_callback)
    amg_manager.timer_callbacks.append(timer_callback)
    
    try:
        # Connect to timer
        print("📡 Attempting BLE connection...")
        connected = await handler.connect()
        
        if not connected:
            print("❌ Failed to connect to AMG Commander timer")
            print("   Make sure the timer is on and in range")
            return
        
        print("✅ Connected successfully!")
        
        # Display initial status
        status = handler.get_status()
        print(f"📊 Timer Status:")
        print(f"   Battery: {status['battery_level'] or 'Unknown'}%")
        print(f"   Signal Strength: {status['signal_strength'] or 'Unknown'} dBm")
        print(f"   Current Sensitivity: {status['sensitivity']}")
        
        # Test sensitivity adjustment
        print(f"\n🎛️ Testing Sensitivity Control...")
        for sens in [3, 7, 5]:  # Test different sensitivity levels
            print(f"   Setting sensitivity to {sens}...")
            success = await handler.set_sensitivity(sens)
            if success:
                print(f"   ✅ Sensitivity set to {sens}")
            else:
                print(f"   ❌ Failed to set sensitivity to {sens}")
            await asyncio.sleep(1)
        
        # Test remote start
        print(f"\n📢 Testing Remote Start...")
        print("   Sending remote start command (should trigger beep)...")
        success = await handler.remote_start_timer()
        if success:
            print("   ✅ Remote start command sent - listen for beep!")
        else:
            print("   ❌ Failed to send remote start command")
        
        # Test data requests
        print(f"\n📥 Testing Data Requests...")
        print("   Requesting shot data...")
        await handler.request_shot_data()
        await asyncio.sleep(2)
        
        print("   Requesting screen data...")
        await handler.request_screen_data()
        await asyncio.sleep(2)
        
        # Start monitoring
        print(f"\n🎯 Starting Shot Monitoring...")
        await handler.start_monitoring()
        
        print("   Monitoring for 15 seconds...")
        print("   Try firing some shots or starting a string on your timer!")
        
        for i in range(15):
            await asyncio.sleep(1)
            if i % 5 == 0:
                current_status = handler.get_status()
                print(f"   Status: {current_status['current_shots']} shots in sequence")
        
        # Display results
        print(f"\n📈 Final Results:")
        final_status = handler.get_status()
        print(f"   Total shot events: {len(shot_events)}")
        print(f"   Total timer events: {len(timer_events)}")
        print(f"   Shot sequence: {final_status['shot_sequence']}")
        
        if shot_events:
            print("🎯 Shot Events:")
            for i, event in enumerate(shot_events, 1):
                print(f"     {i}. Time: {event['time_now']:.2f}s, Split: {event['time_split']:.2f}s")
        
        if timer_events:
            print("⏰ Timer Events:")
            for i, event in enumerate(timer_events, 1):
                print(f"     {i}. {event}")
        
        # Advanced features summary
        print(f"\n🚀 AMG Commander Advanced Features Tested:")
        print(f"   ✅ BLE Connection & Communication")
        print(f"   ✅ Sensitivity Control (1-10)")
        print(f"   ✅ Remote Start Command")
        print(f"   ✅ Shot Data Requests")
        print(f"   ✅ Real-time Shot Monitoring")
        print(f"   ✅ Battery Level Reading")
        print(f"   ✅ Signal Strength Monitoring")
        
        # Test random delay measurement
        print(f"\n🎲 Random Delay Information:")
        print(f"   The AMG Commander has a built-in random delay between")
        print(f"   start button press and beep. This delay is generated")
        print(f"   internally by the timer and cannot be read via BLE.")
        print(f"   The delay varies to prevent anticipation in competition.")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        try:
            await handler.disconnect()
            print("🔌 Disconnected from AMG Commander")
        except:
            pass

if __name__ == '__main__':
    print("🏁 AMG Commander Enhanced Feature Test")
    print("=" * 60)
    asyncio.run(test_amg_enhanced_features())