#!/usr/bin/env bash
REPO_ROOT=$(git rev-parse --show-toplevel)
HOOK_SRC="$REPO_ROOT/.githooks/pre-commit"
HOOK_DEST="$REPO_ROOT/.git/hooks/pre-commit"
if [ -f "$HOOK_DEST" ]; then
  echo "Existing hook at $HOOK_DEST will be overwritten."
fi
cp -f "$HOOK_SRC" "$HOOK_DEST"
chmod +x "$HOOK_DEST"
echo "Installed pre-commit hook to $HOOK_DEST"