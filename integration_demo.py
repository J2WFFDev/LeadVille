#!/usr/bin/env python3
"""
Integration test and demo script for LeadVille timer adapters.
Tests both AMG Commander and SpecialPie adapters with various connection types.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from impact_bridge.timers.factory import create_timer_adapter
from impact_bridge.timers.types import TimerConfig, TimerEvent
from impact_bridge.ws.encode import encode_timer_event


class TimerDemo:
    """Demo application showing timer adapter usage"""
    
    def __init__(self):
        self.adapter = None
        self.running = False
        self.event_count = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('timer_demo')
        
        # Setup signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def run_amg_demo(self, mac_address: str = "60:09:C3:1F:DC:1A"):
        """Demo AMG Commander adapter"""
        self.logger.info("Starting AMG Commander demo")
        
        config = TimerConfig(
            timer_type="amg",
            ble_mac=mac_address
        )
        
        await self._run_adapter_demo(config, "AMG Commander")
    
    async def run_specialpie_serial_demo(self, port: str = "/dev/ttyACM0"):
        """Demo SpecialPie adapter with serial connection"""
        self.logger.info("Starting SpecialPie Serial demo")
        
        config = TimerConfig(
            timer_type="specialpie", 
            serial_port=port,
            serial_baud=115200
        )
        
        await self._run_adapter_demo(config, "SpecialPie (Serial)")
    
    async def run_specialpie_ble_demo(self, mac_address: str = "AA:BB:CC:DD:EE:FF"):
        """Demo SpecialPie adapter with BLE connection"""
        self.logger.info("Starting SpecialPie BLE demo")
        
        config = TimerConfig(
            timer_type="specialpie",
            ble_mac=mac_address
        )
        
        await self._run_adapter_demo(config, "SpecialPie (BLE)")
    
    async def run_specialpie_sim_demo(self):
        """Demo SpecialPie adapter with UDP simulator"""
        self.logger.info("Starting SpecialPie Simulator demo")
        
        config = TimerConfig(
            timer_type="specialpie",
            simulator_enabled=True
        )
        
        await self._run_adapter_demo(config, "SpecialPie (Simulator)")
    
    async def _run_adapter_demo(self, config: TimerConfig, name: str):
        """Run demo for a specific adapter configuration"""
        try:
            # Create adapter
            self.logger.info(f"Creating {name} adapter...")
            self.adapter = await create_timer_adapter(config)
            
            # Connect
            self.logger.info(f"Connecting to {name}...")
            connected = await self.adapter.connect()
            
            if not connected:
                self.logger.error(f"Failed to connect to {name}")
                return
            
            self.logger.info(f"Successfully connected to {name}")
            
            # Listen for events
            self.running = True
            self.event_count = 0
            
            self.logger.info("Listening for timer events (press Ctrl+C to stop)...")
            
            async for event in self.adapter.events:
                if not self.running:
                    break
                
                self.event_count += 1
                await self._handle_event(event, name)
                
                # Stop after 50 events for demo
                if self.event_count >= 50:
                    self.logger.info("Reached 50 events, stopping demo")
                    break
        
        except Exception as e:
            self.logger.error(f"Error in {name} demo: {e}", exc_info=True)
        
        finally:
            if self.adapter:
                self.logger.info(f"Disconnecting from {name}...")
                await self.adapter.disconnect()
    
    async def _handle_event(self, event: TimerEvent, adapter_name: str):
        """Handle a timer event"""
        # Log the event
        self.logger.info(f"Event #{self.event_count}: {event.event_type} - {event}")
        
        # Encode for WebSocket (demo)
        try:
            ws_data = encode_timer_event(event, adapter_name.lower())
            self.logger.debug(f"WebSocket encoding: {ws_data}")
        except Exception as e:
            self.logger.warning(f"Failed to encode event for WebSocket: {e}")
        
        # Simulate some processing delay
        await asyncio.sleep(0.01)


async def main():
    """Main demo entry point"""
    demo = TimerDemo()
    
    if len(sys.argv) < 2:
        print("Timer Adapter Demo")
        print()
        print("Usage:")
        print("  python integration_demo.py amg [MAC_ADDRESS]")
        print("  python integration_demo.py specialpie-serial [SERIAL_PORT]")
        print("  python integration_demo.py specialpie-ble [MAC_ADDRESS]")
        print("  python integration_demo.py specialpie-sim")
        print()
        print("Examples:")
        print("  python integration_demo.py amg 60:09:C3:1F:DC:1A")
        print("  python integration_demo.py specialpie-serial /dev/ttyACM0")
        print("  python integration_demo.py specialpie-ble AA:BB:CC:DD:EE:FF")
        print("  python integration_demo.py specialpie-sim")
        return
    
    demo_type = sys.argv[1].lower()
    
    try:
        if demo_type == "amg":
            mac = sys.argv[2] if len(sys.argv) > 2 else "60:09:C3:1F:DC:1A"
            await demo.run_amg_demo(mac)
        
        elif demo_type == "specialpie-serial":
            port = sys.argv[2] if len(sys.argv) > 2 else "/dev/ttyACM0"
            await demo.run_specialpie_serial_demo(port)
        
        elif demo_type == "specialpie-ble":
            mac = sys.argv[2] if len(sys.argv) > 2 else "AA:BB:CC:DD:EE:FF"
            await demo.run_specialpie_ble_demo(mac)
        
        elif demo_type == "specialpie-sim":
            await demo.run_specialpie_sim_demo()
        
        else:
            print(f"Unknown demo type: {demo_type}")
            print("Valid types: amg, specialpie-serial, specialpie-ble, specialpie-sim")
    
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())