"""WitMotion BT50 vibration sensor BLE client."""

from __future__ import annotations

import asyncio
import logging
import struct
import time
from typing import Callable, Optional, Tuple, List

from bleak import BleakClient, BleakError


logger = logging.getLogger(__name__)


class Bt50Sample:
    """Represents a single BT50 sensor sample."""
    
    def __init__(self, timestamp_ns: int, vx: float, vy: float, vz: float, amplitude: float, 
                 rssi: Optional[float] = None, battery_level: Optional[int] = None):
        self.timestamp_ns = timestamp_ns
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.amplitude = amplitude
        self.rssi = rssi
        self.battery_level = battery_level
    
    def to_dict(self) -> dict:
        """Convert sample to dictionary for logging."""
        result = {
            "ts": self.timestamp_ns,
            "vx": self.vx,
            "vy": self.vy,
            "vz": self.vz,
            "amp": self.amplitude,
        }
        if self.rssi is not None:
            result["rssi"] = self.rssi
        if self.battery_level is not None:
            result["battery"] = self.battery_level
        return result


class Bt50Calibration:
    """Calibration data for BT50 sensor baseline."""
    
    def __init__(self):
        self.baseline_vx = 0.0
        self.baseline_vy = 0.0 
        self.baseline_vz = 0.0
        self.samples_collected = 0
        self.is_calibrated = False
        self.calibration_samples: List[Tuple[float, float, float]] = []
        self.iqr_lower_vx = 0.0
        self.iqr_upper_vx = 0.0
        self.iqr_lower_vy = 0.0
        self.iqr_upper_vy = 0.0
        self.iqr_lower_vz = 0.0
        self.iqr_upper_vz = 0.0
    
    def add_sample(self, vx: float, vy: float, vz: float) -> bool:
        """Add calibration sample. Returns True when calibration is complete."""
        self.calibration_samples.append((vx, vy, vz))
        self.samples_collected += 1
        return self.samples_collected >= 100
    
    def finalize_calibration(self) -> None:
        """Calculate baseline and IQR bounds from collected samples."""
        if len(self.calibration_samples) < 100:
            logger.warning(f"Insufficient samples for calibration: {len(self.calibration_samples)}")
            return
            
        import numpy as np
        
        samples = np.array(self.calibration_samples)
        
        # Calculate quartiles for outlier filtering
        q1_vx, q3_vx = np.percentile(samples[:, 0], [25, 75])
        q1_vy, q3_vy = np.percentile(samples[:, 1], [25, 75])
        q1_vz, q3_vz = np.percentile(samples[:, 2], [25, 75])
        
        iqr_vx = q3_vx - q1_vx
        iqr_vy = q3_vy - q1_vy
        iqr_vz = q3_vz - q1_vz
        
        # Set IQR bounds (1.5 * IQR for outlier detection)
        self.iqr_lower_vx = q1_vx - 1.5 * iqr_vx
        self.iqr_upper_vx = q3_vx + 1.5 * iqr_vx
        self.iqr_lower_vy = q1_vy - 1.5 * iqr_vy
        self.iqr_upper_vy = q3_vy + 1.5 * iqr_vy
        self.iqr_lower_vz = q1_vz - 1.5 * iqr_vz
        self.iqr_upper_vz = q3_vz + 1.5 * iqr_vz
        
        # Filter outliers using IQR method
        filtered_samples = []
        for vx, vy, vz in self.calibration_samples:
            if (self.iqr_lower_vx <= vx <= self.iqr_upper_vx and
                self.iqr_lower_vy <= vy <= self.iqr_upper_vy and
                self.iqr_lower_vz <= vz <= self.iqr_upper_vz):
                filtered_samples.append((vx, vy, vz))
        
        if len(filtered_samples) < 50:  # Need at least 50 good samples
            logger.warning(f"Too many outliers in calibration: {len(filtered_samples)} valid samples")
            # Use all samples if too many outliers
            filtered_samples = self.calibration_samples
            
        # Calculate baseline from filtered samples
        filtered_array = np.array(filtered_samples)
        self.baseline_vx = np.mean(filtered_array[:, 0])
        self.baseline_vy = np.mean(filtered_array[:, 1]) 
        self.baseline_vz = np.mean(filtered_array[:, 2])
        
        self.is_calibrated = True
        
        logger.info(f"BT50 calibration complete:")
        logger.info(f"  Baseline: VX={self.baseline_vx:.6f}, VY={self.baseline_vy:.6f}, VZ={self.baseline_vz:.6f}")
        logger.info(f"  Samples: {len(filtered_samples)}/{len(self.calibration_samples)} after outlier filtering")
    
    def apply_calibration(self, vx: float, vy: float, vz: float) -> Tuple[float, float, float]:
        """Apply baseline correction to sample values."""
        if not self.is_calibrated:
            return vx, vy, vz
        return (vx - self.baseline_vx, vy - self.baseline_vy, vz - self.baseline_vz)


