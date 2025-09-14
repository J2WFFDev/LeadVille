"""Simple tests for WebSocket integration functionality."""

import pytest
from unittest.mock import AsyncMock, patch

from src.impact_bridge.websocket_integration import TimerWebSocketServer, TimerWebSocketIntegration


class TestTimerWebSocketServer:
    """Test TimerWebSocketServer functionality."""
    
    def test_websocket_server_creation(self):
        """Test WebSocket server can be created."""
        server = TimerWebSocketServer(enabled=True)
        
        assert server.enabled is True
        assert server.host == "localhost"
        assert server.port == 8765
        assert server.get_client_count() == 0
        assert server.is_running() is False

    def test_websocket_server_disabled(self):
        """Test WebSocket server when disabled."""
        server = TimerWebSocketServer(enabled=False)
        
        assert server.enabled is False
        assert server.get_client_count() == 0
        assert server.is_running() is False

    def test_websocket_server_methods_exist(self):
        """Test that all required methods exist on WebSocket server."""
        server = TimerWebSocketServer(enabled=True)
        
        # Check that new event broadcasting methods exist
        assert hasattr(server, 'broadcast_timer_event')
        assert hasattr(server, 'broadcast_health_status')
        assert hasattr(server, 'broadcast_session_update')
        assert hasattr(server, 'broadcast_sensor_event')
        assert hasattr(server, 'broadcast_status_update')
        assert hasattr(server, 'broadcast_run_update')
        
        # Check utility methods
        assert hasattr(server, 'get_client_count')
        assert hasattr(server, 'is_running')


class TestTimerWebSocketIntegration:
    """Test TimerWebSocketIntegration functionality."""
    
    def test_websocket_integration_creation(self):
        """Test WebSocket integration can be created."""
        server = TimerWebSocketServer(enabled=True)
        integration = TimerWebSocketIntegration(server)
        
        assert integration.websocket_server == server

    def test_websocket_integration_methods_exist(self):
        """Test that all required integration methods exist."""
        server = TimerWebSocketServer(enabled=True)
        integration = TimerWebSocketIntegration(server)
        
        # Check existing methods
        assert hasattr(integration, 'handle_amg_event')
        assert hasattr(integration, 'handle_health_update')
        assert hasattr(integration, 'handle_session_update')
        
        # Check new methods for required event types
        assert hasattr(integration, 'handle_sensor_event')
        assert hasattr(integration, 'handle_status_update')
        assert hasattr(integration, 'handle_run_update')

    @pytest.mark.asyncio
    async def test_handle_sensor_event(self):
        """Test handling sensor events."""
        server = TimerWebSocketServer(enabled=True)
        integration = TimerWebSocketIntegration(server)
        
        # Mock the server's broadcast method
        with patch.object(server, 'broadcast_sensor_event', new_callable=AsyncMock) as mock_broadcast:
            sensor_data = {
                "sensor_id": "BT50_01",
                "magnitude": 15.5,
                "event_type": "impact_detected"
            }
            
            await integration.handle_sensor_event(sensor_data)
            
            # Verify the broadcast method was called with the data
            mock_broadcast.assert_called_once_with(sensor_data)

    @pytest.mark.asyncio
    async def test_handle_status_update(self):
        """Test handling status updates."""
        server = TimerWebSocketServer(enabled=True)
        integration = TimerWebSocketIntegration(server)
        
        with patch.object(server, 'broadcast_status_update', new_callable=AsyncMock) as mock_broadcast:
            status_data = {
                "system_status": "operational",
                "connected_devices": 2
            }
            
            await integration.handle_status_update(status_data)
            
            mock_broadcast.assert_called_once_with(status_data)

    @pytest.mark.asyncio
    async def test_handle_run_update(self):
        """Test handling run updates."""
        server = TimerWebSocketServer(enabled=True)
        integration = TimerWebSocketIntegration(server)
        
        with patch.object(server, 'broadcast_run_update', new_callable=AsyncMock) as mock_broadcast:
            run_data = {
                "run_id": "run_123",
                "event_type": "run_started",
                "shooter_name": "John Doe"
            }
            
            await integration.handle_run_update(run_data)
            
            mock_broadcast.assert_called_once_with(run_data)


class TestWebSocketBroadcastMethods:
    """Test WebSocket broadcast methods."""
    
    @pytest.mark.asyncio
    async def test_broadcast_sensor_event_disabled_server(self):
        """Test broadcasting when server is disabled."""
        server = TimerWebSocketServer(enabled=False)
        
        # Should not raise error when server is disabled
        sensor_data = {"sensor_id": "BT50_01", "magnitude": 15.5}
        await server.broadcast_sensor_event(sensor_data)

    @pytest.mark.asyncio
    async def test_broadcast_status_update_disabled_server(self):
        """Test broadcasting status when server is disabled."""
        server = TimerWebSocketServer(enabled=False)
        
        # Should not raise error when server is disabled
        status_data = {"system_status": "operational"}
        await server.broadcast_status_update(status_data)

    @pytest.mark.asyncio
    async def test_broadcast_run_update_disabled_server(self):
        """Test broadcasting run update when server is disabled."""
        server = TimerWebSocketServer(enabled=False)
        
        # Should not raise error when server is disabled
        run_data = {"run_id": "run_123", "event_type": "run_started"}
        await server.broadcast_run_update(run_data)

    @pytest.mark.asyncio
    async def test_broadcast_no_clients(self):
        """Test broadcasting when no clients are connected."""
        server = TimerWebSocketServer(enabled=True)
        
        # Should not raise error when no clients are connected
        sensor_data = {"sensor_id": "BT50_01", "magnitude": 15.5}
        await server.broadcast_sensor_event(sensor_data)
        
        status_data = {"system_status": "operational"}
        await server.broadcast_status_update(status_data)
        
        run_data = {"run_id": "run_123", "event_type": "run_started"}
        await server.broadcast_run_update(run_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])