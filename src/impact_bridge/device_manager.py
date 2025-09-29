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
            },
            'SpecialPie': {
                'name_patterns': ['SpecialPie', 'SP M1A2', 'SP-M1A2', 'SPECIAL PIE'],
                'service_uuid': '0000fff0-0000-1000-8000-00805f9b34fb',  # SpecialPie service UUID
                'notification_uuid': '0000fff1-0000-1000-8000-00805f9b34fb',  # Notification characteristic
                'type': 'shot_timer',
                'vendor': 'SpecialPie'
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
        
        # Force reset scanning state if stuck
        if self.scanning:
            logger.warning("Discovery already in progress - forcing reset")
            self.scanning = False
            await asyncio.sleep(1)
            
        self.scanning = True
        self.discovered_devices.clear()
        logger.info(f"Starting BLE device discovery for {duration} seconds...")
        
        try:
            # Pre-emptive Bluetooth reset to ensure clean state
            try:
                import subprocess
                logger.info("Pre-discovery Bluetooth reset...")
                subprocess.run(['sudo', 'hciconfig', 'hci0', 'reset'], 
                             capture_output=True, timeout=3)
                await asyncio.sleep(0.5)
            except Exception as reset_e:
                logger.debug(f"Pre-discovery reset skipped: {reset_e}")
            
            # Use return_adv=True to get RSSI data from advertisements
            discovered = await BleakScanner.discover(timeout=duration, return_adv=True)
            
            # Get list of already paired devices to filter them out
            paired_addresses = set()
            try:
                with get_database_session() as session:
                    paired_sensors = session.query(Sensor).all()
                    paired_addresses = {sensor.hw_addr for sensor in paired_sensors}
                    logger.info(f"Filtering out {len(paired_addresses)} already-paired devices")
            except Exception as e:
                logger.warning(f"Could not load paired devices for filtering: {e}")
            
            for device, adv_data in discovered.values():
                # Skip devices that are already paired
                if device.address in paired_addresses:
                    logger.debug(f"Skipping already-paired device: {device.address}")
                    continue
                    
                device_info = await self._analyze_device(device, adv_data)
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
    
    async def _analyze_device(self, device: BLEDevice, adv_data=None) -> Optional[Dict[str, Any]]:
        """Analyze discovered device and determine type"""
        
        # Extract RSSI from advertisement data if available
        rssi = None
        if adv_data and hasattr(adv_data, 'rssi'):
            rssi = adv_data.rssi
        elif hasattr(device, 'rssi'):
            rssi = device.rssi
        
        device_info = {
            'address': device.address,
            'name': device.name or 'Unknown',
            'rssi': rssi,  # Now properly extracted from advertisement data
            'discovered_at': datetime.utcnow().isoformat(),
            'type': 'unknown',
            'vendor': 'unknown',
            'services': [],
            'pairable': False,
            'battery': None,  # Will be populated during connection
            'connection_status': 'unknown'  # Will be updated during connection
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
        
        # Try to get service information and battery status
        try:
            # For discovery mode, do a quick battery check with longer timeout for BT50
            if hasattr(self, 'scanning') and self.scanning:
                # Fast discovery mode - battery read with adequate timeout for WitMotion
                try:
                    # Use 6 seconds for BT50 devices, 3 for others
                    timeout = 6.0 if 'BT50' in device.name else 3.0
                    async with BleakClient(device, timeout=timeout) as client:
                        logger.debug(f"Quick battery check for {device.address} (timeout: {timeout}s)")
                        
                        # Quick battery read only - this will use the WitMotion protocol for BT50s
                        battery_level = await self._read_battery_level(client)
                        if battery_level is not None:
                            device_info['battery'] = battery_level
                            logger.info(f"✅ Device {device.address} battery: {battery_level}%")
                        else:
                            logger.debug(f"No battery reading available for {device.address}")
                        
                        device_info['connection_status'] = 'reachable'
                        
                except (asyncio.TimeoutError, Exception) as e:
                    # If quick battery read fails, continue without it
                    logger.debug(f"Battery read timeout for {device.address}: {e}")
                    device_info['connection_status'] = 'discoverable'
                    device_info['battery'] = None
            else:
                # Detailed analysis mode (non-discovery)
                async with BleakClient(device, timeout=5.0) as client:
                    logger.debug(f"Connected to {device.address} for detailed analysis")
                    
                    # Get services
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
                    
                    # Try to read battery level
                    battery_level = await self._read_battery_level(client)
                    if battery_level is not None:
                        device_info['battery'] = battery_level
                        logger.info(f"Device {device.address} battery: {battery_level}%")
                    else:
                        device_info['battery'] = None
                        logger.debug(f"No battery service found on {device.address}")
                    
                    # Update RSSI from connected client if available
                    if hasattr(client, 'rssi') and client.rssi:
                        device_info['rssi'] = client.rssi
                    
                    # Mark as connected successfully
                    device_info['connection_status'] = 'reachable'
                    logger.debug(f"Successfully analyzed device {device.address}")
                        
        except asyncio.TimeoutError:
            logger.debug(f"Connection timeout for {device.address}")
            device_info['battery'] = None
            device_info['connection_status'] = 'timeout'
        except Exception as e:
            logger.debug(f"Could not analyze services for {device.address}: {e}")
            device_info['battery'] = None
            device_info['connection_status'] = 'unreachable'
        
        return device_info
    
    async def _read_battery_level(self, client: BleakClient) -> Optional[int]:
        """Read battery level from BLE device (supports both standard BLE and WitMotion BT50)"""
        # Standard Battery Service UUID
        BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
        BATTERY_LEVEL_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
        
        # WitMotion BT50 specific UUIDs
        WITMOTION_SERVICE_UUID = "0000ffe5-0000-1000-8000-00805f9a34fb"
        WITMOTION_CONFIG_UUID = "0000ffe9-0000-1000-8000-00805f9a34fb"
        WITMOTION_DATA_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"
        
        try:
            # Method 1: Try standard battery service first
            try:
                services = await client.get_services()
                for service in services:
                    if str(service.uuid).lower() == BATTERY_SERVICE_UUID.lower():
                        battery_data = await client.read_gatt_char(BATTERY_LEVEL_CHAR_UUID)
                        if battery_data and len(battery_data) > 0:
                            battery_level = int(battery_data[0])
                            logger.debug(f"Standard battery service: {battery_level}% from {client.address}")
                            return battery_level
            except Exception as e:
                logger.debug(f"Standard battery service failed for {client.address}: {e}")
            
            # Method 2: Check if this is a WitMotion BT50 device and use custom protocol
            try:
                services = await client.get_services()
                has_witmotion_service = any(str(service.uuid).lower() == WITMOTION_SERVICE_UUID.lower() 
                                          for service in services)
                
                if has_witmotion_service:
                    logger.debug(f"Detected WitMotion device {client.address}, trying custom battery protocol")
                    battery_level = await self._read_witmotion_battery(client, WITMOTION_CONFIG_UUID, WITMOTION_DATA_UUID)
                    if battery_level is not None:
                        return battery_level
                        
            except Exception as e:
                logger.debug(f"WitMotion battery read failed for {client.address}: {e}")
                
            # Method 3: Try to find battery characteristic by scanning all characteristics  
            try:
                services = await client.get_services()
                for service in services:
                    for characteristic in service.characteristics:
                        if ("battery" in characteristic.description.lower() or 
                            "2a19" in str(characteristic.uuid).lower()):
                            try:
                                battery_data = await client.read_gatt_char(characteristic.uuid)
                                if battery_data and len(battery_data) > 0:
                                    battery_level = int(battery_data[0])
                                    logger.debug(f"Alt battery method: {battery_level}% from {client.address}")
                                    return battery_level
                            except Exception as alt_e:
                                logger.debug(f"Alt battery read failed for {client.address}: {alt_e}")
                                continue
                                
            except Exception as e:
                logger.debug(f"Alternative battery scan failed for {client.address}: {e}")
            
            # Method 4: SpecialPie timers - currently no known battery reading method
            try:
                services = await client.get_services()
                specialpie_service_uuid = "0000fff0-0000-1000-8000-00805f9b34fb"
                has_specialpie_service = any(str(service.uuid).lower() == specialpie_service_uuid.lower() 
                                          for service in services)
                
                if has_specialpie_service:
                    logger.debug(f"Detected SpecialPie timer {client.address} - no battery reading method available yet")
                    return None  # SpecialPie protocol doesn't include battery reading in reference implementation
                    
            except Exception as e:
                logger.debug(f"SpecialPie detection failed for {client.address}: {e}")
                        
        except Exception as e:
            logger.debug(f"Battery level read failed for {client.address}: {e}")
        
        return None

    async def _read_witmotion_battery(self, client: BleakClient, config_uuid: str, data_uuid: str) -> Optional[int]:
        """Read battery level from WitMotion BT50 using custom protocol"""
        battery_response = None
        notification_received = asyncio.Event()
        
        def notification_handler(sender, data):
            nonlocal battery_response
            logger.debug(f"WitMotion notification from {sender}: {data.hex()}")
            
            # Parse multi-frame notifications to find battery data
            offset = 0
            while offset < len(data) - 3:
                if data[offset] == 0x55:
                    frame_type = data[offset + 1]
                    if frame_type == 0x71 and offset + 5 < len(data):
                        # Found battery/status frame: 55 71 64 00 [voltage_low] [voltage_high] ...
                        if data[offset + 2] == 0x64 and data[offset + 3] == 0x00:
                            battery_response = data[offset:offset + 20]  # Extract this frame
                            notification_received.set()
                            logger.debug(f"WitMotion battery frame found: {battery_response.hex()}")
                            return
                    elif frame_type == 0x64 and offset + 5 < len(data):
                        # Original format: 55 64 [voltage_low] [voltage_high]
                        battery_response = data[offset:offset + 20]
                        notification_received.set()
                        logger.debug(f"WitMotion battery response received: {battery_response.hex()}")
                        return
                offset += 1
        
        try:
            # Enable notifications on the data characteristic
            await client.start_notify(data_uuid, notification_handler)
            logger.debug(f"WitMotion notifications enabled on {data_uuid}")
            
            # Send battery voltage query command
            battery_cmd = bytes([0xFF, 0xAA, 0x27, 0x64, 0x00])  # Get battery voltage
            logger.debug(f"Sending WitMotion battery command: {battery_cmd.hex()}")
            await client.write_gatt_char(config_uuid, battery_cmd)
            
            # Wait for response (up to 2 seconds for device manager context)
            try:
                await asyncio.wait_for(notification_received.wait(), timeout=2.0)
                
                if battery_response and len(battery_response) >= 6:
                    # Parse WitMotion battery response
                    if battery_response[0] == 0x55 and battery_response[1] == 0x71:
                        # Format: 0x55 0x71 0x64 0x00 [voltage_low] [voltage_high] ...
                        voltage_raw = int.from_bytes(battery_response[4:6], byteorder='little', signed=False)
                        voltage_v = voltage_raw / 100.0  # Convert to volts
                        
                        # Convert voltage to battery percentage
                        # WitMotion BT50 typical range: 3.0V (0%) to 4.2V (100%)
                        min_voltage = 3.0
                        max_voltage = 4.2
                        battery_pct = int(((voltage_v - min_voltage) / (max_voltage - min_voltage)) * 100)
                        battery_pct = max(0, min(100, battery_pct))  # Clamp to 0-100%
                        
                        logger.debug(f"WitMotion battery: {battery_pct}% ({voltage_v:.2f}V) from {client.address}")
                        return battery_pct
                    elif battery_response[0] == 0x55 and battery_response[1] == 0x64:
                        # Original format: 0x55 0x64 [voltage_low] [voltage_high] [checksum]
                        voltage_raw = int.from_bytes(battery_response[2:4], byteorder='little', signed=False)
                        voltage_v = voltage_raw / 100.0  # Convert to volts
                        
                        min_voltage = 3.0
                        max_voltage = 4.2
                        battery_pct = int(((voltage_v - min_voltage) / (max_voltage - min_voltage)) * 100)
                        battery_pct = max(0, min(100, battery_pct))  # Clamp to 0-100%
                        
                        logger.debug(f"WitMotion battery: {battery_pct}% ({voltage_v:.2f}V) from {client.address}")
                        return battery_pct
                else:
                    logger.debug(f"WitMotion invalid or missing battery response from {client.address}")
                    
            except asyncio.TimeoutError:
                logger.debug(f"WitMotion battery query timeout from {client.address}")
                
            finally:
                # Clean up notifications
                await client.stop_notify(data_uuid)
                
        except Exception as e:
            logger.debug(f"WitMotion battery read failed for {client.address}: {e}")
        
        return None
    
    def _is_relevant_device(self, device_info: Dict[str, Any]) -> bool:
        """Check if device is relevant for shooting sports (BT50 sensors or AMG timers)"""
        device_name = device_info.get('name', '').upper()
        device_type = device_info.get('type', '')
        
        # Check for BT50 sensors (WitMotion accelerometers)
        bt50_patterns = ['BT50', 'WTVB01-BT50', 'WTVB01']
        if any(pattern in device_name for pattern in bt50_patterns):
            return True
        
        # Check for AMG timers (improved detection logic from Denis Zhadan)
        if self._is_amg_lab_timer(device_name):
            return True
        
        # Check for SpecialPie shot timers
        specialpie_patterns = ['SPECIALPIE', 'SP M1A2', 'SP-M1A2', 'SPECIAL PIE']
        if any(pattern in device_name for pattern in specialpie_patterns):
            return True
        
        # Also check by device type
        if device_type in ['accelerometer', 'timer', 'shot_timer']:
            return True
        
        # For debugging: log filtered out devices
        logger.debug(f"Filtered out device: {device_name} ({device_info.get('address')})")
        return False

    def _is_amg_lab_timer(self, device_name: str) -> bool:
        """
        Enhanced AMG Lab Commander timer detection
        Based on Denis Zhadan's improved device identification logic
        """
        if not device_name:
            return False
        
        # Convert to uppercase for case-insensitive matching
        upper_name = device_name.upper()
        
        # Denis Zhadan's detection logic: startsWith checks
        return (upper_name.startswith("AMG LAB COMM") or 
                upper_name.startswith("COMMANDER"))
    
    async def pair_device(self, mac_address: str, label: str) -> Dict[str, Any]:
        """Pair a discovered device and add to database with Bridge ownership"""
        # Allow pairing even if device not in current discovery session
        if mac_address in self.discovered_devices:
            device_info = self.discovered_devices[mac_address]
        else:
            # Create basic device info for devices not in current discovery
            logger.info(f"Pairing device {mac_address} without recent discovery - creating basic device info")
            device_info = {
                'address': mac_address,
                'name': label,
                'type': 'sensor',  # Default type
                'vendor': 'Unknown',
                'rssi': None,
                'pairable': True
            }
        
        # Check if device is already paired and create if needed
        with get_database_session() as session:
            # Get current Bridge within this session
            current_bridge = session.query(Bridge).first()
            if not current_bridge:
                raise ValueError("No Bridge configured - cannot pair devices")
            
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
            
            # Initialize handlers based on device type
            device_type = device_info.get('type', 'sensor')
            vendor = device_info.get('vendor', 'Unknown')
            
            if device_type == 'shot_timer' or 'SpecialPie' in vendor:
                # Initialize SpecialPie handler for shot timers
                try:
                    from .specialpie_handler import specialpie_manager
                    handler = specialpie_manager.add_timer(mac_address)
                    logger.info(f"Initialized SpecialPie timer handler for {mac_address}")
                    
                    # Store device type in calibration data
                    sensor.calib = {'device_type': 'shot_timer', 'vendor': vendor}
                except Exception as e:
                    logger.warning(f"Failed to initialize SpecialPie handler for {mac_address}: {e}")
            
            elif device_type == 'timer' or 'AMG' in vendor or 'Commander' in device_info.get('name', ''):
                # Initialize AMG Commander handler for AMG timers
                try:
                    from .amg_commander_handler import amg_manager
                    handler = amg_manager.add_timer(mac_address)
                    logger.info(f"Initialized AMG Commander timer handler for {mac_address}")
                    
                    # Store device type in calibration data
                    sensor.calib = {'device_type': 'timer', 'vendor': 'AMG Labs'}
                except Exception as e:
                    logger.warning(f"Failed to initialize AMG Commander handler for {mac_address}: {e}")
            
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

    async def refresh_device_battery(self, mac_address: str) -> Optional[int]:
        """Connect to device and read current battery level"""
        logger.info(f"Refreshing battery level for device {mac_address}")
        
        try:
            # Connect to device and read battery
            async with BleakClient(mac_address, timeout=10.0) as client:
                logger.debug(f"Connected to {mac_address} for battery refresh")
                battery_level = await self._read_battery_level(client)
                
                if battery_level is not None:
                    logger.info(f"Battery refresh successful: {mac_address} = {battery_level}%")
                else:
                    logger.warning(f"Battery refresh returned None for {mac_address}")
                    
                return battery_level
                
        except asyncio.TimeoutError:
            logger.warning(f"Battery refresh timeout for {mac_address}")
            return None
        except Exception as e:
            logger.error(f"Battery refresh failed for {mac_address}: {e}")
            return None

    async def refresh_all_device_batteries(self) -> List[Dict[str, Any]]:
        """Refresh battery status for all paired devices"""
        logger.info("Starting batch battery refresh for all paired devices")
        
        # Get all paired devices
        devices = self.get_paired_devices()
        results = []
        
        for device in devices:
            mac_address = device['address']
            logger.debug(f"Refreshing battery for {device['label']} ({mac_address})")
            
            try:
                battery_level = await self.refresh_device_battery(mac_address)
                
                if battery_level is not None:
                    # Update device health with new battery reading
                    await self.update_device_health(mac_address, battery=battery_level)
                    results.append({
                        "mac_address": mac_address,
                        "label": device['label'],
                        "status": "success",
                        "battery": battery_level
                    })
                    logger.info(f"✅ Battery updated: {device['label']} = {battery_level}%")
                else:
                    results.append({
                        "mac_address": mac_address,
                        "label": device['label'],
                        "status": "failed",
                        "battery": None,
                        "error": "Could not read battery level"
                    })
                    logger.warning(f"❌ Battery refresh failed: {device['label']}")
                    
            except Exception as e:
                results.append({
                    "mac_address": mac_address,
                    "label": device['label'],
                    "status": "failed",
                    "battery": None,
                    "error": str(e)
                })
                logger.error(f"❌ Battery refresh error for {device['label']}: {e}")
                
            # Add delay between devices to avoid BLE conflicts
            await asyncio.sleep(1)
        
        successful = len([r for r in results if r["status"] == "success"])
        total = len(results)
        logger.info(f"Batch battery refresh complete: {successful}/{total} successful")
        
        return results
    
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