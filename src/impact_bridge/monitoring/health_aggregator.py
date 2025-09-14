"""Health status aggregation and monitoring coordination."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from .system_monitor import SystemMonitor, SystemMetrics, DiskSpaceStatus, NetworkStatus

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Overall health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Individual component health status."""
    name: str
    status: HealthStatus
    message: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_check'] = self.last_check.isoformat()
        return data


@dataclass
class AggregatedHealth:
    """Aggregated system health status."""
    overall_status: HealthStatus
    timestamp: datetime
    components: List[ComponentHealth]
    system_metrics: Optional[SystemMetrics]
    alerts: List[str]
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'overall_status': self.overall_status.value,
            'timestamp': self.timestamp.isoformat(),
            'components': [comp.to_dict() for comp in self.components],
            'system_metrics': self.system_metrics.to_dict() if self.system_metrics else None,
            'alerts': self.alerts,
            'uptime_seconds': self.uptime_seconds
        }


class HealthAggregator:
    """Coordinates health checks across all system components."""
    
    def __init__(self, 
                 system_monitor: Optional[SystemMonitor] = None,
                 check_interval: float = 30.0):
        self.system_monitor = system_monitor or SystemMonitor()
        self.check_interval = check_interval
        
        # Component health checkers
        self._health_checkers: Dict[str, Callable] = {}
        self._last_health_status: Optional[AggregatedHealth] = None
        self._start_time = time.time()
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Default health checkers
        self._setup_default_checkers()
    
    def _setup_default_checkers(self):
        """Setup default health check functions."""
        self._health_checkers = {
            'system_resources': self._check_system_resources,
            'disk_space': self._check_disk_space,
            'network_connectivity': self._check_network_connectivity,
        }
    
    def register_health_checker(self, name: str, checker_func: Callable):
        """Register a custom health checker function.
        
        Args:
            name: Unique name for the health checker
            checker_func: Async function that returns ComponentHealth
        """
        self._health_checkers[name] = checker_func
        logger.info(f"Registered health checker: {name}")
    
    async def _check_system_resources(self) -> ComponentHealth:
        """Check system resource health (CPU, memory)."""
        try:
            start_time = time.time()
            metrics = await self.system_monitor.get_system_metrics()
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            messages = []
            
            if metrics.cpu_percent >= 90:
                status = HealthStatus.CRITICAL
                messages.append(f"Critical CPU usage: {metrics.cpu_percent}%")
            elif metrics.cpu_percent >= 80:
                status = HealthStatus.WARNING
                messages.append(f"High CPU usage: {metrics.cpu_percent}%")
            
            if metrics.memory_percent >= 95:
                status = HealthStatus.CRITICAL
                messages.append(f"Critical memory usage: {metrics.memory_percent}%")
            elif metrics.memory_percent >= 85:
                status = HealthStatus.WARNING
                messages.append(f"High memory usage: {metrics.memory_percent}%")
            
            if not messages:
                messages.append("System resources within normal limits")
            
            return ComponentHealth(
                name="system_resources",
                status=status,
                message="; ".join(messages),
                last_check=datetime.now(),
                response_time_ms=response_time,
                metadata={
                    'cpu_percent': metrics.cpu_percent,
                    'memory_percent': metrics.memory_percent,
                    'load_average': metrics.load_average
                }
            )
            
        except Exception as e:
            logger.error(f"System resource health check failed: {e}")
            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                last_check=datetime.now()
            )
    
    async def _check_disk_space(self) -> ComponentHealth:
        """Check disk space health."""
        try:
            start_time = time.time()
            disk_statuses = await self.system_monitor.check_disk_space()
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY
            messages = []
            
            critical_disks = [d for d in disk_statuses if d.is_critical]
            warning_disks = [d for d in disk_statuses if d.is_warning and not d.is_critical]
            
            if critical_disks:
                status = HealthStatus.CRITICAL
                for disk in critical_disks:
                    messages.append(f"{disk.path}: {disk.percent_used}% full (critical)")
            
            if warning_disks and status != HealthStatus.CRITICAL:
                status = HealthStatus.WARNING
                for disk in warning_disks:
                    messages.append(f"{disk.path}: {disk.percent_used}% full (warning)")
            
            if not messages:
                messages.append("Disk space within normal limits")
            
            return ComponentHealth(
                name="disk_space",
                status=status,
                message="; ".join(messages),
                last_check=datetime.now(),
                response_time_ms=response_time,
                metadata={
                    'monitored_paths': [d.to_dict() for d in disk_statuses]
                }
            )
            
        except Exception as e:
            logger.error(f"Disk space health check failed: {e}")
            return ComponentHealth(
                name="disk_space",
                status=HealthStatus.CRITICAL,
                message=f"Disk check failed: {str(e)}",
                last_check=datetime.now()
            )
    
    async def _check_network_connectivity(self) -> ComponentHealth:
        """Check network connectivity health."""
        try:
            start_time = time.time()
            network_status = await self.system_monitor.check_network_connectivity()
            response_time = (time.time() - start_time) * 1000
            
            if network_status.is_connected:
                status = HealthStatus.HEALTHY
                message = f"Network connected via {network_status.interface_name}"
                if network_status.ping_latency_ms:
                    message += f" (ping: {network_status.ping_latency_ms}ms)"
            else:
                status = HealthStatus.CRITICAL
                message = network_status.error_message or "Network disconnected"
            
            return ComponentHealth(
                name="network_connectivity",
                status=status,
                message=message,
                last_check=datetime.now(),
                response_time_ms=response_time,
                metadata=network_status.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Network connectivity health check failed: {e}")
            return ComponentHealth(
                name="network_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Network check failed: {str(e)}",
                last_check=datetime.now()
            )
    
    async def check_ble_services(self) -> ComponentHealth:
        """Check BLE services health (placeholder for integration)."""
        # This will be enhanced when integrated with actual BLE services
        return ComponentHealth(
            name="ble_services",
            status=HealthStatus.UNKNOWN,
            message="BLE health check not implemented",
            last_check=datetime.now(),
            metadata={'implementation': 'placeholder'}
        )
    
    async def check_mqtt_broker(self) -> ComponentHealth:
        """Check MQTT broker health (placeholder for integration)."""
        # This will be enhanced when integrated with actual MQTT client
        return ComponentHealth(
            name="mqtt_broker",
            status=HealthStatus.UNKNOWN,
            message="MQTT health check not implemented",
            last_check=datetime.now(),
            metadata={'implementation': 'placeholder'}
        )
    
    async def check_database(self) -> ComponentHealth:
        """Check database health (placeholder for integration)."""
        # This will be enhanced when integrated with actual database
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNKNOWN,
            message="Database health check not implemented",
            last_check=datetime.now(),
            metadata={'implementation': 'placeholder'}
        )
    
    async def check_ntp_synchronization(self) -> ComponentHealth:
        """Check NTP time synchronization (placeholder for integration)."""
        # This will be enhanced when integrated with NTP client
        return ComponentHealth(
            name="ntp_sync",
            status=HealthStatus.UNKNOWN,
            message="NTP sync check not implemented",
            last_check=datetime.now(),
            metadata={'implementation': 'placeholder'}
        )
    
    async def get_aggregated_health(self) -> AggregatedHealth:
        """Get comprehensive health status for all components."""
        try:
            # Run all health checks concurrently
            health_tasks = {
                name: checker() for name, checker in self._health_checkers.items()
            }
            
            # Add placeholder checks that will be integrated later
            health_tasks.update({
                'ble_services': self.check_ble_services(),
                'mqtt_broker': self.check_mqtt_broker(),
                'database': self.check_database(),
                'ntp_sync': self.check_ntp_synchronization()
            })
            
            component_results = await asyncio.gather(
                *health_tasks.values(),
                return_exceptions=True
            )
            
            # Process results
            components = []
            for name, result in zip(health_tasks.keys(), component_results):
                if isinstance(result, Exception):
                    logger.error(f"Health check {name} failed: {result}")
                    components.append(ComponentHealth(
                        name=name,
                        status=HealthStatus.CRITICAL,
                        message=f"Health check exception: {str(result)}",
                        last_check=datetime.now()
                    ))
                else:
                    components.append(result)
            
            # Get system metrics
            try:
                system_metrics = await self.system_monitor.get_system_metrics()
                disk_statuses = await self.system_monitor.check_disk_space()
                alerts = self.system_monitor.get_system_alerts(system_metrics, disk_statuses)
            except Exception as e:
                logger.error(f"Failed to collect system metrics: {e}")
                system_metrics = None
                alerts = [f"System metrics collection failed: {str(e)}"]
            
            # Determine overall status
            overall_status = self._determine_overall_status(components)
            
            # Calculate uptime
            uptime = time.time() - self._start_time
            
            aggregated = AggregatedHealth(
                overall_status=overall_status,
                timestamp=datetime.now(),
                components=components,
                system_metrics=system_metrics,
                alerts=alerts,
                uptime_seconds=uptime
            )
            
            self._last_health_status = aggregated
            return aggregated
            
        except Exception as e:
            logger.error(f"Failed to aggregate health status: {e}")
            return AggregatedHealth(
                overall_status=HealthStatus.CRITICAL,
                timestamp=datetime.now(),
                components=[ComponentHealth(
                    name="health_aggregator",
                    status=HealthStatus.CRITICAL,
                    message=f"Health aggregation failed: {str(e)}",
                    last_check=datetime.now()
                )],
                system_metrics=None,
                alerts=[f"Health aggregation failed: {str(e)}"],
                uptime_seconds=time.time() - self._start_time
            )
    
    def _determine_overall_status(self, components: List[ComponentHealth]) -> HealthStatus:
        """Determine overall system status from component statuses."""
        statuses = [comp.status for comp in components]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in statuses:
            return HealthStatus.WARNING  # Treat unknown as warning
        else:
            return HealthStatus.HEALTHY
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Health monitoring already running")
            return
            
        logger.info("Starting health monitoring")
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous health monitoring loop."""
        while True:
            try:
                health_status = await self.get_aggregated_health()
                
                # Log health status changes
                if health_status.overall_status != HealthStatus.HEALTHY:
                    logger.warning(f"System health: {health_status.overall_status.value}")
                    for alert in health_status.alerts:
                        logger.warning(f"Alert: {alert}")
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def get_last_health_status(self) -> Optional[AggregatedHealth]:
        """Get the last cached health status."""
        return self._last_health_status