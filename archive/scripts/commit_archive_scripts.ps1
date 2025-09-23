# Commit the mover script and remove empty scripts/ dir if present
if (Test-Path 'scripts/archive_scripts_helpers.ps1') { git add scripts/archive_scripts_helpers.ps1 }
# If scripts dir is empty, remove it (PowerShell rmdir will fail if not empty)
$items = Get-ChildItem -Path scripts -Recurse -Force -ErrorAction SilentlyContinue
if (-not $items) { Remove-Item -Path scripts -Recurse -Force -ErrorAction SilentlyContinue; Write-Output 'Removed empty scripts/' }

try { git commit -m 'archive: move scripts helpers into archive/scripts and remove scripts/' | Out-Null; Write-Output 'Committed script moves' } catch { Write-Output 'No commit' }

git status --porcelain
