# PowerShell deployment script for LeadVille Pi services
param(
    [string]$PiHost = "raspberrypi"
)

Write-Host "=== LeadVille Pi Service Deployment ===" -ForegroundColor Green

# Test connectivity
Write-Host "Testing Pi connectivity..." -ForegroundColor Yellow
try {
    $ping = Test-Connection -ComputerName $PiHost -Count 1 -ErrorAction Stop
    Write-Host "✓ Pi is reachable at $($ping.Address)" -ForegroundColor Green
} catch {
    Write-Host "✗ Cannot reach Pi at $PiHost" -ForegroundColor Red
    Write-Host "Please check network connectivity and try again" -ForegroundColor Red
    exit 1
}

# Copy systemd service files
Write-Host "Copying systemd service files..." -ForegroundColor Yellow
scp "systemd\leadville-fastapi.service" "${PiHost}:/tmp/"
scp "systemd\leadville-frontend.service" "${PiHost}:/tmp/"  
scp "systemd\leadville.target" "${PiHost}:/tmp/"
scp "scripts\setup_pi_services.sh" "${PiHost}:/tmp/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to copy files to Pi" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Files copied successfully" -ForegroundColor Green

# Run setup script
Write-Host "Running setup script on Pi..." -ForegroundColor Yellow
ssh $PiHost "chmod +x /tmp/setup_pi_services.sh && /tmp/setup_pi_services.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Deployment completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Services are now available at:" -ForegroundColor Cyan
    Write-Host "  FastAPI Health: http://192.168.1.124:8001/api/health" -ForegroundColor White
    Write-Host "  FastAPI Docs:   http://192.168.1.124:8001/docs" -ForegroundColor White  
    Write-Host "  Frontend:       http://192.168.1.124:5173" -ForegroundColor White
    Write-Host "  WebSocket Logs: ws://192.168.1.124:8001/ws/logs" -ForegroundColor White
    Write-Host "  WebSocket Live: ws://192.168.1.124:8001/ws/live" -ForegroundColor White
    Write-Host ""
    Write-Host "To check service status:" -ForegroundColor Cyan
    Write-Host "  ssh $PiHost 'sudo systemctl status leadville.target'" -ForegroundColor White
} else {
    Write-Host "✗ Deployment failed" -ForegroundColor Red
    Write-Host "Check the output above for errors" -ForegroundColor Red
    exit 1
}