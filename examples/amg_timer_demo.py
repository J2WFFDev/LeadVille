#!/usr/bin/env python3
"""
AMG Timer Integration Demo
Demonstrates all AMG Labs Commander timer features including:
- BLE connectivity and frame processing
- MQTT event publishing 
- Database persistence
- Health monitoring
- Time synchronization
- WebSocket real-time updates
- Timer simulation mode
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from impact_bridge.amg_timer_manager import AMGTimerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def run_amg_timer_demo():
    """Comprehensive AMG timer demonstration"""
    
    print("🎯 AMG Labs Commander Timer Integration Demo")
    print("=" * 60)
    
    # Create logs and data directories
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    # Demo configuration - shows all available options
    config = {
        "amg_timer": {
            "device_id": "60:09:C3:1F:DC:1A",
            "uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
            "frame_validation": True,
            "simulation_mode": True,  # Use simulation for demo
            "health_monitoring": {
                "enabled": True,
                "rssi_check_interval_sec": 15.0,
                "health_report_interval_sec": 30.0
            },
            "time_synchronization": {
                "enabled": True,
                "sync_interval_minutes": 0.5,  # 30 seconds for demo
                "drift_threshold_ms": 100.0
            }
        },
        "mqtt": {
            "enabled": False,  # Disable MQTT broker requirement for demo
            "broker_host": "localhost",
            "broker_port": 1883,
            "topic_prefix": "leadville/timer/events",
            "client_id": "leadville-timer-demo"
        },
        "websocket": {
            "enabled": True,
            "host": "localhost",
            "port": 8765
        },
        "database": {
            "enabled": True,
            "db_path": "data/demo_timer_events.db",
            "json_backup_path": "logs/demo_timer_events.jsonl"
        },
        "simulation": {
            "mode": "precision_match",  # Realistic shooting match
            "num_shots": 5,
            "shot_interval_sec": 8.0,  # 8 seconds between shots
            "start_delay_sec": 3.0,    # 3 second countdown
            "random_timing": True,     # Add realistic variance
            "timing_variance_sec": 2.0  # ±2 second variance
        }
    }
    
    print("📋 Demo Configuration:")
    print(f"  Timer Mode: {'Simulation' if config['amg_timer']['simulation_mode'] else 'Real Hardware'}")
    print(f"  Simulation: {config['simulation']['mode']} - {config['simulation']['num_shots']} shots")
    print(f"  Database: {config['database']['enabled']}")
    print(f"  WebSocket: {config['websocket']['enabled']} (ws://localhost:{config['websocket']['port']})")
    print(f"  MQTT: {config['mqtt']['enabled']}")
    print(f"  Health Monitoring: {config['amg_timer']['health_monitoring']['enabled']}")
    print(f"  Time Sync: {config['amg_timer']['time_synchronization']['enabled']}")
    print()
    
    # Create and start the AMG timer manager
    manager = AMGTimerManager(config)
    
    try:
        print("🚀 Starting AMG Timer Manager...")
        await manager.start()
        
        print("✅ Manager started successfully!")
        print()
        
        if config['websocket']['enabled']:
            print(f"🌐 WebSocket server running on ws://localhost:{config['websocket']['port']}")
            print("   Connect with a WebSocket client to see real-time events")
            print()
        
        print("📊 Running shooting simulation...")
        print("   - Timer will start after 3 second delay")
        print("   - Watch for shot detection events") 
        print("   - Health monitoring active")
        print("   - All events saved to database")
        print()
        
        # Let the simulation run
        simulation_time = (
            config['simulation']['start_delay_sec'] + 
            (config['simulation']['num_shots'] * config['simulation']['shot_interval_sec']) + 
            10  # Extra time for completion
        )
        
        print(f"⏱️  Running for ~{simulation_time:.0f} seconds...")
        
        # Monitor status during simulation
        for i in range(int(simulation_time)):
            await asyncio.sleep(1)
            
            # Print status every 10 seconds
            if i % 10 == 0 and i > 0:
                status = manager.get_status()
                print(f"   Status update: AMG connected={status['amg_connected']}, "
                      f"WebSocket clients={status['websocket_clients']}")
        
        print("\n📈 Simulation completed! Generating summary...")
        
        # Get final status and statistics
        final_status = manager.get_status()
        print("\n📊 Final Status:")
        print(json.dumps(final_status, indent=2, default=str))
        
        # Get recorded events
        print("\n📋 Events Summary:")
        recent_events = await manager.get_recent_events(20)
        session_events = await manager.get_session_events()
        
        print(f"  Total events recorded: {len(recent_events)}")
        print(f"  Session events: {len(session_events)}")
        
        if session_events:
            print("\n🎯 Shot Summary:")
            shot_events = [e for e in session_events if e.event_type == "shot_detected"]
            for event in shot_events:
                print(f"  Shot {event.current_shot}: {event.current_time:.2f}s - {event.event_detail}")
        
        # Show recent events
        if recent_events:
            print("\n📝 Recent Events:")
            for event in recent_events[-5:]:  # Last 5 events
                print(f"  {event.timestamp}: {event.event_type} - {event.event_detail}")
        
        print(f"\n💾 Data saved to:")
        print(f"  Database: {config['database']['db_path']}")
        print(f"  JSON backup: {config['database']['json_backup_path']}")
        
        print(f"\n🎉 Demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo exception")
        
    finally:
        print("\n🛑 Stopping AMG Timer Manager...")
        await manager.stop()
        print("✅ Demo cleanup completed")


async def websocket_client_example():
    """Example WebSocket client to monitor events"""
    try:
        import websockets
        
        print("\n🔌 WebSocket Client Example")
        print("Connecting to ws://localhost:8765...")
        
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("✅ Connected to WebSocket server")
            
            # Send subscription
            subscribe_msg = {
                "type": "subscribe",
                "channels": ["timer_events", "health_status"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            
            print("📡 Listening for events (press Ctrl+C to stop)...")
            
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'timer_event':
                    print(f"🎯 Timer Event: {data['event_type']} - {data['data'].get('event_detail', '')}")
                elif data['type'] == 'health_status':
                    print(f"💚 Health: {data['data']['connection_status']}")
                else:
                    print(f"📨 {data['type']}: {data}")
                    
    except ImportError:
        print("❌ websockets package not available for client example")
    except Exception as e:
        print(f"❌ WebSocket client error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AMG Timer Integration Demo")
    parser.add_argument("--client", action="store_true", 
                       help="Run WebSocket client example instead of full demo")
    
    args = parser.parse_args()
    
    if args.client:
        asyncio.run(websocket_client_example())
    else:
        asyncio.run(run_amg_timer_demo())