"""Admin device management API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from ..device_manager import DeviceManager
from .auth.dependencies import require_admin, get_current_active_user
from .auth.models import User
from .models import (
    DeviceDiscoveryRequest,
    DeviceDiscoveryResponse,
    DevicePairRequest,
    DevicePairResponse,
    DeviceAssignRequest,
    DeviceAssignResponse,
    DeviceUnassignRequest,
    DeviceUnassignResponse,
    DeviceListResponse,
    DeviceHealthMonitoringRequest,
    DeviceHealthMonitoringResponse,
    DeviceInfo,
    DiscoveredDevice,
    DeviceHealthStatus,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Global device manager instance
device_manager = DeviceManager()

router = APIRouter()


async def get_device_manager() -> DeviceManager:
    """Dependency to get device manager instance."""
    return device_manager


@router.post("/discover", 
             response_model=DeviceDiscoveryResponse,
             status_code=status.HTTP_200_OK,
             summary="Discover BLE devices",
             description="Start BLE device discovery scan to find nearby devices.")
async def discover_devices(
    request: DeviceDiscoveryRequest,
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(require_admin)
) -> DeviceDiscoveryResponse:
    """Discover nearby BLE devices."""
    try:
        logger.info(f"Starting device discovery for {request.duration} seconds")
        
        discovered = await manager.start_discovery(request.duration)
        
        # Convert to response models
        device_models = []
        for device in discovered:
            # Convert manufacturer data bytes to hex strings
            manufacturer_data = {
                mfg_id: data.hex() for mfg_id, data in device.manufacturer_data.items()
            }
            
            device_model = DiscoveredDevice(
                address=device.address,
                name=device.name,
                rssi=device.rssi,
                manufacturer_data=manufacturer_data,
                service_uuids=device.service_uuids,
                local_name=device.local_name,
                is_connectable=device.is_connectable,
                device_type=device.device_type
            )
            device_models.append(device_model)
        
        logger.info(f"Discovery completed. Found {len(device_models)} devices")
        
        return DeviceDiscoveryResponse(
            devices=device_models,
            duration=request.duration,
            total_found=len(device_models)
        )
        
    except Exception as e:
        logger.error(f"Error during device discovery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device discovery failed: {str(e)}"
        )


@router.post("/pair",
             response_model=DevicePairResponse,
             status_code=status.HTTP_200_OK,
             summary="Pair with BLE device",
             description="Attempt to pair/connect with a specific BLE device.")
async def pair_device(
    request: DevicePairRequest,
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(require_admin)
) -> DevicePairResponse:
    """Pair with a BLE device."""
    try:
        logger.info(f"Attempting to pair with device {request.address}")
        
        success = await manager.pair_device(request.address, request.device_type)
        
        message = "Successfully paired with device" if success else "Failed to pair with device"
        
        return DevicePairResponse(
            success=success,
            address=request.address,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error pairing with device {request.address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device pairing failed: {str(e)}"
        )


@router.post("/assign",
             response_model=DeviceAssignResponse,
             status_code=status.HTTP_200_OK,
             summary="Assign device to target",
             description="Assign a paired device to a specific target.")
async def assign_device(
    request: DeviceAssignRequest,
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(require_admin)
) -> DeviceAssignResponse:
    """Assign a device to a target."""
    try:
        logger.info(f"Assigning device {request.address} to target {request.target_id}")
        
        success = await manager.assign_device_to_target(request.address, request.target_id)
        
        message = (
            f"Successfully assigned device to target {request.target_id}" 
            if success else f"Failed to assign device to target {request.target_id}"
        )
        
        return DeviceAssignResponse(
            success=success,
            address=request.address,
            target_id=request.target_id,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error assigning device {request.address} to target {request.target_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device assignment failed: {str(e)}"
        )


@router.post("/unassign",
             response_model=DeviceUnassignResponse,
             status_code=status.HTTP_200_OK,
             summary="Unassign device from target",
             description="Remove device assignment from its current target.")
async def unassign_device(
    request: DeviceUnassignRequest,
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(require_admin)
) -> DeviceUnassignResponse:
    """Unassign a device from its target."""
    try:
        logger.info(f"Unassigning device {request.address}")
        
        success = await manager.unassign_device(request.address)
        
        message = (
            "Successfully unassigned device from target" 
            if success else "Failed to unassign device from target"
        )
        
        return DeviceUnassignResponse(
            success=success,
            address=request.address,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error unassigning device {request.address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device unassignment failed: {str(e)}"
        )


@router.get("/list",
            response_model=DeviceListResponse,
            status_code=status.HTTP_200_OK,
            summary="List all devices",
            description="Get list of all known devices with their status.")
async def list_devices(
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(get_current_active_user)
) -> DeviceListResponse:
    """Get list of all known devices."""
    try:
        logger.debug("Retrieving device list")
        
        devices_data = await manager.get_device_list()
        
        # Convert to response models
        device_models = []
        for device_data in devices_data:
            device_model = DeviceInfo(**device_data)
            device_models.append(device_model)
        
        return DeviceListResponse(
            devices=device_models,
            total=len(device_models)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving device list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve device list: {str(e)}"
        )


@router.get("/health/{address}",
            response_model=DeviceHealthStatus,
            status_code=status.HTTP_200_OK,
            summary="Get device health status",
            description="Get health status for a specific device.")
async def get_device_health(
    address: str,
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(get_current_active_user)
) -> DeviceHealthStatus:
    """Get health status for a specific device."""
    try:
        logger.debug(f"Retrieving health status for device {address}")
        
        health = manager.get_health_status(address)
        
        if not health:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {address} not found or no health data available"
            )
        
        return DeviceHealthStatus(
            address=health.address,
            is_connected=health.is_connected,
            rssi=health.rssi,
            battery_level=health.battery_level,
            last_seen=health.last_seen,
            connection_attempts=health.connection_attempts,
            last_error=health.last_error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving health status for device {address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve device health: {str(e)}"
        )


@router.get("/health",
            response_model=List[DeviceHealthStatus],
            status_code=status.HTTP_200_OK,
            summary="Get all device health statuses",
            description="Get health status for all monitored devices.")
async def get_all_device_health(
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(get_current_active_user)
) -> List[DeviceHealthStatus]:
    """Get health status for all devices."""
    try:
        logger.debug("Retrieving health status for all devices")
        
        all_health = manager.get_all_health_status()
        
        health_models = []
        for health in all_health.values():
            health_model = DeviceHealthStatus(
                address=health.address,
                is_connected=health.is_connected,
                rssi=health.rssi,
                battery_level=health.battery_level,
                last_seen=health.last_seen,
                connection_attempts=health.connection_attempts,
                last_error=health.last_error
            )
            health_models.append(health_model)
        
        return health_models
        
    except Exception as e:
        logger.error(f"Error retrieving health status for all devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve device health: {str(e)}"
        )


@router.post("/monitoring",
             response_model=DeviceHealthMonitoringResponse,
             status_code=status.HTTP_200_OK,
             summary="Control health monitoring",
             description="Start or stop device health monitoring.")
async def control_health_monitoring(
    request: DeviceHealthMonitoringRequest,
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(require_admin)
) -> DeviceHealthMonitoringResponse:
    """Start or stop device health monitoring."""
    try:
        if request.enabled:
            logger.info(f"Starting health monitoring with interval {request.interval}s")
            await manager.start_health_monitoring(request.interval)
            message = f"Health monitoring started with {request.interval}s interval"
        else:
            logger.info("Stopping health monitoring")
            await manager.stop_health_monitoring()
            message = "Health monitoring stopped"
        
        return DeviceHealthMonitoringResponse(
            success=True,
            enabled=request.enabled,
            interval=request.interval if request.enabled else None,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error controlling health monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to control health monitoring: {str(e)}"
        )


@router.delete("/{address}",
               status_code=status.HTTP_200_OK,
               summary="Remove device",
               description="Remove a device from the system.")
async def remove_device(
    address: str,
    manager: DeviceManager = Depends(get_device_manager),
    current_user: User = Depends(require_admin)
):
    """Remove a device from the system."""
    try:
        logger.info(f"Removing device {address}")
        
        # First unassign the device
        success = await manager.unassign_device(address)
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Device {address} removed successfully"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {address} not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing device {address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove device: {str(e)}"
        )