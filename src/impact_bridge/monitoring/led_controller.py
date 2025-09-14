"""LED status indicator controller for system health visualization."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from .health_aggregator import HealthStatus, AggregatedHealth

logger = logging.getLogger(__name__)


class LEDState(Enum):
    """LED states for status indication."""
    OFF = "off"
    ON = "on"
    SLOW_BLINK = "slow_blink"      # 1 second interval
    FAST_BLINK = "fast_blink"      # 0.5 second interval
    PULSE = "pulse"                # Breathing effect
    ERROR_PATTERN = "error_pattern" # SOS-like pattern


@dataclass
class LEDConfig:
    """LED configuration for a specific indicator."""
    name: str
    pin: Optional[int] = None       # GPIO pin number
    color: str = "green"           # Color identifier
    inverted: bool = False         # True if LED is active-low
    pwm_capable: bool = False      # True if pin supports PWM for brightness control
    
    # Status mappings
    healthy_state: LEDState = LEDState.ON
    warning_state: LEDState = LEDState.SLOW_BLINK
    critical_state: LEDState = LEDState.FAST_BLINK
    unknown_state: LEDState = LEDState.OFF


class LEDController:
    """Controls hardware LED status indicators.
    
    Provides visual feedback for:
    - BLE device connectivity
    - MQTT broker status
    - Database connectivity
    - Disk space levels
    - NTP synchronization status
    - Overall system health
    """
    
    def __init__(self, enable_hardware: bool = True, simulation_mode: bool = False):
        self.enable_hardware = enable_hardware
        self.simulation_mode = simulation_mode
        
        # LED configurations
        self.led_configs = {
            'system_health': LEDConfig(
                name="System Health",
                pin=18,  # GPIO 18
                color="red",
                healthy_state=LEDState.OFF,
                warning_state=LEDState.SLOW_BLINK,
                critical_state=LEDState.ON
            ),
            'ble_status': LEDConfig(
                name="BLE Status", 
                pin=23,  # GPIO 23
                color="blue",
                healthy_state=LEDState.ON,
                warning_state=LEDState.SLOW_BLINK,
                critical_state=LEDState.OFF
            ),
            'mqtt_status': LEDConfig(
                name="MQTT Status",
                pin=24,  # GPIO 24
                color="yellow",
                healthy_state=LEDState.ON,
                warning_state=LEDState.SLOW_BLINK,
                critical_state=LEDState.OFF
            ),
            'database_status': LEDConfig(
                name="Database Status",
                pin=25,  # GPIO 25
                color="green",
                healthy_state=LEDState.ON,
                warning_state=LEDState.SLOW_BLINK,
                critical_state=LEDState.OFF
            ),
            'disk_space': LEDConfig(
                name="Disk Space",
                pin=12,  # GPIO 12
                color="orange",
                healthy_state=LEDState.OFF,
                warning_state=LEDState.SLOW_BLINK,
                critical_state=LEDState.FAST_BLINK
            ),
            'ntp_sync': LEDConfig(
                name="NTP Sync",
                pin=16,  # GPIO 16
                color="purple",
                healthy_state=LEDState.ON,
                warning_state=LEDState.SLOW_BLINK,
                critical_state=LEDState.OFF
            )
        }
        
        # State tracking
        self._led_states: Dict[str, LEDState] = {}
        self._led_tasks: Dict[str, Optional[asyncio.Task]] = {}
        self._gpio_setup_done = False
        self._gpio = None
        
        # Initialize hardware if enabled
        if self.enable_hardware and not self.simulation_mode:
            self._setup_hardware()
    
    def _setup_hardware(self):
        """Initialize GPIO hardware for LED control."""
        try:
            # Try to import RPi.GPIO for Raspberry Pi
            import RPi.GPIO as GPIO
            self._gpio = GPIO
            
            # Setup GPIO mode
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Initialize all LED pins
            for led_name, config in self.led_configs.items():
                if config.pin is not None:
                    GPIO.setup(config.pin, GPIO.OUT)
                    # Set initial state to OFF
                    GPIO.output(config.pin, GPIO.LOW if not config.inverted else GPIO.HIGH)
                    self._led_states[led_name] = LEDState.OFF
                    self._led_tasks[led_name] = None
            
            self._gpio_setup_done = True
            logger.info("GPIO hardware initialized for LED control")
            
        except ImportError:
            logger.warning("RPi.GPIO not available, LED control disabled")
            self.enable_hardware = False
        except Exception as e:
            logger.error(f"Failed to initialize GPIO hardware: {e}")
            self.enable_hardware = False
    
    async def update_from_health_status(self, health_status: AggregatedHealth):
        """Update all LEDs based on comprehensive health status."""
        try:
            # Update system health LED (overall status)
            await self.set_led_status('system_health', health_status.overall_status)
            
            # Update component-specific LEDs
            component_status = {comp.name: comp.status for comp in health_status.components}
            
            # BLE services
            ble_status = component_status.get('ble_services', HealthStatus.UNKNOWN)
            await self.set_led_status('ble_status', ble_status)
            
            # MQTT broker
            mqtt_status = component_status.get('mqtt_broker', HealthStatus.UNKNOWN)
            await self.set_led_status('mqtt_status', mqtt_status)
            
            # Database
            db_status = component_status.get('database', HealthStatus.UNKNOWN)
            await self.set_led_status('database_status', db_status)
            
            # Disk space (use disk_space component status)
            disk_status = component_status.get('disk_space', HealthStatus.HEALTHY)
            await self.set_led_status('disk_space', disk_status)
            
            # NTP sync
            ntp_status = component_status.get('ntp_sync', HealthStatus.UNKNOWN)
            await self.set_led_status('ntp_sync', ntp_status)
            
        except Exception as e:
            logger.error(f"Error updating LEDs from health status: {e}")
    
    async def set_led_status(self, led_name: str, status: HealthStatus):
        """Set LED status based on health status."""
        if led_name not in self.led_configs:
            logger.warning(f"Unknown LED: {led_name}")
            return
        
        config = self.led_configs[led_name]
        
        # Determine LED state based on status
        if status == HealthStatus.HEALTHY:
            target_state = config.healthy_state
        elif status == HealthStatus.WARNING:
            target_state = config.warning_state
        elif status == HealthStatus.CRITICAL:
            target_state = config.critical_state
        else:  # UNKNOWN
            target_state = config.unknown_state
        
        # Update LED if state changed
        current_state = self._led_states.get(led_name)
        if current_state != target_state:
            await self._set_led_state(led_name, target_state)
    
    async def _set_led_state(self, led_name: str, state: LEDState):
        """Set the physical LED to a specific state."""
        if led_name not in self.led_configs:
            return
        
        config = self.led_configs[led_name]
        
        # Cancel existing LED task
        if led_name in self._led_tasks and self._led_tasks[led_name]:
            self._led_tasks[led_name].cancel()
            try:
                await self._led_tasks[led_name]
            except asyncio.CancelledError:
                pass
        
        # Update state tracking
        self._led_states[led_name] = state
        
        # Set LED based on state
        if state == LEDState.OFF:
            self._set_led_physical(config, False)
        elif state == LEDState.ON:
            self._set_led_physical(config, True)
        elif state == LEDState.SLOW_BLINK:
            self._led_tasks[led_name] = asyncio.create_task(
                self._blink_led(config, 1.0)
            )
        elif state == LEDState.FAST_BLINK:
            self._led_tasks[led_name] = asyncio.create_task(
                self._blink_led(config, 0.5)
            )
        elif state == LEDState.PULSE:
            self._led_tasks[led_name] = asyncio.create_task(
                self._pulse_led(config)
            )
        elif state == LEDState.ERROR_PATTERN:
            self._led_tasks[led_name] = asyncio.create_task(
                self._error_pattern_led(config)
            )
        
        if self.simulation_mode:
            logger.info(f"LED {config.name} ({config.color}) set to {state.value}")
    
    def _set_led_physical(self, config: LEDConfig, on: bool):
        """Set physical LED on/off state."""
        if not self.enable_hardware or not self._gpio_setup_done:
            return
        
        if config.pin is None:
            return
        
        try:
            if config.inverted:
                on = not on
            self._gpio.output(config.pin, self._gpio.HIGH if on else self._gpio.LOW)
        except Exception as e:
            logger.error(f"Error controlling LED {config.name}: {e}")
    
    async def _blink_led(self, config: LEDConfig, interval: float):
        """Blink LED with specified interval."""
        try:
            while True:
                self._set_led_physical(config, True)
                await asyncio.sleep(interval / 2)
                self._set_led_physical(config, False)
                await asyncio.sleep(interval / 2)
        except asyncio.CancelledError:
            self._set_led_physical(config, False)
    
    async def _pulse_led(self, config: LEDConfig):
        """Create breathing/pulse effect for LED."""
        if not config.pwm_capable or not self.enable_hardware:
            # Fallback to slow blink if PWM not available
            await self._blink_led(config, 2.0)
            return
        
        try:
            # PWM pulse implementation would go here
            # For now, fallback to slow blink
            await self._blink_led(config, 2.0)
        except asyncio.CancelledError:
            self._set_led_physical(config, False)
    
    async def _error_pattern_led(self, config: LEDConfig):
        """Create SOS-like error pattern for LED."""
        try:
            while True:
                # SOS pattern: ... --- ...
                # Short blinks
                for _ in range(3):
                    self._set_led_physical(config, True)
                    await asyncio.sleep(0.2)
                    self._set_led_physical(config, False)
                    await asyncio.sleep(0.2)
                
                await asyncio.sleep(0.5)
                
                # Long blinks
                for _ in range(3):
                    self._set_led_physical(config, True)
                    await asyncio.sleep(0.6)
                    self._set_led_physical(config, False)
                    await asyncio.sleep(0.2)
                
                await asyncio.sleep(0.5)
                
                # Short blinks again
                for _ in range(3):
                    self._set_led_physical(config, True)
                    await asyncio.sleep(0.2)
                    self._set_led_physical(config, False)
                    await asyncio.sleep(0.2)
                
                await asyncio.sleep(2.0)  # Pause before repeating
                
        except asyncio.CancelledError:
            self._set_led_physical(config, False)
    
    async def test_all_leds(self, duration: float = 2.0):
        """Test all LEDs by cycling through states."""
        logger.info("Testing all LEDs")
        
        for led_name in self.led_configs.keys():
            logger.info(f"Testing LED: {led_name}")
            
            # Test ON
            await self._set_led_state(led_name, LEDState.ON)
            await asyncio.sleep(duration / 4)
            
            # Test SLOW_BLINK
            await self._set_led_state(led_name, LEDState.SLOW_BLINK)
            await asyncio.sleep(duration / 2)
            
            # Test FAST_BLINK
            await self._set_led_state(led_name, LEDState.FAST_BLINK)
            await asyncio.sleep(duration / 4)
            
            # Turn OFF
            await self._set_led_state(led_name, LEDState.OFF)
        
        logger.info("LED test completed")
    
    def get_led_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current status of all LEDs."""
        status = {}
        for led_name, config in self.led_configs.items():
            current_state = self._led_states.get(led_name, LEDState.OFF)
            status[led_name] = {
                'name': config.name,
                'color': config.color,
                'pin': config.pin,
                'current_state': current_state.value,
                'hardware_enabled': self.enable_hardware and config.pin is not None
            }
        return status
    
    async def cleanup(self):
        """Clean up GPIO resources and cancel tasks."""
        # Cancel all LED tasks
        for task in self._led_tasks.values():
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Turn off all LEDs
        for led_name in self.led_configs.keys():
            await self._set_led_state(led_name, LEDState.OFF)
        
        # Cleanup GPIO
        if self._gpio_setup_done and self._gpio:
            try:
                self._gpio.cleanup()
                logger.info("GPIO cleanup completed")
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self._gpio_setup_done and self._gpio:
            try:
                self._gpio.cleanup()
            except:
                pass