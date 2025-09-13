"""
AMG Timer Simulator
Simulates AMG Labs Commander timer for testing without hardware
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
import json
from pathlib import Path
from dataclasses import dataclass

from .ble.amg_parse import parse_amg_timer_data, ShotState

logger = logging.getLogger(__name__)


class SimulationMode(Enum):
    """Timer simulation modes"""
    SINGLE_SHOT = "single_shot"
    MULTI_SHOT = "multi_shot"
    RAPID_FIRE = "rapid_fire"
    PRECISION_MATCH = "precision_match"
    CUSTOM_SEQUENCE = "custom_sequence"


@dataclass
class SimulationConfig:
    """Configuration for timer simulation"""
    mode: SimulationMode = SimulationMode.MULTI_SHOT
    num_shots: int = 5
    shot_interval_sec: float = 2.0
    start_delay_sec: float = 3.0
    random_timing: bool = False
    timing_variance_sec: float = 0.5
    custom_sequence: Optional[List[float]] = None


class AMGTimerSimulator:
    """Simulates AMG Labs Commander timer behavior"""
    
    def __init__(
        self,
        device_id: str = "SIM:60:09:C3:1F:DC:1A",
        config: Optional[SimulationConfig] = None
    ):
        self.device_id = device_id
        self.config = config or SimulationConfig()
        
        self._running = False
        self._simulation_task: Optional[asyncio.Task] = None
        self._current_shot = 0
        self._total_shots = self.config.num_shots
        self._start_time: Optional[float] = None
        
        # Callbacks (matching AMG client interface)
        self._on_notification: Optional[Callable[[bytes], None]] = None
        self._on_parsed_data: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_t0: Optional[Callable[[int], None]] = None
        self._on_connect: Optional[Callable[[], None]] = None
        self._on_disconnect: Optional[Callable[[], None]] = None
        
    def set_notification_callback(self, callback: Callable[[bytes], None]) -> None:
        """Set callback for raw notifications"""
        self._on_notification = callback
        
    def set_parsed_data_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback for parsed data"""
        self._on_parsed_data = callback
        
    def set_t0_callback(self, callback: Callable[[int], None]) -> None:
        """Set callback for T0 events"""
        self._on_t0 = callback
        
    def set_connect_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for connection"""
        self._on_connect = callback
        
    def set_disconnect_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for disconnection"""
        self._on_disconnect = callback
    
    @property
    def is_connected(self) -> bool:
        """Check if simulator is connected"""
        return self._running
        
    async def start(self) -> None:
        """Start timer simulation"""
        if self._running:
            return
            
        self._running = True
        logger.info(f"Starting AMG timer simulation: {self.config.mode.value}")
        
        # Simulate connection
        await asyncio.sleep(0.5)  # Connection delay
        
        if self._on_connect:
            self._on_connect()
            
        logger.info("Timer simulator connected")
        
        # Start simulation
        self._simulation_task = asyncio.create_task(self._run_simulation())
        
    async def stop(self) -> None:
        """Stop timer simulation"""
        if not self._running:
            return
            
        self._running = False
        
        if self._simulation_task:
            self._simulation_task.cancel()
            try:
                await self._simulation_task
            except asyncio.CancelledError:
                pass
                
        if self._on_disconnect:
            self._on_disconnect()
            
        logger.info("Timer simulator stopped")
        
    async def _run_simulation(self) -> None:
        """Run the timer simulation sequence"""
        try:
            # Send START event
            await self._send_start_event()
            
            # Wait for start delay
            if self.config.start_delay_sec > 0:
                await asyncio.sleep(self.config.start_delay_sec)
            
            # Start timer
            self._start_time = time.time()
            await self._send_timer_start()
            
            # Run shot sequence based on mode
            if self.config.mode == SimulationMode.SINGLE_SHOT:
                await self._simulate_single_shot()
            elif self.config.mode == SimulationMode.MULTI_SHOT:
                await self._simulate_multi_shot()
            elif self.config.mode == SimulationMode.RAPID_FIRE:
                await self._simulate_rapid_fire()
            elif self.config.mode == SimulationMode.PRECISION_MATCH:
                await self._simulate_precision_match()
            elif self.config.mode == SimulationMode.CUSTOM_SEQUENCE:
                await self._simulate_custom_sequence()
                
            # Send STOP event
            await asyncio.sleep(1.0)
            await self._send_stop_event()
            
        except asyncio.CancelledError:
            logger.info("Timer simulation cancelled")
        except Exception as e:
            logger.error(f"Timer simulation error: {e}")
            
    async def _send_start_event(self):
        """Send timer start button press event"""
        # Create START frame (type_id=1, shot_state=5)
        frame_data = self._create_amg_frame(
            type_id=1,
            shot_state=ShotState.START.value,
            current_shot=0,
            total_shots=self._total_shots,
            current_time=0.0
        )
        
        await self._send_frame(frame_data, "TIMER_START")
        
    async def _send_timer_start(self):
        """Send timer beep/start active signal"""
        # Send T0 signal for timer start
        timestamp_ns = time.monotonic_ns()
        if self._on_t0:
            self._on_t0(timestamp_ns)
            
        logger.info("🔔 Timer start beep")
        
    async def _send_shot_event(self, shot_number: int, shot_time: float):
        """Send shot detection event"""
        # Create SHOT frame (type_id=1, shot_state=3)
        frame_data = self._create_amg_frame(
            type_id=1,
            shot_state=ShotState.ACTIVE.value,
            current_shot=shot_number,
            total_shots=self._total_shots,
            current_time=shot_time
        )
        
        await self._send_frame(frame_data, "SHOT")
        
        # Send T0 signal for shot detection
        timestamp_ns = time.monotonic_ns()
        if self._on_t0:
            self._on_t0(timestamp_ns)
            
        logger.info(f"🎯 Shot {shot_number}: {shot_time:.2f}s")
        
    async def _send_stop_event(self):
        """Send timer stop event"""
        current_time = time.time() - self._start_time if self._start_time else 0.0
        
        # Create STOP frame (type_id=1, shot_state=8)
        frame_data = self._create_amg_frame(
            type_id=1,
            shot_state=ShotState.STOPPED.value,
            current_shot=self._current_shot,
            total_shots=self._total_shots,
            current_time=current_time
        )
        
        await self._send_frame(frame_data, "TIMER_STOP")
        logger.info(f"⏹️  Timer stopped: {current_time:.2f}s total")
        
    def _create_amg_frame(
        self,
        type_id: int,
        shot_state: int,
        current_shot: int,
        total_shots: int,
        current_time: float,
        split_time: float = 0.0
    ) -> bytes:
        """Create AMG timer frame bytes"""
        # Convert times to centiseconds (big-endian 16-bit)
        current_time_cs = int(current_time * 100)
        split_time_cs = int(split_time * 100)
        
        # Create 14-byte frame
        frame = bytearray(14)
        frame[0] = type_id
        frame[1] = shot_state
        frame[2] = current_shot
        frame[3] = total_shots
        frame[4] = (current_time_cs >> 8) & 0xFF  # High byte
        frame[5] = current_time_cs & 0xFF         # Low byte
        frame[6] = (split_time_cs >> 8) & 0xFF    # High byte
        frame[7] = split_time_cs & 0xFF           # Low byte
        # Bytes 8-13 can be zeros or other timer data
        
        return bytes(frame)
        
    async def _send_frame(self, frame_data: bytes, event_type: str):
        """Send frame to callbacks"""
        # Send raw notification
        if self._on_notification:
            self._on_notification(frame_data)
            
        # Parse and send structured data
        parsed_data = parse_amg_timer_data(frame_data)
        if parsed_data and self._on_parsed_data:
            self._on_parsed_data(parsed_data)
            
        logger.debug(f"Sent {event_type}: {frame_data.hex()}")
        
    async def _simulate_single_shot(self):
        """Simulate single shot"""
        await asyncio.sleep(self.config.shot_interval_sec)
        
        shot_time = time.time() - self._start_time
        self._current_shot = 1
        await self._send_shot_event(self._current_shot, shot_time)
        
    async def _simulate_multi_shot(self):
        """Simulate multiple shots with intervals"""
        for shot_num in range(1, self._total_shots + 1):
            # Add timing variance if enabled
            interval = self.config.shot_interval_sec
            if self.config.random_timing:
                import random
                variance = random.uniform(
                    -self.config.timing_variance_sec,
                    self.config.timing_variance_sec
                )
                interval = max(0.5, interval + variance)
                
            await asyncio.sleep(interval)
            
            shot_time = time.time() - self._start_time
            self._current_shot = shot_num
            await self._send_shot_event(shot_num, shot_time)
            
    async def _simulate_rapid_fire(self):
        """Simulate rapid fire sequence"""
        rapid_interval = 0.5  # 0.5 seconds between shots
        
        for shot_num in range(1, self._total_shots + 1):
            await asyncio.sleep(rapid_interval)
            
            shot_time = time.time() - self._start_time
            self._current_shot = shot_num
            await self._send_shot_event(shot_num, shot_time)
            
    async def _simulate_precision_match(self):
        """Simulate precision shooting match"""
        # Precision shooting: 10 shots, 30-60 seconds between shots
        precision_intervals = [45, 38, 52, 41, 35, 48, 44, 39, 51, 42]
        
        for i, shot_num in enumerate(range(1, min(10, self._total_shots) + 1)):
            interval = precision_intervals[i] if i < len(precision_intervals) else 45
            await asyncio.sleep(interval)
            
            shot_time = time.time() - self._start_time
            self._current_shot = shot_num
            await self._send_shot_event(shot_num, shot_time)
            
    async def _simulate_custom_sequence(self):
        """Simulate custom timing sequence"""
        if not self.config.custom_sequence:
            logger.warning("Custom sequence not defined, using default intervals")
            await self._simulate_multi_shot()
            return
            
        for i, shot_num in enumerate(range(1, len(self.config.custom_sequence) + 1)):
            if i < len(self.config.custom_sequence):
                await asyncio.sleep(self.config.custom_sequence[i])
                
            shot_time = time.time() - self._start_time
            self._current_shot = shot_num
            await self._send_shot_event(shot_num, shot_time)


