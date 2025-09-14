#!/usr/bin/env python3
"""
Demonstration of LeadVille Impact Bridge Monitoring & Observability System
"""

import asyncio
import json
import time
from datetime import datetime

from src.impact_bridge.monitoring import (
    SystemMonitor,
    HealthAggregator, 
    LEDController,
    AlertManager,
    NTPMonitor
)


async def demonstrate_monitoring():
    """Demonstrate the comprehensive monitoring system."""
    print("🚀 LeadVille Impact Bridge - Monitoring & Observability Demo")
    print("=" * 60)
    
    # Initialize monitoring components
    print("\n📊 Initializing Monitoring Components...")
    system_monitor = SystemMonitor()
    health_aggregator = HealthAggregator(system_monitor=system_monitor)
    led_controller = LEDController(enable_hardware=True, simulation_mode=True)
    alert_manager = AlertManager(enable_mqtt_alerts=False)
    ntp_monitor = NTPMonitor()
    
    print("✅ All monitoring components initialized")
    
    # Demonstrate system monitoring
    print("\n🖥️  System Resource Monitoring:")
    print("-" * 40)
    
    metrics = await system_monitor.get_system_metrics()
    print(f"CPU Usage: {metrics.cpu_percent}%")
    print(f"Memory Usage: {metrics.memory_usage_mb:.1f} MB ({metrics.memory_percent}%)")
    print(f"Disk Usage: {metrics.disk_usage_gb:.1f} GB ({metrics.disk_percent}%)")
    print(f"Process Count: {metrics.process_count}")
    print(f"Uptime: {metrics.uptime_seconds:.1f} seconds")
    
    # Demonstrate disk space monitoring
    print("\n💾 Disk Space Monitoring:")
    print("-" * 40)
    
    disk_statuses = await system_monitor.check_disk_space()
    for disk in disk_statuses:
        status_icon = "🔴" if disk.is_critical else "🟡" if disk.is_warning else "🟢"
        print(f"{status_icon} {disk.path}: {disk.percent_used:.1f}% used ({disk.free_gb:.1f} GB free)")
    
    # Demonstrate network monitoring
    print("\n🌐 Network Connectivity:")
    print("-" * 40)
    
    network_status = await system_monitor.check_network_connectivity()
    status_icon = "🟢" if network_status.is_connected else "🔴"
    print(f"{status_icon} Network Status: {'Connected' if network_status.is_connected else 'Disconnected'}")
    if network_status.interface_name:
        print(f"   Interface: {network_status.interface_name}")
    if network_status.ip_address:
        print(f"   IP Address: {network_status.ip_address}")
    if network_status.ping_latency_ms:
        print(f"   Ping Latency: {network_status.ping_latency_ms:.1f} ms")
    
    # Demonstrate comprehensive health checking
    print("\n🏥 Comprehensive Health Status:")
    print("-" * 40)
    
    health_status = await health_aggregator.get_aggregated_health()
    overall_icon = "🟢" if health_status.overall_status.value == "healthy" else \
                   "🟡" if health_status.overall_status.value == "warning" else "🔴"
    
    print(f"{overall_icon} Overall Status: {health_status.overall_status.value.upper()}")
    print(f"   Components Monitored: {len(health_status.components)}")
    print(f"   Active Alerts: {len(health_status.alerts)}")
    
    print("\n   Component Details:")
    for comp in health_status.components:
        comp_icon = "🟢" if comp.status.value == "healthy" else \
                   "🟡" if comp.status.value == "warning" else \
                   "🔴" if comp.status.value == "critical" else "⚪"
        print(f"   {comp_icon} {comp.name}: {comp.status.value} - {comp.message}")
    
    # Demonstrate alerting system
    print("\n🚨 Alert Management:")
    print("-" * 40)
    
    await alert_manager.process_health_status(health_status)
    active_alerts = alert_manager.get_active_alerts()
    alert_stats = alert_manager.get_alert_statistics()
    
    print(f"Active Alerts: {len(active_alerts)}")
    print(f"Total Alerts (All Time): {alert_stats['total_alerts']}")
    print(f"Alerts (Last 24h): {alert_stats['alerts_last_24h']}")
    
    if active_alerts:
        print("\nActive Alert Details:")
        for alert in active_alerts:
            severity_icon = "🔥" if alert['severity'] == 'critical' else "⚠️"
            print(f"   {severity_icon} [{alert['severity'].upper()}] {alert['message']}")
    
    # Demonstrate LED status indicators
    print("\n💡 LED Status Indicators:")
    print("-" * 40)
    
    await led_controller.update_from_health_status(health_status)
    led_statuses = led_controller.get_led_status()
    
    for led_name, led_info in led_statuses.items():
        state_icon = "🔴" if led_info['current_state'] == 'on' else \
                    "🟡" if 'blink' in led_info['current_state'] else \
                    "⚫" if led_info['current_state'] == 'off' else "⚪"
        
        print(f"   {state_icon} {led_info['name']} ({led_info['color']}): {led_info['current_state']}")
    
    # Demonstrate NTP monitoring (if available)
    print("\n⏰ NTP Time Synchronization:")
    print("-" * 40)
    
    try:
        ntp_status = await ntp_monitor.check_ntp_synchronization()
        sync_icon = "🟢" if ntp_status.is_synchronized and not ntp_status.is_critical else \
                   "🟡" if ntp_status.is_warning else "🔴"
        
        print(f"{sync_icon} NTP Status: {'Synchronized' if ntp_status.is_synchronized else 'Not Synchronized'}")
        if ntp_status.drift_ms is not None:
            print(f"   Time Drift: {ntp_status.drift_ms:.1f} ms")
        print(f"   Successful Servers: {len(ntp_status.successful_servers)}/{ntp_status.server_count}")
        
        if ntp_status.successful_servers:
            print(f"   Working Servers: {', '.join(ntp_status.successful_servers)}")
        if ntp_status.failed_servers:
            print(f"   Failed Servers: {', '.join(ntp_status.failed_servers)}")
            
    except Exception as e:
        print(f"🔴 NTP monitoring failed: {e}")
    
    # Show JSON output for API integration
    print("\n📋 JSON Dashboard Data (API Format):")
    print("-" * 40)
    
    dashboard_data = {
        "timestamp": datetime.now().isoformat(),
        "system_metrics": metrics.to_dict(),
        "health_status": health_status.to_dict(),
        "active_alerts": active_alerts,
        "alert_statistics": alert_stats,
        "led_statuses": led_statuses,
        "monitoring_info": {
            "components_monitored": len(health_status.components),
            "alerts_active": len(active_alerts),
            "system_uptime": metrics.uptime_seconds,
            "overall_status": health_status.overall_status.value
        }
    }
    
    print(json.dumps(dashboard_data, indent=2)[:500] + "...")
    
    print("\n✅ Monitoring System Demonstration Complete!")
    print("\n🚀 Key Features Demonstrated:")
    print("   ✅ Real-time system resource monitoring")
    print("   ✅ Comprehensive health status aggregation")
    print("   ✅ Intelligent alerting with multiple severity levels")
    print("   ✅ LED status indicators for visual feedback")
    print("   ✅ NTP time synchronization monitoring")
    print("   ✅ JSON API output for integration")
    
    print(f"\n📊 Access the monitoring API at:")
    print(f"   - Health: http://localhost:8000/v1/health/comprehensive")
    print(f"   - Metrics: http://localhost:8000/v1/metrics/system")
    print(f"   - Dashboard: http://localhost:8000/v1/monitoring/dashboard")


if __name__ == "__main__":
    asyncio.run(demonstrate_monitoring())