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

### ai-select

```bash
ai-select
```

Select the AI window region and start monitoring immediately.

### ai-watch

```bash
ai-watch
```

Monitor the last selected region again.

- Or double-click `ai-select.command` / `ai-watch.command` on your Desktop.
- To reconfigure notifications later, run `python main.py setup-config` from the `python/` folder.

## More docs

- **Installation & configuration details:** `docs/INSTALL.md`
- **Usage, behavior & Telegram setup:** `docs/USAGE.md`
