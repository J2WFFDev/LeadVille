"""
Timer Health Monitoring
Tracks connection status, signal quality (RSSI), and battery level for AMG timer
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Timer connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected" 
    ERROR = "error"


@dataclass
class TimerHealthStatus:
    """Timer health monitoring data"""
    device_id: str
    connection_status: ConnectionStatus
    rssi: Optional[int] = None
    battery_level: Optional[int] = None
    last_seen: Optional[datetime] = None
    connection_time: Optional[datetime] = None
    disconnect_count: int = 0
    reconnect_count: int = 0
    error_count: int = 0
    uptime_seconds: float = 0.0
    data_rate_events_per_sec: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if self.last_seen:
            data['last_seen'] = self.last_seen.isoformat()
        if self.connection_time:
            data['connection_time'] = self.connection_time.isoformat()
        data['connection_status'] = self.connection_status.value
        return data


class TimerHealthMonitor:
    """Monitor AMG timer health and connection quality"""
    
    def __init__(
        self,
        device_id: str = "60:09:C3:1F:DC:1A",
        rssi_check_interval_sec: float = 30.0,
        health_report_interval_sec: float = 60.0
    ):
        self.device_id = device_id
        self.rssi_check_interval_sec = rssi_check_interval_sec
        self.health_report_interval_sec = health_report_interval_sec
        
        self.health_status = TimerHealthStatus(
            device_id=device_id,
            connection_status=ConnectionStatus.DISCONNECTED
        )
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._rssi_task: Optional[asyncio.Task] = None
        self._stop_monitoring = False
        
        # Event tracking
        self._event_count = 0
        self._event_window_start = time.time()
        self._event_window_duration = 10.0  # 10 second window
        
        # Callbacks
        self._on_health_update: Optional[Callable[[TimerHealthStatus], None]] = None
        self._client: Optional[Any] = None  # BleakClient reference
        
    def set_health_callback(self, callback: Callable[[TimerHealthStatus], None]):
        """Set callback for health status updates"""
        self._on_health_update = callback
        
    def set_bleak_client(self, client: Any):
        """Set BleakClient reference for RSSI monitoring"""
        self._client = client
        
    async def start_monitoring(self):
        """Start health monitoring"""
        self._stop_monitoring = False
        
        # Start monitoring tasks
        self._monitoring_task = asyncio.create_task(self._health_monitoring_loop())
        self._rssi_task = asyncio.create_task(self._rssi_monitoring_loop())
        
        logger.info("Timer health monitoring started")
        
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self._stop_monitoring = True
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
                
        if self._rssi_task:
            self._rssi_task.cancel()
            try:
                await self._rssi_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Timer health monitoring stopped")
        
    def on_connection_established(self):
        """Called when timer connects"""
        self.health_status.connection_status = ConnectionStatus.CONNECTED
        self.health_status.connection_time = datetime.now()
        self.health_status.reconnect_count += 1
        
        logger.info(f"Timer connected - reconnect count: {self.health_status.reconnect_count}")
        self._notify_health_update()
        
    def on_connection_lost(self):
        """Called when timer disconnects"""
        self.health_status.connection_status = ConnectionStatus.DISCONNECTED
        self.health_status.disconnect_count += 1
        
        # Update uptime
        if self.health_status.connection_time:
            uptime = datetime.now() - self.health_status.connection_time
            self.health_status.uptime_seconds += uptime.total_seconds()
            
        logger.warning(f"Timer disconnected - disconnect count: {self.health_status.disconnect_count}")
        self._notify_health_update()
        
    def on_connection_error(self, error: str):
        """Called when connection error occurs"""
        self.health_status.connection_status = ConnectionStatus.ERROR
        self.health_status.error_count += 1
        
        logger.error(f"Timer connection error: {error} (error count: {self.health_status.error_count})")
        self._notify_health_update()
        
    def on_timer_event(self, parsed_data: Dict[str, Any]):
        """Called when timer event is received"""
        self.health_status.last_seen = datetime.now()
        self._event_count += 1
        
        # Update data rate calculation
        self._update_data_rate()
        
    async def _health_monitoring_loop(self):
        """Main health monitoring loop"""
        while not self._stop_monitoring:
            try:
                # Update connection status if connected
                if (self.health_status.connection_status == ConnectionStatus.CONNECTED 
                    and self.health_status.connection_time):
                    
                    uptime = datetime.now() - self.health_status.connection_time
                    self.health_status.uptime_seconds = uptime.total_seconds()
                
                # Check if device is stale (no events for too long)
                if self.health_status.last_seen:
                    time_since_last_event = datetime.now() - self.health_status.last_seen
                    if time_since_last_event > timedelta(minutes=5):
                        logger.warning(f"Timer may be stale - last event: {time_since_last_event} ago")
                
                # Report health status periodically
                self._notify_health_update()
                
                await asyncio.sleep(self.health_report_interval_sec)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(1.0)
                
    async def _rssi_monitoring_loop(self):
        """Monitor RSSI (signal strength)"""
        while not self._stop_monitoring:
            try:
                if (self._client and 
                    hasattr(self._client, 'is_connected') and 
                    self._client.is_connected):
                    
                    try:
                        # Try to get RSSI from BleakClient
                        # Note: RSSI availability depends on platform
                        if hasattr(self._client, 'get_rssi'):
                            rssi = await self._client.get_rssi()
                            if rssi is not None:
                                self.health_status.rssi = rssi
                                logger.debug(f"Timer RSSI: {rssi} dBm")
                    except Exception as e:
                        logger.debug(f"RSSI read failed: {e}")
                        
                await asyncio.sleep(self.rssi_check_interval_sec)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"RSSI monitoring error: {e}")
                await asyncio.sleep(5.0)
                
    def _update_data_rate(self):
        """Update data rate calculation"""
        current_time = time.time()
        window_elapsed = current_time - self._event_window_start
        
        if window_elapsed >= self._event_window_duration:
            # Calculate events per second over the window
            self.health_status.data_rate_events_per_sec = self._event_count / window_elapsed
            
            # Reset for next window
            self._event_count = 0
            self._event_window_start = current_time
            
    def _notify_health_update(self):
        """Notify health status callback"""
        if self._on_health_update:
            try:
                self._on_health_update(self.health_status)
            except Exception as e:
                logger.error(f"Health callback error: {e}")
                
    def get_health_status(self) -> TimerHealthStatus:
        """Get current health status"""
        return self.health_status
        
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for logging"""
        status = self.health_status
        return {
            "connection_status": status.connection_status.value,
            "rssi_dbm": status.rssi,
            "uptime_seconds": status.uptime_seconds,
            "disconnect_count": status.disconnect_count,
            "error_count": status.error_count,
            "data_rate_events_per_sec": round(status.data_rate_events_per_sec, 2),
            "last_seen": status.last_seen.isoformat() if status.last_seen else None
        }


