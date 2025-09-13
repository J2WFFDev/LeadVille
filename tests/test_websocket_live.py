"""Tests for WebSocket live updates functionality."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.impact_bridge.api.main import create_app
from src.impact_bridge.api.websocket import manager, broadcast_status_update, broadcast_sensor_event, broadcast_timer_event, broadcast_run_update


@pytest.fixture
def app():
    """Create test FastAPI app."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestWebSocketLiveEndpoint:
    """Test WebSocket /ws/live endpoint."""
    
    def test_websocket_test_page_available(self, client):
        """Test that WebSocket test page is accessible."""
        response = client.get("/ws/test")
        assert response.status_code == 200
        assert "LeadVille WebSocket Test" in response.text
        assert "ws/live" in response.text

    @pytest.mark.asyncio
    async def test_websocket_connection(self, app):
        """Test WebSocket connection establishment."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws/live") as websocket:
                # Should receive welcome message
                data = websocket.receive_text()
                message = json.loads(data)
                
                assert message["type"] == "status"
                assert message["event_type"] == "connection_established"
                assert "Connected to LeadVille Live Updates" in message["message"]
                assert "capabilities" in message
                
                # Check capabilities include all required event types
                capabilities = message["capabilities"]
                required_types = ["status", "sensor_event", "timer_event", "run_update"]
                for event_type in required_types:
                    assert event_type in capabilities

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, app):
        """Test WebSocket ping/pong functionality."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws/live") as websocket:
                # Skip welcome message
                welcome_data = websocket.receive_text()
                
                # Send ping
                ping_msg = {"type": "ping"}
                websocket.send_text(json.dumps(ping_msg))
                
                # Receive pong
                pong_data = websocket.receive_text()
                pong_message = json.loads(pong_data)
                
                assert pong_message["type"] == "status"
                assert pong_message["event_type"] == "pong"
                assert "timestamp" in pong_message

    @pytest.mark.asyncio  
    async def test_websocket_subscription(self, app):
        """Test WebSocket subscription functionality."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws/live") as websocket:
                # Skip welcome message
                welcome_data = websocket.receive_text()
                
                # Send subscription request
                subscribe_msg = {
                    "type": "subscribe",
                    "channels": ["timer_events", "sensor_events", "status"]
                }
                websocket.send_text(json.dumps(subscribe_msg))
                
                # Receive subscription confirmation
                sub_data = websocket.receive_text()
                sub_message = json.loads(sub_data)
                
                assert sub_message["type"] == "status"
                assert sub_message["event_type"] == "subscription_confirmed"
                assert sub_message["channels"] == ["timer_events", "sensor_events", "status"]
                assert "Subscribed to 3 channels" in sub_message["message"]

    @pytest.mark.asyncio
    async def test_websocket_invalid_message(self, app):
        """Test WebSocket handling of invalid messages."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws/live") as websocket:
                # Skip welcome message
                welcome_data = websocket.receive_text()
                
                # Send invalid JSON
                websocket.send_text("invalid json")
                
                # Receive error response
                error_data = websocket.receive_text()
                error_message = json.loads(error_data)
                
                assert error_message["type"] == "status"
                assert error_message["event_type"] == "error"
                assert "Invalid JSON format" in error_message["message"]

    @pytest.mark.asyncio
    async def test_websocket_unknown_message_type(self, app):
        """Test WebSocket handling of unknown message types."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws/live") as websocket:
                # Skip welcome message
                welcome_data = websocket.receive_text()
                
                # Send unknown message type
                unknown_msg = {"type": "unknown_type", "data": "test"}
                websocket.send_text(json.dumps(unknown_msg))
                
                # Receive error response
                error_data = websocket.receive_text()
                error_message = json.loads(error_data)
                
                assert error_message["type"] == "status"
                assert error_message["event_type"] == "error"
                assert "Unknown message type: unknown_type" in error_message["message"]


class TestWebSocketBroadcasting:
    """Test WebSocket broadcasting functionality."""
    
    @pytest.mark.asyncio
    async def test_broadcast_status_update(self):
        """Test broadcasting status updates."""
        # Mock the manager
        with patch.object(manager, 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            status_data = {
                "system_status": "operational",
                "connected_devices": 2,
                "active_sessions": 1
            }
            
            await broadcast_status_update(status_data)
            
            # Verify broadcast was called with correct message structure
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            
            assert call_args["type"] == "status"
            assert call_args["event_type"] == "system_status_update"
            assert call_args["data"] == status_data
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_sensor_event(self):
        """Test broadcasting sensor events."""
        with patch.object(manager, 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            sensor_data = {
                "event_type": "impact_detected",
                "sensor_id": "BT50_01",
                "magnitude": 15.5,
                "timestamp_sensor": "2023-09-13T18:30:45.123Z"
            }
            
            await broadcast_sensor_event(sensor_data)
            
            # Verify broadcast was called with correct message structure
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            
            assert call_args["type"] == "sensor_event"
            assert call_args["event_type"] == "impact_detected"
            assert call_args["sensor_id"] == "BT50_01"
            assert call_args["data"] == sensor_data
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_timer_event(self):
        """Test broadcasting timer events."""
        with patch.object(manager, 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            timer_data = {
                "event_type": "shot_detected",
                "shot_number": 3,
                "current_time": 15.67,
                "shot_state": "ACTIVE"
            }
            
            await broadcast_timer_event(timer_data)
            
            # Verify broadcast was called with correct message structure
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            
            assert call_args["type"] == "timer_event"
            assert call_args["event_type"] == "shot_detected"
            assert call_args["device_id"] == "60:09:C3:1F:DC:1A"
            assert call_args["data"] == timer_data
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_broadcast_run_update(self):
        """Test broadcasting run updates."""
        with patch.object(manager, 'broadcast', new_callable=AsyncMock) as mock_broadcast:
            run_data = {
                "event_type": "run_started",
                "run_id": "run_123",
                "shooter_name": "John Doe",
                "stage_name": "Stage 1"
            }
            
            await broadcast_run_update(run_data)
            
            # Verify broadcast was called with correct message structure
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args[0][0]
            
            assert call_args["type"] == "run_update"
            assert call_args["event_type"] == "run_started"
            assert call_args["run_id"] == "run_123"
            assert call_args["data"] == run_data
            assert "timestamp" in call_args


class TestWebSocketIntegration:
    """Test WebSocket integration with existing systems."""

    @pytest.mark.asyncio
    async def test_multiple_client_connections(self, app):
        """Test handling multiple WebSocket client connections."""
        with TestClient(app) as client:
            # Connect first client
            with client.websocket_connect("/ws/live") as websocket1:
                # Skip welcome message
                welcome1 = websocket1.receive_text()
                
                # Connect second client
                with client.websocket_connect("/ws/live") as websocket2:
                    # Skip welcome message
                    welcome2 = websocket2.receive_text()
                    
                    # Both should receive welcome messages
                    msg1 = json.loads(welcome1)
                    msg2 = json.loads(welcome2)
                    
                    assert msg1["type"] == "status"
                    assert msg2["type"] == "status"
                    assert "Connected to LeadVille Live Updates" in msg1["message"]
                    assert "Connected to LeadVille Live Updates" in msg2["message"]

    def test_websocket_integration_with_existing_server(self):
        """Test that WebSocket integration works with existing TimerWebSocketServer."""
        from src.impact_bridge.websocket_integration import TimerWebSocketServer, TimerWebSocketIntegration
        
        # Create server and integration
        server = TimerWebSocketServer(enabled=True)
        integration = TimerWebSocketIntegration(server)
        
        # Verify integration methods exist
        assert hasattr(integration, 'handle_sensor_event')
        assert hasattr(integration, 'handle_status_update')
        assert hasattr(integration, 'handle_run_update')
        
        # Verify server methods exist
        assert hasattr(server, 'broadcast_sensor_event')
        assert hasattr(server, 'broadcast_status_update')
        assert hasattr(server, 'broadcast_run_update')
        assert hasattr(server, 'get_client_count')
        assert hasattr(server, 'is_running')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])