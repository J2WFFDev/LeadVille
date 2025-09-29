#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy SpecialPie Timer Integration to LeadVille Bridge Pi
.DESCRIPTION
    Deploys the new SpecialPie timer support files to the Raspberry Pi,
    including the BLE handler, API endpoints, and updated device manager.
#>

param(
    [string]$PiHost = "jrwest@192.168.1.125",
    [string]$PiProjectPath = "/home/jrwest/projects/LeadVille",
    [switch]$RestartServices = $true
)

Write-Host "🚀 Deploying SpecialPie Timer Integration to Pi..." -ForegroundColor Green

# Files to sync for SpecialPie integration
$FilesToSync = @(
    "src/impact_bridge/device_manager.py",
    "src/impact_bridge/specialpie_handler.py", 
    "src/impact_bridge/specialpie_api.py",
    "src/impact_bridge/fastapi_backend.py",
    "src/impact_bridge/database/pool_models.py",
    "migrations/create_device_pool_tables.py",
    "frontend/src/components/DeviceManager.tsx"
)

try {
    # Create backup directory on Pi
    Write-Host "📋 Creating backup directory on Pi..."
    ssh $PiHost "mkdir -p $PiProjectPath/backup/specialpie_integration_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"
    
    # Sync each file
    foreach ($file in $FilesToSync) {
        Write-Host "📁 Syncing $file..." -ForegroundColor Yellow
        
        # Create backup of existing file
        $remoteFile = "$PiProjectPath/$file"
        $backupFile = "$PiProjectPath/backup/specialpie_integration_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')/$(Split-Path $file -Leaf)"
        
        ssh $PiHost "if [ -f '$remoteFile' ]; then cp '$remoteFile' '$backupFile'; fi"
        
        # Copy new file
        scp $file "${PiHost}:${PiProjectPath}/$file"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Successfully synced $file" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to sync $file" -ForegroundColor Red
        }
    }
    
    # Update database schema for SpecialPie support
    Write-Host "🗄️ Updating database schema..." -ForegroundColor Yellow
    ssh $PiHost "cd $PiProjectPath && python3 -c '
import sqlite3
import logging
logging.basicConfig(level=logging.INFO)

# Connect to database
conn = sqlite3.connect(\"db/leadville.db\")
cursor = conn.cursor()

try:
    # Update device_pool table constraint to include shot_timer
    cursor.execute(\"\"\"
        DROP TABLE IF EXISTS device_pool_new;
        CREATE TABLE device_pool_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hw_addr VARCHAR(17) NOT NULL UNIQUE,
            device_type VARCHAR(20) NOT NULL CHECK (device_type IN (\"timer\", \"sensor\", \"shot_timer\", \"other\")),
            label VARCHAR(100) NOT NULL,
            vendor VARCHAR(50),
            model VARCHAR(50),
            status VARCHAR(20) NOT NULL DEFAULT \"available\" CHECK (status IN (\"available\", \"leased\", \"offline\", \"maintenance\")),
            last_seen DATETIME,
            battery INTEGER CHECK (battery >= 0 AND battery <= 100),
            rssi INTEGER CHECK (rssi >= -100 AND rssi <= 0),
            notes TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    \"\"\")
    
    # Copy existing data if table exists
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"device_pool\";\")
    if cursor.fetchone():
        cursor.execute(\"\"\"
            INSERT INTO device_pool_new (id, hw_addr, device_type, label, vendor, model, status, last_seen, battery, rssi, notes, created_at, updated_at)
            SELECT id, hw_addr, device_type, label, vendor, model, status, last_seen, battery, rssi, notes, created_at, updated_at
            FROM device_pool;
        \"\"\")
        
        # Drop old table and rename new one
        cursor.execute(\"DROP TABLE device_pool;\")
    
    cursor.execute(\"ALTER TABLE device_pool_new RENAME TO device_pool;\")
    
    # Recreate indexes
    cursor.execute(\"CREATE INDEX IF NOT EXISTS idx_pool_hw_addr ON device_pool(hw_addr);\")
    cursor.execute(\"CREATE INDEX IF NOT EXISTS idx_pool_status ON device_pool(status);\")
    cursor.execute(\"CREATE INDEX IF NOT EXISTS idx_pool_device_type ON device_pool(device_type);\")
    cursor.execute(\"CREATE INDEX IF NOT EXISTS idx_pool_last_seen ON device_pool(last_seen);\")
    
    conn.commit()
    print(\"✅ Database schema updated for SpecialPie support\")
    
except Exception as e:
    print(f\"❌ Database schema update failed: {e}\")
    conn.rollback()
finally:
    conn.close()
'"
    
    # Test SpecialPie import
    Write-Host "🧪 Testing SpecialPie integration imports..." -ForegroundColor Yellow
    ssh $PiHost "cd $PiProjectPath && python3 -c '
try:
    from src.impact_bridge.specialpie_handler import SpecialPieHandler, specialpie_manager
    from src.impact_bridge.specialpie_api import router as specialpie_router
    print(\"✅ SpecialPie imports successful\")
    print(f\"Manager status: {specialpie_manager.get_status()}\")
except Exception as e:
    print(f\"❌ SpecialPie import failed: {e}\")
    import traceback
    traceback.print_exc()
'"
    
    if ($RestartServices) {
        Write-Host "🔄 Restarting LeadVille services..." -ForegroundColor Yellow
        
        # Restart FastAPI backend
        ssh $PiHost "cd $PiProjectPath && pkill -f fastapi_backend || true"
        Start-Sleep -Seconds 2
        ssh $PiHost "cd $PiProjectPath && nohup python3 -m uvicorn src.impact_bridge.fastapi_backend:app --reload --host 0.0.0.0 --port 8001 > logs/backend.log 2>&1 &"
        
        Write-Host "✅ Services restarted" -ForegroundColor Green
        Start-Sleep -Seconds 3
        
        # Test API health
        Write-Host "🏥 Testing API health..." -ForegroundColor Yellow
        ssh $PiHost "curl -s http://localhost:8001/api/health | head -c 100"
    }
    
    Write-Host ""
    Write-Host "🎉 SpecialPie Timer Integration Deployment Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Test SpecialPie device discovery: http://192.168.1.125:8001/api/admin/devices/discover" -ForegroundColor White
    Write-Host "2. Check SpecialPie API: http://192.168.1.125:8001/api/admin/specialpie/status" -ForegroundColor White
    Write-Host "3. Pair a SpecialPie timer through the device manager UI" -ForegroundColor White
    Write-Host "4. Connect and monitor shot data from the timer" -ForegroundColor White
    Write-Host ""
    Write-Host "🔍 Key Features Added:" -ForegroundColor Cyan
    Write-Host "• SpecialPie SP M1A2 timer detection (⏱️ icon)" -ForegroundColor White
    Write-Host "• BLE characteristic 0000fff1-0000-1000-8000-00805f9b34fb monitoring" -ForegroundColor White
    Write-Host "• Shot timing data parsing (command codes 54, 52, 24)" -ForegroundColor White
    Write-Host "• Real-time shot event callbacks and logging" -ForegroundColor White
    Write-Host "• REST API endpoints for timer management" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "❌ Deployment failed: $_" -ForegroundColor Red
    exit 1
}