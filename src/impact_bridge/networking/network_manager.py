"""Network manager for switching between AP and Client modes."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, Union
import json

logger = logging.getLogger(__name__)


class NetworkManager:
    """Manages network mode switching between AP (offline) and Client (online) modes."""
    
    # Network modes
    MODE_AP = "ap"
    MODE_CLIENT = "client"
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize NetworkManager.
        
        Args:
            config_dir: Directory containing network configuration files
        """
        self.config_dir = config_dir or Path("/etc/leadville/network")
        self.current_mode = self._detect_current_mode()
        self.status_file = Path("/tmp/leadville_network_status.json")
        
    def _detect_current_mode(self) -> str:
        """Detect current network mode by checking running services."""
        try:
            # Check if hostapd is running (AP mode)
            result = subprocess.run(
                ["systemctl", "is-active", "hostapd"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip() == "active":
                return self.MODE_AP
            
            # Check if wpa_supplicant is running (Client mode)
            result = subprocess.run(
                ["systemctl", "is-active", "wpa_supplicant"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip() == "active":
                return self.MODE_CLIENT
                
        except Exception as e:
            logger.warning(f"Failed to detect network mode: {e}")
            
        # Default to AP mode if uncertain
        return self.MODE_AP
    
    def get_status(self) -> Dict[str, Union[str, bool, float]]:
        """Get current network status and connectivity information."""
        status = {
            "mode": self.current_mode,
            "timestamp": time.time(),
            "connected": False,
            "ip_address": None,
            "interface": None,
            "ssid": None
        }
        
        try:
            if self.current_mode == self.MODE_CLIENT:
                # Check client mode connectivity
                status.update(self._get_client_status())
            else:
                # Check AP mode status
                status.update(self._get_ap_status())
                
        except Exception as e:
            logger.error(f"Failed to get network status: {e}")
            status["error"] = str(e)
            
        # Save status to file for monitoring
        self._save_status(status)
        return status
    
    def _get_client_status(self) -> Dict[str, Union[str, bool]]:
        """Get client mode network status."""
        status = {"connected": False}
        
        try:
            # Check internet connectivity
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", "8.8.8.8"],
                capture_output=True,
                text=True
            )
            status["connected"] = result.returncode == 0
            
            # Get IP address and interface
            result = subprocess.run(
                ["ip", "route", "get", "8.8.8.8"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if "src" in parts:
                    src_idx = parts.index("src")
                    if src_idx + 1 < len(parts):
                        status["ip_address"] = parts[src_idx + 1]
                if "dev" in parts:
                    dev_idx = parts.index("dev")
                    if dev_idx + 1 < len(parts):
                        status["interface"] = parts[dev_idx + 1]
            
            # Get connected SSID
            result = subprocess.run(
                ["iwgetid", "-r"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                status["ssid"] = result.stdout.strip()
                
        except Exception as e:
            logger.warning(f"Failed to get client status: {e}")
            
        return status
    
    def _get_ap_status(self) -> Dict[str, Union[str, bool]]:
        """Get AP mode network status."""
        status = {"connected": True}  # AP mode is always "connected" locally
        
        try:
            # Get AP interface IP
            result = subprocess.run(
                ["ip", "addr", "show", "wlan0"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "inet " in line and "scope global" in line:
                        parts = line.strip().split()
                        if parts[0] == "inet":
                            status["ip_address"] = parts[1].split('/')[0]
                            status["interface"] = "wlan0"
                            break
            
            status["ssid"] = "LeadVille-Bridge"  # Default AP SSID
                
        except Exception as e:
            logger.warning(f"Failed to get AP status: {e}")
            
        return status
    
    def switch_to_ap_mode(self) -> bool:
        """Switch to AP (Access Point) mode."""
        if self.current_mode == self.MODE_AP:
            logger.info("Already in AP mode")
            return True
            
        logger.info("Switching to AP mode...")
        
        try:
            # Stop client mode services
            subprocess.run(["sudo", "systemctl", "stop", "wpa_supplicant"], check=False)
            subprocess.run(["sudo", "systemctl", "stop", "dhcpcd"], check=False)
            
            # Start AP mode services
            subprocess.run(["sudo", "systemctl", "start", "hostapd"], check=True)
            subprocess.run(["sudo", "systemctl", "start", "dnsmasq"], check=True)
            
            # Configure interface
            subprocess.run([
                "sudo", "ip", "addr", "add", "192.168.4.1/24", "dev", "wlan0"
            ], check=False)
            
            self.current_mode = self.MODE_AP
            logger.info("Successfully switched to AP mode")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to AP mode: {e}")
            return False
    
    def switch_to_client_mode(self, ssid: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Switch to Client mode with optional network credentials."""
        if self.current_mode == self.MODE_CLIENT:
            logger.info("Already in Client mode")
            return True
            
        logger.info("Switching to Client mode...")
        
        try:
            # Stop AP mode services
            subprocess.run(["sudo", "systemctl", "stop", "hostapd"], check=False)
            subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"], check=False)
            
            # Configure network if credentials provided
            if ssid and password:
                self._configure_wifi_credentials(ssid, password)
            
            # Start client mode services
            subprocess.run(["sudo", "systemctl", "start", "wpa_supplicant"], check=True)
            subprocess.run(["sudo", "systemctl", "start", "dhcpcd"], check=True)
            
            # Wait for connection
            time.sleep(5)
            
            self.current_mode = self.MODE_CLIENT
            logger.info("Successfully switched to Client mode")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to Client mode: {e}")
            return False
    
    def _configure_wifi_credentials(self, ssid: str, password: str) -> None:
        """Configure WiFi credentials for client mode."""
        wpa_config = f'''country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
        
        try:
            with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
                f.write(wpa_config)
            logger.info(f"Configured WiFi credentials for SSID: {ssid}")
        except Exception as e:
            logger.error(f"Failed to configure WiFi credentials: {e}")
            raise
    
    def _save_status(self, status: Dict) -> None:
        """Save network status to file for monitoring."""
        try:
            with open(self.status_file, "w") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save network status: {e}")
    
    def has_internet_connectivity(self) -> bool:
        """Check if device has internet connectivity."""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", "8.8.8.8"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False