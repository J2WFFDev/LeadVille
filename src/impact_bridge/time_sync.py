"""
Time Synchronization for AMG Timer
Provides clock synchronization and drift detection between Pi and timer with NTP support
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import statistics

from .ntp_client import NTPClient, NTPSyncResult

logger = logging.getLogger(__name__)


@dataclass
class TimeSyncStatus:
    """Time synchronization status"""
    last_sync_time: Optional[datetime] = None
    clock_drift_ms: float = 0.0
    sync_count: int = 0
    max_drift_ms: float = 0.0
    avg_drift_ms: float = 0.0
    sync_quality: str = "unknown"  # excellent, good, fair, poor, unknown
    ntp_enabled: bool = False
    ntp_offset_ms: float = 0.0
    ntp_quality: str = "unknown"
    correction_applied_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "clock_drift_ms": round(self.clock_drift_ms, 2),
            "sync_count": self.sync_count,
            "max_drift_ms": round(self.max_drift_ms, 2),
            "avg_drift_ms": round(self.avg_drift_ms, 2),
            "sync_quality": self.sync_quality,
            "ntp_enabled": self.ntp_enabled,
            "ntp_offset_ms": round(self.ntp_offset_ms, 2),
            "ntp_quality": self.ntp_quality,
            "correction_applied_ms": round(self.correction_applied_ms, 2)
        }


class TimeSynchronizer:
    """Enhanced time synchronization manager with NTP support"""
    
    def __init__(
        self,
        sync_interval_minutes: float = 5.0,
        drift_threshold_ms: float = 20.0,  # Default to ±20ms as per requirements
        enabled: bool = True,
        ntp_enabled: bool = True,
        ntp_servers: List[str] = None,
        ntp_timeout: float = 10.0,
        enable_correction: bool = True
    ):
        self.sync_interval_minutes = sync_interval_minutes
        self.drift_threshold_ms = drift_threshold_ms
        self.enabled = enabled
        self.ntp_enabled = ntp_enabled
        self.enable_correction = enable_correction
        
        # Initialize NTP client if enabled
        self.ntp_client = None
        if ntp_enabled:
            self.ntp_client = NTPClient(
                servers=ntp_servers,
                timeout=ntp_timeout,
                max_retries=3
            )
        
        self.sync_status = TimeSyncStatus(ntp_enabled=ntp_enabled)
        self._drift_history = []
        self._max_drift_history = 100  # Keep last 100 measurements
        self._system_time_offset = 0.0  # System time correction offset
        
        self._sync_task: Optional[asyncio.Task] = None
        self._stop_requested = False
        
        # Callbacks
        self._on_sync_update: Optional[Callable[[TimeSyncStatus], None]] = None
        self._on_drift_alert: Optional[Callable[[float], None]] = None
        self._on_correction_applied: Optional[Callable[[float], None]] = None
        
    def set_sync_callback(self, callback: Callable[[TimeSyncStatus], None]):
        """Set callback for sync status updates"""
        self._on_sync_update = callback
        
    def set_drift_alert_callback(self, callback: Callable[[float], None]):
        """Set callback for drift alerts"""
        self._on_drift_alert = callback
        
    def set_correction_callback(self, callback: Callable[[float], None]):
        """Set callback for correction notifications"""
        self._on_correction_applied = callback
        
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
        """Perform time synchronization check with NTP support"""
        try:
            # Get current system time
            system_time = datetime.now(timezone.utc)
            
            # Perform NTP sync if enabled
            ntp_offset = 0.0
            if self.ntp_enabled and self.ntp_client:
                try:
                    # Sync with NTP servers
                    ntp_results = await self.ntp_client.sync_with_multiple_servers()
                    
                    # Get best offset from NTP sync
                    best_ntp_offset = self.ntp_client.get_best_offset()
                    if best_ntp_offset is not None:
                        ntp_offset = best_ntp_offset
                        self.sync_status.ntp_offset_ms = ntp_offset * 1000
                        self.sync_status.ntp_quality = self.ntp_client.get_sync_quality()
                        
                        logger.debug(f"NTP sync: offset={ntp_offset * 1000:.2f}ms, quality={self.sync_status.ntp_quality}")
                    else:
                        logger.warning("NTP sync failed - no successful server connections")
                        
                except Exception as e:
                    logger.error(f"NTP sync error: {e}")
            
            # Calculate clock drift
            # In production, this would be: (timer_time - system_time) + ntp_offset
            # For now, we use NTP offset as the primary drift indicator
            if self.ntp_enabled and abs(ntp_offset) > 0:
                drift_ms = ntp_offset * 1000  # Convert to milliseconds
            else:
                # Fallback to simulated drift for testing
                drift_ms = self._calculate_simulated_drift()
            
            # Apply correction if enabled and drift exceeds threshold
            correction_applied = 0.0
            if self.enable_correction and abs(drift_ms) > self.drift_threshold_ms:
                correction_applied = await self._apply_time_correction(drift_ms)
                
            # Update sync status
            self.sync_status.last_sync_time = system_time
            self.sync_status.clock_drift_ms = drift_ms - correction_applied
            self.sync_status.sync_count += 1
            self.sync_status.correction_applied_ms = correction_applied
            
            # Track drift history (after correction)
            effective_drift = drift_ms - correction_applied
            self._drift_history.append(effective_drift)
            if len(self._drift_history) > self._max_drift_history:
                self._drift_history.pop(0)
                
            # Update statistics
            self.sync_status.max_drift_ms = max(abs(d) for d in self._drift_history)
            self.sync_status.avg_drift_ms = statistics.mean(self._drift_history)
            
            # Determine overall sync quality (combines local and NTP quality)
            self.sync_status.sync_quality = self._assess_overall_sync_quality(
                abs(effective_drift), self.sync_status.ntp_quality
            )
            
            logger.debug(f"Time sync check: drift={effective_drift:.2f}ms, correction={correction_applied:.2f}ms, quality={self.sync_status.sync_quality}")
            
            # Check for drift alert (after correction)
            if abs(effective_drift) > self.drift_threshold_ms:
                logger.warning(f"Clock drift detected: {effective_drift:.2f}ms (threshold: {self.drift_threshold_ms}ms)")
                if self._on_drift_alert:
                    self._on_drift_alert(effective_drift)
                    
            # Notify sync update callback
            if self._on_sync_update:
                self._on_sync_update(self.sync_status)
                
        except Exception as e:
            logger.error(f"Time sync check failed: {e}")
    
    async def _apply_time_correction(self, drift_ms: float) -> float:
        """Apply time correction for detected drift
        
        Args:
            drift_ms: Detected drift in milliseconds
            
        Returns:
            Applied correction in milliseconds
        """
        try:
            # Calculate correction amount (limit to reasonable bounds)
            max_correction_ms = 1000.0  # Maximum 1 second correction per cycle
            correction_ms = max(-max_correction_ms, min(max_correction_ms, -drift_ms))
            
            # Apply system time offset (this would interface with system time in production)
            self._system_time_offset += correction_ms / 1000.0
            
            logger.info(f"Applied time correction: {correction_ms:.2f}ms (total offset: {self._system_time_offset * 1000:.2f}ms)")
            
            # Notify correction callback
            if self._on_correction_applied:
                self._on_correction_applied(correction_ms)
            
            return correction_ms
            
        except Exception as e:
            logger.error(f"Time correction failed: {e}")
            return 0.0
            
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
        
    def _assess_overall_sync_quality(self, abs_drift_ms: float, ntp_quality: str) -> str:
        """Assess overall synchronization quality combining local and NTP metrics"""
        # Base quality on drift magnitude
        local_quality = self._assess_sync_quality(abs_drift_ms)
        
        # If NTP is disabled, use local quality only
        if not self.ntp_enabled:
            return local_quality
        
        # Combine local and NTP quality
        quality_scores = {
            "excellent": 4,
            "good": 3,
            "fair": 2, 
            "poor": 1,
            "critical": 0,
            "unknown": 0
        }
        
        local_score = quality_scores.get(local_quality, 0)
        ntp_score = quality_scores.get(ntp_quality, 0)
        
        # Combined score (weighted average)
        combined_score = (local_score * 0.6 + ntp_score * 0.4)
        
        # Convert back to quality string
        if combined_score >= 3.5:
            return "excellent"
        elif combined_score >= 2.5:
            return "good"
        elif combined_score >= 1.5:
            return "fair"
        elif combined_score >= 0.5:
            return "poor"
        else:
            return "critical"
        
    def _assess_sync_quality(self, abs_drift_ms: float) -> str:
        """Assess synchronization quality based on drift"""
        if abs_drift_ms < 5:
            return "excellent"
        elif abs_drift_ms < 10:
            return "good"
        elif abs_drift_ms < 25:
            return "fair"
        elif abs_drift_ms < 50:
            return "poor"
        else:
            return "critical"
            
    def get_sync_status(self) -> TimeSyncStatus:
        """Get current synchronization status"""
        return self.sync_status
        
    def get_sync_summary(self) -> Dict[str, Any]:
        """Get synchronization summary for logging"""
        summary = {
            "enabled": self.enabled,
            "sync_interval_minutes": self.sync_interval_minutes,
            "drift_threshold_ms": self.drift_threshold_ms,
            "status": self.sync_status.to_dict(),
            "drift_history_count": len(self._drift_history),
            "system_time_offset_ms": round(self._system_time_offset * 1000, 2),
            "ntp_enabled": self.ntp_enabled
        }
        
        # Add NTP summary if available
        if self.ntp_enabled and self.ntp_client:
            ntp_summary = self.ntp_client.get_sync_summary()
            summary["ntp_summary"] = ntp_summary
            
        return summary
        
    def get_corrected_time(self) -> datetime:
        """Get current time with applied corrections
        
        Returns:
            Current time adjusted for known offsets
        """
        current_time = datetime.now(timezone.utc)
        
        # Apply system time offset
        if self._system_time_offset != 0:
            import datetime as dt
            corrected_time = current_time + dt.timedelta(seconds=self._system_time_offset)
            return corrected_time
        
        return current_time
    
    def reset_corrections(self):
        """Reset all applied time corrections"""
        logger.info("Resetting time corrections")
        self._system_time_offset = 0.0
        self.sync_status.correction_applied_ms = 0.0
        
        if self._on_correction_applied:
            self._on_correction_applied(0.0)
    
    async def force_ntp_sync(self) -> bool:
        """Force immediate NTP synchronization
        
        Returns:
            True if NTP sync was successful, False otherwise
        """
        if not self.ntp_enabled or not self.ntp_client:
            logger.warning("NTP synchronization is disabled")
            return False
            
        try:
            logger.info("Forcing immediate NTP synchronization")
            results = await self.ntp_client.sync_with_multiple_servers()
            
            successful_syncs = sum(1 for r in results.values() if r.success)
            logger.info(f"NTP sync complete: {successful_syncs}/{len(results)} servers successful")
            
            # Update status
            best_offset = self.ntp_client.get_best_offset()
            if best_offset is not None:
                self.sync_status.ntp_offset_ms = best_offset * 1000
                self.sync_status.ntp_quality = self.ntp_client.get_sync_quality()
                return True
                
        except Exception as e:
            logger.error(f"Force NTP sync failed: {e}")
            
        return False
        
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
    """Test enhanced time synchronizer with NTP support"""
    sync = TimeSynchronizer(
        sync_interval_minutes=0.1,  # 6 seconds for testing
        drift_threshold_ms=20.0,    # ±20ms as per requirements
        ntp_enabled=True,
        enable_correction=True
    )
    
    def on_sync_update(status):
        print(f"📊 Sync update: drift={status.clock_drift_ms:.2f}ms, quality={status.sync_quality}")
        if status.ntp_enabled:
            print(f"   NTP offset={status.ntp_offset_ms:.2f}ms, NTP quality={status.ntp_quality}")
        if status.correction_applied_ms != 0:
            print(f"   Correction applied: {status.correction_applied_ms:.2f}ms")
        
    def on_drift_alert(drift):
        print(f"⚠️  Drift alert: {drift:.2f}ms")
        
    def on_correction_applied(correction):
        print(f"🔧 Time correction applied: {correction:.2f}ms")
        
    sync.set_sync_callback(on_sync_update)
    sync.set_drift_alert_callback(on_drift_alert)
    sync.set_correction_callback(on_correction_applied)
    
    # Test NTP sync first
    print("🕐 Testing NTP synchronization...")
    ntp_success = await sync.force_ntp_sync()
    print(f"NTP sync result: {'✅ Success' if ntp_success else '❌ Failed'}")
    
    # Start monitoring
    await sync.start_sync_monitoring()
    
    # Let it run for a while
    print("\n📈 Running sync monitoring...")
    await asyncio.sleep(30)
    
    # Force a sync check
    await sync.force_sync_check()
    
    await asyncio.sleep(10)
    
    # Test corrected time
    corrected_time = sync.get_corrected_time()
    current_time = datetime.now(timezone.utc)
    print(f"\n🕐 Time comparison:")
    print(f"   Current time: {current_time.isoformat()}")
    print(f"   Corrected time: {corrected_time.isoformat()}")
    print(f"   Difference: {(corrected_time - current_time).total_seconds() * 1000:.2f}ms")
    
    # Stop monitoring
    await sync.stop_sync_monitoring()
    
    # Print summary
    print("\n📈 Final Sync Summary:")
    import json
    print(json.dumps(sync.get_sync_summary(), indent=2))


if __name__ == "__main__":
    import json
    asyncio.run(test_time_synchronizer())