"""Pydantic models for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class HealthStatus(BaseModel):
    """Basic health status response."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


class ComponentHealth(BaseModel):
    """Individual component health status."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    name: str = Field(..., description="Component name")
    status: str = Field(..., description="Component status (healthy, degraded, unhealthy)")
    message: Optional[str] = Field(None, description="Status message")
    last_check: datetime = Field(..., description="Last health check time")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional component metadata")


class DetailedHealthStatus(BaseModel):
    """Detailed health status with component information."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    components: List[ComponentHealth] = Field(..., description="Individual component health")


class MetricsResponse(BaseModel):
    """System metrics response."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    timestamp: datetime = Field(..., description="Metrics collection timestamp")
    total_requests: int = Field(..., description="Total number of requests processed")
    active_connections: int = Field(..., description="Current active connections")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(..., description="Error timestamp")


class APIInfo(BaseModel):
    """API information response."""
    
    title: str = Field(..., description="API title")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    contact: Optional[Dict[str, str]] = Field(None, description="Contact information")
    license: Optional[Dict[str, str]] = Field(None, description="License information")


# Device Management Models

class DiscoveredDevice(BaseModel):
    """Discovered BLE device information."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    address: str = Field(..., description="Device MAC address")
    name: Optional[str] = Field(None, description="Device name")
    rssi: int = Field(..., description="Signal strength in dBm")
    manufacturer_data: Dict[int, str] = Field(default_factory=dict, description="Manufacturer data (hex encoded)")
    service_uuids: List[str] = Field(default_factory=list, description="Advertised service UUIDs")
    local_name: Optional[str] = Field(None, description="Local device name")
    is_connectable: bool = Field(True, description="Whether device accepts connections")
    device_type: Optional[str] = Field(None, description="Identified device type (bt50, amg, unknown)")


class DeviceHealthStatus(BaseModel):
    """Device health status information."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    address: str = Field(..., description="Device MAC address")
    is_connected: bool = Field(..., description="Current connection status")
    rssi: Optional[int] = Field(None, description="Signal strength in dBm")
    battery_level: Optional[float] = Field(None, description="Battery level percentage")
    last_seen: datetime = Field(..., description="Last successful contact timestamp")
    connection_attempts: int = Field(0, description="Number of connection attempts")
    last_error: Optional[str] = Field(None, description="Last error message")


class DeviceInfo(BaseModel):
    """Complete device information."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    address: str = Field(..., description="Device MAC address")
    label: str = Field(..., description="Device label/name")
    target_id: Optional[int] = Field(None, description="Assigned target ID")
    node_id: Optional[int] = Field(None, description="Assigned node ID")
    last_seen: Optional[datetime] = Field(None, description="Last seen timestamp")
    battery: Optional[float] = Field(None, description="Battery level percentage")
    rssi: Optional[int] = Field(None, description="Signal strength in dBm")
    calibration: Optional[Dict[str, Any]] = Field(None, description="Device calibration data")
    is_connected: bool = Field(False, description="Current connection status")
    last_error: Optional[str] = Field(None, description="Last error message")
    connection_attempts: int = Field(0, description="Number of connection attempts")


class DeviceDiscoveryRequest(BaseModel):
    """Request to start device discovery."""
    
    duration: float = Field(10.0, ge=1.0, le=60.0, description="Discovery duration in seconds")


class DeviceDiscoveryResponse(BaseModel):
    """Response from device discovery."""
    
    devices: List[DiscoveredDevice] = Field(..., description="List of discovered devices")
    duration: float = Field(..., description="Actual discovery duration")
    total_found: int = Field(..., description="Total number of devices found")


class DevicePairRequest(BaseModel):
    """Request to pair with a device."""
    
    address: str = Field(..., description="Device MAC address")
    device_type: str = Field("unknown", description="Device type hint")


class DevicePairResponse(BaseModel):
    """Response from device pairing attempt."""
    
    success: bool = Field(..., description="Whether pairing was successful")
    address: str = Field(..., description="Device MAC address")
    message: str = Field(..., description="Status message")


class DeviceAssignRequest(BaseModel):
    """Request to assign device to target."""
    
    address: str = Field(..., description="Device MAC address")
    target_id: int = Field(..., description="Target ID to assign to")