def load_simulation_config(config_path: Path) -> SimulationConfig:
    """Load simulation configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            
        return SimulationConfig(
            mode=SimulationMode(data.get("mode", "multi_shot")),
            num_shots=data.get("num_shots", 5),
            shot_interval_sec=data.get("shot_interval_sec", 2.0),
            start_delay_sec=data.get("start_delay_sec", 3.0),
            random_timing=data.get("random_timing", False),
            timing_variance_sec=data.get("timing_variance_sec", 0.5),
            custom_sequence=data.get("custom_sequence")
        )
        
    except Exception as e:
        logger.warning(f"Failed to load simulation config: {e}, using defaults")
        return SimulationConfig()


# Example usage
async def test_timer_simulator():
    """Test timer simulator"""
    config = SimulationConfig(
        mode=SimulationMode.MULTI_SHOT,
        num_shots=3,
        shot_interval_sec=1.5,
        start_delay_sec=2.0
    )
    
    simulator = AMGTimerSimulator(config=config)
    
    # Set up callbacks
    def on_parsed_data(data):
        print(f"📊 Event: {data['event_detail']}")
        
    def on_t0(timestamp_ns):
        print(f"⏰ T0 signal at {timestamp_ns}")
        
    simulator.set_parsed_data_callback(on_parsed_data)
    simulator.set_t0_callback(on_t0)
    
    # Run simulation
    await simulator.start()
    await asyncio.sleep(15)  # Let simulation run
    await simulator.stop()


if __name__ == "__main__":
    asyncio.run(test_timer_simulator())