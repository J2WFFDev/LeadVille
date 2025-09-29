"""
SpecialPie Shot Timer BLE Handler
Implements BLE communication protocol for SpecialPie SP M1A2 shot timers.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from bleak import BleakClient

logger = logging.getLogger(__name__)


class SpecialPieHandler:
    """Handler for SpecialPie SP M1A2 shot timer BLE communication"""
    
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self.client: Optional[BleakClient] = None
        self.is_connected = False
        self.is_monitoring = False
        
        # SpecialPie BLE characteristics
        self.notification_uuid = "0000fff1-0000-1000-8000-00805f9b34fb"
        
        # Shot tracking state
        self.previous_time_seconds: Optional[int] = None
        self.previous_time_ms: Optional[int] = None
        self.current_string_shots: List[Dict[str, Any]] = []
        
        # Event callbacks
        self.on_shot: Optional[Callable] = None
        self.on_string_start: Optional[Callable] = None
        self.on_string_stop: Optional[Callable] = None
        self.on_connection_change: Optional[Callable] = None
    
    async def connect(self) -> bool:
        """Connect to the SpecialPie timer"""
        try:
            self.client = BleakClient(self.mac_address, timeout=10.0)
            await self.client.connect()
            
            self.is_connected = self.client.is_connected
            
            if self.is_connected:
                logger.info(f"Connected to SpecialPie timer: {self.mac_address}")
                
                # Start notifications
                await self.client.start_notify(self.notification_uuid, self._notification_handler)
                logger.info(f"Notifications enabled on characteristic: {self.notification_uuid}")
                
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
                logger.error(f"Failed to connect to SpecialPie timer: {self.mac_address}")
                return False
                
        except Exception as e:
            logger.error(f"SpecialPie connection error for {self.mac_address}: {e}")
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
        """Disconnect from the SpecialPie timer"""
        try:
            if self.client and self.is_connected:
                # Stop notifications first
                try:
                    await self.client.stop_notify(self.notification_uuid)
                except Exception as e:
                    logger.warning(f"Error stopping notifications: {e}")
                
                await self.client.disconnect()
                logger.info(f"Disconnected from SpecialPie timer: {self.mac_address}")
            
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
            logger.error(f"SpecialPie disconnect error for {self.mac_address}: {e}")
    
    async def start_monitoring(self):
        """Start monitoring for shot events"""
        if not self.is_connected:
            raise RuntimeError("Must connect before starting monitoring")
        
        self.is_monitoring = True
        self.current_string_shots.clear()
        self.previous_time_seconds = None
        self.previous_time_ms = None
        
        logger.info(f"Started monitoring SpecialPie timer: {self.mac_address}")
    
    async def stop_monitoring(self):
        """Stop monitoring for shot events"""
        self.is_monitoring = False
        logger.info(f"Stopped monitoring SpecialPie timer: {self.mac_address}")
    
    async def _notification_handler(self, sender, data: bytearray):
        """Handle BLE notifications from SpecialPie timer"""
        if not self.is_monitoring:
            return
        
        try:
            # Convert bytearray to hex string representation
            hex_data = ' '.join(format(x, '02x') for x in data)
            
            # Convert hex data to integer array for parsing
            int_values = []
            hex_parts = hex_data.split(' ')
            for part in hex_parts:
                try:
                    int_values.append(int(part, 16))
                except ValueError:
                    continue
            
            if len(int_values) < 3:
                return
            
            # Parse SpecialPie protocol
            await self._parse_specialpie_data(int_values, hex_data)
            
        except Exception as e:
            logger.error(f"SpecialPie notification handler error: {e}")
    
    async def _parse_specialpie_data(self, int_values: List[int], raw_hex: str):
        """Parse SpecialPie timer data according to the protocol"""
        command_code = int_values[2] if len(int_values) > 2 else 0
        
        if command_code == 54:  # 0x36 - Shot data
            await self._handle_shot_data(int_values, raw_hex)
        elif command_code == 52:  # 0x34 - Start command
            await self._handle_string_start(raw_hex)
        elif command_code == 24:  # 0x18 - Stop command
            await self._handle_string_stop(raw_hex)
        else:
            logger.debug(f"Unknown SpecialPie command: {command_code} (hex: {hex(command_code)})")
    
    async def _handle_shot_data(self, int_values: List[int], raw_hex: str):
        """Handle shot timing data from SpecialPie timer"""
        if len(int_values) < 7:
            logger.warning(f"Insufficient shot data: {int_values}")
            return
        
        current_time_seconds = int_values[4]
        current_time_ms = int_values[5]
        shot_number = int_values[6]
        
        # Calculate split time if we have previous timing data
        split_ms = None
        if self.previous_time_seconds is not None and self.previous_time_ms is not None:
            # Calculate difference in milliseconds
            delta_seconds = current_time_seconds - self.previous_time_seconds
            delta_ms = current_time_ms - self.previous_time_ms
            
            # Handle millisecond rollover
            if delta_ms < 0:
                delta_seconds -= 1
                delta_ms += 100  # SpecialPie uses centiseconds (100 per second)
            
            split_ms = (delta_seconds * 1000) + (delta_ms * 10)  # Convert to milliseconds
        
        # Update previous times
        self.previous_time_seconds = current_time_seconds
        self.previous_time_ms = current_time_ms
        
        # Format timing data
        total_time_formatted = f"{current_time_seconds}.{current_time_ms:02d}"
        split_time_formatted = f"{split_ms / 1000:.3f}" if split_ms is not None else "0.000"
        
        # Create shot event
        shot_event = {
            'shot_number': shot_number,
            'total_time_ms': (current_time_seconds * 1000) + (current_time_ms * 10),
            'split_time_ms': split_ms,
            'total_time_formatted': total_time_formatted,
            'split_time_formatted': split_time_formatted,
            'timestamp': datetime.utcnow(),
            'raw_data': raw_hex,
            'device_address': self.mac_address
        }
        
        # Add to current string
        self.current_string_shots.append(shot_event)
        
        logger.info(f"SpecialPie Shot {shot_number}: {total_time_formatted}s (split: {split_time_formatted}s)")
        
        # Fire shot callback
        if self.on_shot:
            await self.on_shot(shot_event)
    
    async def _handle_string_start(self, raw_hex: str):
        """Handle string start event"""
        self.current_string_shots.clear()
        self.previous_time_seconds = None
        self.previous_time_ms = None
        
        start_event = {
            'timestamp': datetime.utcnow(),
            'raw_data': raw_hex,
            'device_address': self.mac_address
        }
        
        logger.info("SpecialPie string started")
        
        if self.on_string_start:
            await self.on_string_start(start_event)
    
    async def _handle_string_stop(self, raw_hex: str):
        """Handle string stop event"""
        stop_event = {
            'timestamp': datetime.utcnow(),
            'total_shots': len(self.current_string_shots),
            'shots': self.current_string_shots.copy(),
            'raw_data': raw_hex,
            'device_address': self.mac_address
        }
        
        if self.current_string_shots:
            total_time = self.current_string_shots[-1]['total_time_formatted']
            logger.info(f"SpecialPie string stopped: {stop_event['total_shots']} shots, {total_time}s total")
        else:
            logger.info("SpecialPie string stopped (no shots recorded)")
        
        if self.on_string_stop:
            await self.on_string_stop(stop_event)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current handler status"""
        return {
            'mac_address': self.mac_address,
            'connected': self.is_connected,
            'monitoring': self.is_monitoring,
            'current_shots': len(self.current_string_shots),
            'last_shot': self.current_string_shots[-1] if self.current_string_shots else None
        }


