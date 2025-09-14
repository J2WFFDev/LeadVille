# LeadVille SystemD Service Files

This directory contains systemd service unit files for LeadVille Impact Bridge components.

## Services

- **leadville-bridge.service** - Main BLE sensor bridge application
- **leadville-api.service** - REST API server
- **leadville-network.service** - Network management service
- **leadville-websocket.service** - WebSocket server for real-time data

## Installation

These service files are automatically installed by `install_pi.sh`.

Manual installation:
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable leadville-bridge leadville-api
sudo systemctl start leadville-bridge leadville-api
```

## Service Management

```bash
# Start/stop services
sudo systemctl start leadville-bridge
sudo systemctl stop leadville-bridge

# View logs
journalctl -u leadville-bridge -f
journalctl -u leadville-api -f

# Check status
systemctl status leadville-bridge
```