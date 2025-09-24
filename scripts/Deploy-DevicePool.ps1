#!/usr/bin/env pwsh
# Device Pool Management Deployment Script
# Deploys new pool system to Pi and runs migration

param(
    [string]$PiHost = "jrwest@192.168.1.124",
    [string]$ProjectPath = "/home/jrwest/projects/LeadVille"
)

Write-Host "🚀 Deploying Device Pool Management System to Pi..." -ForegroundColor Green

# Test connectivity
Write-Host "📡 Testing Pi connectivity..." -ForegroundColor Yellow
try {
    ssh $PiHost "echo 'Pi accessible'" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "SSH connection failed"
    }
    Write-Host "✅ Pi is accessible" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to Pi. Please check connectivity." -ForegroundColor Red
    exit 1
}

# Deploy new files
Write-Host "📦 Deploying new Device Pool Management files..." -ForegroundColor Yellow

$files = @(
    @{
        Local = "src/impact_bridge/database/pool_models.py"
        Remote = "$ProjectPath/src/impact_bridge/database/pool_models.py"
    },
    @{
        Local = "src/impact_bridge/pool_api.py" 
        Remote = "$ProjectPath/src/impact_bridge/pool_api.py"
    },
    @{
        Local = "src/impact_bridge/fastapi_backend.py"
        Remote = "$ProjectPath/src/impact_bridge/fastapi_backend.py"
    },
    @{
        Local = "migrations/create_device_pool_tables.py"
        Remote = "$ProjectPath/migrations/create_device_pool_tables.py"
    }
)

foreach ($file in $files) {
    Write-Host "  📁 $($file.Local)" -ForegroundColor Cyan
    scp $file.Local "${PiHost}:$($file.Remote)"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to deploy $($file.Local)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All files deployed successfully" -ForegroundColor Green

# Create migrations directory if it doesn't exist
Write-Host "📁 Ensuring migrations directory exists..." -ForegroundColor Yellow
ssh $PiHost "mkdir -p $ProjectPath/migrations"

# Run database migration
Write-Host "🗄️ Running database migration..." -ForegroundColor Yellow
ssh $PiHost "cd $ProjectPath && python migrations/create_device_pool_tables.py leadville.db"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Database migration failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Database migration completed" -ForegroundColor Green

# Restart FastAPI service
Write-Host "🔄 Restarting FastAPI service..." -ForegroundColor Yellow
ssh $PiHost "pkill -f uvicorn && sleep 3"
ssh $PiHost "cd $ProjectPath && nohup python -m uvicorn src.impact_bridge.fastapi_backend:app --reload --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &"

# Wait for service to start
Start-Sleep -Seconds 5

# Test API endpoints
Write-Host "🧪 Testing new API endpoints..." -ForegroundColor Yellow
$healthResponse = curl -s http://192.168.1.124:8001/api/health 2>$null
if ($healthResponse) {
    Write-Host "✅ FastAPI service is running" -ForegroundColor Green
    
    # Test device pool endpoint
    $poolResponse = curl -s http://192.168.1.124:8001/api/admin/pool/devices 2>$null
    if ($poolResponse) {
        Write-Host "✅ Device pool API is working" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Device pool API not responding" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ FastAPI service not responding" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Device Pool Management System deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test device discovery: http://192.168.1.124:5173/docs/dashboard/unified_bridge_config.html"
Write-Host "  2. Check device pool API: http://192.168.1.124:8001/api/admin/pool/devices"
Write-Host "  3. View API docs: http://192.168.1.124:8001/docs"