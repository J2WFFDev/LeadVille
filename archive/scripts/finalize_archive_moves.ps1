# Move any remaining helper files into archive and commit the archive list
$files = @('move_archive.py','scripts/move_remaining_to_archive.ps1')
foreach ($f in $files) {
    if (Test-Path $f) {
        Move-Item -Path $f -Destination archive/ -Force
        $line = "- " + $f + ": moved to archive on " + (Get-Date -Format u)
        Add-Content -Path archive/ARCHIVE_LIST.md -Value $line
        Write-Output "Moved $f"
    } else {
        Write-Output "Not found: $f"
    }
}

git add archive/ARCHIVE_LIST.md
try { git commit -m 'archive: move remaining helper scripts to archive' | Out-Null; Write-Output 'Committed' } catch { Write-Output 'No commit (no changes)'}

git status --porcelain
