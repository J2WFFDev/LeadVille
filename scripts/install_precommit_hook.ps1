# PowerShell installer for git hooks (for Windows users)
$repoRoot = (Get-Location).Path
$hookSrc = Join-Path $repoRoot '.githooks\pre-commit'
$hookDest = Join-Path $repoRoot '.git\hooks\pre-commit'
if (Test-Path $hookDest) { Write-Output "Existing hook at $hookDest will be overwritten." }
Copy-Item -Force -Path $hookSrc -Destination $hookDest
Write-Output "Installed pre-commit hook to $hookDest"