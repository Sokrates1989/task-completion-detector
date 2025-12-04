# task-completion-detector
Get notified when your AI coding assistant needs you. Never miss a task completion or required input again.

## Quick install (macOS)

Copy and run in your terminal:

```bash
ORIGINAL_DIR=$(pwd)
mkdir -p /tmp/task-detector-setup && cd /tmp/task-detector-setup
curl -sO https://raw.githubusercontent.com/Sokrates1989/task-completion-detector/main/setup/macos.sh
bash macos.sh
cd "$ORIGINAL_DIR"
rm -rf /tmp/task-detector-setup
```

## Quick usage

### Select region + start watching

```bash
task-watch --select-region
# or: task-watch --select
# or: task-watch -r
```

This opens the region selector, saves the region as the default, and immediately starts monitoring.

### Watch last selected region

```bash
task-watch
```

Reuse the last selected default region and start monitoring it again.

### Edit configuration (monitor + notifications)

```bash
task-watch --config
```

Reruns the guided configuration wizard so you can change:

- Monitor thresholds (interval, stableSecondsThreshold, differenceThreshold)
- Notification channels (Telegram, email, macOS) and their credentials

### Update to latest version (git clone only)

```bash
task-watch --update
```

Runs a `git pull --ff-only` in the installation directory (when it is a git clone) and exits.

Legacy aliases still work and forward to `task-watch`:

- `ai-select` behaves like `task-watch --select-region`
- `ai-watch` behaves like `task-watch`

- Or double-click `task-watch.command`, `ai-select.command` or `ai-watch.command` on your Desktop.

## More docs

- **Installation & configuration details:** `docs/INSTALL.md`
- **Usage, behavior & Telegram setup:** `docs/USAGE.md`
