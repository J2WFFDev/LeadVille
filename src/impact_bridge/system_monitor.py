"""
System monitoring utilities for LeadVille Bridge
Provides CPU, memory, disk, temperature, and service health monitoring
"""

import psutil
import os
import subprocess
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self):
        self.last_cpu_times = None
        self.start_time = time.time()
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            'cpu': self._get_cpu_stats(),
            'memory': self._get_memory_stats(),
            'disk': self._get_disk_stats(),
            'temperature': self._get_temperature_stats(),
            'uptime': self._get_uptime(),
            'load_average': self._get_load_average(),
        }
        return stats
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of critical services"""
        services = {
            'fastapi': self._check_service_status('leadville-fastapi'),
            'nginx': self._check_service_status('nginx'),
            'hostapd': self._check_service_status('hostapd'),
            'dnsmasq': self._check_service_status('dnsmasq'),
            'mosquitto': self._check_service_status('mosquitto'),
            'bluetooth': self._check_service_status('bluetooth'),
        }
        return services
    
    def get_ble_quality(self) -> Dict[str, Any]:
        """Get BLE connection quality and status"""
        try:
            # Check if bluetooth adapter is available
            result = subprocess.run(['hciconfig', 'hci0'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return {'status': 'unavailable', 'adapter': None, 'devices': []}
            
            # Parse adapter status
            adapter_info = self._parse_hciconfig(result.stdout)
            
            # Get connected devices
            connected_devices = self._get_connected_ble_devices()
            
            return {
                'status': 'available',
                'adapter': adapter_info,
                'devices': connected_devices,
                'device_count': len(connected_devices)
            }
            
        except Exception as e:
            logger.error(f"Error getting BLE quality: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_network_interfaces(self) -> Dict[str, Any]:
        """Get network interface statistics"""
        interfaces = {}
        try:
            net_io = psutil.net_io_counters(pernic=True)
            for interface, stats in net_io.items():
                if interface.startswith('lo'):
                    continue  # Skip loopback
                
                interfaces[interface] = {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errors_in': stats.errin,
                    'errors_out': stats.errout,
                    'drops_in': stats.dropin,
                    'drops_out': stats.dropout
                }
        except Exception as e:
            logger.error(f"Error getting network interfaces: {e}")
            
        return interfaces
    
    def _get_cpu_stats(self) -> Dict[str, Any]:
        """Get CPU usage statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            return {
                'usage_percent': round(cpu_percent, 1),
                'core_count': cpu_count,
                'frequency': {
                    'current': round(cpu_freq.current, 0) if cpu_freq else None,
                    'min': round(cpu_freq.min, 0) if cpu_freq else None,
                    'max': round(cpu_freq.max, 0) if cpu_freq else None,
                } if cpu_freq else None
            }
        except Exception as e:
            logger.error(f"Error getting CPU stats: {e}")
            return {'usage_percent': 0, 'core_count': 0, 'frequency': None}
    
    def _get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'free': memory.free,
                'percent': round(memory.percent, 1),
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': round(swap.percent, 1)
                }
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {'total': 0, 'available': 0, 'used': 0, 'free': 0, 'percent': 0}
    
    def _get_disk_stats(self) -> Dict[str, Any]:
        """Get disk usage statistics"""
        try:
            # Get root filesystem stats
            disk = psutil.disk_usage('/')
            
            # Get I/O stats
            disk_io = psutil.disk_io_counters()
            
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': round(disk.percent, 1),
                'io': {
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0,
                    'read_count': disk_io.read_count if disk_io else 0,
                    'write_count': disk_io.write_count if disk_io else 0,
                } if disk_io else None
            }
        except Exception as e:
            logger.error(f"Error getting disk stats: {e}")
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}
    
    def _get_temperature_stats(self) -> Dict[str, Any]:
        """Get system temperature (Pi-specific)"""
        temperatures = {}
        try:
            # Try Pi-specific temperature file
            temp_file = Path('/sys/class/thermal/thermal_zone0/temp')
            if temp_file.exists():
                with open(temp_file, 'r') as f:
                    temp_c = int(f.read().strip()) / 1000.0
                    temperatures['cpu'] = {
                        'current': round(temp_c, 1),
                        'critical': 85.0,  # Pi throttling temp
                        'status': 'normal' if temp_c < 70 else 'warning' if temp_c < 80 else 'critical'
                    }
            
            # Try psutil sensors (may not work on all systems)
            try:
                sensors = psutil.sensors_temperatures()
                for name, entries in sensors.items():
                    if entries:
                        temp_c = entries[0].current
                        temperatures[name] = {
                            'current': round(temp_c, 1),
                            'high': entries[0].high if entries[0].high else None,
                            'critical': entries[0].critical if entries[0].critical else None,
                        }
            except (AttributeError, OSError):
                pass
                
        except Exception as e:
            logger.error(f"Error getting temperature stats: {e}")
            
        return temperatures
    
    def _get_uptime(self) -> Dict[str, Any]:
        """Get system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            return {
                'seconds': int(uptime_seconds),
                'boot_time': boot_time,
                'formatted': self._format_uptime(uptime_seconds)
            }
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return {'seconds': 0, 'boot_time': 0, 'formatted': '0s'}
    
    def _get_load_average(self) -> List[float]:
        """Get system load average"""
        try:
            return list(os.getloadavg())
        except (OSError, AttributeError):
            return [0.0, 0.0, 0.0]
    
    def _check_service_status(self, service_name: str) -> Dict[str, Any]:
        """Check systemd service status"""
        try:
            result = subprocess.run(['systemctl', 'is-active', service_name], 
                                  capture_output=True, text=True)
            is_active = result.returncode == 0
            status = result.stdout.strip()
            
            # Get more detailed info
            result = subprocess.run(['systemctl', 'show', service_name, 
                                   '--property=SubState,LoadState,ActiveState'], 
                                  capture_output=True, text=True)
            
            properties = {}
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        properties[key.lower()] = value
            
            return {
                'name': service_name,
                'active': is_active,
                'status': status,
                'substate': properties.get('substate', 'unknown'),
                'loadstate': properties.get('loadstate', 'unknown'),
            }
            
        except Exception as e:
            logger.error(f"Error checking service {service_name}: {e}")
            return {
                'name': service_name,
                'active': False,
                'status': 'error',
                'error': str(e)
            }
    
    def _parse_hciconfig(self, output: str) -> Dict[str, Any]:
        """Parse hciconfig output for adapter info"""
        info = {}
        try:
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                if 'UP RUNNING' in line:
                    info['status'] = 'running'
                elif 'DOWN' in line:
                    info['status'] = 'down'
                elif 'BD Address' in line:
                    info['address'] = line.split(':')[1].strip()
        except Exception as e:
            logger.error(f"Error parsing hciconfig: {e}")
            
        return info
    
    def _get_connected_ble_devices(self) -> List[Dict[str, Any]]:
        """Get list of connected BLE devices"""
        devices = []
        try:
            result = subprocess.run(['bluetoothctl', 'devices', 'Connected'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('Device'):
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            devices.append({
                                'address': parts[1],
                                'name': parts[2] if len(parts) > 2 else 'Unknown'
                            })
        except Exception as e:
            logger.error(f"Error getting connected BLE devices: {e}")
            
        return devices
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

# CLI interface for testing
if __name__ == "__main__":
    monitor = SystemMonitor()
    
    print("=== System Statistics ===")
    stats = monitor.get_system_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n=== Service Health ===")
    services = monitor.get_service_health()
    print(json.dumps(services, indent=2))
    
    print("\n=== BLE Quality ===")
    ble = monitor.get_ble_quality()
    print(json.dumps(ble, indent=2))