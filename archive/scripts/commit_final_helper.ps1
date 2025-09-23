if (Test-Path 'scripts/commit_archive_helpers.ps1') { git add scripts/commit_archive_helpers.ps1 }
try { git commit -m 'scripts: add commit helper for archive moves' | Out-Null; Write-Output 'Committed final helper' } catch { Write-Output 'No commit' }

git status --porcelain
