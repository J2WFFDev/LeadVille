# LeadVille Bridge Network Management Script
# Switches between Online (client) and Offline (AP) modes

import subprocess
import time
import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class NetworkManager:
    def __init__(self):
        self.config_dir = Path("/etc/leadville/network")
        self.hostapd_conf = "/etc/hostapd/leadville.conf"
        self.dnsmasq_conf = "/etc/dnsmasq.d/leadville.conf"
        self.current_mode = self.get_current_mode()
        
    def get_current_mode(self) -> str:
        """Detect current network mode"""
        try:
            # Check if hostapd is running
            result = subprocess.run(['systemctl', 'is-active', 'hostapd'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return "offline"
            else:
                return "online"
        except Exception:
            return "unknown"
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status and configuration"""
        status = {
            'mode': self.current_mode,
            'ssid': None,
            'ip_addresses': [],
            'connected_clients': 0,
            'interfaces': {}
        }
        
        try:
            # Get IP addresses
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
            if result.returncode == 0:
                status['ip_addresses'] = self._parse_ip_addresses(result.stdout)
            
            # Get WiFi info
            if self.current_mode == "online":
                status['ssid'] = self._get_connected_ssid()
            elif self.current_mode == "offline":
                status['ssid'] = "LeadVille-Bridge"
                status['connected_clients'] = self._get_connected_clients()
                
        except Exception as e:
            logger.error(f"Error getting network status: {e}")
            
        return status
    
    def switch_to_online_mode(self, ssid: str, password: str) -> bool:
        """Switch to online mode (join WiFi network)"""
        try:
            logger.info(f"Switching to online mode, connecting to {ssid}")
            
            # Stop AP services
            subprocess.run(['systemctl', 'stop', 'hostapd'], check=True)
            subprocess.run(['systemctl', 'stop', 'dnsmasq'], check=True)
            
            # Configure wpa_supplicant
            wpa_config = f"""
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
            with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
                f.write(wpa_config)
            
            # Restart networking
            subprocess.run(['systemctl', 'restart', 'wpa_supplicant'], check=True)
            subprocess.run(['systemctl', 'restart', 'dhcpcd'], check=True)
            
            # Wait for connection
            time.sleep(5)
            
            self.current_mode = "online"
            logger.info("Successfully switched to online mode")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to online mode: {e}")
            return False
    
    def switch_to_offline_mode(self) -> bool:
        """Switch to offline mode (AP mode with captive portal)"""
        try:
            logger.info("Switching to offline mode (AP mode)")
            
            # Stop client mode services
            subprocess.run(['systemctl', 'stop', 'wpa_supplicant'], check=False)
            subprocess.run(['systemctl', 'stop', 'dhcpcd'], check=False)
            
            # Configure static IP for wlan0
            subprocess.run(['ip', 'addr', 'flush', 'dev', 'wlan0'], check=True)
            subprocess.run(['ip', 'addr', 'add', '192.168.4.1/24', 'dev', 'wlan0'], check=True)
            subprocess.run(['ip', 'link', 'set', 'wlan0', 'up'], check=True)
            
            # Copy configuration files
            subprocess.run(['cp', str(self.config_dir / "hostapd.conf"), self.hostapd_conf], check=True)
            subprocess.run(['cp', str(self.config_dir / "dnsmasq.conf"), self.dnsmasq_conf], check=True)
            
            # Start AP services
            subprocess.run(['systemctl', 'start', 'hostapd'], check=True)
            subprocess.run(['systemctl', 'start', 'dnsmasq'], check=True)
            
            # Enable IP forwarding (if needed for internet sharing)
            subprocess.run(['sysctl', 'net.ipv4.ip_forward=1'], check=True)
            
            self.current_mode = "offline"
            logger.info("Successfully switched to offline mode")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to offline mode: {e}")
            return False
    
    def _parse_ip_addresses(self, ip_output: str) -> list:
        """Parse IP addresses from ip addr show output"""
        addresses = []
        lines = ip_output.split('\n')
        for line in lines:
            if 'inet ' in line and 'scope global' in line:
                addr = line.strip().split()[1]
                addresses.append(addr)
        return addresses
    
    def _get_connected_ssid(self) -> str:
        """Get currently connected WiFi SSID"""
        try:
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _get_connected_clients(self) -> int:
        """Get number of connected clients in AP mode"""
        try:
            result = subprocess.run(['iw', 'dev', 'wlan0', 'station', 'dump'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Count "Station" entries in output
                return result.stdout.count('Station')
        except Exception:
            pass
        return 0

# CLI interface for network management
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='LeadVille Network Manager')
    parser.add_argument('command', choices=['status', 'online', 'offline'], 
                       help='Network command to execute')
    parser.add_argument('--ssid', help='WiFi SSID for online mode')
    parser.add_argument('--password', help='WiFi password for online mode')
    
    args = parser.parse_args()
    
    nm = NetworkManager()
    
    if args.command == 'status':
        status = nm.get_network_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == 'online':
        if not args.ssid or not args.password:
            print("Error: --ssid and --password required for online mode")
            sys.exit(1)
        success = nm.switch_to_online_mode(args.ssid, args.password)
        sys.exit(0 if success else 1)
    
    elif args.command == 'offline':
        success = nm.switch_to_offline_mode()
        sys.exit(0 if success else 1)