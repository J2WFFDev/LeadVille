$files = @('scripts/commit_archive_scripts.ps1','scripts/commit_final_helper.ps1')
foreach ($f in $files) {
    if (Test-Path $f) {
        Move-Item -Path $f -Destination archive/scripts/ -Force
        $line = "- " + $f + ": moved to archive/scripts on " + (Get-Date -Format u)
        Add-Content -Path archive/ARCHIVE_LIST.md -Value $line
        Write-Output "Moved $f"
    } else { Write-Output "Not found: $f" }
}

git add archive/ARCHIVE_LIST.md
try { git commit -m 'archive: finalize scripts helpers archival' | Out-Null; Write-Output 'Committed' } catch { Write-Output 'No commit' }

git status --porcelain
