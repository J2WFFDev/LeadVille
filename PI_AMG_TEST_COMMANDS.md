# AMG Testing Commands for Raspberry Pi

## Connect to Pi and Check AMG Database

```bash
# Connect to Pi
ssh raspberrypi

# Check if LeadVille bridge is running
sudo systemctl status leadville-bridge
ps aux | grep leadville

# Navigate to LeadVille directory  
cd /opt/LeadVille  # or wherever it's installed

# Check if database exists and examine AMG data
ls -la logs/
sqlite3 logs/bt50_samples.db

# In SQLite, run these commands:
.tables
.schema timer_events
SELECT COUNT(*) FROM timer_events;
SELECT * FROM timer_events ORDER BY ts_ns DESC LIMIT 10;
SELECT event_type, COUNT(*) FROM timer_events GROUP BY event_type;
.quit
```

## Check Bridge Logs for AMG Activity

```bash
# Check recent bridge logs
tail -f logs/console/bridge_console_*.log | grep -i amg

# Or check systemd logs if running as service
journalctl -u leadville-bridge -f | grep -i amg

# Look for AMG connection attempts
grep -i "amg\|timer" logs/console/bridge_console_*.log | tail -20
```

## Test AMG Device Connection (if available)

```bash
# Check Bluetooth devices
bluetoothctl
scan on
# Look for AMG device MAC address
devices
quit

# Check if AMG MAC is in bridge config
grep -i amg /opt/LeadVille/config.json  # or wherever config is stored
```

## Compare Database Tables

```bash
sqlite3 logs/bt50_samples.db
.tables
.schema bt50_samples  
.schema timer_events
SELECT COUNT(*) FROM bt50_samples;
SELECT COUNT(*) FROM timer_events;
.quit
```

## Expected Results

### If AMG is working correctly:
- `timer_events` table should exist
- Should have START/SHOT/STOP events with recent timestamps
- `raw_hex` field should contain AMG frame data (01050..., 01030..., 01080...)

### If AMG is not working:
- `timer_events` table may be empty
- No recent AMG logs in bridge console
- AMG device not connected via Bluetooth

## Key Files to Check on Pi

```bash
# Main bridge application
cat src/impact_bridge/leadville_bridge.py | grep -A 20 "amg_notification_handler"

# Check if new AMG parser files exist
ls -la src/impact_bridge/ble/amg*
```