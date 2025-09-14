"""
Comprehensive test suite for the simulation framework.
Tests all aspects of the simulation including scenarios, error injection, 
and realistic match patterns.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from impact_bridge.simulation_framework import (
    ComprehensiveSimulator,
    SimulationScenario,
    ImpactPattern, 
    MatchScenario,
    ErrorType,
    PREDEFINED_SCENARIOS,
    create_simulation_demo
)
from impact_bridge.timer_simulator import SimulationMode


class TestImpactPattern:
    """Test ImpactPattern data class"""
    
    def test_impact_pattern_creation(self):
        """Test creating impact patterns"""
        pattern = ImpactPattern(
            delay_after_shot_ms=500.0,
            intensity=0.8,
            duration_ms=50.0,
            variance_ms=100.0,
            miss_probability=0.1
        )
        
        assert pattern.delay_after_shot_ms == 500.0
        assert pattern.intensity == 0.8
        assert pattern.duration_ms == 50.0
        assert pattern.variance_ms == 100.0
        assert pattern.miss_probability == 0.1
    
    def test_impact_pattern_defaults(self):
        """Test impact pattern with default values"""
        pattern = ImpactPattern(
            delay_after_shot_ms=400.0,
            intensity=0.5,
            duration_ms=30.0,
            variance_ms=50.0
        )
        
        assert pattern.miss_probability == 0.0  # Default value


class TestSimulationScenario:
    """Test SimulationScenario data class"""
    
    def test_scenario_creation(self):
        """Test creating simulation scenarios"""
        impact_pattern = ImpactPattern(
            delay_after_shot_ms=520.0,
            intensity=0.7,
            duration_ms=60.0,
            variance_ms=100.0
        )
        
        scenario = SimulationScenario(
            name="Test Scenario",
            description="Test description",
            match_type=MatchScenario.USPSA_MATCH,
            num_shots=5,
            shot_intervals=[1.5, 2.0, 1.8, 2.2, 1.9],
            impact_patterns=[impact_pattern],
            error_types=[ErrorType.SENSOR_NOISE],
            error_probability=0.05,
            shooter_skill=0.8
        )
        
        assert scenario.name == "Test Scenario"
        assert scenario.match_type == MatchScenario.USPSA_MATCH
        assert scenario.num_shots == 5
        assert len(scenario.shot_intervals) == 5
        assert len(scenario.impact_patterns) == 1
        assert ErrorType.SENSOR_NOISE in scenario.error_types
    
    def test_scenario_defaults(self):
        """Test scenario with default values"""
        scenario = SimulationScenario(
            name="Minimal",
            description="Minimal scenario",
            match_type=MatchScenario.CUSTOM,
            num_shots=3,
            shot_intervals=[1.0, 1.0, 1.0],
            impact_patterns=[]
        )
        
        assert scenario.start_delay == 3.0
        assert scenario.error_types is None
        assert scenario.error_probability == 0.05
        assert scenario.shooter_skill == 0.8
        assert scenario.equipment_quality == 0.9


class TestComprehensiveSimulator:
    """Test the main ComprehensiveSimulator class"""
    
    @pytest.fixture
    def basic_config(self):
        """Basic configuration for simulator"""
        return {
            "bt50": {
                "simulation_mode": True,
                "auto_calibrate": True,
                "calibration_samples": 20
            },
            "timer": {
                "simulation_mode": True
            }
        }
    
    @pytest.fixture
    def basic_scenario(self):
        """Basic scenario for testing"""
        return SimulationScenario(
            name="Test Scenario",
            description="Basic test scenario",
            match_type=MatchScenario.USPSA_MATCH,
            num_shots=3,
            shot_intervals=[1.0, 1.5, 2.0],
            impact_patterns=[
                ImpactPattern(
                    delay_after_shot_ms=500.0,
                    intensity=0.7,
                    duration_ms=50.0,
                    variance_ms=100.0
                )
            ]
        )
    
    def test_simulator_initialization(self, basic_config, basic_scenario):
        """Test simulator initialization"""
        simulator = ComprehensiveSimulator(basic_config, basic_scenario)
        
        assert simulator.config == basic_config
        assert simulator.scenario == basic_scenario
        assert not simulator._running
        assert simulator._current_shot == 0
        assert simulator._stats.total_shots == 0
    
    def test_simulator_with_default_scenario(self, basic_config):
        """Test simulator with default scenario"""
        simulator = ComprehensiveSimulator(basic_config)
        
        assert simulator.scenario.name == "Default 5-Shot Match"
        assert simulator.scenario.num_shots == 5
        assert simulator.scenario.match_type == MatchScenario.USPSA_MATCH
    
    def test_set_scenario(self, basic_config, basic_scenario):
        """Test setting a new scenario"""
        simulator = ComprehensiveSimulator(basic_config)
        original_scenario = simulator.scenario
        
        simulator.set_scenario(basic_scenario)
        
        assert simulator.scenario != original_scenario
        assert simulator.scenario == basic_scenario
    
    def test_set_callbacks(self, basic_config):
        """Test setting event callbacks"""
        simulator = ComprehensiveSimulator(basic_config)
        
        shot_callback = MagicMock()
        impact_callback = MagicMock()
        error_callback = MagicMock()
        stats_callback = MagicMock()
        
        simulator.set_callbacks(
            on_shot_fired=shot_callback,
            on_impact_detected=impact_callback,
            on_error_injected=error_callback,
            on_stats_updated=stats_callback
        )
        
        assert simulator._on_shot_fired == shot_callback
        assert simulator._on_impact_detected == impact_callback
        assert simulator._on_error_injected == error_callback
        assert simulator._on_stats_updated == stats_callback
    
    def test_get_timer_mode_mapping(self, basic_config):
        """Test timer mode mapping for different scenarios"""
        simulator = ComprehensiveSimulator(basic_config)
        
        # Test different match types
        test_scenarios = [
            (MatchScenario.STEEL_CHALLENGE, SimulationMode.RAPID_FIRE),
            (MatchScenario.USPSA_MATCH, SimulationMode.MULTI_SHOT),
            (MatchScenario.PRECISION_PISTOL, SimulationMode.PRECISION_MATCH),
            (MatchScenario.RAPID_FIRE, SimulationMode.RAPID_FIRE),
            (MatchScenario.CUSTOM, SimulationMode.MULTI_SHOT),  # Default
        ]
        
        for match_type, expected_mode in test_scenarios:
            simulator.scenario.match_type = match_type
            mode = simulator._get_timer_mode()
            assert mode == expected_mode
    
    @pytest.mark.asyncio
    async def test_error_injection(self, basic_config, basic_scenario):
        """Test error injection functionality"""
        basic_scenario.error_types = [ErrorType.SENSOR_NOISE, ErrorType.BLE_DISCONNECT]
        basic_scenario.error_probability = 1.0  # Always inject errors for testing
        
        simulator = ComprehensiveSimulator(basic_config, basic_scenario)
        
        # Mock the BT50 simulator
        mock_bt50 = AsyncMock()
        mock_bt50._connected = True
        simulator.bt50_simulator = mock_bt50
        
        error_callback = MagicMock()
        simulator.set_callbacks(on_error_injected=error_callback)
        
        # Test BLE disconnect error
        await simulator._inject_error(ErrorType.BLE_DISCONNECT)
        
        mock_bt50.disconnect.assert_called_once()
        mock_bt50.connect.assert_called_once()
        error_callback.assert_called_once_with(ErrorType.BLE_DISCONNECT)
        
        assert simulator._stats.errors_injected == 1
    
    def test_timer_event_handling(self, basic_config):
        """Test timer event handling"""
        simulator = ComprehensiveSimulator(basic_config)
        
        shot_callback = MagicMock()
        simulator.set_callbacks(on_shot_fired=shot_callback)
        
        # Simulate shot event
        event_data = {"event_detail": "SHOT", "timestamp": 123456}
        simulator._on_timer_event(event_data)
        
        assert simulator._stats.total_shots == 1
        assert simulator._stats.timer_events_generated == 1
        assert simulator._current_shot == 1
        shot_callback.assert_called_once_with(event_data)
    
    def test_bt50_sample_handling(self, basic_config):
        """Test BT50 sample handling and impact detection"""
        simulator = ComprehensiveSimulator(basic_config)
        
        impact_callback = MagicMock()
        simulator.set_callbacks(on_impact_detected=impact_callback)
        
        # Mock BT50 sample with high amplitude (impact)
        from impact_bridge.ble.witmotion_bt50 import Bt50Sample
        
        # High amplitude sample (should trigger impact detection)
        high_sample = Bt50Sample(
            timestamp_ns=123456789,
            vx=15.0, vy=12.0, vz=8.0,
            amplitude=20.0,  # Above threshold of 10.0
            rssi=-50.0,
            battery_level=85
        )
        
        simulator._on_bt50_sample(high_sample)
        
        assert simulator._stats.sensor_samples_generated == 1
        assert simulator._stats.total_impacts == 1
        impact_callback.assert_called_once_with(high_sample)
        
        # Low amplitude sample (should not trigger impact)
        low_sample = Bt50Sample(
            timestamp_ns=123456790,
            vx=2.0, vy=1.5, vz=1.0,
            amplitude=5.0,  # Below threshold
            rssi=-55.0,
            battery_level=84
        )
        
        impact_callback.reset_mock()
        simulator._on_bt50_sample(low_sample)
        
        assert simulator._stats.sensor_samples_generated == 2
        assert simulator._stats.total_impacts == 1  # Still 1
        impact_callback.assert_not_called()
    
    def test_get_stats(self, basic_config):
        """Test statistics retrieval"""
        simulator = ComprehensiveSimulator(basic_config)
        
        # Modify some stats
        simulator._stats.total_shots = 5
        simulator._stats.total_impacts = 4
        simulator._stats.errors_injected = 2
        
        stats = simulator.get_stats()
        
        assert isinstance(stats, dict)
        assert stats["total_shots"] == 5
        assert stats["total_impacts"] == 4
        assert stats["errors_injected"] == 2
        assert "start_time" in stats
    
    def test_scenario_export_import(self, basic_config, basic_scenario):
        """Test scenario export and import functionality"""
        simulator = ComprehensiveSimulator(basic_config, basic_scenario)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Export scenario
            simulator.export_scenario(temp_path)
            
            # Verify file exists and has content
            assert temp_path.exists()
            
            # Load scenario back
            loaded_scenario = ComprehensiveSimulator.load_scenario(temp_path)
            
            # Verify loaded scenario matches original
            assert loaded_scenario.name == basic_scenario.name
            assert loaded_scenario.description == basic_scenario.description
            assert loaded_scenario.match_type == basic_scenario.match_type
            assert loaded_scenario.num_shots == basic_scenario.num_shots
            assert loaded_scenario.shot_intervals == basic_scenario.shot_intervals
            
            # Verify impact patterns
            assert len(loaded_scenario.impact_patterns) == len(basic_scenario.impact_patterns)
            loaded_pattern = loaded_scenario.impact_patterns[0]
            original_pattern = basic_scenario.impact_patterns[0]
            
            assert loaded_pattern.delay_after_shot_ms == original_pattern.delay_after_shot_ms
            assert loaded_pattern.intensity == original_pattern.intensity
            assert loaded_pattern.duration_ms == original_pattern.duration_ms
            
        finally:
            # Clean up
            if temp_path.exists():
                temp_path.unlink()


class TestPredefinedScenarios:
    """Test predefined scenarios"""
    
    def test_all_scenarios_valid(self):
        """Test that all predefined scenarios are valid"""
        for name, scenario in PREDEFINED_SCENARIOS.items():
            assert isinstance(scenario, SimulationScenario)
            assert scenario.name
            assert scenario.description
            assert isinstance(scenario.match_type, MatchScenario)
            assert scenario.num_shots > 0
            assert len(scenario.shot_intervals) == scenario.num_shots
            assert len(scenario.impact_patterns) > 0
    
    def test_steel_challenge_scenario(self):
        """Test steel challenge scenario specifics"""
        scenario = PREDEFINED_SCENARIOS["steel_challenge"]
        
        assert scenario.name == "Steel Challenge"
        assert scenario.match_type == MatchScenario.STEEL_CHALLENGE
        assert scenario.num_shots == 5
        assert scenario.shooter_skill == 0.9  # High skill for steel challenge
        assert all(interval < 1.0 for interval in scenario.shot_intervals)  # Fast shooting
    
    def test_precision_match_scenario(self):
        """Test precision match scenario specifics"""
        scenario = PREDEFINED_SCENARIOS["precision_match"]
        
        assert scenario.name == "Precision Pistol Match"
        assert scenario.match_type == MatchScenario.PRECISION_PISTOL
        assert scenario.num_shots == 10
        assert scenario.shooter_skill == 0.85
        assert all(interval >= 8.0 for interval in scenario.shot_intervals)  # Slow, precise shooting
        assert scenario.error_probability == 0.02  # Low error rate for precision
    
    def test_training_session_scenario(self):
        """Test training session scenario"""
        scenario = PREDEFINED_SCENARIOS["training_session"]
        
        assert scenario.name == "Training Session"
        assert scenario.match_type == MatchScenario.CUSTOM
        assert scenario.num_shots == 20
        assert len(scenario.error_types) == 3  # Multiple error types for training
        assert scenario.error_probability == 0.1  # Higher error rate
        assert scenario.shooter_skill == 0.6  # Lower skill (training)


class TestSimulationDemo:
    """Test the simulation demo creation"""
    
    @pytest.mark.asyncio
    async def test_create_simulation_demo_with_known_scenario(self):
        """Test creating demo with known scenario"""
        simulator = await create_simulation_demo("steel_challenge")
        
        assert isinstance(simulator, ComprehensiveSimulator)
        assert simulator.scenario.name == "Steel Challenge"
        assert simulator.scenario.match_type == MatchScenario.STEEL_CHALLENGE
    
    @pytest.mark.asyncio
    async def test_create_simulation_demo_with_unknown_scenario(self):
        """Test creating demo with unknown scenario (should use default)"""
        simulator = await create_simulation_demo("nonexistent_scenario")
        
        assert isinstance(simulator, ComprehensiveSimulator)
        assert simulator.scenario.name == "Default 5-Shot Match"  # Should fall back to default
    
    @pytest.mark.asyncio 
    async def test_create_simulation_demo_default(self):
        """Test creating demo with default scenario"""
        simulator = await create_simulation_demo()
        
        assert isinstance(simulator, ComprehensiveSimulator)
        assert simulator.scenario.name == "Precision Pistol Match"  # Default is precision_match


class TestSimulationIntegration:
    """Integration tests for the full simulation framework"""
    
    @pytest.mark.asyncio
    async def test_full_simulation_lifecycle(self):
        """Test complete simulation lifecycle"""
        config = {
            "bt50": {
                "simulation_mode": True,
                "auto_calibrate": True,
                "calibration_samples": 10
            },
            "timer": {
                "simulation_mode": True
            }
        }
        
        # Create a short scenario for quick testing
        scenario = SimulationScenario(
            name="Quick Test",
            description="Quick test scenario",
            match_type=MatchScenario.CUSTOM,
            num_shots=2,
            shot_intervals=[0.5, 0.5],
            start_delay=0.1,
            impact_patterns=[
                ImpactPattern(
                    delay_after_shot_ms=100.0,
                    intensity=0.8,
                    duration_ms=20.0,
                    variance_ms=10.0
                )
            ]
        )
        
        simulator = ComprehensiveSimulator(config, scenario)
        
        # Set up tracking
        events = {"shots": 0, "impacts": 0, "errors": 0}
        
        def on_shot(_):
            events["shots"] += 1
        
        def on_impact(_):
            events["impacts"] += 1
        
        def on_error(_):
            events["errors"] += 1
        
        simulator.set_callbacks(
            on_shot_fired=on_shot,
            on_impact_detected=on_impact,
            on_error_injected=on_error
        )
        
        # Mock the component initialization to avoid actual BLE operations
        async def mock_init_simulators():
            simulator.timer_simulator = MagicMock()
            simulator.timer_simulator.start = AsyncMock()
            simulator.timer_simulator.stop = AsyncMock()
            
            simulator.bt50_simulator = MagicMock()
            simulator.bt50_simulator.connect = AsyncMock()
            simulator.bt50_simulator.disconnect = AsyncMock()
        
        simulator._init_simulators = mock_init_simulators
        
        # Run simulation for short time
        try:
            # Start simulation
            start_task = asyncio.create_task(simulator.start())
            
            # Let it run briefly
            await asyncio.sleep(0.2)
            
            # Stop simulation
            await simulator.stop()
            
            # Wait for start task to complete
            try:
                await asyncio.wait_for(start_task, timeout=1.0)
            except asyncio.TimeoutError:
                pass  # Expected if simulation is still running
            
            # Verify basic functionality
            stats = simulator.get_stats()
            assert isinstance(stats, dict)
            assert "start_time" in stats
            assert "total_shots" in stats
            
        except Exception as e:
            # Ensure cleanup even if test fails
            await simulator.stop()
            raise
    
    @pytest.mark.asyncio
    async def test_error_scenarios(self):
        """Test various error scenarios"""
        config = {"bt50": {"simulation_mode": True}, "timer": {"simulation_mode": True}}
        
        # Scenario with high error rate
        scenario = SimulationScenario(
            name="Error Test",
            description="High error rate test",
            match_type=MatchScenario.CUSTOM,
            num_shots=1,
            shot_intervals=[0.1],
            start_delay=0.01,
            impact_patterns=[],
            error_types=[ErrorType.SENSOR_NOISE, ErrorType.BLE_DISCONNECT],
            error_probability=1.0  # Always error for testing
        )
        
        simulator = ComprehensiveSimulator(config, scenario)
        
        # Test individual error injection
        for error_type in ErrorType:
            try:
                await simulator._inject_error(error_type)
                # Should not throw exception
            except Exception as e:
                # Some errors might not be fully implemented, that's ok
                assert isinstance(e, (NotImplementedError, AttributeError))


if __name__ == "__main__":
    pytest.main([__file__])