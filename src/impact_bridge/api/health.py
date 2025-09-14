"""Health check endpoints and services."""

import asyncio
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..logs import NdjsonLogger
from ..monitoring import HealthAggregator, SystemMonitor
from .config import api_config
from .models import ComponentHealth, DetailedHealthStatus, HealthStatus

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Application start time for uptime calculation
_app_start_time = time.time()

# Global health aggregator instance
_health_aggregator: Optional[HealthAggregator] = None


def get_health_aggregator() -> HealthAggregator:
    """Get or create the global health aggregator instance."""
    global _health_aggregator
    if _health_aggregator is None:
        system_monitor = SystemMonitor()
        _health_aggregator = HealthAggregator(system_monitor=system_monitor)
    return _health_aggregator


class HealthChecker:
    """Service for checking component health."""
    
    def __init__(self, logger: NdjsonLogger, health_aggregator: Optional[HealthAggregator] = None):
        self.logger = logger
        self.health_aggregator = health_aggregator or get_health_aggregator()
    
    async def check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        start_time = time.time()
        try:
            # TODO: Implement actual database health check when SQLAlchemy is integrated
            await asyncio.sleep(0.001)  # Simulate check
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="database",
                status="healthy",
                message="Database connection successful",
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata={"type": "sqlite", "url": api_config.database_url}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                name="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=response_time
            )
    
    async def check_mqtt(self) -> ComponentHealth:
        """Check MQTT broker connectivity."""
        start_time = time.time()
        try:
            # TODO: Implement actual MQTT health check when MQTT client is integrated
            await asyncio.sleep(0.001)  # Simulate check
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="mqtt",
                status="healthy",
                message="MQTT broker connection successful",
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata={
                    "broker_host": api_config.mqtt_broker_host,
                    "broker_port": api_config.mqtt_broker_port
                }
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"MQTT health check failed: {e}")
            return ComponentHealth(
                name="mqtt",
                status="unhealthy",
                message=f"MQTT broker connection failed: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=response_time
            )
    
    async def check_ble_services(self) -> ComponentHealth:
        """Check BLE services availability."""
        start_time = time.time()
        try:
            # TODO: Implement actual BLE health check when BLE services are integrated
            await asyncio.sleep(0.001)  # Simulate check
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="ble_services",
                status="healthy",
                message="BLE services operational",
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                metadata={"amg_timer": "ready", "bt50_sensors": "ready"}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"BLE services health check failed: {e}")
            return ComponentHealth(
                name="ble_services",
                status="unhealthy",
                message=f"BLE services failed: {str(e)}",
                last_check=datetime.utcnow(),
                response_time_ms=response_time
            )
    
    async def get_comprehensive_health(self) -> DetailedHealthStatus:
        """Get comprehensive health status using the health aggregator."""
        try:
            aggregated_health = await self.health_aggregator.get_aggregated_health()
            uptime = time.time() - _app_start_time
            
            # Convert monitoring ComponentHealth to API ComponentHealth
            api_components = []
            for comp in aggregated_health.components:
                api_components.append(ComponentHealth(
                    name=comp.name,
                    status=comp.status.value,
                    message=comp.message,
                    last_check=comp.last_check,
                    response_time_ms=comp.response_time_ms,
                    metadata=comp.metadata
                ))
            
            return DetailedHealthStatus(
                status=aggregated_health.overall_status.value,
                timestamp=aggregated_health.timestamp,
                version=api_config.api_version,
                uptime_seconds=uptime,
                components=api_components
            )
            
        except Exception as e:
            self.logger.error(f"Comprehensive health check failed: {e}")
            uptime = time.time() - _app_start_time
            return DetailedHealthStatus(
                status="unhealthy",
                timestamp=datetime.utcnow(),
                version=api_config.api_version,
                uptime_seconds=uptime,
                components=[ComponentHealth(
                    name="health_system",
                    status="unhealthy",
                    message=f"Health system failure: {str(e)}",
                    last_check=datetime.utcnow()
                )]
            )


def get_health_checker() -> HealthChecker:
    """Dependency to get health checker instance."""
    # TODO: Integrate with actual logger instance
    from ..logs import NdjsonLogger
    logger = NdjsonLogger("/tmp", "api")
    health_aggregator = get_health_aggregator()
    return HealthChecker(logger, health_aggregator)


@router.get("/health", response_model=HealthStatus)
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def basic_health_check(request: Request) -> HealthStatus:
    """Basic health check endpoint."""
    uptime = time.time() - _app_start_time
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=api_config.api_version,
        uptime_seconds=uptime
    )


@router.get("/health/detailed", response_model=DetailedHealthStatus)
@limiter.limit(f"{api_config.rate_limit_requests}/minute")
async def detailed_health_check(
    request: Request,
    health_checker: HealthChecker = Depends(get_health_checker)
) -> DetailedHealthStatus:
    """Detailed health check with comprehensive component status."""
    return await health_checker.get_comprehensive_health()


@router.get("/health/comprehensive", response_model=DetailedHealthStatus)
@limiter.limit(f"{api_config.rate_limit_requests}/minute")  
async def comprehensive_health_check(
    request: Request,
    health_checker: HealthChecker = Depends(get_health_checker)
) -> DetailedHealthStatus:
    """Comprehensive health check using advanced monitoring system."""
    return await health_checker.get_comprehensive_health()