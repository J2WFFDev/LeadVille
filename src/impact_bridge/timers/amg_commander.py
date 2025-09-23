"""
AMG Commander timer adapter conforming to ITimerAdapter interface.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Any, AsyncIterator

try:
    from bleak import BleakClient, BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False

from .base import BaseTimerAdapter
from .types import (
    TimerEvent, TimerInfo, ConnectionType,
    TimerConnected, TimerDisconnected, TimerReady,
    Shot, StringStart, StringStop, Battery, ClockSync
)

# Import existing AMG parser
try:
    from ..ble.amg_parse import parse_amg_timer_data, format_amg_event
    AMG_PARSER_AVAILABLE = True
except ImportError:
    AMG_PARSER_AVAILABLE = False

logger = logging.getLogger(__name__)


class AMGCommanderAdapter(BaseTimerAdapter):
    """AMG Commander timer adapter using existing AMG integration."""
    
    # AMG Commander BLE service UUID
    AMG_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
    AMG_NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    AMG_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    
    def __init__(self, **config):
        super().__init__("amg_commander")
        self.config = config
        self.ble_client = None
        self.device_info = TimerInfo(
            model="AMG Commander",
            firmware_version="Unknown",
            connection_type=ConnectionType.BLE
        )
        
        # State tracking for event generation
        self.current_string = None
        self.shot_count = 0
        self.string_start_time = None
        
    async def connect(self, **kwargs) -> None:
        """Connect to AMG Commander via BLE."""
        if not BLE_AVAILABLE:
            raise RuntimeError("bleak not available for AMG Commander")
        
        connection_args = {**self.config, **kwargs}
        mac_address = connection_args.get('mac_address') or connection_args.get('ble')
        
        if not mac_address:
            # Scan for AMG devices
            mac_address = await self._scan_for_amg()
            if not mac_address:
                raise RuntimeError("No AMG Commander devices found")
        
        logger.info(f"Connecting to AMG Commander: {mac_address}")
        
        try:
            self.ble_client = BleakClient(mac_address)
            await self.ble_client.connect()
            
            # Start notifications
            await self.ble_client.start_notify(
                self.AMG_NOTIFY_UUID, 
                self._amg_notification_handler
            )
            
            self._connected = True
            
            # Get device info
            try:
                device_name = await self.ble_client.read_gatt_char("00002a00-0000-1000-8000-00805f9b34fb")
                self.device_info.model = device_name.decode('utf-8').strip()
            except:
                pass
            
            await self._emit_event(TimerConnected(
                timestamp_ms=int(time.time() * 1000),
                raw={'connection': 'ble', 'mac': mac_address},
                info=self.device_info
            ))
            
            # AMG is ready when connected
            await self._emit_event(TimerReady(
                timestamp_ms=int(time.time() * 1000),
                raw={'status': 'ready'}
            ))
            
        except Exception as e:
            logger.error(f"Failed to connect to AMG Commander: {e}")
            raise
    
    async def _scan_for_amg(self) -> str | None:
        """Scan for AMG Commander devices."""
        logger.info("Scanning for AMG Commander devices...")
        
        devices = await BleakScanner.discover(timeout=10.0)
        for device in devices:
            # Look for AMG devices by service UUID or name
            if device.name:
                name_lower = device.name.lower()
                if any(keyword in name_lower for keyword in ['amg', 'commander', 'dc1a']):
                    logger.info(f"Found AMG device: {device.name} ({device.address})")
                    return device.address
        
        return None
    
    def _amg_notification_handler(self, sender: int, data: bytes) -> None:
        """Handle AMG BLE notifications and convert to timer events."""
        timestamp_ms = int(time.time() * 1000)
        hex_data = data.hex().upper()
        
        # Parse using existing AMG parser if available
        parsed_data = None
        if AMG_PARSER_AVAILABLE:
            try:
                parsed_data = parse_amg_timer_data(data)
            except Exception as e:
                logger.debug(f"AMG parsing failed: {e}")
        
        # Create raw data for event
        raw_data = {
            'hex': hex_data,
            'parsed': parsed_data,
            'length': len(data),
            'adapter': 'amg_commander'
        }
        
        # Convert to standardized timer events
        event = self._convert_amg_to_event(data, timestamp_ms, raw_data, parsed_data)
        if event:
            asyncio.create_task(self._emit_event(event))
    
    def _convert_amg_to_event(self, data: bytes, timestamp_ms: int, raw_data: Dict[str, Any], parsed_data: Dict[str, Any] = None) -> TimerEvent | None:
        """Convert AMG frame to standardized timer event."""
        if len(data) < 2:
            return None
        
        frame_header = data[0]
        frame_type = data[1]
        
        # Use parsed data if available, otherwise fall back to basic parsing
        if parsed_data:
            shot_state = parsed_data.get('shot_state', 'UNKNOWN')
            current_time = parsed_data.get('current_time', 0.0)
            current_shot = parsed_data.get('current_shot', 0)
            current_round = parsed_data.get('current_round', 0)
            
            if shot_state == 'START':
                self.current_string = current_round
                self.shot_count = 0
                self.string_start_time = timestamp_ms
                
                return StringStart(
                    timestamp_ms=timestamp_ms,
                    raw=raw_data,
                    string_number=current_round
                )
            
            elif shot_state == 'ACTIVE' and parsed_data.get('type_id') == 1:
                self.shot_count += 1
                split_ms = int(current_time * 1000) if current_time else None
                
                return Shot(
                    timestamp_ms=timestamp_ms,
                    raw=raw_data,
                    split_ms=split_ms,
                    shot_number=self.shot_count,
                    string_number=self.current_string
                )
            
            elif shot_state == 'STOPPED':
                total_ms = int(current_time * 1000) if current_time else 0
                shot_count = self.shot_count
                string_number = self.current_string
                
                # Reset state
                self.current_string = None
                self.shot_count = 0
                self.string_start_time = None
                
                return StringStop(
                    timestamp_ms=timestamp_ms,
                    raw=raw_data,
                    total_ms=total_ms,
                    shot_count=shot_count,
                    string_number=string_number
                )
        
        else:
            # Fallback to basic frame parsing
            if frame_header == 0x01 and frame_type == 0x05:  # START
                string_number = data[13] if len(data) >= 14 else None
                self.current_string = string_number
                self.shot_count = 0
                self.string_start_time = timestamp_ms
                
                return StringStart(
                    timestamp_ms=timestamp_ms,
                    raw=raw_data,
                    string_number=string_number
                )
            
            elif frame_header == 0x01 and frame_type == 0x03:  # SHOT
                if len(data) >= 14:
                    self.shot_count += 1
                    time_cs = (data[4] << 8) | data[5]
                    split_ms = int(time_cs * 10)  # Convert centiseconds to milliseconds
                    
                    return Shot(
                        timestamp_ms=timestamp_ms,
                        raw=raw_data,
                        split_ms=split_ms,
                        shot_number=self.shot_count,
                        string_number=self.current_string
                    )
            
            elif frame_header == 0x01 and frame_type == 0x08:  # STOP
                if len(data) >= 14:
                    time_cs = (data[4] << 8) | data[5]
                    total_ms = int(time_cs * 10)  # Convert centiseconds to milliseconds
                    shot_count = self.shot_count
                    string_number = data[13] if len(data) >= 14 else self.current_string
                    
                    # Reset state
                    self.current_string = None
                    self.shot_count = 0
                    self.string_start_time = None
                    
                    return StringStop(
                        timestamp_ms=timestamp_ms,
                        raw=raw_data,
                        total_ms=total_ms,
                        shot_count=shot_count,
                        string_number=string_number
                    )
        
        return None
    
    async def stop(self) -> None:
        """Stop the AMG adapter."""
        await super().stop()
        
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.disconnect()
            except Exception as e:
                logger.debug(f"Error disconnecting AMG: {e}")
        
        self.ble_client = None
        self._connected = False
    
    def info(self) -> TimerInfo:
        """Get AMG Commander device information."""
        return self.device_info