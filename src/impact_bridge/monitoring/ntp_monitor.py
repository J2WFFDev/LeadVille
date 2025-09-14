"""NTP synchronization monitoring for time drift detection."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..ntp_client import NTPClient, NTPSyncResult
from .health_aggregator import ComponentHealth, HealthStatus

logger = logging.getLogger(__name__)


@dataclass
class NTPMonitorStatus:
    """NTP monitoring status."""
    is_synchronized: bool
    last_sync_time: Optional[datetime]
    drift_ms: Optional[float]
    server_count: int
    successful_servers: List[str]
    failed_servers: List[str]
    average_offset_ms: Optional[float]
    max_drift_threshold_ms: float
    is_critical: bool
    is_warning: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'is_synchronized': self.is_synchronized,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'drift_ms': self.drift_ms,
            'server_count': self.server_count,
            'successful_servers': self.successful_servers,
            'failed_servers': self.failed_servers,
            'average_offset_ms': self.average_offset_ms,
            'max_drift_threshold_ms': self.max_drift_threshold_ms,
            'is_critical': self.is_critical,
            'is_warning': self.is_warning,
            'error_message': self.error_message
        }


class NTPMonitor:
    """Monitors NTP synchronization and time drift."""
    
    def __init__(
        self,
        ntp_servers: Optional[List[str]] = None,
        drift_warning_threshold_ms: float = 50.0,
        drift_critical_threshold_ms: float = 100.0,
        sync_check_interval_minutes: int = 5,
        sync_timeout_seconds: int = 10
    ):
        # Default NTP servers if none provided
        if ntp_servers is None:
            ntp_servers = [
                "pool.ntp.org",
                "time.nist.gov", 
                "time.google.com",
                "time.cloudflare.com"
            ]
        
        self.ntp_servers = ntp_servers
        self.drift_warning_threshold_ms = drift_warning_threshold_ms
        self.drift_critical_threshold_ms = drift_critical_threshold_ms
        self.sync_check_interval_minutes = sync_check_interval_minutes
        self.sync_timeout_seconds = sync_timeout_seconds
        
        # NTP client
        self.ntp_client = NTPClient(
            servers=ntp_servers,
            timeout=sync_timeout_seconds
        )
        
        # State tracking
        self._last_sync_results: List[NTPSyncResult] = []
        self._last_check_time: Optional[datetime] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._sync_history: List[NTPSyncResult] = []
        
    async def check_ntp_synchronization(self) -> NTPMonitorStatus:
        """Check NTP synchronization status and calculate drift."""
        try:
            # Perform NTP sync with all servers
            sync_results = await self.ntp_client.sync_with_multiple_servers()
            
            self._last_sync_results = sync_results
            self._last_check_time = datetime.now()
            
            # Add to history (keep last 100 results)
            self._sync_history.extend(sync_results)
            if len(self._sync_history) > 100:
                self._sync_history = self._sync_history[-100:]
            
            # Analyze results
            successful_results = [r for r in sync_results if r.success]
            failed_results = [r for r in sync_results if not r.success]
            
            successful_servers = [r.server for r in successful_results]
            failed_servers = [r.server for r in failed_results]
            
            if not successful_results:
                # No successful synchronization
                return NTPMonitorStatus(
                    is_synchronized=False,
                    last_sync_time=self._last_check_time,
                    drift_ms=None,
                    server_count=len(sync_results),
                    successful_servers=successful_servers,
                    failed_servers=failed_servers,
                    average_offset_ms=None,
                    max_drift_threshold_ms=self.drift_critical_threshold_ms,
                    is_critical=True,
                    is_warning=False,
                    error_message="No NTP servers responding"
                )
            
            # Calculate average offset from successful servers
            offsets_ms = [r.offset * 1000 for r in successful_results]
            average_offset_ms = sum(offsets_ms) / len(offsets_ms)
            max_offset_ms = max(abs(offset) for offset in offsets_ms)
            
            # Determine status based on drift
            is_critical = max_offset_ms >= self.drift_critical_threshold_ms
            is_warning = max_offset_ms >= self.drift_warning_threshold_ms and not is_critical
            
            return NTPMonitorStatus(
                is_synchronized=True,
                last_sync_time=self._last_check_time,
                drift_ms=max_offset_ms,
                server_count=len(sync_results),
                successful_servers=successful_servers,
                failed_servers=failed_servers,
                average_offset_ms=average_offset_ms,
                max_drift_threshold_ms=self.drift_critical_threshold_ms,
                is_critical=is_critical,
                is_warning=is_warning,
                error_message=None if not failed_servers else f"Failed servers: {', '.join(failed_servers)}"
            )
            
        except Exception as e:
            logger.error(f"NTP synchronization check failed: {e}")
            return NTPMonitorStatus(
                is_synchronized=False,
                last_sync_time=datetime.now(),
                drift_ms=None,
                server_count=len(self.ntp_servers),
                successful_servers=[],
                failed_servers=self.ntp_servers,
                average_offset_ms=None,
                max_drift_threshold_ms=self.drift_critical_threshold_ms,
                is_critical=True,
                is_warning=False,
                error_message=str(e)
            )
    
    async def get_ntp_health_component(self) -> ComponentHealth:
        """Get NTP synchronization as a health component."""
        start_time = time.time()
        
        try:
            ntp_status = await self.check_ntp_synchronization()
            response_time = (time.time() - start_time) * 1000
            
            # Determine health status
            if ntp_status.is_critical:
                health_status = HealthStatus.CRITICAL
                message = f"NTP sync critical: drift {ntp_status.drift_ms:.1f}ms" if ntp_status.drift_ms else "NTP sync failed"
            elif ntp_status.is_warning:
                health_status = HealthStatus.WARNING
                message = f"NTP sync warning: drift {ntp_status.drift_ms:.1f}ms"
            elif ntp_status.is_synchronized:
                health_status = HealthStatus.HEALTHY
                message = f"NTP synchronized: drift {ntp_status.drift_ms:.1f}ms" if ntp_status.drift_ms else "NTP synchronized"
            else:
                health_status = HealthStatus.CRITICAL
                message = "NTP synchronization failed"
            
            return ComponentHealth(
                name="ntp_sync",
                status=health_status,
                message=message,
                last_check=datetime.now(),
                response_time_ms=response_time,
                metadata=ntp_status.to_dict()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"NTP health check failed: {e}")
            return ComponentHealth(
                name="ntp_sync",
                status=HealthStatus.CRITICAL,
                message=f"NTP health check failed: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
    
    async def start_monitoring(self):
        """Start continuous NTP monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("NTP monitoring already running")
            return
            
        logger.info("Starting NTP monitoring")
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop continuous NTP monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("NTP monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous NTP monitoring loop."""
        while True:
            try:
                ntp_status = await self.check_ntp_synchronization()
                
                # Log significant drift
                if ntp_status.is_critical:
                    logger.error(f"Critical NTP drift: {ntp_status.drift_ms:.1f}ms")
                elif ntp_status.is_warning:
                    logger.warning(f"NTP drift warning: {ntp_status.drift_ms:.1f}ms")
                
                # Wait for next check
                await asyncio.sleep(self.sync_check_interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in NTP monitoring loop: {e}")
                await asyncio.sleep(self.sync_check_interval_minutes * 60)
    
    def get_ntp_statistics(self) -> Dict[str, Any]:
        """Get NTP synchronization statistics."""
        if not self._sync_history:
            return {
                'total_checks': 0,
                'successful_checks': 0,
                'failed_checks': 0,
                'success_rate': 0.0,
                'average_offset_ms': None,
                'max_offset_ms': None,
                'server_statistics': {}
            }
        
        successful_syncs = [r for r in self._sync_history if r.success]
        failed_syncs = [r for r in self._sync_history if not r.success]
        
        # Calculate server statistics
        server_stats = {}
        for server in self.ntp_servers:
            server_results = [r for r in self._sync_history if r.server == server]
            server_successes = [r for r in server_results if r.success]
            
            server_stats[server] = {
                'total_attempts': len(server_results),
                'successful_attempts': len(server_successes),
                'success_rate': len(server_successes) / len(server_results) if server_results else 0.0,
                'average_offset_ms': sum(r.offset * 1000 for r in server_successes) / len(server_successes) if server_successes else None,
                'average_delay_ms': sum(r.delay * 1000 for r in server_successes) / len(server_successes) if server_successes else None
            }
        
        # Overall statistics
        if successful_syncs:
            offsets_ms = [r.offset * 1000 for r in successful_syncs]
            average_offset_ms = sum(abs(offset) for offset in offsets_ms) / len(offsets_ms)
            max_offset_ms = max(abs(offset) for offset in offsets_ms)
        else:
            average_offset_ms = None
            max_offset_ms = None
        
        return {
            'total_checks': len(self._sync_history),
            'successful_checks': len(successful_syncs),
            'failed_checks': len(failed_syncs),
            'success_rate': len(successful_syncs) / len(self._sync_history),
            'average_offset_ms': average_offset_ms,
            'max_offset_ms': max_offset_ms,
            'server_statistics': server_stats,
            'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None
        }
    
    def get_last_sync_status(self) -> Optional[NTPMonitorStatus]:
        """Get the last NTP synchronization status."""
        if not self._last_sync_results or not self._last_check_time:
            return None
        
        # Recreate status from last results
        successful_results = [r for r in self._last_sync_results if r.success]
        
        if not successful_results:
            return None
        
        offsets_ms = [r.offset * 1000 for r in successful_results]
        max_offset_ms = max(abs(offset) for offset in offsets_ms)
        
        return NTPMonitorStatus(
            is_synchronized=len(successful_results) > 0,
            last_sync_time=self._last_check_time,
            drift_ms=max_offset_ms,
            server_count=len(self._last_sync_results),
            successful_servers=[r.server for r in successful_results],
            failed_servers=[r.server for r in self._last_sync_results if not r.success],
            average_offset_ms=sum(offsets_ms) / len(offsets_ms),
            max_drift_threshold_ms=self.drift_critical_threshold_ms,
            is_critical=max_offset_ms >= self.drift_critical_threshold_ms,
            is_warning=max_offset_ms >= self.drift_warning_threshold_ms and max_offset_ms < self.drift_critical_threshold_ms
        )