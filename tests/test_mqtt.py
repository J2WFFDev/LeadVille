"""Tests for MQTT functionality."""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.impact_bridge.mqtt import MqttClient, MqttTopics


class TestMqttTopics:
    """Test MQTT topic management."""
    
    def test_topic_structure(self):
        """Test topic structure and formatting."""
        assert MqttTopics.BASE == "leadville"
        assert MqttTopics.BRIDGE_STATUS == "leadville/bridge/status"
        assert MqttTopics.SENSOR_TELEMETRY == "leadville/sensor/{sensor_id}/telemetry"
    
    def test_sensor_topic_formatting(self):
        """Test sensor topic formatting."""
        sensor_id = "BT50_01"
        telemetry_topic = MqttTopics.sensor_telemetry(sensor_id)
        status_topic = MqttTopics.sensor_status(sensor_id)
        
        assert telemetry_topic == "leadville/sensor/BT50_01/telemetry"
        assert status_topic == "leadville/sensor/BT50_01/status"
    
    def test_run_topic_formatting(self):
        """Test run topic formatting."""
        run_id = "RUN_001"
        events_topic = MqttTopics.run_events(run_id)
        status_topic = MqttTopics.run_status(run_id)
        
        assert events_topic == "leadville/run/RUN_001/events"
        assert status_topic == "leadville/run/RUN_001/status"
    
    def test_get_all_topics(self):
        """Test getting all static topics."""
        topics = MqttTopics.get_all_topics()
        
        assert "leadville/bridge/status" in topics
        assert "leadville/timer/events" in topics
        assert "leadville/detection/impacts" in topics
        assert len(topics) == 6
    
    def test_get_topic_info(self):
        """Test topic information retrieval."""
        topic_info = MqttTopics.get_topic_info()
        
        assert isinstance(topic_info, dict)
        assert "leadville/bridge/status" in topic_info
        assert "Bridge system status" in topic_info["leadville/bridge/status"]


