# Safe move of remaining top-level files into archive/
# - Uses `git mv` for tracked files to preserve history, falls back to Move-Item for untracked files
# - Appends an entry to archive/ARCHIVE_LIST.md for each moved file
# - Commits the ARCHIVE_LIST.md at the end (if there are changes)

param()

$archive = "archive"
if (-not (Test-Path $archive)) { New-Item -ItemType Directory -Path $archive | Out-Null }

# Keep list: directories and files that should remain in the project root
$keep = @(
    'src', 'frontend', 'docs', '.git', '.github', '.vscode', 'pyproject.toml', 'requirements.txt', 'requirements_pi.txt',
    'README.md', 'LICENSE', 'config', 'systemd', 'migrations', 'tools', 'tests', 'bin', '.gitignore', 'setup_pi.sh', 'setup_service_bridge.py',
    'archive', 'db'
)

Write-Output "Scanning top-level files to move (excluding keep list):"
Get-ChildItem -Path . -File | Where-Object { -not ($keep -contains $_.Name) } | ForEach-Object {
    $name = $_.Name
    Write-Output "Processing: $name"
    try {
        # If the file is tracked by git, use git mv to preserve history
        git ls-files --error-unmatch $name > $null 2>$null
        git mv --force $name $archive/ 2>$null
        Write-Output "  -> git mv (tracked)"
    } catch {
        # Untracked: use Move-Item
        Move-Item -Path $name -Destination $archive/ -Force
        Write-Output "  -> moved (untracked)"
    }
    # Use concatenation to avoid PowerShell parsing issues with colons
    $timestamp = (Get-Date -Format u)
    $line = "- " + $name + ": moved to archive on " + $timestamp
    Add-Content -Path "$archive/ARCHIVE_LIST.md" -Value $line
}

# Stage and commit the archive list
if (Test-Path "$archive/ARCHIVE_LIST.md") {
    git add "$archive/ARCHIVE_LIST.md"
    try {
        git commit -m "archive: move remaining top-level files to archive" | Out-Null
        Write-Output "Committed archive/ARCHIVE_LIST.md"
    } catch {
        Write-Output "No commit created (nothing to commit or no changes)"
    }
}

# Print resulting status and archive listing (top 200 chars per filename for readability)
Write-Output "\nGit status (porcelain):"
git status --porcelain

Write-Output "\nArchive contents:"
Get-ChildItem -Path $archive | ForEach-Object { Write-Output ("  " + $_.Name) }

Write-Output "Done."
