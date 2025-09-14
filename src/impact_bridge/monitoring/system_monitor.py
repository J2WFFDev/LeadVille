"""System resource monitoring for LeadVille Impact Bridge."""

import asyncio
import psutil
import shutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics snapshot."""
    timestamp: datetime
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    disk_usage_gb: float
    disk_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: Optional[List[float]] = None
    uptime_seconds: float = 0.0
    process_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class DiskSpaceStatus:
    """Disk space monitoring status."""
    path: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float
    is_critical: bool
    is_warning: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass  
class NetworkStatus:
    """Network connectivity status."""
    is_connected: bool
    interface_name: Optional[str]
    ip_address: Optional[str]
    ping_latency_ms: Optional[float]
    last_check: datetime
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['last_check'] = self.last_check.isoformat()
        return data


class SystemMonitor:
    """System resource and health monitoring."""
    
    def __init__(
        self,
        disk_warning_threshold: float = 80.0,
        disk_critical_threshold: float = 90.0,
        memory_warning_threshold: float = 85.0,
        cpu_warning_threshold: float = 80.0,
        monitored_paths: Optional[List[str]] = None
    ):
        self.disk_warning_threshold = disk_warning_threshold
        self.disk_critical_threshold = disk_critical_threshold
        self.memory_warning_threshold = memory_warning_threshold
        self.cpu_warning_threshold = cpu_warning_threshold
        
        # Default monitored paths
        if monitored_paths is None:
            monitored_paths = ["/", "/tmp", "/var/log"]
        self.monitored_paths = monitored_paths
        
        # State tracking
        self._start_time = time.time()
        self._last_network_stats = None
        self._network_baseline_time = time.time()
        
    async def get_system_metrics(self) -> SystemMetrics:
        """Get comprehensive system metrics."""
        try:
            # CPU usage (with brief interval for accuracy)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            
            # Disk usage (root filesystem)
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_free_gb = disk.free / 1024 / 1024 / 1024
            
            # Network I/O
            net_io = psutil.net_io_counters()
            if self._last_network_stats:
                time_diff = time.time() - self._network_baseline_time
                sent_mb = (net_io.bytes_sent - self._last_network_stats.bytes_sent) / 1024 / 1024 / time_diff
                recv_mb = (net_io.bytes_recv - self._last_network_stats.bytes_recv) / 1024 / 1024 / time_diff
            else:
                sent_mb = 0.0
                recv_mb = 0.0
            
            self._last_network_stats = net_io
            self._network_baseline_time = time.time()
            
            # Load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                load_avg = None
            
            # Process count
            process_count = len(psutil.pids())
            
            # Uptime
            uptime = time.time() - self._start_time
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=round(cpu_percent, 2),
                memory_usage_mb=round(memory_mb, 2),
                memory_percent=round(memory.percent, 2),
                disk_usage_gb=round(disk_used_gb, 2),
                disk_percent=round((disk.used / disk.total) * 100, 2),
                disk_free_gb=round(disk_free_gb, 2),
                network_sent_mb=round(sent_mb, 2),
                network_recv_mb=round(recv_mb, 2),
                load_average=load_avg,
                uptime_seconds=round(uptime, 2),
                process_count=process_count
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise
    
    async def check_disk_space(self, paths: Optional[List[str]] = None) -> List[DiskSpaceStatus]:
        """Check disk space for specified paths."""
        if paths is None:
            paths = self.monitored_paths
            
        disk_statuses = []
        
        for path in paths:
            try:
                if not Path(path).exists():
                    continue
                    
                usage = shutil.disk_usage(path)
                total_gb = usage.total / 1024 / 1024 / 1024
                used_gb = (usage.total - usage.free) / 1024 / 1024 / 1024
                free_gb = usage.free / 1024 / 1024 / 1024
                percent_used = (used_gb / total_gb) * 100
                
                is_critical = percent_used >= self.disk_critical_threshold
                is_warning = percent_used >= self.disk_warning_threshold
                
                disk_statuses.append(DiskSpaceStatus(
                    path=path,
                    total_gb=round(total_gb, 2),
                    used_gb=round(used_gb, 2),
                    free_gb=round(free_gb, 2),
                    percent_used=round(percent_used, 2),
                    is_critical=is_critical,
                    is_warning=is_warning
                ))
                
            except Exception as e:
                logger.warning(f"Error checking disk space for {path}: {e}")
                
        return disk_statuses
    
    async def check_network_connectivity(self, target_host: str = "8.8.8.8") -> NetworkStatus:
        """Check network connectivity with ping test."""
        try:
            # Get network interface info
            interfaces = psutil.net_if_addrs()
            active_interface = None
            ip_address = None
            
            # Find active network interface (not loopback)
            for iface_name, addresses in interfaces.items():
                if iface_name.startswith(('lo', 'Local')):
                    continue
                for addr in addresses:
                    if addr.family == 2:  # IPv4
                        active_interface = iface_name
                        ip_address = addr.address
                        break
                if active_interface:
                    break
            
            # Perform ping test
            try:
                import subprocess
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '3', target_host],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    # Extract ping time from output
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if 'time=' in line:
                            try:
                                time_part = line.split('time=')[1].split(' ')[0]
                                ping_ms = float(time_part)
                                break
                            except:
                                ping_ms = None
                    else:
                        ping_ms = None
                    
                    return NetworkStatus(
                        is_connected=True,
                        interface_name=active_interface,
                        ip_address=ip_address,
                        ping_latency_ms=ping_ms,
                        last_check=datetime.now()
                    )
                else:
                    return NetworkStatus(
                        is_connected=False,
                        interface_name=active_interface,
                        ip_address=ip_address,
                        ping_latency_ms=None,
                        last_check=datetime.now(),
                        error_message="Ping failed"
                    )
                    
            except subprocess.TimeoutExpired:
                return NetworkStatus(
                    is_connected=False,
                    interface_name=active_interface,
                    ip_address=ip_address,
                    ping_latency_ms=None,
                    last_check=datetime.now(),
                    error_message="Ping timeout"
                )
                
        except Exception as e:
            logger.error(f"Error checking network connectivity: {e}")
            return NetworkStatus(
                is_connected=False,
                interface_name=None,
                ip_address=None,
                ping_latency_ms=None,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    def get_system_alerts(self, metrics: SystemMetrics, disk_statuses: List[DiskSpaceStatus]) -> List[str]:
        """Generate system alert messages based on thresholds."""
        alerts = []
        
        # CPU alerts
        if metrics.cpu_percent >= self.cpu_warning_threshold:
            alerts.append(f"High CPU usage: {metrics.cpu_percent}%")
            
        # Memory alerts
        if metrics.memory_percent >= self.memory_warning_threshold:
            alerts.append(f"High memory usage: {metrics.memory_percent}%")
            
        # Disk space alerts
        for disk in disk_statuses:
            if disk.is_critical:
                alerts.append(f"Critical disk space on {disk.path}: {disk.percent_used}% used")
            elif disk.is_warning:
                alerts.append(f"Low disk space on {disk.path}: {disk.percent_used}% used")
                
        return alerts