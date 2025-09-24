# Execute local reorganization: move logs to logs/, db files to db/, move setup scripts to deploy/, update .gitignore
# Ensure we run from the repository root (parent of the scripts/ folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = Split-Path -Parent $scriptDir
Set-Location -Path $repoRoot

# Create directories
New-Item -ItemType Directory -Path db -Force | Out-Null
New-Item -ItemType Directory -Path logs -Force | Out-Null
New-Item -ItemType Directory -Path deploy -Force | Out-Null

# Move .log files
Get-ChildItem -Path . -Filter *.log -File | ForEach-Object {
    $n = $_.Name
    try { git ls-files --error-unmatch $n > $null 2>$null; git mv $n logs/ } catch { Move-Item -Path $n -Destination logs/ -Force }
}

# Move DB files
foreach ($f in @('bt50_samples.db','bt50_samples.db-wal','bt50_samples.db-shm')) {
    if (Test-Path $f) {
        try { git ls-files --error-unmatch $f > $null 2>$null; git mv $f db/ } catch { Move-Item -Path $f -Destination db/ -Force }
    }
}

# Move setup scripts
foreach ($s in @('setup_pi.sh','setup_service_bridge.py')) {
    if (Test-Path $s) {
        try { git ls-files --error-unmatch $s > $null 2>$null; git mv $s deploy/ } catch { Move-Item -Path $s -Destination deploy/ -Force }
    }
}

# Update .gitignore
if (-not (Select-String -Path .gitignore -Pattern '^logs/?' -Quiet)) {
    Add-Content -Path .gitignore -Value "`n# runtime logs and capture DB`nlogs/`n"
}
if (-not (Select-String -Path .gitignore -Pattern '^db/?' -Quiet)) {
    Add-Content -Path .gitignore -Value "# db runtime files`ndb/*.db`n"
}

# Untrack DB if necessary (call git directly so PowerShell parameters aren't passed to git)
try { & git rm --cached db/bt50_samples.db } catch {}

# Commit changes
git add -A
try { git commit -m "chore: move runtime logs to logs/ and capture DB to db/; move provisioning scripts to deploy/; ignore runtime artifacts" | Out-Null; Write-Output 'Committed' } catch { Write-Output 'No commit' }

# Show status
git status --porcelain
