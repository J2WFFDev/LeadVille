#!/usr/bin/env python3
"""
LeadVille Bridge CLI with timer adapter support.
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from impact_bridge.timers import create_timer, get_supported_timers, get_timer_info
from impact_bridge.ws.encode import TimerEventEncoder

logger = logging.getLogger(__name__)


class BridgeApplication:
    """Main bridge application with timer adapter support."""
    
    def __init__(self):
        self.timer_adapter = None
        self.running = False
        self.event_encoder = None
        
    async def run(self, args):
        """Run the bridge application."""
        self.running = True
        
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
        
        try:
            # Create and configure timer adapter
            await self._setup_timer(args)
            
            # Start event processing
            await self._process_events()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Bridge error: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _setup_timer(self, args):
        """Setup timer adapter based on CLI arguments."""
        timer_type = args.timer
        logger.info(f"Setting up {timer_type} timer adapter")
        
        # Build connection config
        config = {}
        
        if args.serial:
            config['port'] = args.serial
        if args.ble:
            config['mac_address'] = args.ble
        if args.sim:
            config['simulator'] = True
        if args.baud:
            config['baud'] = args.baud
        
        # Create timer adapter
        self.timer_adapter = create_timer(timer_type, **config)
        self.event_encoder = TimerEventEncoder(timer_type)
        
        # Connect to timer
        await self.timer_adapter.connect(**config)
        await self.timer_adapter.start()
        
        logger.info(f"Timer adapter {timer_type} started successfully")
    
    async def _process_events(self):
        """Process timer events and emit to WebSocket/logging."""
        logger.info("Starting event processing...")
        
        async for event in self.timer_adapter.events:
            if not self.running:
                break
            
            # Encode event for WebSocket
            encoded = self.event_encoder.encode_json(event)
            
            # Log event (structured logging)
            event_data = {
                'component': 'timer',
                'adapter': self.timer_adapter.name,
                'event': event.__class__.__name__,
                'timestamp_ms': event.timestamp_ms,
                'encoded': encoded
            }
            
            logger.info(f"Timer event: {event.__class__.__name__}", extra=event_data)
            
            # TODO: Emit to WebSocket clients
            # TODO: Update metrics
            
    async def _cleanup(self):
        """Cleanup resources."""
        if self.timer_adapter:
            try:
                await self.timer_adapter.stop()
            except Exception as e:
                logger.error(f"Error stopping timer adapter: {e}")
        
        logger.info("Bridge cleanup complete")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.running = False


def create_parser():
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="LeadVille Impact Bridge with timer adapter support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # AMG Commander via BLE
  %(prog)s --timer amg --ble AA:BB:CC:DD:EE:FF
  
  # SpecialPie via USB serial
  %(prog)s --timer specialpie --serial /dev/ttyACM0
  
  # SpecialPie via BLE
  %(prog)s --timer specialpie --ble AA:BB:CC:DD:EE:FF
  
  # SpecialPie simulator (UDP)
  %(prog)s --timer specialpie --sim
        """
    )
    
    # Timer selection
    supported_timers = get_supported_timers()
    parser.add_argument(
        '--timer',
        choices=supported_timers,
        default='amg',
        help=f'Timer type ({", ".join(supported_timers)})'
    )
    
    # Connection options
    connection_group = parser.add_argument_group('Connection options')
    connection_group.add_argument(
        '--serial',
        metavar='PORT',
        help='Serial port path (e.g., /dev/ttyACM0, COM3)'
    )
    connection_group.add_argument(
        '--ble',
        metavar='MAC',
        help='Bluetooth LE MAC address (e.g., AA:BB:CC:DD:EE:FF)'
    )
    connection_group.add_argument(
        '--sim',
        action='store_true',
        help='Use simulator mode (UDP)'
    )
    connection_group.add_argument(
        '--baud',
        type=int,
        default=115200,
        help='Serial baud rate (default: 115200)'
    )
    
    # Logging options
    logging_group = parser.add_argument_group('Logging options')
    logging_group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    logging_group.add_argument(
        '--log-format',
        choices=['text', 'json'],
        default='text',
        help='Log format (default: text)'
    )
    
    # Info commands
    info_group = parser.add_argument_group('Information')
    info_group.add_argument(
        '--list-timers',
        action='store_true',
        help='List supported timer types and exit'
    )
    info_group.add_argument(
        '--timer-info',
        metavar='TYPE',
        choices=supported_timers,
        help='Show detailed info about a timer type'
    )
    
    return parser


def setup_logging(level: str, format_type: str):
    """Setup logging configuration."""
    log_level = getattr(logging, level.upper())
    
    if format_type == 'json':
        import json
        
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': self.formatTime(record),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                }
                
                # Add extra fields if present
                if hasattr(record, 'component'):
                    log_data.update({
                        'component': record.component,
                        'adapter': getattr(record, 'adapter', None),
                        'event': getattr(record, 'event', None),
                    })
                
                return json.dumps(log_data)
        
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle info commands
    if args.list_timers:
        print("Supported timer types:")
        for timer_type in get_supported_timers():
            info = get_timer_info(timer_type)
            print(f"  {timer_type}: {info.get('name', 'Unknown')}")
            print(f"    Connections: {', '.join(info.get('connection_types', []))}")
            print(f"    Description: {info.get('description', 'No description')}")
        return 0
    
    if args.timer_info:
        info = get_timer_info(args.timer_info)
        print(f"Timer: {info.get('name', 'Unknown')}")
        print(f"Type: {args.timer_info}")
        print(f"Description: {info.get('description', 'No description')}")
        print(f"Connection types: {', '.join(info.get('connection_types', []))}")
        print(f"Protocols: {', '.join(info.get('protocols', []))}")
        print(f"Features: {', '.join(info.get('features', []))}")
        return 0
    
    # Validate connection arguments
    connection_count = sum([bool(args.serial), bool(args.ble), bool(args.sim)])
    if connection_count == 0:
        parser.error("Must specify one connection type: --serial, --ble, or --sim")
    elif connection_count > 1:
        parser.error("Can only specify one connection type")
    
    # Setup logging
    setup_logging(args.log_level, args.log_format)
    
    # Run bridge application
    app = BridgeApplication()
    
    try:
        asyncio.run(app.run(args))
        return 0
    except Exception as e:
        logger.error(f"Bridge failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())