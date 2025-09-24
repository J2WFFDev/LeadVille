#!/usr/bin/env python3
"""
scripts/ensure_layout.py

Audit and optionally move misplaced files from the repository root into
`scripts/`, `tests/`, or `docs/dashboard/`.

Usage:
  python scripts/ensure_layout.py          # dry-run (report only)
  python scripts/ensure_layout.py --move   # perform moves (but do not git commit)
  python scripts/ensure_layout.py --move --commit  # perform moves and git commit
  python scripts/ensure_layout.py --move --commit --yes  # no prompts

Rules (default):
- Files named test_*.py -> `tests/`
- Files ending with .py and not under `src/`/`scripts/`/`tools/`/`archive/` -> `scripts/`
- HTML files matching timer_dashboard_*.html -> `docs/dashboard/`

This script is careful: by default does a dry-run and prints what it WOULD do.
When --move is passed it will move files on the filesystem. When --commit is
passed it will run `git add` and `git commit` with a generated message.

"""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / 'scripts'
TESTS_DIR = ROOT / 'tests'
DOCS_DASHBOARD = ROOT / 'docs' / 'dashboard'

IGNORED_DIRS = {'src', 'scripts', 'tools', 'archive', 'deploy', 'db', 'logs', '.git'}


def find_misplaced(root: Path):
    misplaced = []
    for p in root.iterdir():
        if p.is_dir():
            continue
        name = p.name
        if p.suffix == '.py':
            # allow some special root files (LICENSE, pyproject etc are not .py)
            # if file is in allowed list, skip - otherwise it's misplaced
            # tests are expected under tests/
            if name.startswith('test_'):
                target = TESTS_DIR / name
                misplaced.append((p, target))
            else:
                # .py in root -> scripts/
                target = SCRIPTS_DIR / name
                misplaced.append((p, target))
        elif p.suffix in {'.html', '.htm'} and name.startswith('timer_dashboard_'):
            target = DOCS_DASHBOARD / name
            misplaced.append((p, target))
    return misplaced


def ensure_dirs():
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DASHBOARD.mkdir(parents=True, exist_ok=True)


def run_git(cmd_args, cwd=ROOT):
    try:
        subprocess.run(['git'] + cmd_args, cwd=str(cwd), check=True)
    except subprocess.CalledProcessError as e:
        print('git command failed:', e)
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--move', action='store_true', help='Actually perform moves')
    ap.add_argument('--commit', action='store_true', help='Stage and commit moved files')
    ap.add_argument('--yes', action='store_true', help='Answer yes to prompts')
    args = ap.parse_args()

    ensure_dirs()
    misplaced = find_misplaced(ROOT)
    if not misplaced:
        print('No misplaced files found in repository root.')
        return

    print('Found misplaced files:')
    for src, dest in misplaced:
        print(f'  {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}')

    if not args.move:
        print('\nDry-run complete. To move files, run with --move')
        return

    # confirm
    if not args.yes:
        reply = input('\nProceed to move these files? [y/N]: ').strip().lower()
        if reply not in ('y', 'yes'):
            print('Aborted by user.')
            return

    # perform moves
    for src, dest in misplaced:
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f'Moving {src} -> {dest}')
        try:
            shutil.move(str(src), str(dest))
        except Exception as e:
            print(f'Failed to move {src}: {e}')

    if args.commit:
        # run git add/commit
        run_git(['add'] + [str(d.relative_to(ROOT)) for _, d in misplaced])
        msg_lines = ['chore(repo): move misplaced root files']
        for s, d in misplaced:
            msg_lines.append(f'- {s.name} -> {d.parent.relative_to(ROOT)}/{d.name}')
        run_git(['commit', '-m', '\n'.join(msg_lines)])
        print('Committed moved files.')

    print('\nDone.')


if __name__ == '__main__':
    main()
