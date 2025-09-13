#!/usr/bin/env python3
"""Demo script showing pluggable timer driver architecture."""

import asyncio
import logging
from src.impact_bridge.timer_drivers import registry

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_driver_registry():
    """Demonstrate driver registration and discovery."""
    print("=" * 60)
    print("🎯 PLUGGABLE TIMER DRIVER ARCHITECTURE DEMO")
    print("=" * 60)
    
    # Show available drivers
    print("\n📋 Available Timer Drivers:")
    available = registry.get_available_drivers()
    
    for vendor_id, info in available.items():
        print(f"  🔌 {vendor_id}:")
        print(f"    - Vendor: {info['vendor_name']}")
        print(f"    - Device: {info['device_type']}")
        print(f"    - Features: {', '.join(info['supported_features'])}")
        print()


async def demo_amg_driver():
    """Demonstrate AMG Labs Commander driver."""
    print("\n🏭 AMG Labs Commander Driver Demo")
    print("-" * 40)
    
    config = {
        "device_id": "60:09:C3:1F:DC:1A",
        "uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
        "simulation_mode": True,
        "simulation": {
            "mode": "single_shot",
            "num_shots": 1,
            "start_delay_sec": 1.0
        }
    }
    
    # Create AMG driver
    amg_driver = registry.create_driver("amg_labs", config)
    
    # Show driver info
    info = await amg_driver.get_device_info()
    print(f"📱 Device Info: {info['vendor']} {info['device_type']}")
    print(f"🔧 Features: {', '.join(info['supported_features'])}")
    
    # Setup callbacks
    def on_timer_event(data):
        print(f"⏰ Timer Event: {data}")
    
    def on_shot_detected(data):
        print(f"🎯 Shot Detected: {data}")
    
    amg_driver.set_callback("on_timer_event", on_timer_event)
    amg_driver.set_callback("on_shot_detected", on_shot_detected)
    
    # Test driver lifecycle
    print(f"📊 Initial Status: {await amg_driver.get_status()}")
    
    print("🚀 Starting AMG driver...")
    await amg_driver.start()
    
    print(f"📊 Running Status: {await amg_driver.get_status()}")
    
    # Let it run for a few seconds
    await asyncio.sleep(3)
    
    print("🔌 Stopping AMG driver...")
    await amg_driver.stop()
    
    print(f"📊 Final Status: {await amg_driver.get_status()}")


async def demo_specialpie_driver():
    """Demonstrate SpecialPie driver."""
    print("\n🥧 SpecialPie Pro Timer Driver Demo")
    print("-" * 40)
    
    config = {
        "device_id": "SP:12:34:56:78:90",
        "protocol_version": "2.0",
        "connection_timeout": 5.0
    }
    
    # Create SpecialPie driver
    sp_driver = registry.create_driver("specialpie", config)
    
    # Show driver info
    info = await sp_driver.get_device_info()
    print(f"📱 Device Info: {info['vendor']} {info['device_type']}")
    print(f"🔧 Features: {', '.join(info['supported_features'])}")
    print(f"💾 Firmware: {info['firmware_version']}")
    
    # Test driver lifecycle
    print(f"📊 Initial Status: {await sp_driver.get_status()}")
    
    print("🚀 Starting SpecialPie driver...")
    await sp_driver.start()
    
    print(f"📊 Running Status: {await sp_driver.get_status()}")
    
    print("🔌 Stopping SpecialPie driver...")
    await sp_driver.stop()
    
    print(f"📊 Final Status: {await sp_driver.get_status()}")


async def demo_vendor_switching():
    """Demonstrate vendor switching capability.""" 
    print("\n🔄 Vendor Switching Demo")
    print("-" * 40)
    
    configs = {
        "amg_labs": {
            "device_id": "60:09:C3:1F:DC:1A",
            "simulation_mode": True
        },
        "specialpie": {
            "device_id": "SP:00:00:00:00:00",
            "protocol_version": "1.0"
        }
    }
    
    current_vendor = "amg_labs"
    current_driver = registry.create_driver(current_vendor, configs[current_vendor])
    
    print(f"🎯 Starting with {current_driver.vendor_name} {current_driver.device_type}")
    await current_driver.start()
    await asyncio.sleep(1)
    
    # Switch vendors
    await current_driver.stop()
    
    new_vendor = "specialpie"
    print(f"🔄 Switching to {new_vendor}...")
    
    new_driver = registry.create_driver(new_vendor, configs[new_vendor])
    print(f"🎯 Now using {new_driver.vendor_name} {new_driver.device_type}")
    await new_driver.start()
    await asyncio.sleep(1)
    await new_driver.stop()
    
    print("✅ Vendor switching completed successfully!")


async def main():
    """Main demo function."""
    try:
        await demo_driver_registry()
        await demo_amg_driver()
        await demo_specialpie_driver()
        await demo_vendor_switching()
        
        print("\n" + "=" * 60)
        print("✅ PLUGGABLE TIMER DRIVER DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())