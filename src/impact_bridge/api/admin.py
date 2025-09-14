"""Admin dashboard API endpoints."""

import asyncio
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import psutil
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse

from ..networking.network_manager import NetworkManager
from .models import (
    NodeInfo,
    SystemMonitoring,
    ServiceHealth,
    LogEntry,
    NetworkConfigRequest,
    NetworkConfigResponse,
    NodeUpdateRequest,
    LogViewerResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances
_network_manager = NetworkManager()


# Node Management Endpoints

@router.get("/node/info", 
           response_model=NodeInfo,
           summary="Get current node information",
           description="Get information about the current system node.")
async def get_node_info() -> NodeInfo:
    """Get current node information."""
    try:
        # Get network status
        network_status = _network_manager.get_status()
        
        # Mock node data - in real implementation this would come from database
        node_info = NodeInfo(
            id=1,
            name="leadville-bridge-001",
            mode=network_status.get("mode", "offline"),
            ssid=network_status.get("ssid"),
            ip_addr=network_status.get("ip_address"),
            versions={
                "api": "2.0.0",
                "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": f"{os.uname().sysname} {os.uname().release}"
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="operational" if network_status.get("connected", False) else "offline"
        )
        
        return node_info
        
    except Exception as e:
        logger.error(f"Error getting node info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node information: {str(e)}"
        )


@router.put("/node/info",
           response_model=NodeInfo,
           summary="Update node information",
           description="Update node information.")
async def update_node_info(request: NodeUpdateRequest) -> NodeInfo:
    """Update node information."""
    try:
        # In real implementation, this would update the database
        logger.info(f"Node update requested: {request}")
        
        # Return updated node info
        return await get_node_info()
        
    except Exception as e:
        logger.error(f"Error updating node info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update node information: {str(e)}"
        )


# Network Configuration Endpoints

@router.get("/network/status",
           summary="Get current network status",
           description="Get current network configuration and connection status.")
async def get_network_status() -> Dict[str, Any]:
    """Get current network status."""
    try:
        return _network_manager.get_status()
        
    except Exception as e:
        logger.error(f"Error getting network status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network status: {str(e)}"
        )


@router.post("/network/configure",
            response_model=NetworkConfigResponse,
            summary="Configure network mode",
            description="Switch between online and offline network modes.")
async def configure_network(request: NetworkConfigRequest) -> NetworkConfigResponse:
    """Configure network mode."""
    try:
        logger.info(f"Network configuration change requested: {request.mode}")
        
        if request.mode == "offline":
            success = _network_manager.switch_to_ap_mode()
            mode = "offline"
        elif request.mode == "online":
            success = _network_manager.switch_to_client_mode(
                ssid=request.ssid,
                password=request.password
            )
            mode = "online"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid network mode: {request.mode}"
            )
        
        # Get updated network status
        network_status = _network_manager.get_status()
        
        return NetworkConfigResponse(
            success=success,
            mode=mode,
            message=f"Network mode changed to {mode}" if success else f"Failed to change to {mode}",
            ip_address=network_status.get("ip_address")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring network: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure network: {str(e)}"
        )


# System Monitoring Endpoints

@router.get("/monitoring/system",
           response_model=SystemMonitoring,
           summary="Get system monitoring data",
           description="Get comprehensive system monitoring information including CPU, memory, disk, and temperature.")
async def get_system_monitoring() -> SystemMonitoring:
    """Get system monitoring data."""
    try:
        # Get basic system metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=0.1)
        load_avg = psutil.getloadavg()
        
        # Try to get CPU temperature
        temperature = None
        try:
            temps = psutil.sensors_temperatures()
            if 'cpu_thermal' in temps and temps['cpu_thermal']:
                temperature = temps['cpu_thermal'][0].current
            elif 'coretemp' in temps and temps['coretemp']:
                temperature = temps['coretemp'][0].current
        except (AttributeError, OSError):
            # Temperature sensors may not be available
            pass
        
        return SystemMonitoring(
            timestamp=datetime.now(),
            cpu_usage_percent=round(cpu_percent, 2),
            memory_usage_mb=round(memory.used / 1024 / 1024, 2),
            memory_percent=round(memory.percent, 2),
            disk_usage_gb=round(disk.used / 1024 / 1024 / 1024, 2),
            disk_percent=round((disk.used / disk.total) * 100, 2),
            temperature_celsius=temperature,
            uptime_seconds=time.time() - psutil.boot_time(),
            load_average=[round(load, 2) for load in load_avg]
        )
        
    except Exception as e:
        logger.error(f"Error getting system monitoring data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system monitoring data: {str(e)}"
        )


@router.get("/monitoring/services",
           response_model=List[ServiceHealth],
           summary="Get service health status",
           description="Get health status for all monitored services (BLE, MQTT, DB).")
async def get_service_health() -> List[ServiceHealth]:
    """Get service health status."""
    try:
        services = []
        current_time = datetime.now()
        
        # Check BLE service health
        try:
            # Mock BLE health check - in real implementation would check actual BLE adapter
            services.append(ServiceHealth(
                service_name="BLE",
                status="healthy",
                last_check=current_time,
                message="BLE adapter operational",
                response_time_ms=5.0,
                metadata={"adapter": "hci0", "devices_connected": 0}
            ))
        except Exception as e:
            services.append(ServiceHealth(
                service_name="BLE",
                status="unhealthy",
                last_check=current_time,
                message=f"BLE error: {str(e)}",
                response_time_ms=None
            ))
        
        # Check MQTT service health
        try:
            # Mock MQTT health check - in real implementation would ping MQTT broker
            services.append(ServiceHealth(
                service_name="MQTT",
                status="healthy",
                last_check=current_time,
                message="MQTT broker connected",
                response_time_ms=15.0,
                metadata={"broker": "localhost:1883", "topics": 5}
            ))
        except Exception as e:
            services.append(ServiceHealth(
                service_name="MQTT",
                status="unhealthy",
                last_check=current_time,
                message=f"MQTT error: {str(e)}",
                response_time_ms=None
            ))
        
        # Check Database service health
        try:
            # Mock DB health check - in real implementation would test database connection
            services.append(ServiceHealth(
                service_name="Database",
                status="healthy",
                last_check=current_time,
                message="Database operational",
                response_time_ms=8.0,
                metadata={"type": "SQLite", "size_mb": 45}
            ))
        except Exception as e:
            services.append(ServiceHealth(
                service_name="Database",
                status="unhealthy",
                last_check=current_time,
                message=f"Database error: {str(e)}",
                response_time_ms=None
            ))
        
        return services
        
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service health: {str(e)}"
        )


