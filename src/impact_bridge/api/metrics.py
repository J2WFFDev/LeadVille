"""System metrics and monitoring endpoints."""

import psutil
import time
from datetime import datetime

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import api_config
from .models import MetricsResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Global counters for metrics
_request_counter = 0
_active_connections = 0
_app_start_time = time.time()


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
    """Get system metrics and performance statistics."""
    
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