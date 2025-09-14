"""System metrics and monitoring endpoints."""

import psutil
import time
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..monitoring import SystemMonitor, HealthAggregator, AlertManager
from .config import api_config
from .models import MetricsResponse, SystemMetricsResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Global counters for metrics
_request_counter = 0
_active_connections = 0
_app_start_time = time.time()

# Global monitoring instances
_system_monitor: Optional[SystemMonitor] = None
_health_aggregator: Optional[HealthAggregator] = None
_alert_manager: Optional[AlertManager] = None


def get_system_monitor() -> SystemMonitor:
    """Get or create the global system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor


def get_health_aggregator() -> HealthAggregator:
    """Get or create the global health aggregator instance."""
    global _health_aggregator
    if _health_aggregator is None:
        system_monitor = get_system_monitor()
        _health_aggregator = HealthAggregator(system_monitor=system_monitor)
    return _health_aggregator


def get_alert_manager() -> AlertManager:
    """Get or create the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(
            enable_mqtt_alerts=True,
            mqtt_topic_prefix="leadville/alerts"
        )
    return _alert_manager


def increment_request_counter():
    """Increment the global request counter."""
    global _request_counter
    _request_counter += 1


def increment_active_connections():
    """Increment active connections counter."""
    global _active_connections
    _active_connections += 1


def decrement_active_connections():
    """Decrement active connections counter."""
    global _active_connections
    _active_connections = max(0, _active_connections - 1)


@router.get("/metrics", response_model=MetricsResponse)
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def get_metrics(request: Request) -> MetricsResponse:
    """Get basic system metrics and performance statistics."""
    
    # Get system metrics
    memory_info = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    uptime = time.time() - _app_start_time
    
    return MetricsResponse(
        timestamp=datetime.utcnow(),
        total_requests=_request_counter,
        active_connections=_active_connections,
        memory_usage_mb=round(memory_info.used / 1024 / 1024, 2),
        cpu_usage_percent=round(cpu_percent, 2),
        uptime_seconds=uptime
    )


@router.get("/metrics/system", response_model=SystemMetricsResponse)
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def get_system_metrics(
    request: Request,
    system_monitor: SystemMonitor = Depends(get_system_monitor)
) -> SystemMetricsResponse:
    """Get comprehensive system metrics including disk, network, and processes."""
    try:
        # Get comprehensive system metrics
        metrics = await system_monitor.get_system_metrics()
        disk_statuses = await system_monitor.check_disk_space()
        network_status = await system_monitor.check_network_connectivity()
        
        # Generate alerts
        alerts = system_monitor.get_system_alerts(metrics, disk_statuses)
        
        return SystemMetricsResponse(
            timestamp=metrics.timestamp,
            cpu_percent=metrics.cpu_percent,
            memory_usage_mb=metrics.memory_usage_mb,
            memory_percent=metrics.memory_percent,
            disk_usage_gb=metrics.disk_usage_gb,
            disk_percent=metrics.disk_percent,
            disk_free_gb=metrics.disk_free_gb,
            network_sent_mb=metrics.network_sent_mb,
            network_recv_mb=metrics.network_recv_mb,
            load_average=metrics.load_average,
            uptime_seconds=metrics.uptime_seconds,
            process_count=metrics.process_count,
            disk_statuses=[disk.to_dict() for disk in disk_statuses],
            network_status=network_status.to_dict(),
            alerts=alerts,
            total_requests=_request_counter,
            active_connections=_active_connections
        )
        
    except Exception as e:
        # Fallback to basic metrics if comprehensive monitoring fails
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        uptime = time.time() - _app_start_time
        
        return SystemMetricsResponse(
            timestamp=datetime.utcnow(),
            cpu_percent=round(cpu_percent, 2),
            memory_usage_mb=round(memory_info.used / 1024 / 1024, 2),
            memory_percent=round(memory_info.percent, 2),
            disk_usage_gb=0.0,
            disk_percent=0.0,
            disk_free_gb=0.0,
            network_sent_mb=0.0,
            network_recv_mb=0.0,
            uptime_seconds=uptime,
            process_count=len(psutil.pids()),
            alerts=[f"System monitoring error: {str(e)}"],
            total_requests=_request_counter,
            active_connections=_active_connections
        )


@router.get("/metrics/alerts")
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def get_alert_metrics(
    request: Request,
    alert_manager: AlertManager = Depends(get_alert_manager)
) -> Dict[str, Any]:
    """Get alert statistics and active alerts."""
    return {
        'active_alerts': alert_manager.get_active_alerts(),
        'alert_statistics': alert_manager.get_alert_statistics(),
        'recent_alerts': alert_manager.get_alert_history(limit=20)
    }


@router.get("/metrics/monitoring")
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def get_monitoring_status(
    request: Request,
    health_aggregator: HealthAggregator = Depends(get_health_aggregator)
) -> Dict[str, Any]:
    """Get comprehensive monitoring and observability status."""
    try:
        # Get the last cached health status for performance
        last_health = health_aggregator.get_last_health_status()
        
        if last_health is None:
            # If no cached status, get fresh status
            last_health = await health_aggregator.get_aggregated_health()
        
        return {
            'monitoring_active': True,
            'last_health_check': last_health.timestamp.isoformat(),
            'overall_status': last_health.overall_status.value,
            'component_count': len(last_health.components),
            'alert_count': len(last_health.alerts),
            'system_uptime_seconds': last_health.uptime_seconds,
            'monitoring_uptime_seconds': time.time() - _app_start_time
        }
        
    except Exception as e:
        return {
            'monitoring_active': False,
            'error': str(e),
            'monitoring_uptime_seconds': time.time() - _app_start_time
        }