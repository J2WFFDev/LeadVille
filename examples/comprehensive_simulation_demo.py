#!/usr/bin/env python3
"""
Comprehensive Simulation Demo for LeadVille Impact Bridge

This demo showcases the complete simulation framework including:
- Multiple predefined scenarios (Steel Challenge, USPSA, Precision, etc.)
- Real-time statistics and monitoring
- Error injection and testing
- Interactive scenario configuration
- Performance benchmarking
- Export/import of scenarios
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SimulationDemo:
    """Interactive simulation demo with comprehensive features"""
    
    def __init__(self):
        self.simulator: Optional[ComprehensiveSimulator] = None
        self.stats_history = []
        self.demo_config = {
            "bt50": {
                "simulation_mode": True,
                "auto_calibrate": True,
                "calibration_samples": 20,
                "health_monitoring": {
                    "enabled": True,
                    "check_interval_sec": 5.0
                }
            },
            "timer": {
                "simulation_mode": True,
                "frame_validation": True
            },
            "logging": {
                "console_level": "INFO",
                "file_level": "DEBUG",
                "enable_raw_data_logging": True
            }
        }
    
    async def main_menu(self):
        """Display main menu and handle user input"""
        while True:
            print("\n" + "="*60)
            print("🎯 LeadVille Comprehensive Simulation Demo")
            print("="*60)
            print("1. Quick Demo - Steel Challenge")
            print("2. Precision Match Simulation") 
            print("3. Training Session with Errors")
            print("4. Custom Scenario Builder")
            print("5. Performance Benchmark")
            print("6. Scenario Import/Export")
            print("7. Real-time Statistics Monitor")
            print("8. Error Injection Testing")
            print("9. List All Predefined Scenarios")
            print("0. Exit")
            print("-"*60)
            
            choice = input("Enter your choice (0-9): ").strip()
            
            try:
                if choice == "0":
                    print("👋 Exiting simulation demo. Goodbye!")
                    break
                elif choice == "1":
                    await self.quick_demo()
                elif choice == "2":
                    await self.precision_match_demo()
                elif choice == "3":
                    await self.training_session_demo()
                elif choice == "4":
                    await self.custom_scenario_builder()
                elif choice == "5":
                    await self.performance_benchmark()
                elif choice == "6":
                    await self.scenario_import_export()
                elif choice == "7":
                    await self.statistics_monitor()
                elif choice == "8":
                    await self.error_injection_demo()
                elif choice == "9":
                    self.list_predefined_scenarios()
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n⚠️ Operation cancelled by user.")
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.exception("Demo error")
    
    async def quick_demo(self):
        """Quick steel challenge demo"""
        print("\n🏃 Quick Demo - Steel Challenge")
        print("-" * 40)
        
        scenario = PREDEFINED_SCENARIOS["steel_challenge"]
        print(f"Scenario: {scenario.name}")
        print(f"Description: {scenario.description}")
        print(f"Shots: {scenario.num_shots}")
        print(f"Estimated Duration: {sum(scenario.shot_intervals) + scenario.start_delay:.1f} seconds")
        
        input("\nPress Enter to start simulation...")
        
        simulator = ComprehensiveSimulator(self.demo_config, scenario)
        
        # Set up event monitoring
        stats = {"shots": 0, "impacts": 0, "errors": 0}
        
        def on_shot(event_data):
            stats["shots"] += 1
            print(f"💥 Shot #{stats['shots']} fired at {event_data.get('timestamp', 'unknown')}")
        
        def on_impact(sample):
            stats["impacts"] += 1
            print(f"🎯 Impact #{stats['impacts']} detected - Amplitude: {sample.amplitude:.1f}")
        
        def on_error(error_type):
            stats["errors"] += 1
            print(f"⚠️ Error injected: {error_type.value}")
        
        simulator.set_callbacks(
            on_shot_fired=on_shot,
            on_impact_detected=on_impact,
            on_error_injected=on_error
        )
        
        try:
            print("\n🚀 Starting steel challenge simulation...")
            start_task = asyncio.create_task(simulator.start())
            
            # Monitor for a reasonable duration
            await asyncio.sleep(10.0)
            
            await simulator.stop()
            
            try:
                await asyncio.wait_for(start_task, timeout=2.0)
            except asyncio.TimeoutError:
                pass
            
            # Display results
            final_stats = simulator.get_stats()
            print("\n📊 Simulation Results:")
            print(f"   Total Shots: {final_stats['total_shots']}")
            print(f"   Total Impacts: {final_stats['total_impacts']}")
            print(f"   Errors Injected: {final_stats['errors_injected']}")
            print(f"   Sensor Samples: {final_stats['sensor_samples_generated']}")
            
        except Exception as e:
            print(f"❌ Simulation error: {e}")
            if simulator:
                await simulator.stop()
    
    async def precision_match_demo(self):
        """Precision pistol match demonstration"""
        print("\n🎯 Precision Match Simulation")
        print("-" * 40)
        
        scenario = PREDEFINED_SCENARIOS["precision_match"]
        
        # Show scenario details
        print(f"Match Type: {scenario.match_type.value.replace('_', ' ').title()}")
        print(f"Number of Shots: {scenario.num_shots}")
        print(f"Shot Intervals: {scenario.shot_intervals[0]:.1f}s (consistent)")
        print(f"Shooter Skill Level: {scenario.shooter_skill * 100:.0f}%")
        print(f"Error Rate: {scenario.error_probability * 100:.1f}%")
        
        # Ask for modifications
        modify = input("\nModify parameters? (y/n): ").lower().startswith('y')
        
        if modify:
            try:
                num_shots = int(input(f"Number of shots [{scenario.num_shots}]: ") or scenario.num_shots)
                shot_interval = float(input(f"Shot interval [{scenario.shot_intervals[0]:.1f}s]: ") or scenario.shot_intervals[0])
                skill_level = float(input(f"Skill level (0.0-1.0) [{scenario.shooter_skill:.1f}]: ") or scenario.shooter_skill)
                
                # Create modified scenario
                modified_scenario = SimulationScenario(
                    name=f"Custom {scenario.name}",
                    description=f"Modified precision match - {num_shots} shots",
                    match_type=scenario.match_type,
                    num_shots=num_shots,
                    shot_intervals=[shot_interval] * num_shots,
                    impact_patterns=scenario.impact_patterns,
                    shooter_skill=skill_level,
                    error_probability=scenario.error_probability
                )
                
                scenario = modified_scenario
                
            except ValueError:
                print("Invalid input, using default values.")
        
        input("\nPress Enter to start precision match...")
        
        await self._run_detailed_simulation(scenario)
    
    async def training_session_demo(self):
        """Training session with error injection"""
        print("\n📚 Training Session with Error Injection")
        print("-" * 45)
        
        scenario = PREDEFINED_SCENARIOS["training_session"]
        
        print(f"Training Scenario: {scenario.name}")
        print(f"Number of Shots: {scenario.num_shots}")
        print(f"Error Types: {[e.value for e in scenario.error_types]}")
        print(f"Error Probability: {scenario.error_probability * 100:.0f}%")
        print(f"Miss Probability: {scenario.impact_patterns[0].miss_probability * 100:.0f}%")
        
        print("\n🎓 This training session will demonstrate:")
        print("   • Random shot intervals (realistic training)")
        print("   • Equipment malfunctions and errors")
        print("   • Missing targets occasionally")
        print("   • BLE disconnection recovery")
        print("   • Sensor noise and false positives")
        
        input("\nPress Enter to start training session...")
        
        await self._run_detailed_simulation(scenario)
    
    async def custom_scenario_builder(self):
        """Interactive custom scenario builder"""
        print("\n🔧 Custom Scenario Builder")
        print("-" * 30)
        
        try:
            name = input("Scenario name: ").strip() or "Custom Scenario"
            description = input("Description: ").strip() or "User-created scenario"
            
            # Match type selection
            print("\nMatch Types:")
            for i, match_type in enumerate(MatchScenario, 1):
                print(f"  {i}. {match_type.value.replace('_', ' ').title()}")
            
            match_choice = int(input("Select match type (1-7): ") or "2") - 1
            match_type = list(MatchScenario)[match_choice]
            
            # Basic parameters
            num_shots = int(input("Number of shots [5]: ") or "5")
            shot_interval = float(input("Average shot interval (seconds) [2.0]: ") or "2.0")
            start_delay = float(input("Start delay (seconds) [3.0]: ") or "3.0")
            
            # Impact configuration
            impact_delay = float(input("Shot-to-impact delay (ms) [520]: ") or "520")
            impact_variance = float(input("Timing variance (ms) [100]: ") or "100")
            miss_probability = float(input("Miss probability (0.0-1.0) [0.1]: ") or "0.1")
            
            # Error configuration
            enable_errors = input("Enable error injection? (y/n) [n]: ").lower().startswith('y')
            error_types = []
            error_probability = 0.0
            
            if enable_errors:
                print("\nAvailable Error Types:")
                for i, error_type in enumerate(ErrorType, 1):
                    print(f"  {i}. {error_type.value.replace('_', ' ').title()}")
                
                error_choices = input("Select error types (comma-separated numbers) [1,2]: ").strip()
                if error_choices:
                    try:
                        indices = [int(x.strip()) - 1 for x in error_choices.split(',')]
                        error_types = [list(ErrorType)[i] for i in indices if 0 <= i < len(ErrorType)]
                    except:
                        error_types = [ErrorType.SENSOR_NOISE, ErrorType.BLE_DISCONNECT]
                
                error_probability = float(input("Error probability (0.0-1.0) [0.05]: ") or "0.05")
            
            # Create scenario
            impact_pattern = ImpactPattern(
                delay_after_shot_ms=impact_delay,
                intensity=0.7,
                duration_ms=50.0,
                variance_ms=impact_variance,
                miss_probability=miss_probability
            )
            
            scenario = SimulationScenario(
                name=name,
                description=description,
                match_type=match_type,
                num_shots=num_shots,
                shot_intervals=[shot_interval] * num_shots,
                start_delay=start_delay,
                impact_patterns=[impact_pattern],
                error_types=error_types if error_types else None,
                error_probability=error_probability
            )
            
            print(f"\n✅ Custom scenario '{name}' created!")
            
            # Option to save scenario
            save_scenario = input("Save scenario to file? (y/n) [n]: ").lower().startswith('y')
            if save_scenario:
                filename = input("Filename [custom_scenario.json]: ").strip() or "custom_scenario.json"
                
                # Create scenarios directory if it doesn't exist
                scenarios_dir = Path("scenarios")
                scenarios_dir.mkdir(exist_ok=True)
                
                file_path = scenarios_dir / filename
                
                # Export scenario
                simulator = ComprehensiveSimulator(self.demo_config, scenario)
                simulator.export_scenario(file_path)
                print(f"📁 Scenario saved to {file_path}")
            
            # Run the custom scenario
            run_now = input("Run scenario now? (y/n) [y]: ").lower()
            if not run_now.startswith('n'):
                await self._run_detailed_simulation(scenario)
                
        except (ValueError, IndexError) as e:
            print(f"❌ Invalid input: {e}")
        except Exception as e:
            print(f"❌ Error creating scenario: {e}")
    
    async def performance_benchmark(self):
        """Performance benchmarking of simulation framework"""
        print("\n⚡ Performance Benchmark")
        print("-" * 25)
        
        scenarios_to_test = [
            ("steel_challenge", "Steel Challenge (Fast)"),
            ("precision_match", "Precision Match (Slow)"),
            ("training_session", "Training (High Error Rate)")
        ]
        
        results = []
        
        for scenario_key, display_name in scenarios_to_test:
            print(f"\n🧪 Benchmarking: {display_name}")
            
            scenario = PREDEFINED_SCENARIOS[scenario_key]
            # Reduce duration for benchmarking
            short_scenario = SimulationScenario(
                name=f"Benchmark {scenario.name}",
                description="Short version for benchmarking",
                match_type=scenario.match_type,
                num_shots=5,  # Fixed number for consistency
                shot_intervals=[0.5] * 5,  # Fast intervals
                start_delay=0.1,  # Minimal delay
                impact_patterns=scenario.impact_patterns,
                error_types=scenario.error_types,
                error_probability=scenario.error_probability / 2  # Reduce errors for cleaner benchmark
            )
            
            simulator = ComprehensiveSimulator(self.demo_config, short_scenario)
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                start_task = asyncio.create_task(simulator.start())
                await asyncio.sleep(3.0)  # Short run
                await simulator.stop()
                
                try:
                    await asyncio.wait_for(start_task, timeout=1.0)
                except asyncio.TimeoutError:
                    pass
                
                end_time = asyncio.get_event_loop().time()
                
                stats = simulator.get_stats()
                
                benchmark_result = {
                    "scenario": display_name,
                    "duration_sec": end_time - start_time,
                    "shots_fired": stats["total_shots"],
                    "impacts_detected": stats["total_impacts"],
                    "sensor_samples": stats["sensor_samples_generated"],
                    "timer_events": stats["timer_events_generated"],
                    "errors_injected": stats["errors_injected"]
                }
                
                results.append(benchmark_result)
                
                print(f"   ⏱️ Duration: {benchmark_result['duration_sec']:.2f}s")
                print(f"   🎯 Events: {benchmark_result['shots_fired']} shots, {benchmark_result['impacts_detected']} impacts")
                print(f"   📊 Samples: {benchmark_result['sensor_samples']}")
                
            except Exception as e:
                print(f"   ❌ Benchmark failed: {e}")
                if simulator:
                    await simulator.stop()
        
        # Display benchmark summary
        print(f"\n📈 Benchmark Summary")
        print("-" * 20)
        for result in results:
            efficiency = result["sensor_samples"] / result["duration_sec"] if result["duration_sec"] > 0 else 0
            print(f"{result['scenario']:25} | {efficiency:8.0f} samples/sec | {result['shots_fired']} shots")
    
    async def scenario_import_export(self):
        """Demonstrate scenario import/export functionality"""
        print("\n📁 Scenario Import/Export")
        print("-" * 30)
        
        scenarios_dir = Path("scenarios")
        scenarios_dir.mkdir(exist_ok=True)
        
        print("1. Export predefined scenario")
        print("2. Import scenario from file") 
        print("3. List saved scenarios")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            # Export predefined scenario
            print("\nPredefined Scenarios:")
            scenario_names = list(PREDEFINED_SCENARIOS.keys())
            for i, name in enumerate(scenario_names, 1):
                print(f"  {i}. {name}")
            
            try:
                scenario_index = int(input("Select scenario to export (number): ")) - 1
                scenario_key = scenario_names[scenario_index]
                scenario = PREDEFINED_SCENARIOS[scenario_key]
                
                filename = input(f"Filename [{scenario_key}.json]: ").strip() or f"{scenario_key}.json"
                file_path = scenarios_dir / filename
                
                # Create temporary simulator to use export function
                simulator = ComprehensiveSimulator(self.demo_config, scenario)
                simulator.export_scenario(file_path)
                
                print(f"✅ Exported '{scenario.name}' to {file_path}")
                
            except (ValueError, IndexError):
                print("❌ Invalid selection")
        
        elif choice == "2":
            # Import scenario from file
            json_files = list(scenarios_dir.glob("*.json"))
            
            if not json_files:
                print("No scenario files found in scenarios/ directory")
                return
            
            print("\nSaved Scenarios:")
            for i, file_path in enumerate(json_files, 1):
                print(f"  {i}. {file_path.name}")
            
            try:
                file_index = int(input("Select file to import (number): ")) - 1
                file_path = json_files[file_index]
                
                scenario = ComprehensiveSimulator.load_scenario(file_path)
                print(f"✅ Loaded scenario: {scenario.name}")
                print(f"   Description: {scenario.description}")
                print(f"   Shots: {scenario.num_shots}")
                
                run_imported = input("Run imported scenario? (y/n) [n]: ").lower().startswith('y')
                if run_imported:
                    await self._run_detailed_simulation(scenario)
                    
            except (ValueError, IndexError):
                print("❌ Invalid selection")
            except Exception as e:
                print(f"❌ Error loading scenario: {e}")
        
        elif choice == "3":
            # List saved scenarios
            json_files = list(scenarios_dir.glob("*.json"))
            
            if not json_files:
                print("No saved scenarios found")
                return
            
            print("\n📋 Saved Scenarios:")
            for file_path in json_files:
                try:
                    scenario = ComprehensiveSimulator.load_scenario(file_path)
                    print(f"   📄 {file_path.name}")
                    print(f"      Name: {scenario.name}")
                    print(f"      Type: {scenario.match_type.value}")
                    print(f"      Shots: {scenario.num_shots}")
                    print()
                except Exception as e:
                    print(f"   ❌ {file_path.name} (Error: {e})")
    
    async def statistics_monitor(self):
        """Real-time statistics monitoring"""
        print("\n📊 Real-time Statistics Monitor")
        print("-" * 35)
        
        scenario = PREDEFINED_SCENARIOS["precision_match"]
        
        # Modify for longer monitoring
        extended_scenario = SimulationScenario(
            name="Extended Monitoring Test",
            description="Long-running scenario for statistics monitoring",
            match_type=scenario.match_type,
            num_shots=20,
            shot_intervals=[3.0] * 20,  # 3-second intervals
            impact_patterns=scenario.impact_patterns,
            error_types=[ErrorType.SENSOR_NOISE, ErrorType.BLE_DISCONNECT],
            error_probability=0.1
        )
        
        simulator = ComprehensiveSimulator(self.demo_config, extended_scenario)
        
        print(f"Starting extended simulation: {extended_scenario.name}")
        print("Statistics will be displayed every 2 seconds")
        print("Press Ctrl+C to stop monitoring\n")
        
        stats_update_count = 0
        
        def on_stats_update(stats):
            nonlocal stats_update_count
            stats_update_count += 1
            
            if stats_update_count % 2 == 0:  # Update every 2 seconds (monitor runs every 1 second)
                print(f"\r🔄 Statistics Update #{stats_update_count//2}")
                print(f"   Shots Fired: {stats['total_shots']:3d} | Impacts: {stats['total_impacts']:3d} | Samples: {stats['sensor_samples_generated']:6d}")
                print(f"   Errors: {stats['errors_injected']:2d} | Timer Events: {stats['timer_events_generated']:3d}")
                
                if stats['total_shots'] > 0:
                    accuracy = (stats['total_impacts'] / stats['total_shots']) * 100
                    print(f"   Accuracy: {accuracy:5.1f}%")
                
                print("-" * 60)
        
        simulator.set_callbacks(on_stats_updated=on_stats_update)
        
        try:
            start_task = asyncio.create_task(simulator.start())
            
            # Monitor for longer duration
            await asyncio.sleep(30.0)
            
            await simulator.stop()
            
            try:
                await asyncio.wait_for(start_task, timeout=2.0)
            except asyncio.TimeoutError:
                pass
            
            print("\n📈 Final Statistics:")
            final_stats = simulator.get_stats()
            for key, value in final_stats.items():
                if isinstance(value, (int, float)):
                    print(f"   {key.replace('_', ' ').title()}: {value}")
            
        except KeyboardInterrupt:
            print("\n⚠️ Monitoring stopped by user")
            await simulator.stop()
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            if simulator:
                await simulator.stop()
    
    async def error_injection_demo(self):
        """Error injection testing demonstration"""
        print("\n⚠️ Error Injection Testing")
        print("-" * 25)
        
        print("Available Error Types:")
        for i, error_type in enumerate(ErrorType, 1):
            print(f"  {i}. {error_type.value.replace('_', ' ').title()}")
        
        print("  0. Test All Error Types")
        
        try:
            choice = int(input("Select error type to test (0-7): ") or "0")
            
            if choice == 0:
                error_types_to_test = list(ErrorType)
            else:
                error_types_to_test = [list(ErrorType)[choice - 1]]
            
            # Create simple scenario for error testing
            test_scenario = SimulationScenario(
                name="Error Injection Test",
                description="Testing error injection capabilities",
                match_type=MatchScenario.CUSTOM,
                num_shots=10,
                shot_intervals=[1.0] * 10,
                start_delay=0.5,
                impact_patterns=[
                    ImpactPattern(
                        delay_after_shot_ms=200.0,
                        intensity=0.8,
                        duration_ms=30.0,
                        variance_ms=50.0
                    )
                ],
                error_types=error_types_to_test,
                error_probability=0.3  # High error rate for testing
            )
            
            simulator = ComprehensiveSimulator(self.demo_config, test_scenario)
            
            errors_detected = []
            
            def on_error_injected(error_type):
                errors_detected.append(error_type)
                print(f"🚨 Error Injected: {error_type.value.replace('_', ' ').title()}")
            
            simulator.set_callbacks(on_error_injected=on_error_injected)
            
            print(f"\n🧪 Testing {len(error_types_to_test)} error type(s)")
            print("Watch for error injection messages...")
            
            start_task = asyncio.create_task(simulator.start())
            
            # Run for a reasonable duration to see errors
            await asyncio.sleep(8.0)
            
            await simulator.stop()
            
            try:
                await asyncio.wait_for(start_task, timeout=2.0)
            except asyncio.TimeoutError:
                pass
            
            print(f"\n📋 Error Injection Results:")
            print(f"   Total Errors Injected: {len(errors_detected)}")
            
            if errors_detected:
                error_counts = {}
                for error in errors_detected:
                    error_counts[error] = error_counts.get(error, 0) + 1
                
                for error_type, count in error_counts.items():
                    print(f"   {error_type.value.replace('_', ' ').title()}: {count}")
            else:
                print("   No errors were injected (may be due to randomness)")
            
        except (ValueError, IndexError):
            print("❌ Invalid selection")
        except Exception as e:
            print(f"❌ Error testing failed: {e}")
    
    def list_predefined_scenarios(self):
        """List all predefined scenarios with details"""
        print("\n📋 Predefined Scenarios")
        print("=" * 25)
        
        for key, scenario in PREDEFINED_SCENARIOS.items():
            print(f"\n🎯 {scenario.name}")
            print(f"   Key: {key}")
            print(f"   Type: {scenario.match_type.value.replace('_', ' ').title()}")
            print(f"   Shots: {scenario.num_shots}")
            print(f"   Duration: ~{sum(scenario.shot_intervals) + scenario.start_delay:.1f}s")
            print(f"   Skill Level: {scenario.shooter_skill * 100:.0f}%")
            
            if scenario.error_types:
                error_names = [e.value.replace('_', ' ').title() for e in scenario.error_types]
                print(f"   Errors: {', '.join(error_names)} ({scenario.error_probability*100:.1f}%)")
            
            print(f"   Description: {scenario.description}")
    
    async def _run_detailed_simulation(self, scenario: SimulationScenario):
        """Run a simulation with detailed monitoring and feedback"""
        print(f"\n🚀 Starting: {scenario.name}")
        print("=" * 50)
        
        simulator = ComprehensiveSimulator(self.demo_config, scenario)
        
        # Event tracking
        events = {
            "shots": [],
            "impacts": [],
            "errors": []
        }
        
        def on_shot_fired(event_data):
            events["shots"].append(event_data)
            shot_num = len(events["shots"])
            print(f"💥 Shot #{shot_num} fired")
        
        def on_impact_detected(sample):
            events["impacts"].append(sample)
            impact_num = len(events["impacts"])
            print(f"🎯 Impact #{impact_num} detected (Amplitude: {sample.amplitude:.1f})")
        
        def on_error_injected(error_type):
            events["errors"].append(error_type)
            print(f"⚠️ Error: {error_type.value.replace('_', ' ').title()}")
        
        def on_stats_updated(stats):
            # Periodic status updates (less frequent to avoid spam)
            pass
        
        simulator.set_callbacks(
            on_shot_fired=on_shot_fired,
            on_impact_detected=on_impact_detected,
            on_error_injected=on_error_injected,
            on_stats_updated=on_stats_updated
        )
        
        try:
            start_task = asyncio.create_task(simulator.start())
            
            # Calculate expected duration
            expected_duration = sum(scenario.shot_intervals) + scenario.start_delay + 5.0
            
            print(f"⏱️ Expected duration: ~{expected_duration:.1f} seconds")
            print("   (Press Ctrl+C to stop early)")
            print()
            
            # Wait for simulation to complete
            await asyncio.sleep(min(expected_duration, 60.0))  # Cap at 60 seconds
            
            await simulator.stop()
            
            try:
                await asyncio.wait_for(start_task, timeout=3.0)
            except asyncio.TimeoutError:
                pass
            
            # Display comprehensive results
            print("\n" + "=" * 50)
            print("📊 SIMULATION RESULTS")
            print("=" * 50)
            
            stats = simulator.get_stats()
            
            print(f"Scenario: {scenario.name}")
            print(f"Duration: {(stats['end_time'] - stats['start_time']).total_seconds():.1f}s" if stats['end_time'] else "Unknown")
            print()
            
            print("📈 Performance Metrics:")
            print(f"   Shots Fired: {stats['total_shots']}")
            print(f"   Impacts Detected: {stats['total_impacts']}")
            print(f"   Missed Shots: {stats['missed_shots']}")
            print(f"   False Positives: {stats['false_positives']}")
            
            if stats['total_shots'] > 0:
                accuracy = (stats['total_impacts'] / stats['total_shots']) * 100
                print(f"   Accuracy: {accuracy:.1f}%")
            
            print()
            print("🔧 Technical Stats:")
            print(f"   Sensor Samples: {stats['sensor_samples_generated']:,}")
            print(f"   Timer Events: {stats['timer_events_generated']}")
            print(f"   Errors Injected: {stats['errors_injected']}")
            
            if stats['total_impacts'] > 0 and stats['avg_shot_to_impact_ms'] > 0:
                print(f"   Avg Shot-to-Impact: {stats['avg_shot_to_impact_ms']:.1f}ms")
            
        except KeyboardInterrupt:
            print("\n⚠️ Simulation stopped by user")
            await simulator.stop()
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")
            logger.exception("Detailed simulation error")
            if simulator:
                await simulator.stop()


async def main():
    """Main entry point for the simulation demo"""
    print("🎯 LeadVille Comprehensive Simulation Demo")
    print("==========================================")
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    Path("scenarios").mkdir(exist_ok=True)
    
    demo = SimulationDemo()
    
    try:
        await demo.main_menu()
    except KeyboardInterrupt:
        print("\n👋 Demo terminated by user. Goodbye!")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        logger.exception("Main demo error")


if __name__ == "__main__":
    asyncio.run(main())