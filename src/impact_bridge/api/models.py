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


class SystemMetricsResponse(BaseModel):
    """Comprehensive system metrics response."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    timestamp: datetime = Field(..., description="Metrics collection timestamp")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    memory_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_gb: float = Field(..., description="Disk usage in GB")
    disk_percent: float = Field(..., description="Disk usage percentage")
    disk_free_gb: float = Field(..., description="Disk free space in GB")
    network_sent_mb: float = Field(..., description="Network data sent in MB")
    network_recv_mb: float = Field(..., description="Network data received in MB")
    load_average: Optional[List[float]] = Field(None, description="System load average")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    process_count: int = Field(..., description="Number of running processes")
    disk_statuses: List[Dict[str, Any]] = Field(default_factory=list, description="Disk space status for monitored paths")
    network_status: Optional[Dict[str, Any]] = Field(None, description="Network connectivity status")
    alerts: List[str] = Field(default_factory=list, description="Active system alerts")
    total_requests: int = Field(..., description="Total API requests processed")
    active_connections: int = Field(..., description="Current active connections")


class MonitoringStatusResponse(BaseModel):
    """Monitoring system status response."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    monitoring_active: bool = Field(..., description="Whether monitoring is active")
    last_health_check: datetime = Field(..., description="Last health check timestamp")
    overall_status: str = Field(..., description="Overall system health status")
    component_count: int = Field(..., description="Number of monitored components")
    alert_count: int = Field(..., description="Number of active alerts")
    system_uptime_seconds: float = Field(..., description="System uptime")
    monitoring_uptime_seconds: float = Field(..., description="Monitoring system uptime")


class LEDStatusResponse(BaseModel):
    """LED status indicators response."""
    
    led_statuses: Dict[str, Dict[str, Any]] = Field(..., description="Status of all LED indicators")
    hardware_enabled: bool = Field(..., description="Whether hardware LED control is enabled")
    simulation_mode: bool = Field(..., description="Whether running in simulation mode")


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


# Scorekeeper Interface Models

class RunInfo(BaseModel):
    """Basic run information for scorekeeper interface."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: int = Field(..., description="Run ID")
    match_id: int = Field(..., description="Match ID")
    stage_id: int = Field(..., description="Stage ID")
    shooter_id: int = Field(..., description="Shooter ID")
    shooter_name: str = Field(..., description="Shooter name")
    squad: Optional[str] = Field(None, description="Shooter squad")
    stage_name: str = Field(..., description="Stage name")
    stage_number: int = Field(..., description="Stage number")
    match_name: str = Field(..., description="Match name")
    status: str = Field(..., description="Run status")
    started_ts: Optional[datetime] = Field(None, description="Run start timestamp")
    ended_ts: Optional[datetime] = Field(None, description="Run end timestamp")
    timer_events_count: int = Field(0, description="Number of timer events")
    sensor_events_count: int = Field(0, description="Number of sensor events")
    has_notes: bool = Field(False, description="Whether run has notes")
    created_at: datetime = Field(..., description="Run creation timestamp")
    updated_at: datetime = Field(..., description="Run last updated timestamp")


class RunsListRequest(BaseModel):
    """Request to list runs with filtering."""
    
    match_id: Optional[int] = Field(None, description="Filter by match ID")
    stage_id: Optional[int] = Field(None, description="Filter by stage ID")
    squad: Optional[str] = Field(None, description="Filter by squad")
    status: Optional[str] = Field(None, description="Filter by status")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=500, description="Page size")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class RunsListResponse(BaseModel):
    """Response containing paginated list of runs."""
    
    runs: List[RunInfo] = Field(..., description="List of runs")
    total: int = Field(..., description="Total number of runs")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


class TimerEventInfo(BaseModel):
    """Timer event information for alignment validation."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: int = Field(..., description="Timer event ID")
    ts_utc: datetime = Field(..., description="Event timestamp")
    type: str = Field(..., description="Event type")
    raw: Optional[str] = Field(None, description="Raw event data")
    is_aligned: bool = Field(True, description="Whether event is properly aligned")
    alignment_offset_ms: Optional[float] = Field(None, description="Alignment offset in milliseconds")


