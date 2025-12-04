#!/usr/bin/env bash
set -e

TARGET_DIR="$HOME/tools/task-completion-detector"
REPO_URL="https://github.com/Sokrates1989/task-completion-detector.git"

echo "➡️ Installing task-completion-detector into $TARGET_DIR"

# Step 1: Clone or update the repository
if [[ ! -d "$TARGET_DIR/.git" ]]; then
  mkdir -p "$TARGET_DIR"
  cd "$TARGET_DIR"
  git clone "$REPO_URL" .
else
  echo "ℹ️ task-completion-detector already cloned – attempting to update..."
  cd "$TARGET_DIR"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git pull --ff-only || echo "⚠️ Could not fast-forward; continuing with existing clone."
  fi
fi

# Step 2: Ensure installer is executable and run it with sudo for symlink creation
sudo bash install.sh
