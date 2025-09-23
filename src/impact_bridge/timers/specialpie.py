"""
SpecialPie timer adapter implementation.

Supports multiple connection modes:
- USB Serial (CDC)
- Bluetooth LE
- UDP simulator
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import time
from typing import Dict, Any, Optional, AsyncIterator
from dataclasses import asdict

try:
    import serial_asyncio
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

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

logger = logging.getLogger(__name__)


class SpecialPieFramer:
    """
    Incremental frame decoder for SpecialPie protocol.
    """
    
    # TODO: fill from SpecialPie SDK
    FRAME_START = b'\xAA'  # Frame start marker
    FRAME_END = b'\x55'    # Frame end marker
    MIN_FRAME_SIZE = 8     # Minimum frame size
    MAX_FRAME_SIZE = 64    # Maximum frame size
    
    def __init__(self):
        self.buffer = bytearray()
    
    def feed(self, data: bytes) -> list[Dict[str, Any]]:
        """
        Feed incoming data and return complete frames.
        
        Args:
            data: Raw bytes from device
            
        Returns:
            List of parsed frame dictionaries
        """
        self.buffer.extend(data)
        frames = []
        
        while len(self.buffer) >= self.MIN_FRAME_SIZE:
            # Find frame start
            start_idx = self.buffer.find(self.FRAME_START)
            if start_idx == -1:
                # No frame start found, discard buffer
                self.buffer.clear()
                break
            
            # Remove data before frame start
            if start_idx > 0:
                self.buffer = self.buffer[start_idx:]
            
            # Look for frame end
            end_idx = self.buffer.find(self.FRAME_END, 1)
            if end_idx == -1:
                # No complete frame yet
                break
            
            # Extract frame
            frame_data = bytes(self.buffer[1:end_idx])  # Exclude start/end markers
            self.buffer = self.buffer[end_idx + 1:]
            
            # Parse frame
            try:
                parsed_frame = self._parse_frame(frame_data)
                if parsed_frame:
                    frames.append(parsed_frame)
            except Exception as e:
                logger.warning(f"Failed to parse SpecialPie frame: {e}, data: {frame_data.hex()}")
                continue
        
        # Prevent buffer overflow
        if len(self.buffer) > self.MAX_FRAME_SIZE * 2:
            logger.warning("SpecialPie frame buffer overflow, clearing")
            self.buffer.clear()
        
        return frames
    
    def _parse_frame(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse a single frame into a dictionary."""
        if len(data) < 4:
            return None
        
        # TODO: fill from SpecialPie SDK
        # Basic frame structure: [opcode][length][payload][checksum]
        opcode = data[0]
        length = data[1]
        
        if len(data) < length + 2:  # +2 for opcode and length
            return None
        
        payload = data[2:length]
        checksum = data[length] if length < len(data) else 0
        
        # Verify checksum (simple XOR for now)
        calculated_checksum = opcode ^ length
        for byte in payload:
            calculated_checksum ^= byte
        
        if checksum != calculated_checksum:
            logger.warning(f"SpecialPie frame checksum mismatch: got {checksum}, expected {calculated_checksum}")
            return None
        
        return {
            'opcode': opcode,
            'length': length,
            'payload': payload,
            'raw_hex': data.hex(),
            'timestamp_ms': int(time.time() * 1000)
        }


def parse_specialpie_frame(frame: Dict[str, Any]) -> Optional[TimerEvent]:
    """
    Parse a SpecialPie frame into a timer event.
    
    Args:
        frame: Parsed frame dictionary from SpecialPieFramer
        
    Returns:
        TimerEvent or None if frame is not recognized
    """
    opcode = frame.get('opcode', 0)
    payload = frame.get('payload', b'')
    timestamp_ms = frame.get('timestamp_ms', int(time.time() * 1000))
    
    # TODO: fill from SpecialPie SDK - these are placeholder opcodes
    if opcode == 0x01:  # String start
        string_number = payload[0] if len(payload) > 0 else None
        return StringStart(
            timestamp_ms=timestamp_ms,
            raw=frame,
            string_number=string_number
        )
    
    elif opcode == 0x02:  # Shot detected
        if len(payload) >= 4:
            split_ms = int.from_bytes(payload[0:2], 'little')
            shot_number = payload[2] if len(payload) > 2 else None
            string_number = payload[3] if len(payload) > 3 else None
            
            return Shot(
                timestamp_ms=timestamp_ms,
                raw=frame,
                split_ms=split_ms,
                shot_number=shot_number,
                string_number=string_number
            )
    
    elif opcode == 0x03:  # String stop
        if len(payload) >= 6:
            total_ms = int.from_bytes(payload[0:4], 'little')
            shot_count = payload[4]
            string_number = payload[5] if len(payload) > 5 else None
            
            return StringStop(
                timestamp_ms=timestamp_ms,
                raw=frame,
                total_ms=total_ms,
                shot_count=shot_count,
                string_number=string_number
            )
    
    elif opcode == 0x04:  # Battery status
        if len(payload) >= 1:
            level_pct = payload[0]
            return Battery(
                timestamp_ms=timestamp_ms,
                raw=frame,
                level_pct=level_pct
            )
    
    elif opcode == 0x05:  # Clock sync
        if len(payload) >= 8:
            device_time_ms = int.from_bytes(payload[0:4], 'little')
            host_time_ms = int.from_bytes(payload[4:8], 'little')
            delta_ms = device_time_ms - host_time_ms
            
            return ClockSync(
                timestamp_ms=timestamp_ms,
                raw=frame,
                delta_ms=delta_ms,
                device_time_ms=device_time_ms,
                host_time_ms=host_time_ms
            )
    
    elif opcode == 0x06:  # Ready status
        return TimerReady(
            timestamp_ms=timestamp_ms,
            raw=frame
        )
    
    # Unknown opcode
    logger.debug(f"Unknown SpecialPie opcode: {opcode:02x}")
    return None


