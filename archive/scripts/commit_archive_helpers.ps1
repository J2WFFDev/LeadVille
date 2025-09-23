$toAdd = @('archive/move_archive.py','archive/move_remaining_to_archive.ps1','scripts/finalize_archive_moves.ps1')
foreach ($p in $toAdd) { if (Test-Path $p) { git add $p } }
try { git commit -m 'archive: add mover helper scripts to archive and scripts/' | Out-Null; Write-Output 'Committed helpers' } catch { Write-Output 'No commit (nothing to commit)'}

git status --porcelain
