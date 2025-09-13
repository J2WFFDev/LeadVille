"""AMG Labs Commander timer driver implementation."""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from .base import TimerDriverInterface
from ..ble.amg import AmgClient
from ..timer_simulator import AMGTimerSimulator, SimulationConfig, SimulationMode

logger = logging.getLogger(__name__)


class AMGTimerDriver(TimerDriverInterface):
    """Timer driver for AMG Labs Commander devices."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.amg_client: Optional[AmgClient] = None
        self.simulator: Optional[AMGTimerSimulator] = None
        
        # AMG-specific config with defaults
        self.device_id = config.get("device_id", "60:09:C3:1F:DC:1A")
        self.uuid = config.get("uuid", "6e400003-b5a3-f393-e0a9-e50e24dcca9e")
        self.simulation_mode = config.get("simulation_mode", False)
        self.frame_validation = config.get("frame_validation", True)
    
    @property
    def vendor_name(self) -> str:
        """Return the vendor name for this timer driver."""
        return "AMG Labs"
    
    @property
    def device_type(self) -> str:
        """Return the device type/model for this timer driver."""
        return "Commander"
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features."""
        return [
            "bluetooth_le",
            "shot_detection", 
            "t0_timing",
            "frame_validation",
            "health_monitoring",
            "simulation_mode"
        ]
    
    async def start(self) -> None:
        """Start the AMG timer driver."""
        if self._running:
            logger.warning("AMG timer driver already running")
            return
        
        try:
            if self.simulation_mode:
                await self._start_simulator()
            else:
                await self._start_real_timer()
            
            self._running = True
            await self._notify_callback('on_connect')
            logger.info(f"🎯 AMG timer driver started (simulation: {self.simulation_mode})")
            
        except Exception as e:
            logger.error(f"Failed to start AMG timer driver: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the AMG timer driver."""
        if not self._running:
            return
        
        try:
            if self.amg_client:
                await self.amg_client.stop()
                self.amg_client = None
            
            if self.simulator:
                await self.simulator.stop()
                self.simulator = None
            
            self._running = False
            await self._notify_callback('on_disconnect')
            logger.info("🔌 AMG timer driver stopped")
            
        except Exception as e:
            logger.error(f"Error stopping AMG timer driver: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current status of the AMG timer driver."""
        status = {
            'vendor': self.vendor_name,
            'device_type': self.device_type,
            'running': self._running,
            'simulation_mode': self.simulation_mode,
            'device_id': self.device_id,
            'connected': False
        }
        
        if self.simulation_mode and self.simulator:
            status['connected'] = self.simulator.is_connected
            status['device_id'] = self.simulator.device_id
        elif self.amg_client:
            status['connected'] = self.amg_client.is_connected
        
        return status
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get AMG device information."""
        return {
            'vendor': self.vendor_name,
            'device_type': self.device_type,
            'device_id': self.device_id,
            'uuid': self.uuid,
            'frame_validation': self.frame_validation,
            'supported_features': self.supported_features
        }
    
    async def _start_real_timer(self) -> None:
        """Start real AMG timer connection."""
        self.amg_client = AmgClient(
            mac_address=self.device_id,
            start_uuid=self.uuid
        )
        
        # Setup callbacks to bridge to our interface
        self.amg_client.set_parsed_data_callback(self._on_amg_event)
        self.amg_client.set_t0_callback(self._on_t0_event)
        self.amg_client.set_connect_callback(self._on_connect_event)
        self.amg_client.set_disconnect_callback(self._on_disconnect_event)
        
        await self.amg_client.start()
    
    async def _start_simulator(self) -> None:
        """Start AMG timer simulator."""
        sim_config_data = self.config.get("simulation", {})
        sim_config = SimulationConfig(
            mode=SimulationMode(sim_config_data.get("mode", "multi_shot")),
            num_shots=sim_config_data.get("num_shots", 5),
            shot_interval_sec=sim_config_data.get("shot_interval_sec", 2.0),
            start_delay_sec=sim_config_data.get("start_delay_sec", 3.0),
            random_timing=sim_config_data.get("random_timing", False),
            timing_variance_sec=sim_config_data.get("timing_variance_sec", 0.5),
            custom_sequence=sim_config_data.get("custom_sequence")
        )
        
        self.simulator = AMGTimerSimulator(config=sim_config)
        
        # Setup callbacks to bridge to our interface
        self.simulator.set_parsed_data_callback(self._on_amg_event)
        self.simulator.set_t0_callback(self._on_t0_event)
        self.simulator.set_connect_callback(self._on_connect_event)
        self.simulator.set_disconnect_callback(self._on_disconnect_event)
        
        await self.simulator.start()
    
    async def _on_amg_event(self, parsed_data: Dict[str, Any]) -> None:
        """Handle AMG timer events."""
        try:
            # Notify timer event callback
            await self._notify_callback('on_timer_event', parsed_data)
            
            # Check for shot detection
            if parsed_data.get('shot_state') == 'ACTIVE':
                await self._notify_callback('on_shot_detected', parsed_data)
                
        except Exception as e:
            logger.error(f"Error processing AMG event: {e}")
    
    async def _on_t0_event(self, timestamp_ns: int) -> None:
        """Handle T0 timing signal."""
        try:
            await self._notify_callback('on_t0_signal', timestamp_ns)
        except Exception as e:
            logger.error(f"Error processing T0 event: {e}")
    
    def _on_connect_event(self) -> None:
        """Handle connection event."""
        asyncio.create_task(self._notify_callback('on_connect'))
    
    def _on_disconnect_event(self) -> None:
        """Handle disconnection event.""" 
        asyncio.create_task(self._notify_callback('on_disconnect'))