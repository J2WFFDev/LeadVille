"""Tests for networking components."""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from impact_bridge.networking import NetworkManager, NetworkMonitor, CaptivePortal
from impact_bridge.networking.web_server import NetworkWebServer


class TestNetworkManager:
    """Test NetworkManager functionality."""
    
    def test_init(self):
        """Test NetworkManager initialization."""
        nm = NetworkManager()
        assert nm.current_mode in [NetworkManager.MODE_AP, NetworkManager.MODE_CLIENT]
        assert nm.MODE_AP == "ap"
        assert nm.MODE_CLIENT == "client"
    
    @patch('subprocess.run')
    def test_detect_current_mode_ap(self, mock_run):
        """Test detecting AP mode."""
        # Mock hostapd active
        mock_run.return_value = Mock(returncode=0, stdout="active")
        
        nm = NetworkManager()
        mode = nm._detect_current_mode()
        assert mode == NetworkManager.MODE_AP
    
    @patch('subprocess.run')
    def test_detect_current_mode_client(self, mock_run):
        """Test detecting client mode."""
        # Mock hostapd inactive, wpa_supplicant active
        def side_effect(*args, **kwargs):
            if 'hostapd' in args[0]:
                return Mock(returncode=1, stdout="inactive")
            elif 'wpa_supplicant' in args[0]:
                return Mock(returncode=0, stdout="active")
            return Mock(returncode=1, stdout="inactive")
        
        mock_run.side_effect = side_effect
        
        nm = NetworkManager()
        mode = nm._detect_current_mode()
        assert mode == NetworkManager.MODE_CLIENT
    
    @patch('subprocess.run')
    def test_has_internet_connectivity_success(self, mock_run):
        """Test successful internet connectivity check."""
        mock_run.return_value = Mock(returncode=0)
        
        nm = NetworkManager()
        assert nm.has_internet_connectivity() is True
    
    @patch('subprocess.run')
    def test_has_internet_connectivity_failure(self, mock_run):
        """Test failed internet connectivity check."""
        mock_run.return_value = Mock(returncode=1)
        
        nm = NetworkManager()
        assert nm.has_internet_connectivity() is False
    
    def test_get_status(self):
        """Test get_status method."""
        nm = NetworkManager()
        status = nm.get_status()
        
        assert isinstance(status, dict)
        assert 'mode' in status
        assert 'timestamp' in status
        assert 'connected' in status
        assert status['mode'] in [NetworkManager.MODE_AP, NetworkManager.MODE_CLIENT]


class TestNetworkMonitor:
    """Test NetworkMonitor functionality."""
    
    def test_init(self):
        """Test NetworkMonitor initialization."""
        nm = NetworkManager()
        monitor = NetworkMonitor(nm)
        
        assert monitor.network_manager is nm
        assert monitor.check_interval == 30
        assert monitor.failure_threshold == 3
        assert monitor.failure_count == 0
        assert monitor.is_monitoring is False
    
    def test_get_monitoring_status(self):
        """Test get_monitoring_status method."""
        nm = NetworkManager()
        monitor = NetworkMonitor(nm)
        
        status = monitor.get_monitoring_status()
        
        assert isinstance(status, dict)
        assert 'is_monitoring' in status
        assert 'check_interval' in status
        assert 'failure_threshold' in status
        assert 'failure_count' in status
        assert 'timestamp' in status
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        nm = NetworkManager()
        monitor = NetworkMonitor(nm, check_interval=1, failure_threshold=2)
        
        # Start monitoring
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True
        
        # Brief wait to ensure monitoring is active
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False


class TestCaptivePortal:
    """Test CaptivePortal functionality."""
    
    def test_init(self):
        """Test CaptivePortal initialization."""
        portal = CaptivePortal()
        assert portal.bridge_url == "http://bridge.local"
        assert portal.app is not None
    
    def test_init_custom_url(self):
        """Test CaptivePortal initialization with custom URL."""
        custom_url = "http://custom.local"
        portal = CaptivePortal(custom_url)
        assert portal.bridge_url == custom_url
    
    def test_get_app(self):
        """Test get_app method."""
        portal = CaptivePortal()
        app = portal.get_app()
        
        from flask import Flask
        assert isinstance(app, Flask)


class TestNetworkWebServer:
    """Test NetworkWebServer functionality."""
    
    def test_init(self):
        """Test NetworkWebServer initialization."""
        nm = NetworkManager()
        monitor = NetworkMonitor(nm)
        server = NetworkWebServer(nm, monitor)
        
        assert server.network_manager is nm
        assert server.network_monitor is monitor
        assert server.app is not None
    
    def test_parse_iwlist_output(self):
        """Test iwlist output parsing."""
        nm = NetworkManager()
        monitor = NetworkMonitor(nm)
        server = NetworkWebServer(nm, monitor)
        
        # Mock iwlist output
        iwlist_output = """
        Cell 01 - Address: AA:BB:CC:DD:EE:FF
                  ESSID:"TestNetwork"
                  Quality=70/70  Signal level=-40 dBm
                  Encryption key:on
        
        Cell 02 - Address: 11:22:33:44:55:66
                  ESSID:"OpenNetwork"
                  Quality=50/70  Signal level=-50 dBm
                  Encryption key:off
        """
        
        networks = server._parse_iwlist_output(iwlist_output)
        
        assert len(networks) == 2
        assert networks[0]['ssid'] == "TestNetwork"
        assert networks[0]['encrypted'] is True
        assert networks[0]['quality'] == 100
        
        assert networks[1]['ssid'] == "OpenNetwork"
        assert networks[1]['encrypted'] is False
        assert networks[1]['quality'] > 0
    
    def test_get_app(self):
        """Test get_app method."""
        nm = NetworkManager()
        monitor = NetworkMonitor(nm)
        server = NetworkWebServer(nm, monitor)
        
        from flask import Flask
        app = server.get_app()
        assert isinstance(app, Flask)


@pytest.mark.integration
class TestNetworkingIntegration:
    """Integration tests for networking components."""
    
    @pytest.mark.asyncio
    async def test_full_networking_stack(self):
        """Test the full networking stack initialization."""
        # Initialize all components
        nm = NetworkManager()
        monitor = NetworkMonitor(nm, check_interval=1, failure_threshold=2)
        server = NetworkWebServer(nm, monitor)
        portal = CaptivePortal()
        
        # Verify they can work together
        status = nm.get_status()
        monitor_status = monitor.get_monitoring_status()
        
        assert isinstance(status, dict)
        assert isinstance(monitor_status, dict)
        
        # Test brief monitoring cycle
        await monitor.start_monitoring()
        await asyncio.sleep(0.1)
        await monitor.stop_monitoring()
        
        # Verify no errors occurred
        assert True  # If we get here without exceptions, the test passes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])