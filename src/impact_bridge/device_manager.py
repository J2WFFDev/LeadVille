"""Device management service for BLE device discovery, pairing, and assignment."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from bleak import BleakScanner, BleakClient, BLEDevice
from bleak.exc import BleakError

from .database.models import Sensor, Target, Stage, Node
from .database.engine import get_database_session
from .database.crud import SensorCRUD


logger = logging.getLogger(__name__)


@dataclass
class DiscoveredDevice:
    """Represents a discovered BLE device."""
    address: str
    name: Optional[str]
    rssi: int
    manufacturer_data: Dict[int, bytes]
    service_uuids: List[str]
    local_name: Optional[str]
    advertisement_data: Dict[str, Any]
    is_connectable: bool = True
    device_type: Optional[str] = None  # 'bt50', 'amg', 'unknown'


@dataclass
class DeviceHealth:
    """Device health status information."""
    address: str
    is_connected: bool
    rssi: Optional[int]
    battery_level: Optional[float]
    last_seen: datetime
    connection_attempts: int
    last_error: Optional[str]


class DeviceManager:
    """Manages BLE device discovery, pairing, and assignment."""
    
    # Known device signatures for automatic identification
    KNOWN_DEVICES = {
        'bt50': {
            'name_patterns': ['WitMotion', 'BWT50', 'WT50'],
            'service_uuids': ['0000ffe0-0000-1000-8000-00805f9a34fb'],
            'manufacturer_ids': [0x0183]  # WitMotion manufacturer ID
        },
        'amg': {
            'name_patterns': ['AMG', 'Commander'],
            'service_uuids': ['6e400001-b5a3-f393-e0a9-e50e24dcca9e'],
            'manufacturer_ids': []
        }
    }
    
    def __init__(self):
        self._discovered_devices: Dict[str, DiscoveredDevice] = {}
        self._device_health: Dict[str, DeviceHealth] = {}
        self._scanning = False
        self._health_monitoring = False
        self._scan_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None
        
    async def start_discovery(self, duration: float = 10.0) -> List[DiscoveredDevice]:
        """Start BLE device discovery scan."""
        logger.info(f"Starting BLE device discovery for {duration} seconds")
        
        self._discovered_devices.clear()
        self._scanning = True
        
        def detection_callback(device: BLEDevice, advertisement_data):
            """Handle discovered device."""
            if device.address in self._discovered_devices:
                # Update RSSI if device seen again
                self._discovered_devices[device.address].rssi = advertisement_data.rssi
                return
                
            # Identify device type
            device_type = self._identify_device_type(device, advertisement_data)
            
            discovered = DiscoveredDevice(
                address=device.address,
                name=device.name,
                rssi=advertisement_data.rssi,
                manufacturer_data=advertisement_data.manufacturer_data,
                service_uuids=advertisement_data.service_uuids,
                local_name=advertisement_data.local_name,
                advertisement_data=dict(advertisement_data),
                is_connectable=True,  # Assume connectable unless proven otherwise
                device_type=device_type
            )
            
            self._discovered_devices[device.address] = discovered
            logger.debug(f"Discovered device: {device.address} ({device.name}) - Type: {device_type}")
        
        try:
            # Start scanning
            async with BleakScanner(detection_callback=detection_callback) as scanner:
                await asyncio.sleep(duration)
                
        except Exception as e:
            logger.error(f"Error during BLE scanning: {e}")
            raise
        finally:
            self._scanning = False
            
        devices = list(self._discovered_devices.values())
        logger.info(f"Discovery completed. Found {len(devices)} devices")
        return devices
    
    def _identify_device_type(self, device: BLEDevice, advertisement_data) -> str:
        """Identify device type based on advertisement data."""
        device_name = device.name or advertisement_data.local_name or ""
        service_uuids = [str(uuid) for uuid in advertisement_data.service_uuids]
        manufacturer_data = advertisement_data.manufacturer_data
        
        for device_type, signatures in self.KNOWN_DEVICES.items():
            # Check name patterns
            if any(pattern.lower() in device_name.lower() for pattern in signatures['name_patterns']):
                return device_type
                
            # Check service UUIDs
            if any(uuid in service_uuids for uuid in signatures['service_uuids']):
                return device_type
                
            # Check manufacturer IDs
            if any(mfg_id in manufacturer_data for mfg_id in signatures['manufacturer_ids']):
                return device_type
        
        return 'unknown'
    
    async def pair_device(self, address: str, device_type: str = 'unknown') -> bool:
        """Attempt to pair with a BLE device."""
        logger.info(f"Attempting to pair with device {address} (type: {device_type})")
        
        try:
            async with BleakClient(address) as client:
                if await client.is_connected():
                    logger.info(f"Successfully paired with device {address}")
                    
                    # Update device health
                    self._device_health[address] = DeviceHealth(
                        address=address,
                        is_connected=True,
                        rssi=None,  # Will be updated during health monitoring
                        battery_level=None,
                        last_seen=datetime.utcnow(),
                        connection_attempts=1,
                        last_error=None
                    )
                    
                    return True
                else:
                    logger.warning(f"Failed to connect to device {address}")
                    return False
                    
        except BleakError as e:
            logger.error(f"BLE error pairing with {address}: {e}")
            self._update_device_error(address, str(e))
            return False
        except Exception as e:
            logger.error(f"Unexpected error pairing with {address}: {e}")
            self._update_device_error(address, str(e))
            return False
    
    async def assign_device_to_target(self, device_address: str, target_id: int) -> bool:
        """Assign a device to a specific target."""
        logger.info(f"Assigning device {device_address} to target {target_id}")
        
        try:
            with get_database_session() as session:
                # Check if sensor already exists
                sensor = SensorCRUD.get_by_hw_addr(session, device_address)
                
                if sensor:
                    # Update existing sensor
                    SensorCRUD.update(session, sensor.id, target_id=target_id)
                else:
                    # Create new sensor record
                    sensor = SensorCRUD.create(
                        session=session,
                        hw_addr=device_address,
                        label=f"Sensor-{device_address[-4:]}",  # Last 4 chars of MAC
                        target_id=target_id
                    )
                
                session.commit()
                logger.info(f"Successfully assigned device {device_address} to target {target_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error assigning device to target: {e}")
            return False
    
    async def unassign_device(self, device_address: str) -> bool:
        """Remove device assignment from target."""
        logger.info(f"Unassigning device {device_address}")
        
        try:
            with get_database_session() as session:
                sensor = SensorCRUD.get_by_hw_addr(session, device_address)
                
                if sensor:
                    SensorCRUD.update(session, sensor.id, target_id=None)
                    session.commit()
                    logger.info(f"Successfully unassigned device {device_address}")
                    return True
                else:
                    logger.warning(f"Device {device_address} not found in database")
                    return False
                    
        except Exception as e:
            logger.error(f"Error unassigning device: {e}")
            return False
    
    async def get_device_list(self) -> List[Dict[str, Any]]:
        """Get list of all known devices with their status."""
        devices = []
        
        try:
            with get_database_session() as session:
                sensors = SensorCRUD.list_sensors(session)
                
                for sensor in sensors:
                    health = self._device_health.get(sensor.hw_addr)
                    device_info = {
                        'address': sensor.hw_addr,
                        'label': sensor.label,
                        'target_id': sensor.target_id,
                        'node_id': sensor.node_id,
                        'last_seen': sensor.last_seen,
                        'battery': sensor.battery,
                        'rssi': sensor.rssi,
                        'calibration': sensor.calib,
                        'is_connected': health.is_connected if health else False,
                        'last_error': health.last_error if health else None,
                        'connection_attempts': health.connection_attempts if health else 0
                    }
                    devices.append(device_info)
                    
        except Exception as e:
            logger.error(f"Error retrieving device list: {e}")
            
        return devices
    
    async def start_health_monitoring(self, interval: float = 30.0):
        """Start continuous device health monitoring."""
        if self._health_monitoring:
            logger.warning("Health monitoring already running")
            return
            
        logger.info(f"Starting device health monitoring (interval: {interval}s)")
        self._health_monitoring = True
        
        self._health_task = asyncio.create_task(self._health_monitoring_loop(interval))
    
    async def stop_health_monitoring(self):
        """Stop device health monitoring."""
        if not self._health_monitoring:
            return
            
        logger.info("Stopping device health monitoring")
        self._health_monitoring = False
        
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
    
    async def _health_monitoring_loop(self, interval: float):
        """Main health monitoring loop."""
        while self._health_monitoring:
            try:
                await self._check_device_health()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def _check_device_health(self):
        """Check health status of all known devices."""
        try:
            with get_database_session() as session:
                sensors = SensorCRUD.list_sensors(session)
                
                for sensor in sensors:
                    health = await self._check_single_device_health(sensor.hw_addr)
                    
                    if health:
                        # Update sensor record with latest health data
                        SensorCRUD.update_status(
                            session=session,
                            sensor_id=sensor.id,
                            last_seen=health.last_seen,
                            rssi=health.rssi,
                            battery=health.battery_level
                        )
                        
                session.commit()
                
        except Exception as e:
            logger.error(f"Error checking device health: {e}")
    
    async def _check_single_device_health(self, address: str) -> Optional[DeviceHealth]:
        """Check health of a single device."""
        try:
            # Attempt quick connection to check if device is responsive
            async with BleakClient(address, timeout=5.0) as client:
                if await client.is_connected():
                    # Device is healthy
                    health = DeviceHealth(
                        address=address,
                        is_connected=True,
                        rssi=None,  # Would need to implement RSSI reading
                        battery_level=None,  # Would need to implement battery reading
                        last_seen=datetime.utcnow(),
                        connection_attempts=self._device_health.get(address, DeviceHealth(address, False, None, None, datetime.utcnow(), 0, None)).connection_attempts,
                        last_error=None
                    )
                    
                    self._device_health[address] = health
                    return health
                    
        except Exception as e:
            # Device is not responding
            prev_health = self._device_health.get(address)
            health = DeviceHealth(
                address=address,
                is_connected=False,
                rssi=None,
                battery_level=None,
                last_seen=prev_health.last_seen if prev_health else datetime.utcnow() - timedelta(hours=1),
                connection_attempts=(prev_health.connection_attempts if prev_health else 0) + 1,
                last_error=str(e)
            )
            
            self._device_health[address] = health
            return health
        
        return None
    
    def _update_device_error(self, address: str, error: str):
        """Update device error status."""
        if address in self._device_health:
            self._device_health[address].last_error = error
            self._device_health[address].connection_attempts += 1
        else:
            self._device_health[address] = DeviceHealth(
                address=address,
                is_connected=False,
                rssi=None,
                battery_level=None,
                last_seen=datetime.utcnow(),
                connection_attempts=1,
                last_error=error
            )
    
    def get_health_status(self, address: str) -> Optional[DeviceHealth]:
        """Get health status for a specific device."""
        return self._device_health.get(address)
    
    def get_all_health_status(self) -> Dict[str, DeviceHealth]:
        """Get health status for all monitored devices."""
        return self._device_health.copy()
    
    async def shutdown(self):
        """Shutdown device manager and cleanup resources."""
        logger.info("Shutting down device manager")
        
        await self.stop_health_monitoring()
        
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
        
        self._discovered_devices.clear()
        self._device_health.clear()