"""Network monitor for automatic fallback to AP mode."""

import asyncio
import logging
import time
from typing import Optional

from .network_manager import NetworkManager

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Monitors network connectivity and handles automatic fallback to AP mode."""
    
    def __init__(self, network_manager: NetworkManager, check_interval: int = 30,
                 failure_threshold: int = 3):
        """Initialize NetworkMonitor.
        
        Args:
            network_manager: NetworkManager instance
            check_interval: Seconds between connectivity checks
            failure_threshold: Number of consecutive failures before fallback
        """
        self.network_manager = network_manager
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self) -> None:
        """Start network monitoring."""
        if self.is_monitoring:
            logger.warning("Network monitoring already started")
            return
            
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started network monitoring (check_interval={self.check_interval}s)")
        
    async def stop_monitoring(self) -> None:
        """Stop network monitoring."""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped network monitoring")
        
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await self._check_connectivity()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
                
    async def _check_connectivity(self) -> None:
        """Check network connectivity and handle failures."""
        # Only monitor connectivity in client mode
        if self.network_manager.current_mode != NetworkManager.MODE_CLIENT:
            self.failure_count = 0
            return
        
        has_internet = self.network_manager.has_internet_connectivity()
        
        if has_internet:
            # Reset failure count on successful connection
            if self.failure_count > 0:
                logger.info("Internet connectivity restored")
                self.failure_count = 0
        else:
            self.failure_count += 1
            logger.warning(f"Internet connectivity check failed "
                         f"({self.failure_count}/{self.failure_threshold})")
            
            # Fallback to AP mode after threshold failures
            if self.failure_count >= self.failure_threshold:
                logger.error("Internet connectivity lost, falling back to AP mode")
                await self._fallback_to_ap_mode()
                
    async def _fallback_to_ap_mode(self) -> None:
        """Fallback to AP mode due to connectivity loss."""
        try:
            success = self.network_manager.switch_to_ap_mode()
            if success:
                logger.info("Successfully fell back to AP mode")
                self.failure_count = 0
            else:
                logger.error("Failed to fallback to AP mode")
        except Exception as e:
            logger.error(f"Error during AP mode fallback: {e}")
            
    def get_monitoring_status(self) -> dict:
        """Get current monitoring status."""
        return {
            "is_monitoring": self.is_monitoring,
            "check_interval": self.check_interval,
            "failure_threshold": self.failure_threshold,
            "failure_count": self.failure_count,
            "timestamp": time.time()
        }