class SpecialPieAdapter(BaseTimerAdapter):
    """SpecialPie timer adapter supporting serial, BLE, and UDP connections."""
    
    def __init__(self, **config):
        super().__init__("specialpie")
        self.config = config
        self.connection_type = None
        self.device_info = TimerInfo(
            model="SpecialPie Timer",
            firmware_version="Unknown",
            connection_type=ConnectionType.SERIAL
        )
        
        # Connection objects
        self.serial_connection = None
        self.ble_client = None
        self.udp_socket = None
        
        # Frame processing
        self.framer = SpecialPieFramer()
        
        # Watchdog and reconnection
        self.last_data_time = time.time()
        self.watchdog_timeout = 3.0  # 3 seconds
        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 30.0
        
    async def connect(self, **kwargs) -> None:
        """Connect to SpecialPie timer device."""
        # Merge config with connection args
        connection_args = {**self.config, **kwargs}
        
        # Determine connection type
        if 'port' in connection_args or 'serial' in connection_args:
            await self._connect_serial(connection_args)
        elif 'mac_address' in connection_args or 'ble' in connection_args:
            await self._connect_ble(connection_args)
        elif connection_args.get('simulator') or connection_args.get('sim'):
            await self._connect_udp_simulator(connection_args)
        else:
            raise ValueError("No valid connection parameters provided")
    
    async def _connect_serial(self, args: Dict[str, Any]) -> None:
        """Connect via USB serial."""
        if not SERIAL_AVAILABLE:
            raise RuntimeError("pyserial-asyncio not available")
        
        port = args.get('port') or args.get('serial', '/dev/ttyACM0')
        baud = args.get('baud', 115200)
        
        logger.info(f"Connecting to SpecialPie via serial: {port} @ {baud}")
        
        try:
            self.serial_connection = await serial_asyncio.open_serial_connection(
                url=port,
                baudrate=baud,
                timeout=1.0
            )
            
            self.connection_type = ConnectionType.SERIAL
            self.device_info.connection_type = ConnectionType.SERIAL
            self._connected = True
            
            # Start data processing task
            self._create_task(self._process_serial_data())
            
            await self._emit_event(TimerConnected(
                timestamp_ms=int(time.time() * 1000),
                raw={'connection': 'serial', 'port': port},
                info=self.device_info
            ))
            
        except Exception as e:
            logger.error(f"Failed to connect to SpecialPie serial: {e}")
            raise
    
    async def _connect_ble(self, args: Dict[str, Any]) -> None:
        """Connect via Bluetooth LE."""
        if not BLE_AVAILABLE:
            raise RuntimeError("bleak not available")
        
        mac_address = args.get('mac_address') or args.get('ble')
        
        if not mac_address:
            # Scan for SpecialPie devices
            mac_address = await self._scan_for_specialpie()
            if not mac_address:
                raise RuntimeError("No SpecialPie devices found")
        
        logger.info(f"Connecting to SpecialPie via BLE: {mac_address}")
        
        try:
            self.ble_client = BleakClient(mac_address)
            await self.ble_client.connect()
            
            self.connection_type = ConnectionType.BLE
            self.device_info.connection_type = ConnectionType.BLE
            self._connected = True
            
            # SpecialPie uses FFE0 service with FFE1 (notify) and FFE2 (write) 
            NOTIFY_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
            await self.ble_client.start_notify(NOTIFY_UUID, self._ble_notification_handler)
            
            await self._emit_event(TimerConnected(
                timestamp_ms=int(time.time() * 1000),
                raw={'connection': 'ble', 'mac': mac_address},
                info=self.device_info
            ))
            
        except Exception as e:
            logger.error(f"Failed to connect to SpecialPie BLE: {e}")
            raise
    
    async def _connect_udp_simulator(self, args: Dict[str, Any]) -> None:
        """Connect to UDP simulator."""
        port = args.get('sim_port', 12345)
        
        logger.info(f"Starting SpecialPie UDP simulator on port {port}")
        
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind(('localhost', port))
            self.udp_socket.setblocking(False)
            
            self.connection_type = ConnectionType.UDP
            self.device_info.connection_type = ConnectionType.UDP
            self.device_info.model = "SpecialPie Simulator"
            self._connected = True
            
            # Start simulator tasks
            self._create_task(self._process_udp_data())
            self._create_task(self._run_simulator())
            
            await self._emit_event(TimerConnected(
                timestamp_ms=int(time.time() * 1000),
                raw={'connection': 'udp', 'port': port},
                info=self.device_info
            ))
            
        except Exception as e:
            logger.error(f"Failed to start SpecialPie UDP simulator: {e}")
            raise
    
    async def _scan_for_specialpie(self) -> Optional[str]:
        """Scan for SpecialPie BLE devices."""
        logger.info("Scanning for SpecialPie devices...")
        
        devices = await BleakScanner.discover(timeout=10.0)
        for device in devices:
            if device.name and "SpecialPie" in device.name:
                logger.info(f"Found SpecialPie device: {device.name} ({device.address})")
                return device.address
        
        return None
    
    async def _process_serial_data(self) -> None:
        """Process incoming serial data."""
        reader, writer = self.serial_connection
        
        try:
            while self._running and self._connected:
                data = await reader.read(1024)
                if data:
                    self.last_data_time = time.time()
                    await self._process_frame_data(data)
                else:
                    await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Serial data processing error: {e}")
            await self._handle_disconnect("Serial error")
    
    def _ble_notification_handler(self, sender: int, data: bytes) -> None:
        """Handle BLE notifications."""
        self.last_data_time = time.time()
        asyncio.create_task(self._process_frame_data(data))
    
    async def _process_udp_data(self) -> None:
        """Process incoming UDP data."""
        loop = asyncio.get_event_loop()
        
        try:
            while self._running and self._connected:
                try:
                    data, addr = await loop.sock_recvfrom(self.udp_socket, 1024)
                    if data:
                        self.last_data_time = time.time()
                        await self._process_frame_data(data)
                except BlockingIOError:
                    await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"UDP data processing error: {e}")
            await self._handle_disconnect("UDP error")
    
    async def _process_frame_data(self, data: bytes) -> None:
        """Process incoming frame data."""
        frames = self.framer.feed(data)
        
        for frame in frames:
            event = parse_specialpie_frame(frame)
            if event:
                await self._emit_event(event)
    
    async def _run_simulator(self) -> None:
        """Run the UDP simulator, sending demo data."""
        await asyncio.sleep(2)  # Wait for connection to settle
        
        # Send ready event
        await self._send_simulator_frame(0x06, b'')  # Ready
        
        await asyncio.sleep(1)
        
        # Simulate a 5-shot string
        string_num = 1
        
        # String start
        await self._send_simulator_frame(0x01, bytes([string_num]))
        await asyncio.sleep(0.5)
        
        # 5 shots with realistic splits
        splits = [800, 250, 230, 240, 220]  # milliseconds
        for i, split_ms in enumerate(splits, 1):
            shot_data = split_ms.to_bytes(2, 'little') + bytes([i, string_num])
            await self._send_simulator_frame(0x02, shot_data)
            await asyncio.sleep(split_ms / 1000.0)
        
        # String stop
        total_ms = sum(splits)
        stop_data = total_ms.to_bytes(4, 'little') + bytes([len(splits), string_num])
        await self._send_simulator_frame(0x03, stop_data)
        
        logger.info(f"SpecialPie simulator completed demo string: {len(splits)} shots in {total_ms}ms")
    
    async def _send_simulator_frame(self, opcode: int, payload: bytes) -> None:
        """Send a simulated frame via UDP."""
        # Build frame with checksum
        length = len(payload)
        frame_data = bytes([opcode, length]) + payload
        
        # Calculate checksum
        checksum = opcode ^ length
        for byte in payload:
            checksum ^= byte
        
        frame_data += bytes([checksum])
        
        # Wrap with start/end markers
        complete_frame = SpecialPieFramer.FRAME_START + frame_data + SpecialPieFramer.FRAME_END
        
        # Send to ourselves (simulator)
        if self.udp_socket:
            self.udp_socket.sendto(complete_frame, ('localhost', self.udp_socket.getsockname()[1]))
    
    async def _handle_disconnect(self, reason: str) -> None:
        """Handle device disconnection."""
        if not self._connected:
            return
        
        self._connected = False
        logger.warning(f"SpecialPie disconnected: {reason}")
        
        await self._emit_event(TimerDisconnected(
            timestamp_ms=int(time.time() * 1000),
            raw={'reason': reason},
            reason=reason
        ))
        
        # Cleanup connections
        if self.serial_connection:
            try:
                _, writer = self.serial_connection
                writer.close()
                await writer.wait_closed()
            except:
                pass
            self.serial_connection = None
        
        if self.ble_client:
            try:
                await self.ble_client.disconnect()
            except:
                pass
            self.ble_client = None
        
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
            self.udp_socket = None
    
    def info(self) -> TimerInfo:
        """Get timer device information."""
        return self.device_info