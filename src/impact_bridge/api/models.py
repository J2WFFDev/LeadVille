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


# Range Officer (RO) Models

class ROTarget(BaseModel):
    """Range Officer target information."""
    
    id: int = Field(..., description="Target ID")
    label: str = Field(..., description="Target label")
    x: float = Field(..., description="X coordinate on stage layout")
    y: float = Field(..., description="Y coordinate on stage layout")
    status: str = Field(..., description="Target status (online, degraded, offline)")
    device_address: Optional[str] = Field(None, description="Associated device MAC address")
    last_hit: Optional[datetime] = Field(None, description="Last hit timestamp")


class ROStageLayout(BaseModel):
    """Range Officer stage layout configuration."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    stage_id: str = Field(..., description="Stage identifier")
    name: str = Field(..., description="Stage name")
    targets: List[ROTarget] = Field(..., description="List of targets in stage")
    width: float = Field(800, description="Stage layout width")
    height: float = Field(400, description="Stage layout height")


class ROHit(BaseModel):
    """Range Officer hit information."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: str = Field(..., description="Hit ID")
    target_id: int = Field(..., description="Target ID that was hit")
    timestamp: datetime = Field(..., description="Hit timestamp")
    x: Optional[float] = Field(None, description="Hit X coordinate on target")
    y: Optional[float] = Field(None, description="Hit Y coordinate on target")
    string_id: Optional[int] = Field(None, description="Associated string ID")


class ROString(BaseModel):
    """Range Officer string information."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: int = Field(..., description="String ID")
    shooter: str = Field(..., description="Shooter name/identifier")
    start_time: datetime = Field(..., description="String start timestamp")
    end_time: Optional[datetime] = Field(None, description="String end timestamp")
    hits: List[ROHit] = Field(default_factory=list, description="Hits in this string")
    stage_id: str = Field(..., description="Stage identifier")
    status: str = Field(..., description="String status (active, completed, cancelled)")


class ROStringRequest(BaseModel):
    """Request to start a new string."""
    
    shooter: str = Field(..., description="Shooter name/identifier")
    stage_id: str = Field(..., description="Stage identifier")


class ROStringResponse(BaseModel):
    """Response from string operations."""
    
    success: bool = Field(..., description="Whether operation was successful")
    string: Optional[ROString] = Field(None, description="String information")
    message: str = Field(..., description="Status message")


class ROSystemStatus(BaseModel):
    """Range Officer system status."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    system_online: bool = Field(..., description="Overall system status")
    active_string: Optional[ROString] = Field(None, description="Currently active string")
    total_targets: int = Field(..., description="Total number of targets")
    online_targets: int = Field(..., description="Number of online targets")
    degraded_targets: int = Field(..., description="Number of degraded targets")
    offline_targets: int = Field(..., description="Number of offline targets")
    last_update: datetime = Field(..., description="Last status update timestamp")


class ROHitRequest(BaseModel):
    """Request to register a hit."""
    
    target_id: int = Field(..., description="Target ID")
    timestamp: Optional[datetime] = Field(None, description="Hit timestamp (defaults to now)")
    x: Optional[float] = Field(None, description="Hit X coordinate")
    y: Optional[float] = Field(None, description="Hit Y coordinate")


class ROHitResponse(BaseModel):
    """Response from hit registration."""
    
    success: bool = Field(..., description="Whether hit was registered successfully")
    hit: Optional[ROHit] = Field(None, description="Hit information")
    message: str = Field(..., description="Status message")