class Bt50HealthMonitor:
    """Health monitoring for BT50 sensor."""
    
    def __init__(self):
        self.last_sample_ns: Optional[int] = None
        self.connection_start_ns: Optional[int] = None
        self.total_samples = 0
        self.rssi_history: List[float] = []
        self.battery_level: Optional[int] = None
        self.connection_count = 0
        self.last_disconnect_ns: Optional[int] = None
    
    def on_connect(self) -> None:
        """Record connection event."""
        self.connection_start_ns = time.monotonic_ns()
        self.connection_count += 1
    
    def on_disconnect(self) -> None:
        """Record disconnection event."""
        self.last_disconnect_ns = time.monotonic_ns()
    
    def on_sample(self, sample: Bt50Sample) -> None:
        """Update health metrics with new sample."""
        self.last_sample_ns = sample.timestamp_ns
        self.total_samples += 1
        
        if sample.rssi is not None:
            self.rssi_history.append(sample.rssi)
            # Keep only last 100 RSSI readings
            if len(self.rssi_history) > 100:
                self.rssi_history.pop(0)
                
        if sample.battery_level is not None:
            self.battery_level = sample.battery_level
    
    def get_status(self) -> dict:
        """Get current health status."""
        now_ns = time.monotonic_ns()
        
        uptime_sec = None
        if self.connection_start_ns:
            uptime_sec = (now_ns - self.connection_start_ns) / 1_000_000_000
            
        idle_sec = None
        if self.last_sample_ns:
            idle_sec = (now_ns - self.last_sample_ns) / 1_000_000_000
            
        avg_rssi = None
        if self.rssi_history:
            avg_rssi = sum(self.rssi_history) / len(self.rssi_history)
        
        return {
            "total_samples": self.total_samples,
            "uptime_sec": uptime_sec,
            "idle_sec": idle_sec,
            "avg_rssi": avg_rssi,
            "battery_level": self.battery_level,
            "connection_count": self.connection_count,
        }


