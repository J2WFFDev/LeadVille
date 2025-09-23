# Move helper scripts under scripts/ into archive/scripts/ safely
$srcDir = 'scripts'
$destDir = 'archive\scripts'
if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir | Out-Null }

$files = Get-ChildItem -Path $srcDir -File | Where-Object { $_.Name -notin @('archive_scripts_helpers.ps1') }
foreach ($f in $files) {
    $name = $f.Name
    $src = Join-Path $srcDir $name
    $dst = Join-Path $destDir $name
    Write-Output "Processing $src"
    try {
        git ls-files --error-unmatch $src > $null 2>$null
        git mv --force $src $dst
        Write-Output "  -> git mv (tracked)"
    } catch {
        Move-Item -Path $src -Destination $dst -Force
        Write-Output "  -> moved (untracked)"
    }
    $line = "- scripts/" + $name + ": moved to archive/scripts on " + (Get-Date -Format u)
    Add-Content -Path archive/ARCHIVE_LIST.md -Value $line
}

git add archive/ARCHIVE_LIST.md
try { git commit -m 'archive: move scripts helper files into archive/scripts' | Out-Null; Write-Output 'Committed archive list' } catch { Write-Output 'No commit' }

git status --porcelain