class SpecialPieManager:
    """Manager for multiple SpecialPie timers"""
    
    def __init__(self):
        self.handlers: Dict[str, SpecialPieHandler] = {}
        self.shot_callbacks: List[Callable] = []
        self.string_callbacks: List[Callable] = []
    
    def add_timer(self, mac_address: str) -> SpecialPieHandler:
        """Add a SpecialPie timer to management"""
        if mac_address in self.handlers:
            return self.handlers[mac_address]
        
        handler = SpecialPieHandler(mac_address)
        
        # Set up event forwarding
        handler.on_shot = self._forward_shot_event
        handler.on_string_start = self._forward_string_start
        handler.on_string_stop = self._forward_string_stop
        handler.on_connection_change = None  # No connection change callback for now
        
        self.handlers[mac_address] = handler
        logger.info(f"Added SpecialPie timer to manager: {mac_address}")
        return handler
    
    def remove_timer(self, mac_address: str):
        """Remove a SpecialPie timer from management"""
        if mac_address in self.handlers:
            handler = self.handlers[mac_address]
            asyncio.create_task(handler.disconnect())
            del self.handlers[mac_address]
            logger.info(f"Removed SpecialPie timer from manager: {mac_address}")
    
    def get_handler(self, mac_address: str) -> Optional[SpecialPieHandler]:
        """Get handler for specific timer"""
        return self.handlers.get(mac_address)
    
    def add_shot_callback(self, callback: Callable):
        """Add callback for shot events from any timer"""
        self.shot_callbacks.append(callback)
    
    def add_string_callback(self, callback: Callable):
        """Add callback for string start/stop events from any timer"""
        self.string_callbacks.append(callback)
    
    async def _forward_shot_event(self, shot_event: Dict[str, Any]):
        """Forward shot events to registered callbacks"""
        for callback in self.shot_callbacks:
            try:
                await callback(shot_event)
            except Exception as e:
                logger.error(f"Shot callback error: {e}")
    
    async def _forward_string_start(self, start_event: Dict[str, Any]):
        """Forward string start events to registered callbacks"""
        for callback in self.string_callbacks:
            try:
                await callback('start', start_event)
            except Exception as e:
                logger.error(f"String start callback error: {e}")
    
    async def _forward_string_stop(self, stop_event: Dict[str, Any]):
        """Forward string stop events to registered callbacks"""
        for callback in self.string_callbacks:
            try:
                await callback('stop', stop_event)
            except Exception as e:
                logger.error(f"String stop callback error: {e}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect all managed timers"""
        results = {}
        for mac_address, handler in self.handlers.items():
            try:
                results[mac_address] = await handler.connect()
            except Exception as e:
                logger.error(f"Failed to connect SpecialPie timer {mac_address}: {e}")
                results[mac_address] = False
        return results
    
    async def disconnect_all(self):
        """Disconnect all managed timers"""
        for handler in self.handlers.values():
            try:
                await handler.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting SpecialPie timer: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all managed timers"""
        return {
            'total_timers': len(self.handlers),
            'connected_timers': sum(1 for h in self.handlers.values() if h.is_connected),
            'monitoring_timers': sum(1 for h in self.handlers.values() if h.is_monitoring),
            'timers': {addr: handler.get_status() for addr, handler in self.handlers.items()}
        }


# Global SpecialPie manager instance
specialpie_manager = SpecialPieManager()