"""Kiosk API endpoints for boot status screen."""

import asyncio
import json
import logging
import platform
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import psutil

router = APIRouter()

logger = logging.getLogger(__name__)


def get_node_name() -> str:
    """Get the system node name."""
    try:
        return platform.node()
    except Exception:
        return "unknown"


def get_network_info() -> Dict[str, str]:
    """Get network information including mode, SSID, and IPs."""
    network_info = {
        "mode": "unknown",
        "ssid": "N/A", 
        "ipv4": [],
        "ipv6": []
    }
    
    try:
        # Get network interfaces
        interfaces = psutil.net_if_addrs()
        
        for interface_name, addresses in interfaces.items():
            if interface_name.startswith(('lo', 'docker', 'veth')):
                continue
                
            for addr in addresses:
                if addr.family == socket.AF_INET:  # IPv4
                    if not addr.address.startswith('127.'):
                        network_info["ipv4"].append(f"{interface_name}: {addr.address}")
                elif addr.family == socket.AF_INET6:  # IPv6
                    if not addr.address.startswith('::1'):
                        network_info["ipv6"].append(f"{interface_name}: {addr.address}")
        
        # Try to determine if we're on WiFi or Ethernet
        if 'wlan0' in interfaces or any('wl' in name for name in interfaces.keys()):
            network_info["mode"] = "WiFi"
            # Try to get SSID
            try:
                result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    network_info["ssid"] = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                pass
        elif 'eth0' in interfaces or any('en' in name for name in interfaces.keys()):
            network_info["mode"] = "Ethernet"
        
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
    
    return network_info


def get_service_status() -> Dict[str, str]:
    """Get status of key services."""
    services = {
        "leadville_api": "unknown",
        "leadville_bridge": "unknown", 
        "bluetooth": "unknown",
        "networking": "unknown"
    }
    
    try:
        # Check if we're running (API is up)
        services["leadville_api"] = "running"
        
        # Check Bluetooth service
        try:
            result = subprocess.run(['systemctl', 'is-active', 'bluetooth'], 
                                  capture_output=True, text=True, timeout=5)
            services["bluetooth"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        # Check networking
        try:
            result = subprocess.run(['systemctl', 'is-active', 'networking'], 
                                  capture_output=True, text=True, timeout=5)
            services["networking"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback: check if we have network connectivity
            if get_network_info()["ipv4"]:
                services["networking"] = "active"
            
        # Check if leadville bridge service exists
        try:
            result = subprocess.run(['systemctl', 'is-active', 'leadville'], 
                                  capture_output=True, text=True, timeout=5)
            services["leadville_bridge"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
    
    return services


def get_recent_logs(lines: int = 20) -> List[str]:
    """Get recent log lines from various sources."""
    log_lines = []
    
    try:
        # Try to get system logs
        try:
            result = subprocess.run(['journalctl', '-n', str(lines), '--no-pager'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                log_lines.extend(result.stdout.strip().split('\n')[-lines:])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        # Try to get LeadVille logs if available
        log_dirs = [
            Path("logs/main"),
            Path("logs/console"), 
            Path("logs/debug"),
            Path("/tmp/logs")
        ]
        
        for log_dir in log_dirs:
            if log_dir.exists():
                log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
                if log_files:
                    try:
                        with open(log_files[0], 'r') as f:
                            lines_from_file = f.readlines()[-lines:]
                            log_lines.extend([line.strip() for line in lines_from_file])
                        break
                    except Exception:
                        continue
                        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        log_lines.append(f"Error reading logs: {e}")
    
    # If we don't have any logs, add some status info
    if not log_lines:
        log_lines = [
            f"[{datetime.now().strftime('%H:%M:%S')}] LeadVille Boot Status Screen Active",
            f"[{datetime.now().strftime('%H:%M:%S')}] System: {platform.system()} {platform.release()}",
            f"[{datetime.now().strftime('%H:%M:%S')}] Python: {sys.version.split()[0]}",
            f"[{datetime.now().strftime('%H:%M:%S')}] Node: {get_node_name()}"
        ]
    
    return log_lines[-lines:]


@router.get("/status")
async def get_kiosk_status():
    """Get comprehensive system status for kiosk display."""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "node_name": get_node_name(),
            "network": get_network_info(),
            "services": get_service_status(),
            "logs": get_recent_logs(20),
            "system": {
                "platform": platform.system(),
                "release": platform.release(),
                "python_version": sys.version.split()[0],
                "uptime": _get_uptime()
            }
        }
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting kiosk status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


def _get_uptime() -> str:
    """Get system uptime."""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    except Exception:
        return "unknown"