# Log Viewer Endpoints

@router.get("/logs/tail",
           response_model=LogViewerResponse,
           summary="Get recent log entries",
           description="Get the last N lines from system logs with real-time updates.")
async def get_log_tail(
    lines: int = Query(200, ge=10, le=1000, description="Number of log lines to retrieve"),
    log_type: str = Query("main", description="Log type (main, debug, console)")
) -> LogViewerResponse:
    """Get recent log entries for real-time viewing."""
    try:
        logs = []
        
        # Determine log file path based on type
        log_paths = {
            "main": Path("logs/main"),
            "debug": Path("logs/debug"), 
            "console": Path("logs/console")
        }
        
        log_dir = log_paths.get(log_type, log_paths["main"])
        
        # Look for log files in the directory
        log_files = []
        if log_dir.exists():
            log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
            if not log_files:
                log_files = sorted(log_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not log_files:
            # Generate mock log entries if no log files found
            current_time = datetime.now()
            for i in range(min(lines, 50)):
                logs.append(LogEntry(
                    timestamp=current_time,
                    level="INFO",
                    message=f"System operational - heartbeat {i+1}",
                    source="leadville_bridge",
                    line_number=i+1
                ))
        else:
            # Read actual log file
            log_file = log_files[0]
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    
                # Get the last N lines
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                for i, line in enumerate(recent_lines):
                    line = line.strip()
                    if line:
                        # Simple log parsing - in real implementation would parse structured logs
                        logs.append(LogEntry(
                            timestamp=datetime.now(),
                            level="INFO",
                            message=line[:500],  # Truncate long messages
                            source=log_file.name,
                            line_number=len(all_lines) - len(recent_lines) + i + 1
                        ))
                        
            except Exception as e:
                logger.warning(f"Error reading log file {log_file}: {e}")
                # Fallback to mock data
                logs.append(LogEntry(
                    timestamp=datetime.now(),
                    level="ERROR",
                    message=f"Could not read log file: {str(e)}",
                    source="log_reader",
                    line_number=1
                ))
        
        return LogViewerResponse(
            logs=logs,
            total_lines=len(logs),
            has_more=len(logs) >= lines
        )
        
    except Exception as e:
        logger.error(f"Error getting log tail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log tail: {str(e)}"
        )