class TimerAlignmentUpdateRequest(BaseModel):
    """Request to update timer event alignment."""
    
    event_id: int = Field(..., description="Timer event ID")
    new_timestamp: datetime = Field(..., description="New aligned timestamp")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for alignment change")
    author_role: str = Field(..., description="Role of person making change")


class TimerAlignmentUpdateResponse(BaseModel):
    """Response from timer alignment update."""
    
    success: bool = Field(..., description="Whether update was successful")
    event_id: int = Field(..., description="Timer event ID")
    old_timestamp: datetime = Field(..., description="Previous timestamp")
    new_timestamp: datetime = Field(..., description="New timestamp")
    offset_ms: float = Field(..., description="Time offset in milliseconds")
    message: str = Field(..., description="Status message")
    audit_entry_id: Optional[int] = Field(None, description="Audit trail entry ID")


class AuditTrailEntry(BaseModel):
    """Audit trail entry for run corrections."""
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: int = Field(..., description="Audit entry ID")
    run_id: int = Field(..., description="Run ID")
    change_type: str = Field(..., description="Type of change made")
    field_name: str = Field(..., description="Field that was changed")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: Optional[str] = Field(None, description="New value")
    reason: str = Field(..., description="Reason for change")
    author_role: str = Field(..., description="Role of person making change")
    timestamp: datetime = Field(..., description="Change timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional change metadata")


class AuditTrailResponse(BaseModel):
    """Response containing audit trail entries."""
    
    entries: List[AuditTrailEntry] = Field(..., description="List of audit entries")
    total: int = Field(..., description="Total number of entries")
    run_id: int = Field(..., description="Run ID")


class RunExportRequest(BaseModel):
    """Request to export runs data."""
    
    format: str = Field("csv", pattern="^(csv|ndjson)$", description="Export format")
    match_id: Optional[int] = Field(None, description="Filter by match ID")
    stage_id: Optional[int] = Field(None, description="Filter by stage ID")
    squad: Optional[str] = Field(None, description="Filter by squad")
    status: Optional[str] = Field(None, description="Filter by status")
    include_events: bool = Field(False, description="Include timer and sensor events")
    include_audit: bool = Field(False, description="Include audit trail")


class RunExportResponse(BaseModel):
    """Response from run export operation."""
    
    success: bool = Field(..., description="Whether export was successful")
    format: str = Field(..., description="Export format")
    filename: str = Field(..., description="Generated filename")
    download_url: Optional[str] = Field(None, description="Download URL if available")
    record_count: int = Field(..., description="Number of records exported")
    file_size_bytes: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Status message")


class RunValidationResult(BaseModel):
    """Run validation results."""
    
    run_id: int = Field(..., description="Run ID")
    is_valid: bool = Field(..., description="Whether run data is valid")
    issues: List[str] = Field(default_factory=list, description="List of validation issues")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    timer_alignment_status: str = Field(..., description="Timer alignment validation status")
    event_correlation_score: Optional[float] = Field(None, description="Event correlation score (0-1)")


class BulkValidationRequest(BaseModel):
    """Request to validate multiple runs."""
    
    run_ids: List[int] = Field(..., min_items=1, max_items=100, description="List of run IDs to validate")
    check_timer_alignment: bool = Field(True, description="Check timer alignment")
    check_event_correlation: bool = Field(True, description="Check shot-to-impact correlation")


class BulkValidationResponse(BaseModel):
    """Response from bulk validation operation."""
    
    results: List[RunValidationResult] = Field(..., description="Validation results per run")
    summary: Dict[str, int] = Field(..., description="Summary statistics")
    total_processed: int = Field(..., description="Total runs processed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")