class TestMqttClient:
    """Test MQTT client functionality."""
    
    def test_init_defaults(self):
        """Test client initialization with defaults."""
        client = MqttClient()
        
        assert client.broker_host == "localhost"
        assert client.broker_port == 1883
        assert client.enabled is True
        assert client.is_connected is False
    
    def test_init_custom_config(self):
        """Test client initialization with custom configuration."""
        client = MqttClient(
            broker_host="test.broker.com",
            broker_port=8883,
            username="testuser",
            password="testpass",
            enabled=False,
        )
        
        assert client.broker_host == "test.broker.com"
        assert client.broker_port == 8883
        assert client.username == "testuser"
        assert client.password == "testpass"
        assert client.enabled is False
    
    def test_stats_property(self):
        """Test statistics property."""
        client = MqttClient(client_id="test_client")
        stats = client.stats
        
        assert isinstance(stats, dict)
        assert stats["connected"] is False
        assert stats["enabled"] is True
        assert stats["messages_published"] == 0
        assert stats["client_id"] == "test_client"
    
    @pytest.mark.asyncio
    async def test_start_disabled(self):
        """Test starting disabled client."""
        client = MqttClient(enabled=False)
        await client.start()
        
        assert not client.is_connected
        assert client._connection_task is None
    
    @pytest.mark.asyncio
    async def test_publish_disabled(self):
        """Test publishing when disabled."""
        client = MqttClient(enabled=False)
        
        result = await client.publish("test/topic", {"test": "data"})
        
        assert result is False
        assert client.stats["messages_failed"] == 0  # Not counted as failed when disabled
    
    @pytest.mark.asyncio
    async def test_publish_not_connected(self):
        """Test publishing when not connected."""
        client = MqttClient(enabled=True)
        
        result = await client.publish("test/topic", {"test": "data"})
        
        assert result is False
        assert client.stats["messages_failed"] == 1
    
    @pytest.mark.asyncio
    @patch('src.impact_bridge.mqtt.client.AioMqttClient')
    async def test_publish_success(self, mock_client_class):
        """Test successful message publishing."""
        # Mock the async context manager
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        client = MqttClient(enabled=True)
        client._connected = True
        client._client = mock_client
        
        # Test dict payload
        result = await client.publish("test/topic", {"test": "data", "value": 123})
        
        assert result is True
        assert client.stats["messages_published"] == 1
        
        # Verify the publish call
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        
        # Check topic
        assert call_args[0][0] == "test/topic"
        
        # Check payload is JSON with timestamp
        payload = json.loads(call_args[0][1])
        assert payload["test"] == "data"
        assert payload["value"] == 123
        assert "timestamp" in payload
    
    @pytest.mark.asyncio
    @patch('src.impact_bridge.mqtt.client.AioMqttClient')
    async def test_publish_string_payload(self, mock_client_class):
        """Test publishing string payload."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        client = MqttClient(enabled=True)
        client._connected = True
        client._client = mock_client
        
        result = await client.publish("test/topic", "simple string message")
        
        assert result is True
        mock_client.publish.assert_called_once_with(
            "test/topic", "simple string message", qos=1, retain=False
        )
    
    @pytest.mark.asyncio
    @patch('src.impact_bridge.mqtt.client.AioMqttClient')
    async def test_publish_status(self, mock_client_class):
        """Test status message publishing."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        client = MqttClient(enabled=True)
        client._connected = True
        client._client = mock_client
        
        result = await client.publish_status("bridge", {"connected": True})
        
        assert result is True
        mock_client.publish.assert_called_once()
        
        # Check the call arguments
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == "leadville/bridge/status"  # Correct topic
        assert call_args[1]["retain"] is True  # Status messages should be retained
        
        # Check payload content
        payload = json.loads(call_args[0][1])
        assert payload["component"] == "bridge"
        assert payload["status"]["connected"] is True
        assert "client_stats" in payload
    
    @pytest.mark.asyncio
    @patch('src.impact_bridge.mqtt.client.AioMqttClient')
    async def test_publish_event(self, mock_client_class):
        """Test event message publishing."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        client = MqttClient(enabled=True)
        client._connected = True
        client._client = mock_client
        
        event_data = {
            "amplitude": 150.5,
            "timestamp_ns": 1234567890000,
        }
        
        result = await client.publish_event("HIT", event_data, sensor_id="BT50_01")
        
        assert result is True
        mock_client.publish.assert_called_once()
        
        # Check the call arguments
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == "leadville/detection/impacts"  # HIT events go to impacts topic
        
        # Check payload content
        payload = json.loads(call_args[0][1])
        assert payload["event_type"] == "HIT"
        assert payload["data"]["amplitude"] == 150.5
        assert payload["sensor_id"] == "BT50_01"
    
    @pytest.mark.asyncio
    @patch('src.impact_bridge.mqtt.client.AioMqttClient')
    async def test_publish_telemetry(self, mock_client_class):
        """Test telemetry message publishing."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None
        
        client = MqttClient(enabled=True)
        client._connected = True
        client._client = mock_client
        
        telemetry_data = {
            "acceleration": {"x": 1.2, "y": -0.5, "z": 9.8},
            "battery": 85,
            "temperature": 23.5,
        }
        
        result = await client.publish_telemetry("BT50_01", telemetry_data)
        
        assert result is True
        mock_client.publish.assert_called_once()
        
        # Check the call arguments
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == "leadville/sensor/BT50_01/telemetry"
        
        # Check payload content
        payload = json.loads(call_args[0][1])
        assert payload["sensor_id"] == "BT50_01"
        assert payload["telemetry"]["battery"] == 85
    
    @pytest.mark.asyncio
    async def test_stop(self):
        """Test client stop functionality."""
        client = MqttClient()
        
        # Create a real task that we can cancel
        async def dummy_task():
            await asyncio.sleep(10)  # This will be cancelled
        
        client._connection_task = asyncio.create_task(dummy_task())
        client._client = AsyncMock()
        
        await client.stop()
        
        assert client._stop_requested is True
        assert client._connection_task.cancelled()
        assert client._connected is False