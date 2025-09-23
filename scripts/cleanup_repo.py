#!/usr/bin/env python3
"""Dry-run cleanup script to move noisy scripts from project root into `archive/`.

This script is intentionally conservative: it prints planned moves and only executes when
`--apply` is passed. It avoids deleting files and records moves in `archive/ARCHIVE_LIST.md`.

Usage:
    python scripts/cleanup_repo.py           # dry-run, shows planned moves
    python scripts/cleanup_repo.py --apply   # perform moves

Rules:
 - Moves files that match heuristics: filenames with keywords like 'backup', 'test', 'tmp', 'experiment', 'latest', or duplicate launchers.
 - Skips files listed in `KEEP_FILES`.
 - Updates `archive/ARCHIVE_LIST.md` with entries for moved files.
"""

from pathlib import Path
import shutil
import argparse
import re
import datetime

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / 'archive'
ARCHIVE_INDEX = ARCHIVE_DIR / 'ARCHIVE_LIST.md'

# Files to always keep in project root
KEEP_FILES = {
    'README.md', 'pyproject.toml', 'requirements.txt', 'leadville_bridge.py',
    'src', 'src/', '.github', '.vscode', 'scripts'
}

HEURISTICS = [r'backup', r'latest', r'experiment', r'test', r'tmp', r'old', r'patch']


def find_candidates():
    candidates = []
    for p in ROOT.iterdir():
        if p.is_dir():
            continue
        name = p.name.lower()
        if name in KEEP_FILES:
            continue
        for h in HEURISTICS:
            if re.search(h, name):
                candidates.append(p)
                break
    return candidates


def record_archive_entry(file_path, reason):
    ARCHIVE_DIR.mkdir(exist_ok=True)
    entry = f"- {file_path.name} — {reason} — {file_path.relative_to(ROOT)}\n"
    if not ARCHIVE_INDEX.exists():
        ARCHIVE_INDEX.write_text("# Archive index\n\n")
    with ARCHIVE_INDEX.open('a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.utcnow().isoformat()} {entry}")


def move_file(p, apply=False):
    ARCHIVE_DIR.mkdir(exist_ok=True)
    dest = ARCHIVE_DIR / p.name
    if dest.exists():
        dest = ARCHIVE_DIR / f"{p.stem}_{int(datetime.datetime.utcnow().timestamp())}{p.suffix}"
    print(f"MOVE: {p} -> {dest}")
    if apply:
        shutil.move(str(p), str(dest))
        record_archive_entry(p, 'auto-moved by scripts/cleanup_repo.py')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='Perform moves')
    args = ap.parse_args()

    candidates = find_candidates()
    if not candidates:
        print('No candidate files found.')
        return

    print('Candidates to archive:')
    for p in candidates:
        print(' -', p.name)

    if args.apply:
        for p in candidates:
            move_file(p, apply=True)
        print('Moves completed.')
    else:
        print('\nDry-run: use --apply to perform moves')


if __name__ == '__main__':
    main()