class DeviceAssignResponse(BaseModel):
    """Response from device assignment."""
    
    success: bool = Field(..., description="Whether assignment was successful")
    address: str = Field(..., description="Device MAC address")
    target_id: int = Field(..., description="Target ID")
    message: str = Field(..., description="Status message")


class DeviceUnassignRequest(BaseModel):
    """Request to unassign device from target."""
    
    address: str = Field(..., description="Device MAC address")


class DeviceUnassignResponse(BaseModel):
    """Response from device unassignment."""
    
    success: bool = Field(..., description="Whether unassignment was successful")
    address: str = Field(..., description="Device MAC address")
    message: str = Field(..., description="Status message")


class DeviceListResponse(BaseModel):
    """Response containing list of devices."""
    
    devices: List[DeviceInfo] = Field(..., description="List of devices")
    total: int = Field(..., description="Total number of devices")


class DeviceHealthMonitoringRequest(BaseModel):
    """Request to start/stop health monitoring."""
    
    enabled: bool = Field(..., description="Enable or disable monitoring")
    interval: float = Field(30.0, ge=5.0, le=300.0, description="Monitoring interval in seconds")


class DeviceHealthMonitoringResponse(BaseModel):
    """Response from health monitoring operation."""
    
    success: bool = Field(..., description="Whether operation was successful")
    enabled: bool = Field(..., description="Current monitoring status")
    interval: Optional[float] = Field(None, description="Current monitoring interval")
    message: str = Field(..., description="Status message")


# Admin Dashboard Models

class NodeInfo(BaseModel):
    """Node information for admin dashboard."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: int = Field(..., description="Node ID")
    name: str = Field(..., description="Node name")
    mode: str = Field(..., description="Network mode (online, offline, simulation)")
    ssid: Optional[str] = Field(None, description="Connected SSID")
    ip_addr: Optional[str] = Field(None, description="IP address")
    versions: Optional[Dict[str, str]] = Field(None, description="Software version information")
    created_at: datetime = Field(..., description="Node creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    status: str = Field(..., description="Current node status")


class SystemMonitoring(BaseModel):
    """Extended system monitoring information."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    timestamp: datetime = Field(..., description="Monitoring timestamp")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    memory_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_gb: float = Field(..., description="Disk usage in GB")
    disk_percent: float = Field(..., description="Disk usage percentage")
    temperature_celsius: Optional[float] = Field(None, description="CPU temperature in Celsius")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    load_average: List[float] = Field(..., description="System load average (1, 5, 15 min)")


class ServiceHealth(BaseModel):
    """Service health status information."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    last_check: datetime = Field(..., description="Last health check timestamp")
    message: Optional[str] = Field(None, description="Status message")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional service metadata")


class LogEntry(BaseModel):
    """Log entry for real-time viewer."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    timestamp: datetime = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    source: Optional[str] = Field(None, description="Log source")
    line_number: Optional[int] = Field(None, description="Line number in log file")


class NetworkConfigRequest(BaseModel):
    """Network configuration change request."""
    
    mode: str = Field(..., description="Network mode (online/offline)")
    ssid: Optional[str] = Field(None, description="WiFi SSID for online mode")
    password: Optional[str] = Field(None, description="WiFi password for online mode")


class NetworkConfigResponse(BaseModel):
    """Network configuration change response."""
    
    success: bool = Field(..., description="Whether configuration change was successful")
    mode: str = Field(..., description="Current network mode")
    message: str = Field(..., description="Status message")
    ip_address: Optional[str] = Field(None, description="Current IP address")


class NodeUpdateRequest(BaseModel):
    """Request to update node information."""
    
    name: Optional[str] = Field(None, description="Node name")
    mode: Optional[str] = Field(None, description="Network mode")
    versions: Optional[Dict[str, str]] = Field(None, description="Version information")


class LogViewerResponse(BaseModel):
    """Log viewer response with log entries."""
    
    logs: List[LogEntry] = Field(..., description="Log entries")
    total_lines: int = Field(..., description="Total lines available")
    has_more: bool = Field(..., description="Whether there are more logs available")