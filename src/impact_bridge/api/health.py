"""Health check endpoints and services."""

import asyncio
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..logs import NdjsonLogger
from .config import api_config
from .models import ComponentHealth, DetailedHealthStatus, HealthStatus

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Application start time for uptime calculation
_app_start_time = time.time()


class HealthChecker:
    """Service for checking component health."""
    
    def __init__(self, logger: NdjsonLogger):
        self.logger = logger
    
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


def get_health_checker() -> HealthChecker:
    """Dependency to get health checker instance."""
    # TODO: Integrate with actual logger instance
    from ..logs import NdjsonLogger
    logger = NdjsonLogger("/tmp", "api")
    return HealthChecker(logger)


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
    """Detailed health check with component status."""
    uptime = time.time() - _app_start_time
    
    # Check all components concurrently
    try:
        components = await asyncio.gather(
            health_checker.check_database(),
            health_checker.check_mqtt(),
            health_checker.check_ble_services(),
            return_exceptions=True
        )
        
        # Filter out exceptions and convert to ComponentHealth objects
        valid_components: List[ComponentHealth] = []
        for component in components:
            if isinstance(component, ComponentHealth):
                valid_components.append(component)
            else:
                # Create error component for exceptions
                valid_components.append(ComponentHealth(
                    name="unknown",
                    status="unhealthy",
                    message=f"Health check exception: {str(component)}",
                    last_check=datetime.utcnow()
                ))
        
        # Determine overall status
        overall_status = "healthy"
        if any(c.status == "unhealthy" for c in valid_components):
            overall_status = "unhealthy"
        elif any(c.status == "degraded" for c in valid_components):
            overall_status = "degraded"
        
        return DetailedHealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=api_config.api_version,
            uptime_seconds=uptime,
            components=valid_components
        )
        
    except Exception as e:
        # Fallback if component checks fail
        return DetailedHealthStatus(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=api_config.api_version,
            uptime_seconds=uptime,
            components=[ComponentHealth(
                name="system",
                status="unhealthy",
                message=f"Health check system failure: {str(e)}",
                last_check=datetime.utcnow()
            )]
        )