"""
Enhanced AMG Commander Timer Handler
Based on AMG Labs Commander BLE protocol analysis from Denis Zhadan's project.
Supports sensitivity control, battery/signal monitoring, and shot data retrieval.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from bleak import BleakClient

logger = logging.getLogger(__name__)


class AmgCommanderHandler:
    """Enhanced handler for AMG Commander timer BLE communication"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self.client: Optional[BleakClient] = None
        self.is_connected = False
        self.is_monitoring = False
        
        # AMG Commander BLE UUIDs (from Denis Zhadan's analysis)
        self.service_uuid = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
        self.write_char_uuid = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Commands to timer
        self.notify_char_uuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Data from timer
        self.descriptor_uuid = "00002902-0000-1000-8000-00805f9b34fb"
        
        # Shot tracking state
        self.current_shots: List[Dict[str, Any]] = []
        self.time_first: Optional[float] = None
        self.time_now: Optional[float] = None
        self.time_split: Optional[float] = None
        self.shot_sequence: List[float] = []
        
        # Timer settings
        self.sensitivity: int = 5  # Default sensitivity (1-10)
        self.battery_level: Optional[int] = None
        self.signal_strength: Optional[int] = None
        self.random_delay: Optional[float] = None  # Start button to beep delay
        self.screen_data: Optional[Dict[str, Any]] = None  # Current display/screen data
        
        # Event callbacks
        self.on_shot: Optional[Callable] = None
        self.on_string_start: Optional[Callable] = None
        self.on_string_stop: Optional[Callable] = None
        self.on_timer_start: Optional[Callable] = None  # Remote start
        self.on_screen_update: Optional[Callable] = None  # Screen data updates
        self.on_connection_change: Optional[Callable] = None
    
    async def connect(self) -> bool:
        """Connect to the AMG Commander timer"""
        try:
            self.client = BleakClient(self.mac_address, timeout=10.0)
            await self.client.connect()
            
            self.is_connected = self.client.is_connected
            
            if self.is_connected:
                logger.info(f"Connected to AMG Commander: {self.mac_address}")
                
                # Start notifications
                await self.client.start_notify(self.notify_char_uuid, self._notification_handler)
                logger.info(f"AMG notifications enabled on: {self.notify_char_uuid}")
                
                # Read battery and signal strength
                await self._read_device_info()
                
                if self.on_connection_change:
                    try:
                        if asyncio.iscoroutinefunction(self.on_connection_change):
                            await self.on_connection_change(True, "Connected successfully")
                        else:
                            self.on_connection_change(True, "Connected successfully")
                    except Exception as cb_e:
                        logger.warning(f"Connection callback error: {cb_e}")
                
                return True
            else:
                logger.error(f"Failed to connect to AMG Commander: {self.mac_address}")
                return False
                
        except Exception as e:
            logger.error(f"AMG Commander connection error for {self.mac_address}: {e}")
            self.is_connected = False
            if self.on_connection_change:
                try:
                    if asyncio.iscoroutinefunction(self.on_connection_change):
                        await self.on_connection_change(False, f"Connection failed: {e}")
                    else:
                        self.on_connection_change(False, f"Connection failed: {e}")
                except Exception as cb_e:
                    logger.warning(f"Connection callback error: {cb_e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the AMG Commander timer"""
        try:
            if self.client and self.is_connected:
                try:
                    await self.client.stop_notify(self.notify_char_uuid)
                except Exception as e:
                    logger.warning(f"Error stopping notifications: {e}")
                
                await self.client.disconnect()
                logger.info(f"Disconnected from AMG Commander: {self.mac_address}")
            
            self.is_connected = False
            self.is_monitoring = False
            self.client = None
            
            if self.on_connection_change:
                try:
                    if asyncio.iscoroutinefunction(self.on_connection_change):
                        await self.on_connection_change(False, "Disconnected")
                    else:
                        self.on_connection_change(False, "Disconnected")
                except Exception as cb_e:
                    logger.warning(f"Disconnection callback error: {cb_e}")
                
        except Exception as e:
            logger.error(f"AMG Commander disconnect error for {self.mac_address}: {e}")
    
    async def start_monitoring(self):
        """Start monitoring for shot events"""
        if not self.is_connected:
            raise RuntimeError("Must connect before starting monitoring")
        
        self.is_monitoring = True
        self.current_shots.clear()
        self.shot_sequence.clear()
        
        # Request current shot data
        await self.request_shot_data()
        
        logger.info(f"Started monitoring AMG Commander: {self.mac_address}")
    
    async def stop_monitoring(self):
        """Stop monitoring for shot events"""
        self.is_monitoring = False
        logger.info(f"Stopped monitoring AMG Commander: {self.mac_address}")
    
    async def send_command(self, command: str) -> bool:
        """Send command to AMG Commander timer"""
        if not self.client or not self.is_connected:
            logger.error("AMG Commander not connected")
            return False
        
        try:
            command_bytes = command.encode('utf-8')
            await self.client.write_gatt_char(self.write_char_uuid, command_bytes)
            logger.debug(f"AMG Command sent: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to send AMG command '{command}': {e}")
            return False
    
    async def remote_start_timer(self) -> bool:
        """Remotely start the timer (trigger beep)"""
        return await self.send_command("COM START")
    
    async def set_sensitivity(self, sensitivity: int) -> bool:
        """Set timer sensitivity (1-10)"""
        if not 1 <= sensitivity <= 10:
            logger.error(f"Invalid sensitivity: {sensitivity}. Must be 1-10")
            return False
        
        command = f"SET SENSITIVITY {sensitivity:02d}"
        success = await self.send_command(command)
        if success:
            self.sensitivity = sensitivity
            logger.info(f"AMG sensitivity set to: {sensitivity}")
        return success
    
    async def request_shot_data(self) -> bool:
        """Request shot data from timer"""
        return await self.send_command("REQ STRING HEX")
    
    async def request_screen_data(self) -> bool:
        """Request screen/display data from timer"""
        return await self.send_command("REQ SCREEN HEX")
    
    async def _read_device_info(self):
        """Read battery level and signal strength"""
        try:
            # Try to read standard battery service
            battery_service_uuid = "0000180f-0000-1000-8000-00805f9b34fb"
            battery_char_uuid = "00002a19-0000-1000-8000-00805f9b34fb"
            
            services = await self.client.get_services()
            for service in services:
                if str(service.uuid).lower() == battery_service_uuid.lower():
                    try:
                        battery_data = await self.client.read_gatt_char(battery_char_uuid)
                        if battery_data and len(battery_data) > 0:
                            self.battery_level = int(battery_data[0])
                            logger.info(f"AMG Battery level: {self.battery_level}%")
                    except Exception as e:
                        logger.debug(f"AMG battery read failed: {e}")
        except Exception as e:
            logger.debug(f"AMG device info read error: {e}")
    
    def _convert_time_data(self, byte1: int, byte2: int) -> float:
        """Convert AMG time data from 2 bytes to seconds"""
        value = 256 * byte1 + byte2
        if byte2 <= 0:
            value += 256
        return value / 100.0  # Convert centiseconds to seconds
    
    async def _parse_screen_data(self, bytes_data: bytes):
        """Parse screen/display data from REQ SCREEN HEX response"""
        try:
            if len(bytes_data) < 3:
                return
            
            # Basic screen data structure (reverse engineered)
            screen_info = {
                'timestamp': datetime.utcnow(),
                'command_type': bytes_data[0],
                'data_length': bytes_data[1] if len(bytes_data) > 1 else 0,
                'raw_data': ' '.join(f'{b:02x}' for b in bytes_data),
                'parsed_fields': {}
            }
            
            # Try to extract meaningful screen information
            if len(bytes_data) >= 8:
                # Extract potential display values
                screen_info['parsed_fields']['field1'] = self._convert_time_data(bytes_data[2], bytes_data[3])
                screen_info['parsed_fields']['field2'] = self._convert_time_data(bytes_data[4], bytes_data[5])
                screen_info['parsed_fields']['field3'] = self._convert_time_data(bytes_data[6], bytes_data[7])
            
            self.screen_data = screen_info
            logger.info(f"AMG Screen data updated: {len(bytes_data)} bytes")
            logger.debug(f"AMG Screen content: {screen_info['raw_data']}")
            
            if self.on_screen_update:
                try:
                    if asyncio.iscoroutinefunction(self.on_screen_update):
                        await self.on_screen_update(screen_info)
                    else:
                        self.on_screen_update(screen_info)
                except Exception as cb_e:
                    logger.warning(f"Screen update callback error: {cb_e}")
                    
        except Exception as e:
            logger.error(f"AMG screen data parsing error: {e}")
    
    
    async def _notification_handler(self, sender, data: bytearray):
        """Handle BLE notifications from AMG Commander timer"""
        if not self.is_monitoring:
            return
        
        try:
            bytes_data = bytes(data)
            
            # Log raw data for debugging
            hex_str = ' '.join(f'{b:02x}' for b in bytes_data)
            logger.debug(f"AMG notification: {hex_str}")
            
            if len(bytes_data) < 2:
                return
            
            # Parse according to Denis Zhadan's protocol analysis
            command_type = bytes_data[0]
            
            if 10 <= command_type <= 26:
                # Shot sequence data
                shot_count = bytes_data[1]
                if command_type == 10:
                    self.shot_sequence.clear()  # First line of data
                
                # Extract shot times
                for i in range(1, shot_count + 1):
                    if (i * 2 + 1) < len(bytes_data):
                        shot_time = self._convert_time_data(bytes_data[i * 2], bytes_data[i * 2 + 1])
                        self.shot_sequence.append(shot_time)
                
                logger.info(f"AMG shot sequence updated: {len(self.shot_sequence)} shots")
                
            elif command_type == 2:
                # Screen/display data response (REQ SCREEN HEX)
                await self._parse_screen_data(bytes_data)
                
            elif command_type == 1:
                # Timer events
                event_type = bytes_data[1] if len(bytes_data) > 1 else 0
                
                if event_type == 5:
                    # Timer start
                    logger.info("AMG Timer started")
                    if self.on_timer_start:
                        await self.on_timer_start({'timestamp': datetime.utcnow(), 'device': self.mac_address})
                
                elif event_type == 8:
                    # Timer stop/waiting
                    logger.info("AMG Timer stopped")
                    if self.on_string_stop:
                        await self.on_string_stop({
                            'timestamp': datetime.utcnow(),
                            'total_shots': len(self.shot_sequence),
                            'shots': self.shot_sequence.copy(),
                            'device': self.mac_address
                        })
                
                elif event_type == 3 and len(bytes_data) >= 14:
                    # Real-time shot data
                    # bytes[4..5] - current time
                    # bytes[6..7] - split time  
                    # bytes[8..9] - first shot time
                    # bytes[10..11] - unknown field (environmental data?)
                    # bytes[12..13] - series/batch info
                    
                    self.time_now = self._convert_time_data(bytes_data[4], bytes_data[5])
                    self.time_split = self._convert_time_data(bytes_data[6], bytes_data[7])
                    self.time_first = self._convert_time_data(bytes_data[8], bytes_data[9])
                    
                    # Extract additional fields
                    unknown_field = None
                    series_batch = None
                    if len(bytes_data) >= 12:
                        unknown_field = self._convert_time_data(bytes_data[10], bytes_data[11])
                    if len(bytes_data) >= 14:
                        series_batch = self._convert_time_data(bytes_data[12], bytes_data[13])
                    
                    shot_event = {
                        'timestamp': datetime.utcnow(),
                        'time_now': self.time_now,
                        'time_split': self.time_split,
                        'time_first': self.time_first,
                        'unknown_field': unknown_field,  # Additional data field
                        'series_batch': series_batch,    # Series/batch information
                        'device': self.mac_address,
                        'raw_data': hex_str
                    }
                    
                    logger.info(f"AMG Shot: {self.time_now:.2f}s (split: {self.time_split:.2f}s, batch: {series_batch})")
                    
                    if self.on_shot:
                        await self.on_shot(shot_event)
        
        except Exception as e:
            logger.error(f"AMG notification handler error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current handler status"""
        return {
            'mac_address': self.mac_address,
            'connected': self.is_connected,
            'monitoring': self.is_monitoring,
            'sensitivity': self.sensitivity,
            'battery_level': self.battery_level,
            'signal_strength': self.signal_strength,
            'current_shots': len(self.shot_sequence),
            'last_time': self.time_now,
            'last_split': self.time_split,
            'last_first': self.time_first,
            'screen_data': self.screen_data,
            'shot_sequence': self.shot_sequence.copy() if self.shot_sequence else []
        }


class AmgCommanderManager:
    """Manager for multiple AMG Commander timers"""
    
    def __init__(self):
        self.handlers: Dict[str, AmgCommanderHandler] = {}
        self.shot_callbacks: List[Callable] = []
        self.timer_callbacks: List[Callable] = []
    
    def add_timer(self, mac_address: str) -> AmgCommanderHandler:
        """Add an AMG Commander timer to management"""
        if mac_address in self.handlers:
            return self.handlers[mac_address]
        
        handler = AmgCommanderHandler(mac_address)
        
        # Set up event forwarding
        handler.on_shot = self._forward_shot_event
        handler.on_timer_start = self._forward_timer_event
        handler.on_string_stop = self._forward_timer_event
        handler.on_connection_change = None
        
        self.handlers[mac_address] = handler
        logger.info(f"Added AMG Commander timer: {mac_address}")
        return handler
    
    def remove_timer(self, mac_address: str):
        """Remove an AMG Commander timer from management"""
        if mac_address in self.handlers:
            handler = self.handlers[mac_address]
            asyncio.create_task(handler.disconnect())
            del self.handlers[mac_address]
            logger.info(f"Removed AMG Commander timer: {mac_address}")
    
    def get_handler(self, mac_address: str) -> Optional[AmgCommanderHandler]:
        """Get handler for specific timer"""
        return self.handlers.get(mac_address)
    
    async def _forward_shot_event(self, shot_event: Dict[str, Any]):
        """Forward shot events to registered callbacks"""
        for callback in self.shot_callbacks:
            try:
                await callback(shot_event)
            except Exception as e:
                logger.error(f"AMG shot callback error: {e}")
    
    async def _forward_timer_event(self, timer_event: Dict[str, Any]):
        """Forward timer events to registered callbacks"""
        for callback in self.timer_callbacks:
            try:
                await callback(timer_event)
            except Exception as e:
                logger.error(f"AMG timer callback error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all managed timers"""
        return {
            'total_timers': len(self.handlers),
            'connected_timers': sum(1 for h in self.handlers.values() if h.is_connected),
            'monitoring_timers': sum(1 for h in self.handlers.values() if h.is_monitoring),
            'timers': {addr: handler.get_status() for addr, handler in self.handlers.items()}
        }


# Global AMG Commander manager instance
amg_manager = AmgCommanderManager()