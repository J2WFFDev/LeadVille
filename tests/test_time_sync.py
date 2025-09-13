"""
Tests for time synchronization system
"""

import asyncio
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Import from the specific modules to avoid dependency issues
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from impact_bridge.time_sync import TimeSynchronizer, TimeSyncStatus
from impact_bridge.ntp_client import NTPClient, NTPSyncResult


class TestTimeSynchronizer:
    """Test cases for TimeSynchronizer"""
    
    def test_initialization_default(self):
        """Test TimeSynchronizer initialization with defaults"""
        sync = TimeSynchronizer()
        
        assert sync.enabled is True
        assert sync.ntp_enabled is True
        assert sync.drift_threshold_ms == 20.0
        assert sync.sync_interval_minutes == 5.0
        assert sync.enable_correction is True
        assert sync.ntp_client is not None
        
    def test_initialization_custom(self):
        """Test TimeSynchronizer initialization with custom settings"""
        sync = TimeSynchronizer(
            sync_interval_minutes=2.0,
            drift_threshold_ms=10.0,
            enabled=False,
            ntp_enabled=False,
            enable_correction=False
        )
        
        assert sync.enabled is False
        assert sync.ntp_enabled is False
        assert sync.drift_threshold_ms == 10.0
        assert sync.sync_interval_minutes == 2.0
        assert sync.enable_correction is False
        assert sync.ntp_client is None
        
    def test_sync_status_initialization(self):
        """Test sync status initialization"""
        sync = TimeSynchronizer(ntp_enabled=True)
        
        status = sync.get_sync_status()
        assert isinstance(status, TimeSyncStatus)
        assert status.ntp_enabled is True
        assert status.sync_count == 0
        assert status.clock_drift_ms == 0.0
        
    def test_callbacks(self):
        """Test callback registration"""
        sync = TimeSynchronizer()
        
        sync_callback = Mock()
        drift_callback = Mock()
        correction_callback = Mock()
        
        sync.set_sync_callback(sync_callback)
        sync.set_drift_alert_callback(drift_callback)
        sync.set_correction_callback(correction_callback)
        
        assert sync._on_sync_update == sync_callback
        assert sync._on_drift_alert == drift_callback
        assert sync._on_correction_applied == correction_callback
        
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping sync monitoring"""
        sync = TimeSynchronizer(ntp_enabled=False, sync_interval_minutes=0.01)
        
        # Start monitoring
        await sync.start_sync_monitoring()
        assert sync._sync_task is not None
        assert not sync._stop_requested
        
        # Brief delay to let monitoring start
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await sync.stop_sync_monitoring()
        assert sync._stop_requested
        
    @pytest.mark.asyncio
    async def test_force_sync_check_no_ntp(self):
        """Test force sync check without NTP"""
        sync = TimeSynchronizer(ntp_enabled=False)
        
        sync_callback = Mock()
        sync.set_sync_callback(sync_callback)
        
        await sync.force_sync_check()
        
        # Check that sync was performed
        status = sync.get_sync_status()
        assert status.sync_count == 1
        assert status.last_sync_time is not None
        
        # Check callback was called
        sync_callback.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_drift_detection_and_alert(self):
        """Test drift detection and alert system"""
        sync = TimeSynchronizer(
            ntp_enabled=False, 
            drift_threshold_ms=10.0,
            enable_correction=False  # Disable correction for this test
        )
        
        drift_callback = Mock()
        sync.set_drift_alert_callback(drift_callback)
        
        # Mock large drift to trigger alert
        with patch.object(sync, '_calculate_simulated_drift', return_value=15.0):
            await sync.force_sync_check()
            
        # Check alert was triggered
        drift_callback.assert_called_once_with(15.0)
        
    @pytest.mark.asyncio
    async def test_time_correction(self):
        """Test time correction functionality"""
        sync = TimeSynchronizer(
            ntp_enabled=False,
            drift_threshold_ms=10.0,
            enable_correction=True
        )
        
        correction_callback = Mock()
        sync.set_correction_callback(correction_callback)
        
        # Mock drift that exceeds threshold
        with patch.object(sync, '_calculate_simulated_drift', return_value=25.0):
            await sync.force_sync_check()
            
        # Check correction was applied
        correction_callback.assert_called()
        status = sync.get_sync_status()
        assert status.correction_applied_ms != 0.0
        
    def test_corrected_time(self):
        """Test corrected time calculation"""
        sync = TimeSynchronizer()
        
        # Apply some offset
        sync._system_time_offset = 0.1  # 100ms offset
        
        corrected_time = sync.get_corrected_time()
        current_time = datetime.now(timezone.utc)
        
        # Should be close to 100ms difference
        diff_ms = (corrected_time - current_time).total_seconds() * 1000
        assert 95 <= diff_ms <= 105  # Allow some tolerance for execution time
        
    def test_reset_corrections(self):
        """Test correction reset"""
        sync = TimeSynchronizer()
        
        correction_callback = Mock()
        sync.set_correction_callback(correction_callback)
        
        # Apply some offset
        sync._system_time_offset = 0.1
        sync.sync_status.correction_applied_ms = 100.0
        
        # Reset corrections
        sync.reset_corrections()
        
        assert sync._system_time_offset == 0.0
        assert sync.sync_status.correction_applied_ms == 0.0
        correction_callback.assert_called_with(0.0)
        
    def test_sync_quality_assessment(self):
        """Test sync quality assessment"""
        sync = TimeSynchronizer()
        
        # Test different drift levels
        assert sync._assess_sync_quality(2.0) == "excellent"
        assert sync._assess_sync_quality(7.0) == "good"
        assert sync._assess_sync_quality(15.0) == "fair"
        assert sync._assess_sync_quality(40.0) == "poor"
        assert sync._assess_sync_quality(100.0) == "critical"
        
    def test_overall_sync_quality_no_ntp(self):
        """Test overall sync quality without NTP"""
        sync = TimeSynchronizer(ntp_enabled=False)
        
        quality = sync._assess_overall_sync_quality(5.0, "unknown")
        assert quality == "good"  # Should use local quality only
        
    def test_overall_sync_quality_with_ntp(self):
        """Test overall sync quality with NTP"""
        sync = TimeSynchronizer(ntp_enabled=True)
        
        # Test combining good local and excellent NTP
        quality = sync._assess_overall_sync_quality(7.0, "excellent")
        assert quality in ["good", "excellent"]
        
    def test_sync_summary(self):
        """Test sync summary generation"""
        sync = TimeSynchronizer(
            drift_threshold_ms=20.0,
            sync_interval_minutes=5.0,
            ntp_enabled=True
        )
        
        summary = sync.get_sync_summary()
        
        assert summary["enabled"] is True
        assert summary["drift_threshold_ms"] == 20.0
        assert summary["sync_interval_minutes"] == 5.0
        assert summary["ntp_enabled"] is True
        assert "status" in summary
        assert "ntp_summary" in summary
        

class TestNTPClient:
    """Test cases for NTP client functionality"""
    
    def test_initialization_default(self):
        """Test NTP client initialization with defaults"""
        client = NTPClient()
        
        assert len(client.servers) == 4
        assert "pool.ntp.org" in client.servers
        assert client.timeout == 10.0
        assert client.max_retries == 3
        
    def test_initialization_custom(self):
        """Test NTP client initialization with custom settings"""
        servers = ["custom.ntp.server"]
        client = NTPClient(
            servers=servers,
            timeout=5.0,
            max_retries=2
        )
        
        assert client.servers == servers
        assert client.timeout == 5.0
        assert client.max_retries == 2
        
    @pytest.mark.asyncio
    async def test_sync_with_server_success(self):
        """Test successful NTP sync with server"""
        client = NTPClient()
        
        # Mock successful NTP response
        mock_response = Mock()
        mock_response.offset = 0.05  # 50ms offset
        mock_response.delay = 0.02   # 20ms delay
        mock_response.stratum = 2
        mock_response.precision = -20
        mock_response.root_delay = 0.001
        mock_response.root_dispersion = 0.002
        
        with patch.object(client.client, 'request', return_value=mock_response):
            result = await client.sync_with_server("test.ntp.server")
            
        assert result.success is True
        assert result.server == "test.ntp.server"
        assert result.offset == 0.05
        assert result.stratum == 2
        
    @pytest.mark.asyncio
    async def test_sync_with_server_failure(self):
        """Test failed NTP sync with server"""
        client = NTPClient(max_retries=1)
        
        # Mock connection failure
        with patch.object(client.client, 'request', side_effect=Exception("Connection failed")):
            result = await client.sync_with_server("invalid.ntp.server")
            
        assert result.success is False
        assert "invalid.ntp.server" in result.error_message
        
    @pytest.mark.asyncio
    async def test_sync_multiple_servers(self):
        """Test sync with multiple servers"""
        servers = ["server1.ntp", "server2.ntp"]
        client = NTPClient(servers=servers, max_retries=1)
        
        # Mock one success, one failure
        def mock_request(server, timeout):
            if server == "server1.ntp":
                response = Mock()
                response.offset = 0.01
                response.delay = 0.05
                response.stratum = 3
                response.precision = -18
                response.root_delay = 0.002
                response.root_dispersion = 0.003
                return response
            else:
                raise Exception("Server unreachable")
                
        with patch.object(client.client, 'request', side_effect=mock_request):
            results = await client.sync_with_multiple_servers()
            
        assert len(results) == 2
        assert results["server1.ntp"].success is True
        assert results["server2.ntp"].success is False
        
    def test_best_offset_calculation(self):
        """Test best offset calculation from results"""
        client = NTPClient()
        
        # Simulate sync results
        client._last_sync_results = [
            NTPSyncResult("server1", 0.05, 0.02, 2, datetime.now(timezone.utc), -20, 0.001, 0.002, True),
            NTPSyncResult("server2", 0.048, 0.025, 3, datetime.now(timezone.utc), -18, 0.003, 0.004, True),
            NTPSyncResult("server3", 0.052, 0.03, 2, datetime.now(timezone.utc), -19, 0.002, 0.003, True)
        ]
        
        best_offset = client.get_best_offset()
        assert best_offset is not None
        assert 0.045 <= best_offset <= 0.055  # Should be median around 0.05
        
    def test_sync_quality_assessment(self):
        """Test NTP sync quality assessment"""
        client = NTPClient(servers=["s1", "s2", "s3", "s4"])
        
        # High quality: all servers successful, low variance
        client._last_sync_results = [
            NTPSyncResult("s1", 0.01, 0.05, 2, datetime.now(timezone.utc), -20, 0.001, 0.002, True),
            NTPSyncResult("s2", 0.012, 0.06, 2, datetime.now(timezone.utc), -20, 0.001, 0.002, True),
            NTPSyncResult("s3", 0.011, 0.055, 2, datetime.now(timezone.utc), -20, 0.001, 0.002, True),
        ]
        
        quality = client.get_sync_quality()
        assert quality in ["good", "excellent"]
        
    def test_sync_summary(self):
        """Test sync summary generation"""
        client = NTPClient(servers=["s1", "s2"])
        
        # Add some results
        client._last_sync_results = [
            NTPSyncResult("s1", 0.02, 0.05, 2, datetime.now(timezone.utc), -20, 0.001, 0.002, True),
        ]
        
        summary = client.get_sync_summary()
        
        assert summary["servers_configured"] == 2
        assert summary["servers_successful"] == 1
        assert summary["best_offset_ms"] == 20.0  # 0.02 * 1000
        assert "sync_quality" in summary
        assert "last_sync_time" in summary


@pytest.mark.integration
class TestIntegration:
    """Integration tests for complete time sync system"""
    
    @pytest.mark.asyncio
    async def test_full_sync_cycle_with_ntp(self):
        """Test complete sync cycle with NTP enabled"""
        # Use shorter intervals for testing
        sync = TimeSynchronizer(
            sync_interval_minutes=0.01,  # 0.6 seconds
            drift_threshold_ms=15.0,
            ntp_enabled=True,
            ntp_servers=["pool.ntp.org"]  # Use only one server for faster testing
        )
        
        sync_updates = []
        drift_alerts = []
        corrections = []
        
        def on_sync_update(status):
            sync_updates.append(status.to_dict())
            
        def on_drift_alert(drift):
            drift_alerts.append(drift)
            
        def on_correction_applied(correction):
            corrections.append(correction)
            
        sync.set_sync_callback(on_sync_update)
        sync.set_drift_alert_callback(on_drift_alert)
        sync.set_correction_callback(on_correction_applied)
        
        try:
            # Start monitoring
            await sync.start_sync_monitoring()
            
            # Let it run for a short time
            await asyncio.sleep(2.0)
            
            # Force a sync to ensure we get at least one
            await sync.force_sync_check()
            
        finally:
            # Stop monitoring
            await sync.stop_sync_monitoring()
            
        # Verify we got sync updates
        assert len(sync_updates) > 0
        
        # Check sync status
        status = sync.get_sync_status()
        assert status.sync_count > 0
        assert status.last_sync_time is not None
        
        # Get summary
        summary = sync.get_sync_summary()
        assert summary["enabled"] is True
        assert summary["ntp_enabled"] is True
        

if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])