class Bt50Client:
    """BLE client for WitMotion BT50 vibration sensor."""
    
    def __init__(
        self,
        sensor_id: str,
        mac_address: str,
        notify_uuid: str,
        config_uuid: str = "",
        adapter: str = "hci0",
        idle_reconnect_sec: float = 300.0,
        keepalive_batt_sec: float = 30.0,
        reconnect_initial_sec: float = 0.1,
        reconnect_max_sec: float = 2.0,
        reconnect_jitter_sec: float = 0.5,
        auto_calibrate: bool = True,
        calibration_samples: int = 100,
        simulation_mode: bool = False,
    ) -> None:
        self.sensor_id = sensor_id
        self.mac_address = mac_address
        self.notify_uuid = notify_uuid
        self.config_uuid = config_uuid
        self.adapter = adapter
        self.idle_reconnect_sec = idle_reconnect_sec
        self.keepalive_batt_sec = keepalive_batt_sec
        self.reconnect_initial_sec = reconnect_initial_sec
        self.reconnect_max_sec = reconnect_max_sec
        self.reconnect_jitter_sec = reconnect_jitter_sec
        self.auto_calibrate = auto_calibrate
        self.calibration_samples = calibration_samples
        self.simulation_mode = simulation_mode
        
        self._client: Optional[BleakClient] = None
        self._connected = False
        self._stop_requested = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._simulation_task: Optional[asyncio.Task] = None
        
        # Sample tracking
        self._last_sample_ns: Optional[int] = None
        self._sample_count = 0
        
        # Calibration and health monitoring
        self.calibration = Bt50Calibration()
        self.health_monitor = Bt50HealthMonitor()
        self._calibrating = False
        
        # Callbacks
        self._on_sample: Optional[Callable[[Bt50Sample], None]] = None
        self._on_connect: Optional[Callable[[], None]] = None
        self._on_disconnect: Optional[Callable[[], None]] = None
        self._on_calibration_complete: Optional[Callable[[Bt50Calibration], None]] = None
    
    def set_sample_callback(self, callback: Callable[[Bt50Sample], None]) -> None:
        """Set callback for sensor samples."""
        self._on_sample = callback
    
    def set_connect_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for connection events."""
        self._on_connect = callback
    
    def set_disconnect_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for disconnection events."""
        self._on_disconnect = callback
        
    def set_calibration_callback(self, callback: Callable[[Bt50Calibration], None]) -> None:
        """Set callback for calibration completion."""
        self._on_calibration_complete = callback
    
    def start_calibration(self) -> None:
        """Manually start calibration process."""
        logger.info(f"Starting manual calibration for BT50 {self.sensor_id}")
        self.calibration = Bt50Calibration()  # Reset calibration
        self._calibrating = True
    
    def is_calibrating(self) -> bool:
        """Check if sensor is currently calibrating."""
        return self._calibrating
    
    def is_calibrated(self) -> bool:
        """Check if sensor is calibrated."""
        return self.calibration.is_calibrated
        
    def get_health_status(self) -> dict:
        """Get sensor health monitoring information."""
        return self.health_monitor.get_status()
    
    async def start(self) -> None:
        """Start the BT50 client with automatic reconnection."""
        self._stop_requested = False
        
        if self.simulation_mode:
            logger.info(f"Starting BT50 {self.sensor_id} in simulation mode")
            self._simulation_task = asyncio.create_task(self._simulation_loop())
        else:
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())
        
        # Start auto-calibration if enabled
        if self.auto_calibrate:
            self._calibrating = True
            logger.info(f"Auto-calibration enabled for BT50 {self.sensor_id} ({self.calibration_samples} samples)")
    
    async def stop(self) -> None:
        """Stop the BT50 client and disconnect."""
        self._stop_requested = True
        
        # Cancel tasks
        for task in [self._reconnect_task, self._keepalive_task, self._simulation_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        await self._disconnect()
    
    async def write_config(self, data: bytes) -> bool:
        """Write configuration to BT50 device if connected and config UUID configured."""
        if not self._connected or not self._client or not self.config_uuid:
            return False
        
        try:
            await self._client.write_gatt_char(self.config_uuid, data)
            return True
        except BleakError as e:
            logger.warning(f"BT50 {self.sensor_id} config write failed: {e}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if sensor is currently connected."""
        return self._connected
    
    @property
    def sample_count(self) -> int:
        """Get total sample count since start."""
        return self._sample_count
    
    def get_status(self) -> dict:
        """Get sensor status information."""
        health_status = self.health_monitor.get_status()
        
        return {
            "sensor_id": self.sensor_id,
            "connected": self._connected,
            "sample_count": self._sample_count,
            "last_sample_ns": self._last_sample_ns,
            "calibrating": self._calibrating,
            "calibrated": self.calibration.is_calibrated,
            "calibration_samples": self.calibration.samples_collected,
            "simulation_mode": self.simulation_mode,
            "health": health_status,
        }
    
    async def _reconnect_loop(self) -> None:
        """Main reconnection loop with exponential backoff."""
        retry_delay = self.reconnect_initial_sec
        
        while not self._stop_requested:
            try:
                if self.simulation_mode:
                    # In simulation mode, don't try to connect to real hardware
                    logger.info(f"BT50 {self.sensor_id} simulation mode - skipping real connection")
                    await asyncio.sleep(1.0)
                    continue
                    
                await self._connect()
                if self._connected:
                    # Reset retry delay on successful connection
                    retry_delay = self.reconnect_initial_sec
                    # Wait for disconnection
                    await self._wait_for_disconnect()
                
            except Exception as e:
                logger.warning(f"BT50 {self.sensor_id} connection failed: {e}")
            
            if not self._stop_requested:
                # Wait before retry with jitter
                jitter = (asyncio.get_event_loop().time() % 1.0) * self.reconnect_jitter_sec
                await asyncio.sleep(retry_delay + jitter)
                
                # Exponential backoff
                retry_delay = min(retry_delay * 2, self.reconnect_max_sec)
    
    async def _keepalive_loop(self) -> None:
        """Keepalive loop to detect idle sensors and force reconnection."""
        while not self._stop_requested:
            await asyncio.sleep(self.keepalive_batt_sec)
            
            if self._connected and self._last_sample_ns:
                idle_time_sec = (time.monotonic_ns() - self._last_sample_ns) / 1_000_000_000
                
                if idle_time_sec > self.idle_reconnect_sec:
                    logger.warning(
                        f"BT50 {self.sensor_id} idle for {idle_time_sec:.1f}s, reconnecting"
                    )
                    await self._disconnect()
    
    async def _connect(self) -> None:
        """Connect to BT50 device and setup notifications."""
        if self._connected:
            return
        
        logger.info(f"Connecting to BT50 {self.sensor_id} at {self.mac_address}")
        
        self._client = BleakClient(
            self.mac_address,
            adapter=self.adapter,
            disconnected_callback=self._on_device_disconnect,
        )
        
        await self._client.connect()
        self._connected = True
        
        # Subscribe to notifications
        await self._client.start_notify(self.notify_uuid, self._handle_notification)
        
        # Update health monitor
        self.health_monitor.on_connect()
        
        logger.info(f"BT50 {self.sensor_id} connected and notifications enabled")
        
        if self._on_connect:
            self._on_connect()
    
    async def _disconnect(self) -> None:
        """Disconnect from BT50 device."""
        if not self._connected:
            return
        
        self._connected = False
        
        # Update health monitor
        self.health_monitor.on_disconnect()
        
        if self._client:
            try:
                if self._client.is_connected:
                    await self._client.disconnect()
            except Exception as e:
                logger.warning(f"Error during BT50 {self.sensor_id} disconnect: {e}")
            finally:
                self._client = None
        
        if self._on_disconnect:
            self._on_disconnect()
        
        logger.info(f"BT50 {self.sensor_id} disconnected")
    
    async def _wait_for_disconnect(self) -> None:
        """Wait for device to disconnect."""
        while self._connected and not self._stop_requested:
            await asyncio.sleep(1.0)
    
    def _on_device_disconnect(self, client: BleakClient) -> None:
        """Handle device disconnection callback from Bleak."""
        logger.warning(f"BT50 {self.sensor_id} device disconnected")
        self._connected = False
        self.health_monitor.on_disconnect()
        if self._on_disconnect:
            self._on_disconnect()
    
    def _handle_notification(self, sender: int, data: bytes) -> None:
        """Handle incoming BLE notifications from BT50 sensor."""
        timestamp_ns = time.monotonic_ns()
        self._last_sample_ns = timestamp_ns
        self._sample_count += 1
        
        # Parse BT50 data packet
        sample = self._parse_bt50_data(timestamp_ns, data)
        
        if sample:
            # Update health monitor
            self.health_monitor.on_sample(sample)
            
            # Handle calibration if in progress
            if self._calibrating:
                calibration_complete = self.calibration.add_sample(sample.vx, sample.vy, sample.vz)
                
                if calibration_complete:
                    self.calibration.finalize_calibration()
                    self._calibrating = False
                    logger.info(f"BT50 {self.sensor_id} calibration complete")
                    
                    if self._on_calibration_complete:
                        self._on_calibration_complete(self.calibration)
            
            # Apply calibration correction if available
            if self.calibration.is_calibrated:
                corrected_vx, corrected_vy, corrected_vz = self.calibration.apply_calibration(
                    sample.vx, sample.vy, sample.vz
                )
                # Update sample with corrected values
                sample.vx = corrected_vx
                sample.vy = corrected_vy
                sample.vz = corrected_vz
                # Recalculate amplitude with corrected values
                sample.amplitude = (corrected_vx * corrected_vx + corrected_vy * corrected_vy + corrected_vz * corrected_vz) ** 0.5
            
            if self._on_sample:
                self._on_sample(sample)
    
    def _parse_bt50_data(self, timestamp_ns: int, data: bytes) -> Optional[Bt50Sample]:
        """
        Parse BT50 notification data into sensor sample.
        
        Expected format: 20-byte packets with acceleration data
        """
        if len(data) != 20:
            logger.debug(f"BT50 {self.sensor_id} unexpected packet length: {len(data)}")
            return None
        
        try:
            # Parse based on known BT50 packet structure
            # This may need adjustment based on actual device behavior
            
            # Extract acceleration values (assuming little-endian format)
            # Bytes 0-1: Header
            # Bytes 2-3: VX (int16)
            # Bytes 4-5: VY (int16) 
            # Bytes 6-7: VZ (int16)
            # Remaining bytes: other sensor data
            
            if data[0] != 0x55 or data[1] != 0x61:  # Check header
                logger.debug(f"BT50 {self.sensor_id} invalid header: {data[0]:02x}{data[1]:02x}")
                return None
            
            # Extract 16-bit signed acceleration values
            vx_raw = struct.unpack("<h", data[2:4])[0]
            vy_raw = struct.unpack("<h", data[4:6])[0]
            vz_raw = struct.unpack("<h", data[6:8])[0]
            
            # Convert to physical units (adjust scale factor as needed)
            # BT50 typically uses mg units (milli-g)
            scale = 1.0 / 32768.0 * 16.0  # Assuming ±16g range
            vx = vx_raw * scale
            vy = vy_raw * scale
            vz = vz_raw * scale
            
            # Calculate amplitude (magnitude)
            amplitude = (vx * vx + vy * vy + vz * vz) ** 0.5
            
            # Get RSSI if client is available
            rssi = None
            if self._client and self._client.is_connected:
                try:
                    # Note: RSSI retrieval depends on bleak version and platform
                    rssi = getattr(self._client, 'rssi', None)
                except:
                    pass
            
            # Extract battery level from packet if available (implementation dependent)
            battery_level = None
            if len(data) >= 12:
                try:
                    # This is a placeholder - actual battery extraction depends on BT50 protocol
                    battery_raw = data[11] 
                    if battery_raw <= 100:  # Simple validation
                        battery_level = battery_raw
                except:
                    pass
            
            return Bt50Sample(timestamp_ns, vx, vy, vz, amplitude, rssi, battery_level)
            
        except (struct.error, IndexError) as e:
            logger.warning(f"BT50 {self.sensor_id} parse error: {e}")
            return None
    
    async def _simulation_loop(self) -> None:
        """Simulation loop for testing without hardware."""
        import random
        import math
        
        self._connected = True
        self.health_monitor.on_connect()
        
        if self._on_connect:
            self._on_connect()
            
        logger.info(f"BT50 {self.sensor_id} simulation started")
        
        sample_count = 0
        base_time = time.monotonic_ns()
        
        # Simulate baseline for calibration
        baseline_vx = random.uniform(-0.1, 0.1)
        baseline_vy = random.uniform(-0.1, 0.1) 
        baseline_vz = random.uniform(0.9, 1.1)  # Simulate gravity
        
        while not self._stop_requested:
            try:
                # Simulate 100Hz sampling
                await asyncio.sleep(0.01)
                
                timestamp_ns = time.monotonic_ns()
                
                # Generate realistic sensor data
                noise_scale = 0.02
                impact_chance = 0.001  # 0.1% chance of impact per sample
                
                if random.random() < impact_chance:
                    # Simulate impact
                    impact_magnitude = random.uniform(5.0, 50.0)
                    impact_direction = random.uniform(0, 2 * math.pi)
                    vx = baseline_vx + impact_magnitude * math.cos(impact_direction) + random.uniform(-noise_scale, noise_scale)
                    vy = baseline_vy + impact_magnitude * math.sin(impact_direction) + random.uniform(-noise_scale, noise_scale)
                    vz = baseline_vz + random.uniform(-impact_magnitude/2, impact_magnitude/2) + random.uniform(-noise_scale, noise_scale)
                else:
                    # Normal sensor noise
                    vx = baseline_vx + random.uniform(-noise_scale, noise_scale)
                    vy = baseline_vy + random.uniform(-noise_scale, noise_scale)
                    vz = baseline_vz + random.uniform(-noise_scale, noise_scale)
                
                amplitude = (vx * vx + vy * vy + vz * vz) ** 0.5
                
                # Simulate RSSI and battery
                rssi = random.uniform(-70, -40)  # Typical BLE RSSI range
                battery_level = max(1, 100 - (sample_count // 10000))  # Simulate battery drain
                
                sample = Bt50Sample(timestamp_ns, vx, vy, vz, amplitude, rssi, battery_level)
                
                # Update counters and health
                self._last_sample_ns = timestamp_ns
                self._sample_count += 1
                sample_count += 1
                self.health_monitor.on_sample(sample)
                
                # Handle calibration
                if self._calibrating:
                    calibration_complete = self.calibration.add_sample(vx, vy, vz)
                    
                    if calibration_complete:
                        self.calibration.finalize_calibration()
                        self._calibrating = False
                        logger.info(f"BT50 {self.sensor_id} simulation calibration complete")
                        
                        if self._on_calibration_complete:
                            self._on_calibration_complete(self.calibration)
                
                # Apply calibration if available
                if self.calibration.is_calibrated:
                    corrected_vx, corrected_vy, corrected_vz = self.calibration.apply_calibration(vx, vy, vz)
                    sample.vx = corrected_vx
                    sample.vy = corrected_vy
                    sample.vz = corrected_vz
                    sample.amplitude = (corrected_vx * corrected_vx + corrected_vy * corrected_vy + corrected_vz * corrected_vz) ** 0.5
                
                if self._on_sample:
                    self._on_sample(sample)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"BT50 {self.sensor_id} simulation error: {e}")
                await asyncio.sleep(1.0)
        
        self._connected = False
        self.health_monitor.on_disconnect()
        
        if self._on_disconnect:
            self._on_disconnect()
            
        logger.info(f"BT50 {self.sensor_id} simulation stopped")