"""Main network service that integrates all networking components."""

import asyncio
import logging
import signal
import sys
import threading
from pathlib import Path

from .network_manager import NetworkManager
from .network_monitor import NetworkMonitor
from .web_server import NetworkWebServer
from .captive_portal import CaptivePortal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class NetworkService:
    """Main network service coordinator."""
    
    def __init__(self):
        """Initialize NetworkService."""
        self.network_manager = NetworkManager()
        self.network_monitor = NetworkMonitor(self.network_manager)
        self.web_server = NetworkWebServer(self.network_manager, self.network_monitor)
        self.captive_portal = CaptivePortal()
        
        self.running = False
        self.web_thread = None
        self.captive_thread = None
        
    async def start(self):
        """Start the network service."""
        logger.info("Starting LeadVille Network Service...")
        
        self.running = True
        
        # Start network monitoring
        await self.network_monitor.start_monitoring()
        
        # Start web server in separate thread
        self.web_thread = threading.Thread(
            target=self._start_web_server,
            daemon=True
        )
        self.web_thread.start()
        
        # Start captive portal if in AP mode
        if self.network_manager.current_mode == NetworkManager.MODE_AP:
            self.captive_thread = threading.Thread(
                target=self._start_captive_portal,
                daemon=True
            )
            self.captive_thread.start()
        
        logger.info("Network service started successfully")
        
        # Keep service running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the network service."""
        logger.info("Stopping LeadVille Network Service...")
        
        self.running = False
        
        # Stop network monitoring
        await self.network_monitor.stop_monitoring()
        
        logger.info("Network service stopped")
    
    def _start_web_server(self):
        """Start the web server in a separate thread."""
        try:
            logger.info("Starting web server on port 5000...")
            self.web_server.run(host='0.0.0.0', port=5000, debug=False)
        except Exception as e:
            logger.error(f"Web server error: {e}")
    
    def _start_captive_portal(self):
        """Start the captive portal in a separate thread."""
        try:
            logger.info("Starting captive portal on port 8080...")
            self.captive_portal.run(host='0.0.0.0', port=8080, debug=False)
        except Exception as e:
            logger.error(f"Captive portal error: {e}")


async def main():
    """Main service entry point."""
    service = NetworkService()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received termination signal")
        loop.create_task(service.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await service.start()
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)