"""MQTT topic structure definitions for LeadVille Impact Bridge."""

from typing import Dict, List


class MqttTopics:
    """Centralized MQTT topic definitions and management."""
    
    # Base topic prefix
    BASE = "leadville"
    
    # System status topics
    BRIDGE_STATUS = f"{BASE}/bridge/status"
    SYSTEM_HEALTH = f"{BASE}/system/health"
    
    # Sensor telemetry topics (template with {sensor_id})
    SENSOR_TELEMETRY = f"{BASE}/sensor/{{sensor_id}}/telemetry"
    SENSOR_STATUS = f"{BASE}/sensor/{{sensor_id}}/status"
    
    # Timer event topics  
    TIMER_EVENTS = f"{BASE}/timer/events"
    TIMER_STATUS = f"{BASE}/timer/status"
    
    # Run-specific event topics (template with {run_id})
    RUN_EVENTS = f"{BASE}/run/{{run_id}}/events"
    RUN_STATUS = f"{BASE}/run/{{run_id}}/status"
    
    # Detection events
    IMPACT_EVENTS = f"{BASE}/detection/impacts"
    SHOT_EVENTS = f"{BASE}/detection/shots"
    
    @classmethod
    def sensor_telemetry(cls, sensor_id: str) -> str:
        """Get sensor telemetry topic for specific sensor."""
        return cls.SENSOR_TELEMETRY.format(sensor_id=sensor_id)
    
    @classmethod
    def sensor_status(cls, sensor_id: str) -> str:
        """Get sensor status topic for specific sensor."""
        return cls.SENSOR_STATUS.format(sensor_id=sensor_id)
    
    @classmethod
    def run_events(cls, run_id: str) -> str:
        """Get run events topic for specific run."""
        return cls.RUN_EVENTS.format(run_id=run_id)
    
    @classmethod
    def run_status(cls, run_id: str) -> str:
        """Get run status topic for specific run."""
        return cls.RUN_STATUS.format(run_id=run_id)
    
    @classmethod
    def get_all_topics(cls) -> List[str]:
        """Get list of all static topics (excluding templates)."""
        return [
            cls.BRIDGE_STATUS,
            cls.SYSTEM_HEALTH,
            cls.TIMER_EVENTS,
            cls.TIMER_STATUS,
            cls.IMPACT_EVENTS,
            cls.SHOT_EVENTS,
        ]
    
    @classmethod
    def get_topic_info(cls) -> Dict[str, str]:
        """Get topic information for documentation."""
        return {
            cls.BRIDGE_STATUS: "Bridge system status updates (connection states, detector status)",
            cls.SYSTEM_HEALTH: "System health metrics and monitoring data",
            cls.SENSOR_TELEMETRY.replace("{sensor_id}", "ID"): "Real-time sensor telemetry data (acceleration, battery)",
            cls.SENSOR_STATUS.replace("{sensor_id}", "ID"): "Sensor connection and calibration status",
            cls.TIMER_EVENTS: "Timer events (T0, shot detection, stop signals)",
            cls.TIMER_STATUS: "Timer connection and operational status",
            cls.RUN_EVENTS.replace("{run_id}", "ID"): "Run-specific events (start, impacts, end)",
            cls.RUN_STATUS.replace("{run_id}", "ID"): "Run status and progress tracking",
            cls.IMPACT_EVENTS: "Impact detection events with timing correlation",
            cls.SHOT_EVENTS: "Shot detection events from timer system",
        }