"""
NTP Client for Time Synchronization
Provides Network Time Protocol client functionality for accurate time synchronization
"""

import asyncio
import logging
import socket
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import statistics

import ntplib

logger = logging.getLogger(__name__)


@dataclass
class NTPSyncResult:
    """NTP synchronization result"""
    server: str
    offset: float  # Clock offset in seconds
    delay: float  # Network delay in seconds
    stratum: int  # NTP stratum level
    sync_time: datetime
    precision: float  # Server precision
    root_delay: float  # Root delay
    root_dispersion: float  # Root dispersion
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "server": self.server,
            "offset_ms": round(self.offset * 1000, 2),
            "delay_ms": round(self.delay * 1000, 2),
            "stratum": self.stratum,
            "sync_time": self.sync_time.isoformat(),
            "precision": self.precision,
            "root_delay": self.root_delay,
            "root_dispersion": self.root_dispersion,
            "success": self.success,
            "error_message": self.error_message
        }


class NTPClient:
    """NTP client for time synchronization with multiple server support"""
    
    def __init__(
        self,
        servers: List[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize NTP client
        
        Args:
            servers: List of NTP servers (defaults to common public servers)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        # Default NTP servers if none provided
        self.servers = servers or [
            "pool.ntp.org",
            "time.nist.gov",
            "time.google.com",
            "time.cloudflare.com"
        ]
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.client = ntplib.NTPClient()
        self._last_sync_results: List[NTPSyncResult] = []
        
    async def sync_with_server(self, server: str) -> NTPSyncResult:
        """Synchronize with a specific NTP server
        
        Args:
            server: NTP server hostname or IP
            
        Returns:
            NTPSyncResult with sync details
        """
        for attempt in range(self.max_retries):
            try:
                # Run NTP request in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.client.request(server, timeout=self.timeout)
                )
                
                sync_time = datetime.now(timezone.utc)
                
                return NTPSyncResult(
                    server=server,
                    offset=response.offset,
                    delay=response.delay,
                    stratum=response.stratum,
                    sync_time=sync_time,
                    precision=response.precision,
                    root_delay=response.root_delay,
                    root_dispersion=response.root_dispersion,
                    success=True
                )
                
            except socket.gaierror as e:
                error_msg = f"DNS resolution failed for {server}: {e}"
                logger.warning(f"NTP sync attempt {attempt + 1}/{self.max_retries} failed: {error_msg}")
                
            except socket.timeout as e:
                error_msg = f"Timeout connecting to {server}: {e}"
                logger.warning(f"NTP sync attempt {attempt + 1}/{self.max_retries} failed: {error_msg}")
                
            except Exception as e:
                error_msg = f"NTP sync error with {server}: {e}"
                logger.warning(f"NTP sync attempt {attempt + 1}/{self.max_retries} failed: {error_msg}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
        # All attempts failed
        return NTPSyncResult(
            server=server,
            offset=0.0,
            delay=0.0,
            stratum=0,
            sync_time=datetime.now(timezone.utc),
            precision=0.0,
            root_delay=0.0,
            root_dispersion=0.0,
            success=False,
            error_message=f"Failed to sync with {server} after {self.max_retries} attempts"
        )
    
    async def sync_with_multiple_servers(self) -> Dict[str, NTPSyncResult]:
        """Synchronize with multiple NTP servers concurrently
        
        Returns:
            Dictionary mapping server names to sync results
        """
        logger.info(f"Starting NTP sync with {len(self.servers)} servers")
        
        # Run sync requests concurrently
        tasks = [
            self.sync_with_server(server) 
            for server in self.servers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        sync_results = {}
        for i, result in enumerate(results):
            server = self.servers[i]
            if isinstance(result, Exception):
                sync_results[server] = NTPSyncResult(
                    server=server,
                    offset=0.0,
                    delay=0.0,
                    stratum=0,
                    sync_time=datetime.now(timezone.utc),
                    precision=0.0,
                    root_delay=0.0,
                    root_dispersion=0.0,
                    success=False,
                    error_message=f"Exception during sync: {result}"
                )
            else:
                sync_results[server] = result
        
        # Store results for analysis
        self._last_sync_results = [r for r in sync_results.values() if r.success]
        
        successful_syncs = sum(1 for r in sync_results.values() if r.success)
        logger.info(f"NTP sync complete: {successful_syncs}/{len(self.servers)} servers successful")
        
        return sync_results
    
    def get_best_offset(self) -> Optional[float]:
        """Get the best clock offset from recent sync results
        
        Uses median offset from successful syncs to reduce impact of outliers
        
        Returns:
            Best offset in seconds, or None if no successful syncs
        """
        if not self._last_sync_results:
            return None
        
        # Filter results by quality (low stratum and reasonable delay)
        quality_results = [
            r for r in self._last_sync_results
            if r.stratum <= 4 and r.delay < 1.0  # Good stratum and delay
        ]
        
        # Fall back to all results if no quality results
        if not quality_results:
            quality_results = self._last_sync_results
        
        offsets = [r.offset for r in quality_results]
        
        # Use median to reduce impact of outliers
        return statistics.median(offsets)
    
    def get_sync_quality(self) -> str:
        """Assess synchronization quality based on recent results
        
        Returns:
            Quality assessment: 'excellent', 'good', 'fair', 'poor', 'unknown'
        """
        if not self._last_sync_results:
            return "unknown"
        
        successful_count = len(self._last_sync_results)
        total_count = len(self.servers)
        success_ratio = successful_count / total_count
        
        # Analyze offset consistency
        offsets = [r.offset for r in self._last_sync_results]
        if len(offsets) > 1:
            offset_std = statistics.stdev(offsets)
        else:
            offset_std = 0.0
        
        # Analyze average delay
        avg_delay = statistics.mean(r.delay for r in self._last_sync_results)
        
        # Quality assessment
        if success_ratio >= 0.75 and offset_std < 0.01 and avg_delay < 0.1:
            return "excellent"
        elif success_ratio >= 0.5 and offset_std < 0.05 and avg_delay < 0.5:
            return "good"
        elif success_ratio >= 0.25 and offset_std < 0.1:
            return "fair"
        else:
            return "poor"
    
    def get_sync_summary(self) -> Dict[str, Any]:
        """Get synchronization summary for monitoring
        
        Returns:
            Dictionary with sync statistics and status
        """
        if not self._last_sync_results:
            return {
                "servers_configured": len(self.servers),
                "servers_successful": 0,
                "best_offset_ms": None,
                "sync_quality": "unknown",
                "last_sync_time": None
            }
        
        best_offset = self.get_best_offset()
        
        return {
            "servers_configured": len(self.servers),
            "servers_successful": len(self._last_sync_results),
            "best_offset_ms": round(best_offset * 1000, 2) if best_offset else None,
            "sync_quality": self.get_sync_quality(),
            "last_sync_time": self._last_sync_results[0].sync_time.isoformat(),
            "avg_delay_ms": round(
                statistics.mean(r.delay for r in self._last_sync_results) * 1000, 2
            ),
            "offset_std_ms": round(
                statistics.stdev(r.offset for r in self._last_sync_results) * 1000, 2
            ) if len(self._last_sync_results) > 1 else 0.0
        }


# Example usage and testing
async def test_ntp_client():
    """Test NTP client functionality"""
    client = NTPClient(timeout=5.0, max_retries=2)
    
    print("🕐 Testing NTP client...")
    
    # Test single server sync
    result = await client.sync_with_server("pool.ntp.org")
    print(f"📊 Single server sync result:")
    print(f"   Server: {result.server}")
    print(f"   Success: {result.success}")
    print(f"   Offset: {result.offset * 1000:.2f}ms")
    if result.success:
        print(f"   Delay: {result.delay * 1000:.2f}ms")
        print(f"   Stratum: {result.stratum}")
    else:
        print(f"   Error: {result.error_message}")
    
    # Test multiple server sync
    results = await client.sync_with_multiple_servers()
    print(f"\n📊 Multiple server sync results:")
    for server, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"   {status} {server}: {result.offset * 1000:.2f}ms offset")
    
    # Get best offset and quality
    best_offset = client.get_best_offset()
    quality = client.get_sync_quality()
    summary = client.get_sync_summary()
    
    print(f"\n📈 Sync Summary:")
    print(f"   Best offset: {best_offset * 1000:.2f}ms" if best_offset else "No offset available")
    print(f"   Quality: {quality}")
    print(f"   Summary: {summary}")


if __name__ == "__main__":
    asyncio.run(test_ntp_client())