class TimerHealthIntegration:
    """Integration class to connect AMG client with health monitoring"""
    
    def __init__(self, health_monitor: TimerHealthMonitor):
        self.health_monitor = health_monitor
        
    def setup_amg_client_callbacks(self, amg_client):
        """Setup health monitoring callbacks on AMG client"""
        # Store reference for RSSI monitoring
        self.health_monitor.set_bleak_client(amg_client._client)
        
        # Wrap existing callbacks to include health monitoring
        original_connect_cb = amg_client._on_connect
        original_disconnect_cb = amg_client._on_disconnect
        original_parsed_data_cb = amg_client._on_parsed_data
        
        def enhanced_connect_cb():
            self.health_monitor.on_connection_established()
            if original_connect_cb:
                original_connect_cb()
                
        def enhanced_disconnect_cb():
            self.health_monitor.on_connection_lost()
            if original_disconnect_cb:
                original_disconnect_cb()
                
        def enhanced_parsed_data_cb(parsed_data):
            self.health_monitor.on_timer_event(parsed_data)
            if original_parsed_data_cb:
                original_parsed_data_cb(parsed_data)
        
        # Set enhanced callbacks
        amg_client.set_connect_callback(enhanced_connect_cb)
        amg_client.set_disconnect_callback(enhanced_disconnect_cb)
        amg_client.set_parsed_data_callback(enhanced_parsed_data_cb)