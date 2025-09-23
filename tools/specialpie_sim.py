#!/usr/bin/env python3
"""
SpecialPie Timer UDP Simulator

Simulates a SpecialPie timer by sending UDP packets with demo shooting data.
Useful for testing the SpecialPie adapter without physical hardware.
"""

import asyncio
import logging
import signal
import socket
import time
from typing import Optional

# Demo shooting data - 3 strings of 5 shots each
DEMO_STRINGS = [
    # String 1: Fast shooting
    {
        "shots": [0.234, 0.445, 0.623, 0.834, 1.045],
        "par_time": 5.0
    },
    # String 2: Precision shooting  
    {
        "shots": [1.234, 2.456, 3.678, 4.890, 6.123],
        "par_time": 8.0
    },
    # String 3: Mixed timing
    {
        "shots": [0.567, 1.234, 1.789, 2.345, 2.901],
        "par_time": 6.0
    }
]


class SpecialPieSimulator:
    """UDP simulator for SpecialPie timer protocol"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 12345):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.sequence = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('specialpie_sim')
        
        # Setup signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _calculate_checksum(self, data: str) -> int:
        """Calculate simple checksum for frame"""
        return sum(ord(c) for c in data) & 0xFF
    
    def _create_frame(self, event_type: str, data: str = "") -> bytes:
        """Create a SpecialPie protocol frame"""
        self.sequence += 1
        timestamp = int(time.time() * 1000)  # milliseconds
        
        # Build frame content
        content = f"{event_type}:{self.sequence}:{timestamp}"
        if data:
            content += f":{data}"
        
        # Add checksum
        checksum = self._calculate_checksum(content)
        frame = f"SP|{content}|{checksum:02X}\n"
        
        return frame.encode('ascii')
    
    async def _send_frame(self, event_type: str, data: str = ""):
        """Send a frame via UDP"""
        if not self.socket:
            return
        
        frame = self._create_frame(event_type, data)
        
        try:
            # Send to any clients listening
            self.socket.sendto(frame, (self.host, self.port))
            self.logger.info(f"Sent: {frame.decode().strip()}")
        except Exception as e:
            self.logger.error(f"Failed to send frame: {e}")
    
    async def _simulate_string(self, string_num: int, string_data: dict):
        """Simulate a complete shooting string"""
        shots = string_data["shots"]
        par_time = string_data["par_time"]
        
        self.logger.info(f"Starting String {string_num} ({len(shots)} shots, {par_time}s par)")
        
        # Send string start
        await self._send_frame("STRING_START", f"string={string_num};par={par_time}")
        await asyncio.sleep(0.5)
        
        # Send shots
        string_start_time = time.time()
        for shot_num, shot_time in enumerate(shots, 1):
            # Wait until shot time
            elapsed = time.time() - string_start_time
            if elapsed < shot_time:
                await asyncio.sleep(shot_time - elapsed)
            
            # Send shot event
            actual_time = time.time() - string_start_time
            await self._send_frame("SHOT", f"shot={shot_num};time={actual_time:.3f};string={string_num}")
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(0.5)
        
        # Send string stop
        total_time = time.time() - string_start_time
        await self._send_frame("STRING_STOP", f"string={string_num};total={total_time:.3f};shots={len(shots)}")
        
        self.logger.info(f"Completed String {string_num} in {total_time:.3f}s")
    
    async def run_demo(self):
        """Run the demo simulation"""
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            
            self.logger.info(f"SpecialPie Simulator listening on {self.host}:{self.port}")
            self.logger.info("Waiting 3 seconds before starting demo...")
            
            self.running = True
            
            # Initial connection and sync events
            await asyncio.sleep(3.0)
            await self._send_frame("TIMER_CONNECTED", "device=SpecialPie_SIM;version=1.0")
            await asyncio.sleep(0.5)
            await self._send_frame("CLOCK_SYNC", f"host_time={int(time.time() * 1000)};skew=0")
            await asyncio.sleep(1.0)
            
            # Run demo strings
            for string_num, string_data in enumerate(DEMO_STRINGS, 1):
                if not self.running:
                    break
                
                await self._simulate_string(string_num, string_data)
                
                if string_num < len(DEMO_STRINGS):
                    self.logger.info("Waiting 5 seconds before next string...")
                    await asyncio.sleep(5.0)
            
            # Send final status
            await asyncio.sleep(1.0)
            await self._send_frame("TIMER_DISCONNECTED", "reason=demo_complete")
            
            self.logger.info("Demo complete!")
            
        except Exception as e:
            self.logger.error(f"Simulator error: {e}", exc_info=True)
        
        finally:
            if self.socket:
                self.socket.close()
    
    async def run_continuous(self):
        """Run continuous simulation (repeating)"""
        self.logger.info("Starting continuous simulation mode...")
        
        while self.running:
            await self.run_demo()
            
            if self.running:
                self.logger.info("Restarting demo in 10 seconds...")
                await asyncio.sleep(10.0)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SpecialPie Timer UDP Simulator")
    parser.add_argument("--host", default="127.0.0.1", help="UDP host address")
    parser.add_argument("--port", type=int, default=12345, help="UDP port")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    
    args = parser.parse_args()
    
    simulator = SpecialPieSimulator(args.host, args.port)
    
    try:
        if args.continuous:
            await simulator.run_continuous()
        else:
            await simulator.run_demo()
    except KeyboardInterrupt:
        print("\nSimulator interrupted by user")
    except Exception as e:
        print(f"Simulator failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())