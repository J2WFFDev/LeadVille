"""
Device Management Module for LeadVille Bridge
Handles BLE device discovery, pairing, assignment, and health monitoring
"""

import asyncio
import json
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

from .database.database import init_database, get_database_session
from .database.models import Sensor, Node, Target, Bridge
from .database.crud import SensorCRUD, NodeCRUD

logger = logging.getLogger(__name__)

class DeviceManager:
    """Manages BLE device discovery, pairing, and assignment"""
    
    def __init__(self):
        self.scanning = False
        self.discovered_devices: Dict[str, Dict[str, Any]] = {}
        self.known_devices = {
            # Known device types and their characteristics
            'BT50': {
                'name_patterns': ['BT50', 'WTVB01'],
                'service_uuid': '0000ffe4-0000-1000-8000-00805f9a34fb',
                'type': 'accelerometer',
                'vendor': 'WitMotion'
            },
            'AMG': {
                'name_patterns': ['AMG', 'Commander'],
                'service_uuid': '6e400003-b5a3-f393-e0a9-e50e24dcca9e',
                'type': 'timer',
                'vendor': 'AMG Labs'
            }
        }
    
    def get_current_bridge(self) -> Optional[Bridge]:
        """Get the current Bridge configuration"""
        with get_database_session() as session:
            return session.query(Bridge).first()
    
    def get_bridge_assigned_sensors(self) -> List[str]:
        """Get MAC addresses of sensors assigned to this Bridge"""
        with get_database_session() as session:
            bridge = session.query(Bridge).first()
            if not bridge or not bridge.current_stage_id:
                return []
            
            # Get all sensors assigned to targets in this Bridge's stage
            target_config_ids = [target.id for target in bridge.current_stage.target_configs]
            if not target_config_ids:
                return []
            
            sensors = session.query(Sensor).filter(
                Sensor.target_config_id.in_(target_config_ids)
            ).all()
            
            return [sensor.hw_addr for sensor in sensors]
        
    async def discover_devices(self, duration: int = 10) -> List[Dict[str, Any]]:
        """Discover available BLE devices (filtered to BT50 sensors and AMG timers)"""
        if self.scanning:
            raise ValueError("Discovery already in progress")
            
        self.scanning = True
        self.discovered_devices.clear()
        logger.info(f"Starting BLE device discovery for {duration} seconds...")
        
        try:
            devices = await BleakScanner.discover(timeout=duration)
            
            for device in devices:
                device_info = await self._analyze_device(device)
                if device_info and self._is_relevant_device(device_info):
                    self.discovered_devices[device.address] = device_info
                    
        except Exception as e:
            error_msg = str(e)
            if "Operation already in progress" in error_msg or "InProgress" in error_msg:
                logger.warning("BLE discovery conflict detected - attempting Bluetooth reset")
                
                # Try to reset the Bluetooth adapter
                try:
                    import subprocess
                    logger.info("Resetting Bluetooth adapter...")
                    subprocess.run(['sudo', 'hciconfig', 'hci0', 'down'], 
                                 capture_output=True, timeout=5)
                    await asyncio.sleep(1)
                    subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], 
                                 capture_output=True, timeout=5)
                    await asyncio.sleep(2)
                    logger.info("Bluetooth adapter reset complete")
                except Exception as reset_e:
                    logger.warning(f"Bluetooth reset failed: {reset_e}")
                
                # Try discovery again after reset
                try:
                    logger.info("Retrying discovery after Bluetooth reset...")
                    devices = await BleakScanner.discover(timeout=min(duration, 8))
                    for device in devices:
                        device_info = await self._analyze_device(device)
                        if device_info and self._is_relevant_device(device_info):
                            self.discovered_devices[device.address] = device_info
                    logger.info("Discovery retry successful")
                except Exception as retry_e:
                    logger.error(f"Device discovery failed after Bluetooth reset: {retry_e}")
                    # If still failing, return empty list rather than crash
                    logger.warning("Returning empty device list due to persistent BLE conflicts")
                    return []
            else:
                logger.error(f"Device discovery failed: {e}")
                raise
        finally:
            self.scanning = False
            
        logger.info(f"Discovered {len(self.discovered_devices)} relevant devices (BT50/AMG)")
        return list(self.discovered_devices.values())
    
    async def _analyze_device(self, device: BLEDevice) -> Optional[Dict[str, Any]]:
        """Analyze discovered device and determine type"""
        device_info = {
            'address': device.address,
            'name': device.name or 'Unknown',
            'rssi': getattr(device, 'rssi', None),  # Safely get rssi if available
            'discovered_at': datetime.utcnow().isoformat(),
            'type': 'unknown',
            'vendor': 'unknown',
            'services': [],
            'pairable': False
        }
        
        # Try to determine device type from name
        if device.name:
            for device_type, config in self.known_devices.items():
                for pattern in config['name_patterns']:
                    if pattern.lower() in device.name.lower():
                        device_info.update({
                            'type': config['type'],
                            'vendor': config['vendor'],
                            'pairable': True
                        })
                        break
        
        # Try to get service information (may not work for all devices)
        try:
            async with BleakClient(device) as client:
                services = await client.get_services()
                device_info['services'] = [str(service.uuid) for service in services]
                
                # Check for known service UUIDs
                for device_type, config in self.known_devices.items():
                    if config['service_uuid'] in device_info['services']:
                        device_info.update({
                            'type': config['type'],
                            'vendor': config['vendor'],
                            'pairable': True
                        })
                        break
                        
        except Exception as e:
            logger.debug(f"Could not analyze services for {device.address}: {e}")
        
        return device_info
    
    def _is_relevant_device(self, device_info: Dict[str, Any]) -> bool:
        """Check if device is relevant for shooting sports (BT50 sensors or AMG timers)"""
        device_name = device_info.get('name', '').upper()
        device_type = device_info.get('type', '')
        
        # Check for BT50 sensors (WitMotion accelerometers)
        bt50_patterns = ['BT50', 'WTVB01-BT50', 'WTVB01']
        if any(pattern in device_name for pattern in bt50_patterns):
            return True
        
        # Check for AMG timers
        amg_patterns = ['AMG', 'COMMANDER']
        if any(pattern in device_name for pattern in amg_patterns):
            return True
        
        # Also check by device type
        if device_type in ['accelerometer', 'timer']:
            return True
        
        # For debugging: log filtered out devices
        logger.debug(f"Filtered out device: {device_name} ({device_info.get('address')})")
        return False
    
    async def pair_device(self, mac_address: str, label: str) -> Dict[str, Any]:
        """Pair a discovered device and add to database with Bridge ownership"""
        if mac_address not in self.discovered_devices:
            raise ValueError(f"Device {mac_address} not found in discovered devices")
        
        device_info = self.discovered_devices[mac_address]
        
        # Get current Bridge
        current_bridge = self.get_current_bridge()
        if not current_bridge:
            raise ValueError("No Bridge configured - cannot pair devices")
        
        # Check if device is already paired
        with get_database_session() as session:
            existing_sensor = SensorCRUD.get_by_hw_addr(session, mac_address)
            if existing_sensor:
                # Update Bridge ownership if not set
                if not existing_sensor.bridge_id:
                    existing_sensor.bridge_id = current_bridge.id
                    session.commit()
                
                return {
                    'status': 'already_paired',
                    'sensor_id': existing_sensor.id,
                    'bridge_id': existing_sensor.bridge_id,
                    'message': f"Device {mac_address} is already paired to Bridge {current_bridge.name}"
                }
            
            # Create new sensor record with Bridge ownership
            sensor = SensorCRUD.create(
                session=session,
                hw_addr=mac_address,
                label=label,
                last_seen=datetime.utcnow(),
                rssi=device_info.get('rssi')
            )
            
            # Assign to current Bridge
            sensor.bridge_id = current_bridge.id
            session.commit()
            
            logger.info(f"Successfully paired device {mac_address} as {label} to Bridge {current_bridge.name}")
            return {
                'status': 'paired',
                'sensor_id': sensor.id,
                'bridge_id': sensor.bridge_id,
                'message': f"Device {mac_address} paired successfully to Bridge {current_bridge.name}"
            }
    
    def get_paired_devices(self) -> List[Dict[str, Any]]:
        """Get all paired devices from database"""
        with get_database_session() as session:
            sensors = session.query(Sensor).all()
            devices = []
            
            for sensor in sensors:
                device_info = {
                    'id': sensor.id,
                    'address': sensor.hw_addr,
                    'label': sensor.label,
                    'type': 'sensor',  # Could be enhanced with device type detection
                    'battery': sensor.battery,
                    'rssi': sensor.rssi,
                    'last_seen': sensor.last_seen.isoformat() if sensor.last_seen else None,
                    'target_id': sensor.target_id,
                    'target_name': sensor.target.label if sensor.target else None,
                    'target_config_id': sensor.target_config_id,
                    'status': self._get_device_status(sensor),
                    'created_at': sensor.created_at.isoformat(),
                    'updated_at': sensor.updated_at.isoformat()
                }
                devices.append(device_info)
                
            return devices
    
    def _get_device_status(self, sensor: Sensor) -> str:
        """Determine device status based on sensor data"""
        if not sensor.last_seen:
            return 'never_connected'
        
        # Device is considered offline if not seen in last 30 seconds
        offline_threshold = datetime.utcnow() - timedelta(seconds=30)
        if sensor.last_seen < offline_threshold:
            return 'offline'
        
        # Check battery level
        if sensor.battery and sensor.battery < 20:
            return 'low_battery'
        
        # Check signal strength
        if sensor.rssi and sensor.rssi < -80:
            return 'weak_signal'
        
        return 'connected'
    
    async def assign_device_to_target(self, sensor_id: int, target_id: int) -> Dict[str, Any]:
        """Assign a paired device to a target"""
        with get_database_session() as session:
            # Verify sensor exists
            sensor = SensorCRUD.get_by_id(session, sensor_id)
            if not sensor:
                raise ValueError(f"Sensor {sensor_id} not found")
            
            # Verify target exists
            target = session.query(Target).filter(Target.id == target_id).first()
            if not target:
                raise ValueError(f"Target {target_id} not found")
            
            # Check if target already has a sensor assigned
            existing_assignment = SensorCRUD.list_by_target(session, target_id)
            if existing_assignment:
                return {
                    'status': 'error',
                    'message': f"Target {target_id} already has a sensor assigned"
                }
            
            # Assign sensor to target
            updated_sensor = SensorCRUD.assign_to_target(session, sensor_id, target_id)
            session.commit()
            
            logger.info(f"Assigned sensor {sensor_id} to target {target_id}")
            return {
                'status': 'assigned',
                'sensor_id': sensor_id,
                'target_id': target_id,
                'message': f"Sensor {updated_sensor.label} assigned to target {target.label}"
            }
    
    async def unassign_device(self, sensor_id: int) -> Dict[str, Any]:
        """Remove device assignment from target"""
        with get_database_session() as session:
            sensor = SensorCRUD.assign_to_target(session, sensor_id, None)
            if not sensor:
                raise ValueError(f"Sensor {sensor_id} not found")
            
            session.commit()
            logger.info(f"Unassigned sensor {sensor_id}")
            return {
                'status': 'unassigned',
                'sensor_id': sensor_id,
                'message': f"Sensor {sensor.label} unassigned"
            }
    
    async def update_device_health(self, mac_address: str, battery: int = None, 
                                 rssi: int = None) -> Dict[str, Any]:
        """Update device health status"""
        with get_database_session() as session:
            sensor = SensorCRUD.get_by_hw_addr(session, mac_address)
            if not sensor:
                raise ValueError(f"Device {mac_address} not found")
            
            SensorCRUD.update_status(
                session=session,
                sensor_id=sensor.id,
                battery=battery,
                rssi=rssi,
                last_seen=datetime.utcnow()
            )
            session.commit()
            
            return {
                'status': 'updated',
                'sensor_id': sensor.id,
                'battery': battery,
                'rssi': rssi
            }
    
    async def remove_device(self, sensor_id: int) -> Dict[str, Any]:
        """Remove a paired device"""
        with get_database_session() as session:
            sensor = SensorCRUD.get_by_id(session, sensor_id)
            if not sensor:
                raise ValueError(f"Sensor {sensor_id} not found")
            
            label = sensor.label
            session.delete(sensor)
            session.commit()
            
            logger.info(f"Removed device {sensor_id} ({label})")
            return {
                'status': 'removed',
                'sensor_id': sensor_id,
                'message': f"Device {label} removed"
            }
    
    def get_device_assignments(self) -> Dict[str, Any]:
        """Get current device-to-target assignments"""
        with get_database_session() as session:
            # Get all sensors with target assignments
            sensors = session.query(Sensor).filter(Sensor.target_id.isnot(None)).all()
            assignments = {}
            
            for sensor in sensors:
                assignments[f"target_{sensor.target_id}"] = {
                    'sensor_id': sensor.id,
                    'sensor_address': sensor.hw_addr,
                    'sensor_label': sensor.label,
                    'target_id': sensor.target_id,
                    'target_label': sensor.target.label if sensor.target else None,
                    'status': self._get_device_status(sensor)
                }
            
            return {
                'assignments': assignments,
                'total_assigned': len(assignments),
                'total_sensors': session.query(Sensor).count(),
                'total_targets': session.query(Target).count()
            }

# Global device manager instance
device_manager = DeviceManager()