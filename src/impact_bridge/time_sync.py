"""
Time Synchronization for AMG Timer
Provides clock synchronization and drift detection between Pi and timer
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class TimeSyncStatus:
    """Time synchronization status"""
    last_sync_time: Optional[datetime] = None
    clock_drift_ms: float = 0.0
    sync_count: int = 0
    max_drift_ms: float = 0.0
    avg_drift_ms: float = 0.0
    sync_quality: str = "unknown"  # good, fair, poor, unknown
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "clock_drift_ms": round(self.clock_drift_ms, 2),
            "sync_count": self.sync_count,
            "max_drift_ms": round(self.max_drift_ms, 2),
            "avg_drift_ms": round(self.avg_drift_ms, 2),
            "sync_quality": self.sync_quality
        }


class TimeSynchronizer:
    """Time synchronization manager for AMG timer"""
    
    def __init__(
        self,
        sync_interval_minutes: float = 5.0,
        drift_threshold_ms: float = 100.0,
        enabled: bool = True
    ):
        self.sync_interval_minutes = sync_interval_minutes
        self.drift_threshold_ms = drift_threshold_ms
        self.enabled = enabled
        
        self.sync_status = TimeSyncStatus()
        self._drift_history = []
        self._max_drift_history = 100  # Keep last 100 measurements
        
        self._sync_task: Optional[asyncio.Task] = None
        self._stop_requested = False
        
        # Callbacks
        self._on_sync_update: Optional[Callable[[TimeSyncStatus], None]] = None
        self._on_drift_alert: Optional[Callable[[float], None]] = None
        
    def set_sync_callback(self, callback: Callable[[TimeSyncStatus], None]):
        """Set callback for sync status updates"""
        self._on_sync_update = callback
        
    def set_drift_alert_callback(self, callback: Callable[[float], None]):
        """Set callback for drift alerts"""
        self._on_drift_alert = callback
        
    async def start_sync_monitoring(self):
        """Start time synchronization monitoring"""
        if not self.enabled:
            logger.info("Time synchronization disabled")
            return
            
        self._stop_requested = False
        self._sync_task = asyncio.create_task(self._sync_monitoring_loop())
        
        logger.info(f"Time synchronization started (interval: {self.sync_interval_minutes} minutes)")
        
    async def stop_sync_monitoring(self):
        """Stop time synchronization monitoring"""
        if not self.enabled:
            return
            
        self._stop_requested = True
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Time synchronization stopped")
        
    async def _sync_monitoring_loop(self):
        """Main synchronization monitoring loop"""
        while not self._stop_requested:
            try:
                # Perform time synchronization check
                await self._perform_sync_check()
                
                # Wait for next sync interval
                await asyncio.sleep(self.sync_interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Time sync monitoring error: {e}")
                await asyncio.sleep(30)  # Brief pause before retry
                
    async def _perform_sync_check(self):
        """Perform time synchronization check"""
        try:
            # Get current system time
            system_time = datetime.now(timezone.utc)
            
            # For real implementation, this would query the AMG timer's clock
            # For now, we simulate drift detection by comparing with monotonic time
            monotonic_time = time.monotonic()
            
            # Calculate theoretical drift (for simulation)
            # In real implementation, this would be: timer_time - system_time
            drift_ms = self._calculate_simulated_drift()
            
            # Update sync status
            self.sync_status.last_sync_time = system_time
            self.sync_status.clock_drift_ms = drift_ms
            self.sync_status.sync_count += 1
            
            # Track drift history
            self._drift_history.append(drift_ms)
            if len(self._drift_history) > self._max_drift_history:
                self._drift_history.pop(0)
                
            # Update statistics
            self.sync_status.max_drift_ms = max(abs(d) for d in self._drift_history)
            self.sync_status.avg_drift_ms = statistics.mean(self._drift_history)
            
            # Determine sync quality
            self.sync_status.sync_quality = self._assess_sync_quality(abs(drift_ms))
            
            logger.debug(f"Time sync check: drift={drift_ms:.2f}ms, quality={self.sync_status.sync_quality}")
            
            # Check for drift alert
            if abs(drift_ms) > self.drift_threshold_ms:
                logger.warning(f"Clock drift detected: {drift_ms:.2f}ms (threshold: {self.drift_threshold_ms}ms)")
                if self._on_drift_alert:
                    self._on_drift_alert(drift_ms)
                    
            # Notify sync update callback
            if self._on_sync_update:
                self._on_sync_update(self.sync_status)
                
        except Exception as e:
            logger.error(f"Time sync check failed: {e}")
            
    def _calculate_simulated_drift(self) -> float:
        """
        Calculate simulated clock drift for testing.
        In real implementation, this would query AMG timer clock.
        """
        # Simulate small random drift
        import random
        base_drift = random.uniform(-50, 50)  # ±50ms base drift
        
        # Add some systematic drift over time
        time_factor = (time.time() % 3600) / 3600  # 0-1 over an hour
        systematic_drift = time_factor * 20  # Up to 20ms systematic drift
        
        return base_drift + systematic_drift
        
    def _assess_sync_quality(self, abs_drift_ms: float) -> str:
        """Assess synchronization quality based on drift"""
        if abs_drift_ms < 25:
            return "good"
        elif abs_drift_ms < 75:
            return "fair"
        elif abs_drift_ms < 150:
            return "poor"
        else:
            return "critical"
            
    def get_sync_status(self) -> TimeSyncStatus:
        """Get current synchronization status"""
        return self.sync_status
        
    def get_sync_summary(self) -> Dict[str, Any]:
        """Get synchronization summary for logging"""
        return {
            "enabled": self.enabled,
            "sync_interval_minutes": self.sync_interval_minutes,
            "drift_threshold_ms": self.drift_threshold_ms,
            "status": self.sync_status.to_dict(),
            "drift_history_count": len(self._drift_history)
        }
        
    async def force_sync_check(self):
        """Force an immediate synchronization check"""
        if self.enabled:
            logger.info("Forcing immediate time sync check")
            await self._perform_sync_check()
        else:
            logger.warning("Time synchronization is disabled")
            
    def correct_drift(self, correction_ms: float):
        """Apply drift correction (for manual adjustment)"""
        logger.info(f"Applying time drift correction: {correction_ms:.2f}ms")
        
        # In real implementation, this would send correction to AMG timer
        # For now, we just log the correction
        self.sync_status.clock_drift_ms -= correction_ms
        
        if self._on_sync_update:
            self._on_sync_update(self.sync_status)


class TimeSyncIntegration:
    """Integration class to connect time sync with AMG events"""
    
    def __init__(self, time_synchronizer: TimeSynchronizer):
        self.time_synchronizer = time_synchronizer
        
    async def handle_amg_timer_event(self, parsed_data: Dict[str, Any]):
        """Handle AMG timer event for time synchronization"""
        # Use timer events to validate synchronization
        event_time = parsed_data.get("current_time", 0.0)
        shot_state = parsed_data.get("shot_state", "")
        
        # If this is a timer start event, we can use it for sync validation
        if shot_state == "START":
            logger.debug("Timer start event - validating time sync")
            # Could trigger sync check here if needed
            
        elif shot_state == "ACTIVE":
            # Use active timer events to check for time consistency
            current_shot = parsed_data.get("current_shot", 0)
            if current_shot > 0:
                logger.debug(f"Shot {current_shot} at {event_time:.2f}s - time sync OK")
                
    async def handle_sync_update(self, sync_status: TimeSyncStatus):
        """Handle time sync status update"""
        if sync_status.sync_quality == "critical":
            logger.error(f"Critical time drift detected: {sync_status.clock_drift_ms:.2f}ms")
        elif sync_status.sync_quality == "poor":
            logger.warning(f"Poor time sync quality: {sync_status.clock_drift_ms:.2f}ms")
            
    async def handle_drift_alert(self, drift_ms: float):
        """Handle drift alert"""
        logger.warning(f"🕐 Time drift alert: {drift_ms:.2f}ms")
        
        # Could trigger corrective actions here
        if abs(drift_ms) > 200:  # Critical drift
            logger.error("Critical time drift - consider manual sync")


# Example usage
async def test_time_synchronizer():
    """Test time synchronizer"""
    sync = TimeSynchronizer(
        sync_interval_minutes=0.1,  # 6 seconds for testing
        drift_threshold_ms=50.0
    )
    
    def on_sync_update(status):
        print(f"📊 Sync update: drift={status.clock_drift_ms:.2f}ms, quality={status.sync_quality}")
        
    def on_drift_alert(drift):
        print(f"⚠️  Drift alert: {drift:.2f}ms")
        
    sync.set_sync_callback(on_sync_update)
    sync.set_drift_alert_callback(on_drift_alert)
    
    # Start monitoring
    await sync.start_sync_monitoring()
    
    # Let it run for a while
    await asyncio.sleep(30)
    
    # Force a sync check
    await sync.force_sync_check()
    
    await asyncio.sleep(10)
    
    # Stop monitoring
    await sync.stop_sync_monitoring()
    
    # Print summary
    print("📈 Sync Summary:")
    print(json.dumps(sync.get_sync_summary(), indent=2))


if __name__ == "__main__":
    import json
    asyncio.run(test_time_synchronizer())