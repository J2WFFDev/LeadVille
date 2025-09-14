"""
Comprehensive Simulation Framework for LeadVille Impact Bridge

This module provides a complete simulation environment for testing and demonstration,
including realistic match scenarios, configurable error injection, and comprehensive
data generation for both AMG timers and BT50 sensors.
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import math

from .timer_simulator import AMGTimerSimulator, SimulationConfig as TimerConfig, SimulationMode
from .ble.witmotion_bt50 import Bt50Client, Bt50Sample

logger = logging.getLogger(__name__)


class MatchScenario(Enum):
    """Predefined match scenarios for simulation"""
    STEEL_CHALLENGE = "steel_challenge"
    USPSA_MATCH = "uspsa_match"
    IDPA_MATCH = "idpa_match" 
    PRECISION_PISTOL = "precision_pistol"
    RAPID_FIRE = "rapid_fire"
    BULLSEYE = "bullseye"
    CUSTOM = "custom"


class ErrorType(Enum):
    """Types of errors that can be simulated"""
    BLE_DISCONNECT = "ble_disconnect"
    TIMER_MALFUNCTION = "timer_malfunction"
    SENSOR_NOISE = "sensor_noise"
    MISSED_IMPACT = "missed_impact"
    FALSE_POSITIVE = "false_positive"
    TIMING_DRIFT = "timing_drift"
    BATTERY_LOW = "battery_low"


@dataclass
class ImpactPattern:
    """Defines an impact pattern for simulation"""
    delay_after_shot_ms: float  # Delay from shot to impact
    intensity: float  # Impact intensity (0.0-1.0)
    duration_ms: float  # Impact duration
    variance_ms: float  # Timing variance
    miss_probability: float = 0.0  # Probability of missing target


@dataclass 
class SimulationScenario:
    """Complete simulation scenario configuration"""
    name: str
    description: str
    match_type: MatchScenario
    
    # Timing configuration
    num_shots: int
    shot_intervals: List[float]  # Intervals between shots (seconds)
    
    # Impact patterns
    impact_patterns: List[ImpactPattern]
    
    # Optional fields with defaults
    start_delay: float = 3.0
    error_types: Optional[List[ErrorType]] = None
    error_probability: float = 0.05  # 5% chance of errors
    
    # Performance characteristics
    shooter_skill: float = 0.8  # 0.0 (beginner) to 1.0 (expert)
    equipment_quality: float = 0.9  # Equipment reliability
    
    # Environmental factors
    temperature: float = 20.0  # Celsius
    humidity: float = 50.0  # Percent
    wind_speed: float = 0.0  # m/s


@dataclass
class SimulationStats:
    """Statistics collected during simulation"""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_shots: int = 0
    total_impacts: int = 0
    missed_shots: int = 0
    false_positives: int = 0
    errors_injected: int = 0
    avg_shot_to_impact_ms: float = 0.0
    sensor_samples_generated: int = 0
    timer_events_generated: int = 0


class ComprehensiveSimulator:
    """Main simulation framework coordinating all components"""
    
    def __init__(
        self, 
        config: Dict[str, Any],
        scenario: Optional[SimulationScenario] = None
    ):
        self.config = config
        self.scenario = scenario or self._create_default_scenario()
        
        # Component simulators
        self.timer_simulator: Optional[AMGTimerSimulator] = None
        self.bt50_simulator: Optional[Bt50Client] = None
        
        # Simulation state
        self._running = False
        self._stats = SimulationStats(start_time=datetime.now())
        self._current_shot = 0
        self._tasks: List[asyncio.Task] = []
        
        # Event callbacks
        self._on_shot_fired: Optional[Callable] = None
        self._on_impact_detected: Optional[Callable] = None
        self._on_error_injected: Optional[Callable] = None
        self._on_stats_updated: Optional[Callable] = None
        
        logger.info(f"Comprehensive simulator initialized with scenario: {self.scenario.name}")
    
    def _create_default_scenario(self) -> SimulationScenario:
        """Create a default simulation scenario"""
        return SimulationScenario(
            name="Default 5-Shot Match",
            description="Basic 5-shot simulation with realistic timing",
            match_type=MatchScenario.USPSA_MATCH,
            num_shots=5,
            shot_intervals=[2.0, 1.5, 2.5, 1.8, 2.2],  # Varied intervals
            impact_patterns=[
                ImpactPattern(
                    delay_after_shot_ms=520.0,
                    intensity=0.7,
                    duration_ms=50.0,
                    variance_ms=100.0,
                    miss_probability=0.1
                )
            ],
            error_types=[ErrorType.SENSOR_NOISE, ErrorType.TIMING_DRIFT],
            shooter_skill=0.7
        )
    
    def set_scenario(self, scenario: SimulationScenario):
        """Set the simulation scenario"""
        self.scenario = scenario
        logger.info(f"Scenario updated: {scenario.name}")
    
    def set_callbacks(
        self,
        on_shot_fired: Optional[Callable] = None,
        on_impact_detected: Optional[Callable] = None,
        on_error_injected: Optional[Callable] = None,
        on_stats_updated: Optional[Callable] = None
    ):
        """Set event callbacks for simulation monitoring"""
        self._on_shot_fired = on_shot_fired
        self._on_impact_detected = on_impact_detected
        self._on_error_injected = on_error_injected
        self._on_stats_updated = on_stats_updated
    
    async def start(self) -> None:
        """Start the comprehensive simulation"""
        if self._running:
            logger.warning("Simulation already running")
            return
            
        self._running = True
        self._stats = SimulationStats(start_time=datetime.now())
        self._current_shot = 0
        
        logger.info(f"Starting comprehensive simulation: {self.scenario.name}")
        
        try:
            # Initialize component simulators
            await self._init_simulators()
            
            # Start background monitoring
            monitor_task = asyncio.create_task(self._monitor_simulation())
            self._tasks.append(monitor_task)
            
            # Execute the match scenario
            await self._execute_scenario()
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def stop(self) -> None:
        """Stop the simulation"""
        if not self._running:
            return
            
        logger.info("Stopping comprehensive simulation")
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        await self._cleanup()
        
        # Finalize stats
        self._stats.end_time = datetime.now()
        logger.info(f"Simulation completed: {self._stats.total_shots} shots, {self._stats.total_impacts} impacts")
    
    async def _init_simulators(self) -> None:
        """Initialize component simulators"""
        # Initialize timer simulator with scenario configuration
        timer_config = TimerConfig(
            mode=self._get_timer_mode(),
            num_shots=self.scenario.num_shots,
            shot_interval_sec=2.0,  # Base interval, will be overridden
            start_delay_sec=self.scenario.start_delay,
            random_timing=True,
            timing_variance_sec=0.5
        )
        
        self.timer_simulator = AMGTimerSimulator(config=timer_config)
        
        # Set up timer callbacks
        self.timer_simulator.set_parsed_data_callback(self._on_timer_event)
        
        # Initialize BT50 simulator
        bt50_config = self.config.get("bt50", {})
        bt50_config["simulation_mode"] = True
        
        self.bt50_simulator = Bt50Client(
            device_address="SIM:F8:FE:92:31:12:E3",
            config=bt50_config
        )
        
        # Set up BT50 callbacks
        self.bt50_simulator.set_sample_callback(self._on_bt50_sample)
        
        logger.info("Component simulators initialized")
    
    def _get_timer_mode(self) -> SimulationMode:
        """Get timer simulation mode based on scenario"""
        mode_mapping = {
            MatchScenario.STEEL_CHALLENGE: SimulationMode.RAPID_FIRE,
            MatchScenario.USPSA_MATCH: SimulationMode.MULTI_SHOT,
            MatchScenario.PRECISION_PISTOL: SimulationMode.PRECISION_MATCH,
            MatchScenario.RAPID_FIRE: SimulationMode.RAPID_FIRE,
        }
        return mode_mapping.get(self.scenario.match_type, SimulationMode.MULTI_SHOT)
    
    async def _execute_scenario(self) -> None:
        """Execute the main simulation scenario"""
        logger.info(f"Executing scenario: {self.scenario.name}")
        
        # Start timer simulator
        await self.timer_simulator.start()
        
        # Start BT50 simulator  
        await self.bt50_simulator.connect()
        
        # Wait for scenario completion
        scenario_duration = (
            self.scenario.start_delay + 
            sum(self.scenario.shot_intervals) + 
            10.0  # Buffer time
        )
        
        await asyncio.sleep(scenario_duration)
    
    async def _monitor_simulation(self) -> None:
        """Background monitoring and statistics collection"""
        while self._running:
            try:
                # Update statistics
                await self._update_stats()
                
                # Inject errors if configured
                await self._maybe_inject_error()
                
                # Call stats callback
                if self._on_stats_updated:
                    self._on_stats_updated(self._stats)
                
                await asyncio.sleep(1.0)  # Update every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_stats(self) -> None:
        """Update simulation statistics"""
        # This would be populated by callbacks from actual events
        pass
    
    async def _maybe_inject_error(self) -> None:
        """Randomly inject errors based on scenario configuration"""
        if not self.scenario.error_types:
            return
            
        if random.random() < self.scenario.error_probability:
            error_type = random.choice(self.scenario.error_types)
            await self._inject_error(error_type)
    
    async def _inject_error(self, error_type: ErrorType) -> None:
        """Inject a specific type of error"""
        logger.info(f"Injecting error: {error_type.value}")
        self._stats.errors_injected += 1
        
        if error_type == ErrorType.BLE_DISCONNECT:
            # Simulate BLE disconnection
            if self.bt50_simulator and self.bt50_simulator._connected:
                await self.bt50_simulator.disconnect()
                # Reconnect after delay
                await asyncio.sleep(2.0)
                await self.bt50_simulator.connect()
                
        elif error_type == ErrorType.SENSOR_NOISE:
            # Increase sensor noise temporarily
            pass  # Would modify BT50 simulator parameters
            
        elif error_type == ErrorType.TIMING_DRIFT:
            # Introduce timing drift
            pass  # Would modify timer parameters
        
        if self._on_error_injected:
            self._on_error_injected(error_type)
    
    def _on_timer_event(self, event_data: Dict[str, Any]) -> None:
        """Handle timer events"""
        if event_data.get("event_detail") == "SHOT":
            self._stats.total_shots += 1
            self._stats.timer_events_generated += 1
            self._current_shot += 1
            
            if self._on_shot_fired:
                self._on_shot_fired(event_data)
            
            # Schedule corresponding impact (only if running)
            if self._running:
                try:
                    asyncio.create_task(self._simulate_impact())
                except RuntimeError:
                    # No event loop running (e.g., during testing)
                    pass
    
    def _on_bt50_sample(self, sample: Bt50Sample) -> None:
        """Handle BT50 sensor samples"""
        self._stats.sensor_samples_generated += 1
        
        # Detect impacts based on amplitude
        if sample.amplitude > 10.0:  # Impact threshold
            self._stats.total_impacts += 1
            
            if self._on_impact_detected:
                self._on_impact_detected(sample)
    
    async def _simulate_impact(self) -> None:
        """Simulate realistic impact after shot"""
        if not self.scenario.impact_patterns:
            return
            
        pattern = random.choice(self.scenario.impact_patterns)
        
        # Check for miss
        if random.random() < pattern.miss_probability:
            self._stats.missed_shots += 1
            return
        
        # Calculate delay with variance
        delay_ms = pattern.delay_after_shot_ms + random.uniform(
            -pattern.variance_ms, pattern.variance_ms
        )
        
        await asyncio.sleep(delay_ms / 1000.0)
        
        # Generate impact in BT50 simulator
        # This would require modifying the BT50 simulator to accept external impacts
        # For now, we rely on its built-in random impact generation
    
    async def _cleanup(self) -> None:
        """Cleanup simulation resources"""
        if self.timer_simulator:
            await self.timer_simulator.stop()
        
        if self.bt50_simulator:
            await self.bt50_simulator.disconnect()
        
        logger.info("Simulation cleanup completed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current simulation statistics"""
        return asdict(self._stats)
    
    def export_scenario(self, path: Path) -> None:
        """Export current scenario to JSON file"""
        scenario_data = asdict(self.scenario)
        # Convert enums to strings for JSON serialization
        scenario_data["match_type"] = self.scenario.match_type.value
        if self.scenario.error_types:
            scenario_data["error_types"] = [e.value for e in self.scenario.error_types]
        
        with open(path, 'w') as f:
            json.dump(scenario_data, f, indent=2)
        
        logger.info(f"Scenario exported to {path}")
    
    @classmethod
    def load_scenario(cls, path: Path) -> SimulationScenario:
        """Load scenario from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Convert strings back to enums
        data["match_type"] = MatchScenario(data["match_type"])
        if "error_types" in data and data["error_types"] is not None:
            data["error_types"] = [ErrorType(e) for e in data["error_types"]]
        
        # Convert impact patterns
        if "impact_patterns" in data:
            data["impact_patterns"] = [
                ImpactPattern(**pattern) for pattern in data["impact_patterns"]
            ]
        
        return SimulationScenario(**data)


# Predefined scenarios for common use cases
PREDEFINED_SCENARIOS = {
    "steel_challenge": SimulationScenario(
        name="Steel Challenge",
        description="Fast-paced steel target shooting",
        match_type=MatchScenario.STEEL_CHALLENGE,
        num_shots=5,
        shot_intervals=[0.8, 0.6, 0.9, 0.7, 0.8],
        impact_patterns=[
            ImpactPattern(delay_after_shot_ms=300.0, intensity=0.9, duration_ms=30.0, variance_ms=50.0)
        ],
        shooter_skill=0.9
    ),
    
    "precision_match": SimulationScenario(
        name="Precision Pistol Match",
        description="Slow-fire precision shooting",
        match_type=MatchScenario.PRECISION_PISTOL,
        num_shots=10,
        shot_intervals=[8.0] * 10,
        impact_patterns=[
            ImpactPattern(delay_after_shot_ms=520.0, intensity=0.6, duration_ms=80.0, variance_ms=20.0)
        ],
        shooter_skill=0.85,
        error_probability=0.02
    ),
    
    "training_session": SimulationScenario(
        name="Training Session",
        description="Mixed training with errors for testing",
        match_type=MatchScenario.CUSTOM,
        num_shots=20,
        shot_intervals=[random.uniform(1.0, 4.0) for _ in range(20)],
        impact_patterns=[
            ImpactPattern(delay_after_shot_ms=500.0, intensity=0.7, duration_ms=60.0, variance_ms=150.0, miss_probability=0.15)
        ],
        error_types=[ErrorType.BLE_DISCONNECT, ErrorType.SENSOR_NOISE, ErrorType.FALSE_POSITIVE],
        error_probability=0.1,
        shooter_skill=0.6
    )
}


async def create_simulation_demo(scenario_name: str = "precision_match") -> ComprehensiveSimulator:
    """Create a demo simulation with predefined scenario"""
    config = {
        "bt50": {
            "simulation_mode": True,
            "auto_calibrate": True,
            "calibration_samples": 20
        },
        "timer": {
            "simulation_mode": True
        }
    }
    
    scenario = PREDEFINED_SCENARIOS.get(scenario_name)
    if not scenario:
        logger.warning(f"Unknown scenario '{scenario_name}', using default")
        scenario = None
    
    simulator = ComprehensiveSimulator(config, scenario)
    return simulator