# Usage, behavior & Telegram setup

## What this tool does

`task-completion-detector` watches a user-selected region of your screen (typically your AI assistant window).
It periodically captures screenshots of that region and compares them. When the pixels stop changing for a
configurable amount of time, it assumes the AI task has finished or your input is needed and sends you a
notification.

Notifications can be sent via:

- Telegram
- Email
- Local notifications (macOS Notification Center or Windows Toast Notifications)

---

## Commands and launchers

After installation you can use the `task-watch` launcher (recommended) or, for advanced usage, the Python CLI.

### task-watch (recommended)

**macOS - From Terminal:**

- `task-watch --select-region [name]`  – select a screen region and immediately start monitoring it. If `name` is provided, the region is saved under both `name` and the default region name.
  - Short aliases: `task-watch --select [name]`, `task-watch -r [name]`, or `task-watch -s [name]`.
- `task-watch` – monitor the last selected default region again.
- `task-watch [name]` – monitor a previously selected named region.
- `task-watch --config` – rerun the guided configuration wizard / config editor.
- `task-watch --update` – update the local git clone of task-completion-detector (when installed from git) and exit.

**Windows - From PowerShell (after restarting terminal):**

- `task-watch -r [name]` or `task-watch -s [name]`  – select a screen region and immediately start monitoring it. If `name` is provided, the region is saved under both `name` and the default region name.
- `task-watch` – monitor the last selected default region again.
- `task-watch [name]` – monitor a previously selected named region.
- `task-watch -c` – rerun the guided configuration wizard / config editor.
- `task-watch -u` – update the local git clone of task-completion-detector (when installed from git) and exit.

**Desktop shortcuts:**

- **macOS:** Double-click `task-watch.command` on your Desktop.
  - Backward-compatible shortcuts `ai-select.command` and `ai-watch.command` are also provided and forward to the same behaviors.
- **Windows:** Double-click `task-watch.lnk` on your Desktop.

**Legacy aliases (macOS only, still supported):**

- `ai-select` behaves like `task-watch --select-region`.
- `ai-watch` behaves like `task-watch`.

### Python CLI (inside the `python/` folder, advanced)

```bash
cd /path/to/task-completion-detector/python

# Re-run the guided configuration / config editor
python main.py setup-config

# Low-level region control (normally you just use task-watch)
python main.py select-region --name default
python main.py monitor --name default
```

---

## Typical workflow

1. **Run the installer once** (see `docs/INSTALL.md`). It will:
   - Set up launchers and shortcuts.
   - Start the guided configuration wizard.

2. **Configure notifications** in the wizard:
   - Choose whether to use Telegram, email, macOS notifications, or any combination.
   - For Telegram and email, follow the prompts to enter the required credentials.

3. **Select the region to watch:**
- Run `task-watch --select-region` (Terminal) or double-click `task-watch.command`.
  - Follow the on-screen prompts:
     - Click once at the top-left corner of the region.
     - Click once at the bottom-right corner of the region.
   - The selected region is stored in `config/config.txt` as your default.

4. **Let the tool monitor the region:**
- After a successful selection via `task-watch --select-region`, monitoring starts automatically.
- You can also run `task-watch` later to reuse the last selected default region.

5. **Get notified when the AI stops changing the UI:**
   - The monitor checks the region every `intervalSeconds` seconds.
   - When the visual difference stays below `differenceThreshold` for `stableSecondsThreshold` seconds,
     it treats the task as "completed / needs your attention" and sends notifications.

You can tune these thresholds by:

- Running `task-watch --config` to rerun the guided configuration wizard. If a config already exists, it:
  - Shows your current monitor settings as defaults.
  - Lets you re-enable/disable Telegram, email, or macOS notifications and update credentials.
- Manually editing the `monitor` and `notifications` sections in `config/config.txt`.

---

## Telegram setup (detailed)

You can complete all of these steps via the guided `setup-config` wizard. The instructions below mirror
what the wizard does, so you can refer back to them later.

### 1. Prepare Telegram

1. Install **Telegram Desktop** and log in to your account.
2. In Telegram, start a chat with **@BotFather**.

### 2. Create your bot and get the HTTP API token

1. In the chat with BotFather, send `/newbot`.
2. Choose:
   - A **bot name**, e.g. `AI Task Watcher`.
   - A **bot username**, e.g. `ai_task_watcher_bot`.
3. BotFather will reply with a line like:

   > Use this token to access the HTTP API: `<TOKEN>`

4. This `<TOKEN>` is your **HTTP API token**:
   - Paste it into the wizard when it asks for the Telegram token.
   - It is stored only in your local `config/config.txt` and used solely to call Telegram's HTTP API
     to send notifications.

### 3. Open a chat with your bot

1. In BotFather's message you will see a link like `t.me/<bot-username>` (for example `t.me/ai_task_watcher_bot`).
2. Click that link to open a chat with your new bot.
3. Send the bot a short message such as `hi`.

The wizard will pause here until you confirm that you've sent a message to your bot.

### 4. Find your chat ID via getUpdates

1. After you have sent at least one message to your bot, the wizard prints a URL like:

   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```

   with your actual token already filled in.

2. Open this URL in a browser (you can often Cmd+Click it directly from the terminal).
3. In the JSON response, look for a section like:

   ```json
   "chat": { "id": 123456789, ... }
   ```

   The `id` value (e.g. `123456789`) is your **chat ID**.

4. If you only see an empty `"result": []` or no `chat` section yet:
   - Send another message to your bot in Telegram.
   - Refresh the `getUpdates` URL until a `"chat": { "id": ... }` entry appears.

5. Paste this chat ID back into the wizard when prompted.

After completing these steps, the tool can send Telegram messages to you whenever it detects that your
AI assistant has finished a task or is waiting for your input.

---

## Email and local notifications (overview)

- **Email:**
  - The config wizard asks for SMTP server, port, sender address and password, and receiver address.
  - These values are stored in `config/config.txt` and used to send simple text emails when a task completes.

- **macOS notifications:**
  - If enabled, the tool uses `osascript display notification` to post messages to Notification Center.
  - If you do not see notifications, open System Settings → Notifications, find your terminal application,
    and allow alerts/banners for it.

- **Windows notifications:**
  - If enabled, the tool uses PowerShell to send Windows toast notifications.
  - For enhanced notifications, install the BurntToast module: `Install-Module -Name BurntToast -Scope CurrentUser`
  - If you do not see notifications, check that Focus Assist is not blocking them, and open Action Center (Win+A)
    to see if notifications were delivered silently.

For low-level configuration details and troubleshooting, see `docs/INSTALL.md`.
