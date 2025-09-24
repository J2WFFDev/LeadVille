$toAdd = @('archive/scripts/commit_archive_scripts.ps1','archive/scripts/commit_final_helper.ps1','scripts/move_last_scripts_helpers.ps1')
foreach ($p in $toAdd) { if (Test-Path $p) { git add $p } }
try { git commit -m 'archive: add final scripts helpers and mover' | Out-Null; Write-Output 'Committed final helpers' } catch { Write-Output 'No commit' }

git status --porcelain
