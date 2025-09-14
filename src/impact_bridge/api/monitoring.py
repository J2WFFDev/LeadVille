"""Monitoring and observability API endpoints."""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Request, Depends, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..monitoring import SystemMonitor, HealthAggregator, LEDController, AlertManager
from .config import api_config
from .models import LEDStatusResponse, MonitoringStatusResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Global monitoring instances
_system_monitor: SystemMonitor = None
_health_aggregator: HealthAggregator = None
_led_controller: LEDController = None
_alert_manager: AlertManager = None
_monitoring_task: asyncio.Task = None


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


def get_led_controller() -> LEDController:
    """Get or create the global LED controller instance."""
    global _led_controller
    if _led_controller is None:
        # Enable simulation mode for development/testing
        _led_controller = LEDController(enable_hardware=True, simulation_mode=True)
    return _led_controller


def get_alert_manager() -> AlertManager:
    """Get or create the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(
            enable_mqtt_alerts=True,
            mqtt_topic_prefix="leadville/alerts"
        )
    return _alert_manager


@router.get("/monitoring/status", response_model=MonitoringStatusResponse)
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def get_monitoring_status(
    request: Request,
    health_aggregator: HealthAggregator = Depends(get_health_aggregator)
) -> MonitoringStatusResponse:
    """Get comprehensive monitoring system status."""
    try:
        # Get the last cached health status for performance
        last_health = health_aggregator.get_last_health_status()
        
        if last_health is None:
            # If no cached status, get fresh status
            last_health = await health_aggregator.get_aggregated_health()
        
        return MonitoringStatusResponse(
            monitoring_active=True,
            last_health_check=last_health.timestamp,
            overall_status=last_health.overall_status.value,
            component_count=len(last_health.components),
            alert_count=len(last_health.alerts),
            system_uptime_seconds=last_health.uptime_seconds,
            monitoring_uptime_seconds=time.time() - last_health.uptime_seconds
        )
        
    except Exception as e:
        return MonitoringStatusResponse(
            monitoring_active=False,
            last_health_check=datetime.utcnow(),
            overall_status="error",
            component_count=0,
            alert_count=1,
            system_uptime_seconds=0.0,
            monitoring_uptime_seconds=0.0
        )


@router.get("/monitoring/leds", response_model=LEDStatusResponse)
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def get_led_status(
    request: Request,
    led_controller: LEDController = Depends(get_led_controller)
) -> LEDStatusResponse:
    """Get status of all LED health indicators."""
    led_statuses = led_controller.get_led_status()
    
    return LEDStatusResponse(
        led_statuses=led_statuses,
        hardware_enabled=led_controller.enable_hardware,
        simulation_mode=led_controller.simulation_mode
    )


@router.post("/monitoring/leds/test")
@limiter.limit("5/minute")  # Stricter limit for test operations
async def test_leds(
    request: Request,
    duration: float = Query(default=2.0, ge=0.5, le=10.0),
    led_controller: LEDController = Depends(get_led_controller)
) -> Dict[str, Any]:
    """Test all LED indicators by cycling through states."""
    try:
        await led_controller.test_all_leds(duration=duration)
        return {
            "status": "success",
            "message": f"LED test completed (duration: {duration}s)",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"LED test failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/monitoring/dashboard")
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def get_monitoring_dashboard(
    request: Request,
    system_monitor: SystemMonitor = Depends(get_system_monitor),
    health_aggregator: HealthAggregator = Depends(get_health_aggregator),
    alert_manager: AlertManager = Depends(get_alert_manager),
    led_controller: LEDController = Depends(get_led_controller)
) -> Dict[str, Any]:
    """Get comprehensive monitoring dashboard data."""
    try:
        # Get all monitoring data concurrently
        dashboard_data = await asyncio.gather(
            system_monitor.get_system_metrics(),
            system_monitor.check_disk_space(),
            system_monitor.check_network_connectivity(),
            health_aggregator.get_aggregated_health(),
            return_exceptions=True
        )
        
        system_metrics, disk_statuses, network_status, health_status = dashboard_data
        
        # Handle any exceptions
        if isinstance(system_metrics, Exception):
            system_metrics = None
        if isinstance(disk_statuses, Exception):
            disk_statuses = []
        if isinstance(network_status, Exception):
            network_status = None
        if isinstance(health_status, Exception):
            health_status = None
        
        # Get alert information
        active_alerts = alert_manager.get_active_alerts()
        alert_stats = alert_manager.get_alert_statistics()
        
        # Get LED statuses
        led_statuses = led_controller.get_led_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": system_metrics.to_dict() if system_metrics else None,
            "disk_statuses": [disk.to_dict() for disk in disk_statuses],
            "network_status": network_status.to_dict() if network_status else None,
            "health_status": health_status.to_dict() if health_status else None,
            "active_alerts": active_alerts,
            "alert_statistics": alert_stats,
            "led_statuses": led_statuses,
            "monitoring_info": {
                "hardware_enabled": led_controller.enable_hardware,
                "simulation_mode": led_controller.simulation_mode,
                "monitored_components": len(health_status.components) if health_status else 0,
                "system_uptime_seconds": system_metrics.uptime_seconds if system_metrics else 0.0
            }
        }
        
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "monitoring_active": False
        }


@router.post("/monitoring/start")
@limiter.limit("2/minute")  # Very strict limit for control operations
async def start_monitoring(
    request: Request,
    health_aggregator: HealthAggregator = Depends(get_health_aggregator),
    alert_manager: AlertManager = Depends(get_alert_manager)
) -> Dict[str, Any]:
    """Start continuous health monitoring and alerting."""
    global _monitoring_task
    
    try:
        # Start health monitoring
        await health_aggregator.start_monitoring()
        
        # Start monitoring task that processes alerts
        if _monitoring_task is None or _monitoring_task.done():
            _monitoring_task = asyncio.create_task(_monitoring_loop(health_aggregator, alert_manager))
        
        return {
            "status": "success",
            "message": "Monitoring started successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to start monitoring: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/monitoring/stop")
@limiter.limit("2/minute")  # Very strict limit for control operations
async def stop_monitoring(
    request: Request,
    health_aggregator: HealthAggregator = Depends(get_health_aggregator)
) -> Dict[str, Any]:
    """Stop continuous health monitoring."""
    global _monitoring_task
    
    try:
        # Stop health monitoring
        await health_aggregator.stop_monitoring()
        
        # Cancel monitoring task
        if _monitoring_task and not _monitoring_task.done():
            _monitoring_task.cancel()
            try:
                await _monitoring_task
            except asyncio.CancelledError:
                pass
        
        return {
            "status": "success",
            "message": "Monitoring stopped successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to stop monitoring: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


async def _monitoring_loop(health_aggregator: HealthAggregator, alert_manager: AlertManager):
    """Main monitoring loop that processes health status and alerts."""
    led_controller = get_led_controller()
    
    while True:
        try:
            # Get current health status
            health_status = await health_aggregator.get_aggregated_health()
            
            # Process alerts
            await alert_manager.process_health_status(health_status)
            
            # Update LED indicators
            await led_controller.update_from_health_status(health_status)
            
            # Wait before next check
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            # Log error but continue monitoring
            print(f"Error in monitoring loop: {e}")
            await asyncio.sleep(30)


@router.get("/monitoring/logs")
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def get_monitoring_logs(
    request: Request,
    lines: int = Query(default=100, ge=1, le=1000)
) -> Dict[str, Any]:
    """Get recent monitoring and alert logs."""
    # This would integrate with the actual logging system
    # For now, return placeholder data
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "log_lines": lines,
        "logs": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "component": "monitoring",
                "message": "Monitoring system operational"
            }
        ]
    }