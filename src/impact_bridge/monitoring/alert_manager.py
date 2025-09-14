"""Alert management and notification system for system health monitoring."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum

from .health_aggregator import HealthStatus, AggregatedHealth, ComponentHealth

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels."""
    LOG = "log"
    MQTT = "mqtt"
    EMAIL = "email"
    WEBHOOK = "webhook"
    CONSOLE = "console"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    component: str
    condition: str  # Description of the condition
    severity: AlertSeverity
    threshold_value: Optional[float] = None
    cooldown_minutes: int = 5  # Minimum time between same alerts
    channels: List[AlertChannel] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = [AlertChannel.LOG]


@dataclass
class Alert:
    """Active alert instance."""
    rule_name: str
    component: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_timestamp:
            data['resolved_timestamp'] = self.resolved_timestamp.isoformat()
        return data


class AlertManager:
    """Manages alerts, notifications, and alerting rules."""
    
    def __init__(
        self,
        enable_mqtt_alerts: bool = False,
        enable_email_alerts: bool = False,
        enable_webhook_alerts: bool = False,
        mqtt_topic_prefix: str = "leadville/alerts",
        webhook_url: Optional[str] = None,
        email_config: Optional[Dict[str, Any]] = None
    ):
        self.enable_mqtt_alerts = enable_mqtt_alerts
        self.enable_email_alerts = enable_email_alerts
        self.enable_webhook_alerts = enable_webhook_alerts
        self.mqtt_topic_prefix = mqtt_topic_prefix
        self.webhook_url = webhook_url
        self.email_config = email_config or {}
        
        # Alert rules
        self.alert_rules: Dict[str, AlertRule] = {}
        
        # Active alerts tracking
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Notification handlers
        self.notification_handlers: Dict[AlertChannel, Callable] = {
            AlertChannel.LOG: self._send_log_alert,
            AlertChannel.CONSOLE: self._send_console_alert,
        }
        
        # Setup default alert rules
        self._setup_default_rules()
        
        # Optional external handlers (will be set up if services are available)
        if self.enable_mqtt_alerts:
            self.notification_handlers[AlertChannel.MQTT] = self._send_mqtt_alert
        if self.enable_email_alerts:
            self.notification_handlers[AlertChannel.EMAIL] = self._send_email_alert
        if self.enable_webhook_alerts:
            self.notification_handlers[AlertChannel.WEBHOOK] = self._send_webhook_alert
    
    def _setup_default_rules(self):
        """Setup default alerting rules."""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                component="system_resources",
                condition="CPU usage > 85%",
                severity=AlertSeverity.WARNING,
                threshold_value=85.0,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE]
            ),
            AlertRule(
                name="critical_cpu_usage", 
                component="system_resources",
                condition="CPU usage > 95%",
                severity=AlertSeverity.CRITICAL,
                threshold_value=95.0,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE, AlertChannel.MQTT]
            ),
            AlertRule(
                name="high_memory_usage",
                component="system_resources",
                condition="Memory usage > 90%",
                severity=AlertSeverity.WARNING,
                threshold_value=90.0,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE]
            ),
            AlertRule(
                name="critical_memory_usage",
                component="system_resources", 
                condition="Memory usage > 95%",
                severity=AlertSeverity.CRITICAL,
                threshold_value=95.0,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE, AlertChannel.MQTT]
            ),
            AlertRule(
                name="low_disk_space",
                component="disk_space",
                condition="Disk space > 80% full",
                severity=AlertSeverity.WARNING,
                threshold_value=80.0,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE]
            ),
            AlertRule(
                name="critical_disk_space",
                component="disk_space",
                condition="Disk space > 90% full", 
                severity=AlertSeverity.CRITICAL,
                threshold_value=90.0,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE, AlertChannel.MQTT]
            ),
            AlertRule(
                name="ble_service_down",
                component="ble_services",
                condition="BLE services unhealthy",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE, AlertChannel.MQTT]
            ),
            AlertRule(
                name="mqtt_broker_down",
                component="mqtt_broker",
                condition="MQTT broker disconnected",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE]
            ),
            AlertRule(
                name="database_down", 
                component="database",
                condition="Database connection failed",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE, AlertChannel.MQTT]
            ),
            AlertRule(
                name="network_disconnected",
                component="network_connectivity",
                condition="Network connectivity lost",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE]
            ),
            AlertRule(
                name="ntp_sync_failed",
                component="ntp_sync",
                condition="NTP synchronization failed",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG, AlertChannel.CONSOLE]
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule."""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule."""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    async def process_health_status(self, health_status: AggregatedHealth):
        """Process health status and trigger alerts based on rules."""
        try:
            # Check each component against alert rules
            component_status = {comp.name: comp for comp in health_status.components}
            
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                component = component_status.get(rule.component)
                if not component:
                    continue
                
                # Check if alert should be triggered
                should_alert = await self._evaluate_alert_rule(rule, component, health_status)
                
                if should_alert:
                    await self._trigger_alert(rule, component, health_status)
                else:
                    # Check if we should resolve an existing alert
                    await self._check_alert_resolution(rule, component)
            
        except Exception as e:
            logger.error(f"Error processing health status for alerts: {e}")
    
    async def _evaluate_alert_rule(
        self, 
        rule: AlertRule, 
        component: ComponentHealth, 
        health_status: AggregatedHealth
    ) -> bool:
        """Evaluate if an alert rule condition is met."""
        # Skip if we're in cooldown period
        if self._is_in_cooldown(rule.name):
            return False
        
        # General status-based rules
        if rule.name.endswith("_down") or rule.name.endswith("_failed"):
            return component.status == HealthStatus.CRITICAL
        
        # Specific threshold-based rules
        if rule.component == "system_resources" and health_status.system_metrics:
            metrics = health_status.system_metrics
            
            if "cpu" in rule.name and rule.threshold_value:
                return metrics.cpu_percent >= rule.threshold_value
            elif "memory" in rule.name and rule.threshold_value:
                return metrics.memory_percent >= rule.threshold_value
        
        elif rule.component == "disk_space" and rule.threshold_value:
            # Check if any monitored disk exceeds threshold
            if component.metadata and 'monitored_paths' in component.metadata:
                for disk_info in component.metadata['monitored_paths']:
                    if disk_info.get('percent_used', 0) >= rule.threshold_value:
                        return True
        
        # Default to component status evaluation
        if rule.severity == AlertSeverity.CRITICAL:
            return component.status == HealthStatus.CRITICAL
        elif rule.severity == AlertSeverity.WARNING:
            return component.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]
        
        return False
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Check if alert rule is in cooldown period."""
        if rule_name not in self.last_alert_times:
            return False
        
        rule = self.alert_rules.get(rule_name)
        if not rule:
            return False
        
        last_alert = self.last_alert_times[rule_name]
        cooldown_period = timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.now() - last_alert < cooldown_period
    
    async def _trigger_alert(
        self, 
        rule: AlertRule, 
        component: ComponentHealth, 
        health_status: AggregatedHealth
    ):
        """Trigger an alert for the given rule."""
        alert_id = f"{rule.name}_{component.name}"
        
        # Skip if alert is already active
        if alert_id in self.active_alerts:
            return
        
        # Create alert message
        message = self._generate_alert_message(rule, component, health_status)
        
        # Create alert
        alert = Alert(
            rule_name=rule.name,
            component=component.name,
            severity=rule.severity,
            message=message,
            timestamp=datetime.now(),
            metadata={
                'component_status': component.status.value,
                'response_time_ms': component.response_time_ms,
                'rule_condition': rule.condition
            }
        )
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_times[rule.name] = alert.timestamp
        
        # Send notifications
        await self._send_alert_notifications(alert, rule)
        
        logger.warning(f"Alert triggered: {rule.name} - {message}")
    
    def _generate_alert_message(
        self, 
        rule: AlertRule, 
        component: ComponentHealth, 
        health_status: AggregatedHealth
    ) -> str:
        """Generate a descriptive alert message."""
        base_message = f"{rule.condition} for {component.name}"
        
        # Add specific details based on component
        if component.name == "system_resources" and health_status.system_metrics:
            metrics = health_status.system_metrics
            if "cpu" in rule.name:
                base_message += f" (Current: {metrics.cpu_percent}%)"
            elif "memory" in rule.name:
                base_message += f" (Current: {metrics.memory_percent}%)"
        
        elif component.name == "disk_space" and component.metadata:
            if 'monitored_paths' in component.metadata:
                critical_disks = [
                    disk for disk in component.metadata['monitored_paths']
                    if disk.get('percent_used', 0) >= (rule.threshold_value or 80)
                ]
                if critical_disks:
                    disk_details = ", ".join([
                        f"{disk['path']}: {disk['percent_used']}%"
                        for disk in critical_disks
                    ])
                    base_message += f" ({disk_details})"
        
        # Add component message if available
        if component.message:
            base_message += f" - {component.message}"
        
        return base_message
    
    async def _check_alert_resolution(self, rule: AlertRule, component: ComponentHealth):
        """Check if an active alert should be resolved."""
        alert_id = f"{rule.name}_{component.name}"
        
        if alert_id not in self.active_alerts:
            return
        
        alert = self.active_alerts[alert_id]
        
        # Check if condition is resolved
        is_resolved = False
        
        if rule.severity == AlertSeverity.CRITICAL:
            is_resolved = component.status != HealthStatus.CRITICAL
        elif rule.severity == AlertSeverity.WARNING:
            is_resolved = component.status == HealthStatus.HEALTHY
        
        if is_resolved:
            # Mark alert as resolved
            alert.resolved = True
            alert.resolved_timestamp = datetime.now()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            # Send resolution notification
            resolution_message = f"RESOLVED: {alert.message}"
            await self._send_resolution_notification(alert, rule, resolution_message)
            
            logger.info(f"Alert resolved: {rule.name} - {component.name}")
    
    async def _send_alert_notifications(self, alert: Alert, rule: AlertRule):
        """Send alert notifications through configured channels."""
        for channel in rule.channels:
            if channel in self.notification_handlers:
                try:
                    await self.notification_handlers[channel](alert, is_resolution=False)
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel.value}: {e}")
    
    async def _send_resolution_notification(self, alert: Alert, rule: AlertRule, message: str):
        """Send alert resolution notifications."""
        resolution_alert = Alert(
            rule_name=alert.rule_name,
            component=alert.component,
            severity=AlertSeverity.INFO,
            message=message,
            timestamp=datetime.now(),
            resolved=True
        )
        
        for channel in rule.channels:
            if channel in self.notification_handlers:
                try:
                    await self.notification_handlers[channel](resolution_alert, is_resolution=True)
                except Exception as e:
                    logger.error(f"Failed to send resolution notification via {channel.value}: {e}")
    
    async def _send_log_alert(self, alert: Alert, is_resolution: bool = False):
        """Send alert to application log."""
        level = logging.INFO if is_resolution or alert.severity == AlertSeverity.INFO else \
                logging.WARNING if alert.severity == AlertSeverity.WARNING else \
                logging.ERROR
        
        prefix = "RESOLVED" if is_resolution else "ALERT"
        logger.log(level, f"{prefix}: [{alert.severity.value.upper()}] {alert.message}")
    
    async def _send_console_alert(self, alert: Alert, is_resolution: bool = False):
        """Send alert to console output."""
        prefix = "✅ RESOLVED" if is_resolution else "🚨 ALERT"
        severity_icon = "ℹ️" if alert.severity == AlertSeverity.INFO else \
                      "⚠️" if alert.severity == AlertSeverity.WARNING else "🔥"
        
        print(f"{prefix} {severity_icon} [{alert.severity.value.upper()}] {alert.message}")
    
    async def _send_mqtt_alert(self, alert: Alert, is_resolution: bool = False):
        """Send alert via MQTT (placeholder for integration)."""
        # This will be implemented when MQTT client is integrated
        topic = f"{self.mqtt_topic_prefix}/{alert.severity.value}"
        payload = {
            'alert': alert.to_dict(),
            'is_resolution': is_resolution,
            'timestamp': datetime.now().isoformat()
        }
        logger.debug(f"MQTT alert would be sent to {topic}: {payload}")
    
    async def _send_email_alert(self, alert: Alert, is_resolution: bool = False):
        """Send alert via email (placeholder for implementation)."""
        # This would integrate with an email service
        logger.debug(f"Email alert would be sent: {alert.message}")
    
    async def _send_webhook_alert(self, alert: Alert, is_resolution: bool = False):
        """Send alert via webhook (placeholder for implementation)."""
        # This would make HTTP POST to webhook URL
        logger.debug(f"Webhook alert would be sent to {self.webhook_url}: {alert.message}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently active alerts."""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history."""
        # Sort by timestamp, most recent first
        sorted_alerts = sorted(
            self.alert_history, 
            key=lambda a: a.timestamp, 
            reverse=True
        )
        return [alert.to_dict() for alert in sorted_alerts[:limit]]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_week = now - timedelta(days=7)
        
        recent_alerts = [a for a in self.alert_history if a.timestamp >= last_24h]
        weekly_alerts = [a for a in self.alert_history if a.timestamp >= last_week]
        
        return {
            'total_alerts': len(self.alert_history),
            'active_alerts': len(self.active_alerts),
            'alerts_last_24h': len(recent_alerts),
            'alerts_last_week': len(weekly_alerts),
            'alert_breakdown_24h': {
                'critical': len([a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]),
                'warning': len([a for a in recent_alerts if a.severity == AlertSeverity.WARNING]),
                'info': len([a for a in recent_alerts if a.severity == AlertSeverity.INFO])
            },
            'most_frequent_alerts': self._get_most_frequent_alerts()
        }
    
    def _get_most_frequent_alerts(self, limit: int = 5) -> List[Dict[str, int]]:
        """Get most frequently triggered alert rules."""
        rule_counts: Dict[str, int] = {}
        
        for alert in self.alert_history:
            rule_counts[alert.rule_name] = rule_counts.get(alert.rule_name, 0) + 1
        
        sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'rule': rule, 'count': count} for rule, count in sorted_rules[:limit]]