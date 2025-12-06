import json
import os
import platform
from typing import Any, Dict


DEFAULT_MONITOR = {
    "intervalSeconds": 1.0,
    "stableSecondsThreshold": 40.0,
    "differenceThreshold": 1.0,
}

DEFAULT_MONITOR_CHANGE = {
    "intervalSeconds": 1.0,
    # No stability duration for change-watch – we only care about sensitivity.
    "differenceThreshold": 10.0,
}


def _yes_no(prompt: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        raw = input(f"{prompt} {suffix} ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("Please answer y or n.")


def _input_float(prompt: str, default: float) -> float:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            print("Please enter a valid number.")


def _build_config_interactive(existing: Dict[str, Any]) -> Dict[str, Any]:
    print("\n=== Guided configuration for AI Task Completion Detector ===")

    existing_monitor = existing.get("monitor", {})
    monitor_defaults = {
        "intervalSeconds": float(existing_monitor.get("intervalSeconds", DEFAULT_MONITOR["intervalSeconds"])),
        "stableSecondsThreshold": float(existing_monitor.get("stableSecondsThreshold", DEFAULT_MONITOR["stableSecondsThreshold"])),
        "differenceThreshold": float(existing_monitor.get("differenceThreshold", DEFAULT_MONITOR["differenceThreshold"])),
    }

    # Monitor settings (stability mode / task-watch)
    print("\nCurrent monitor settings (from existing config or defaults):")
    print(f"  intervalSeconds: {monitor_defaults['intervalSeconds']}")
    print(f"  stableSecondsThreshold: {monitor_defaults['stableSecondsThreshold']}")
    print(f"  differenceThreshold: {monitor_defaults['differenceThreshold']}")

    use_defaults = _yes_no("Keep these monitor settings?", default=True)
    if use_defaults:
        monitor = dict(monitor_defaults)
    else:
        monitor = {
            "intervalSeconds": _input_float("intervalSeconds (seconds between checks)", monitor_defaults["intervalSeconds"]),
            "stableSecondsThreshold": _input_float(
                "stableSecondsThreshold (seconds of no change before notifying)",
                monitor_defaults["stableSecondsThreshold"],
            ),
            "differenceThreshold": _input_float(
                "differenceThreshold (pixel change sensitivity; lower = stricter)",
                monitor_defaults["differenceThreshold"],
            ),
        }

    # Change-watch settings (change mode / change-watch)
    existing_change = existing.get("monitorChange", {})
    change_defaults = {
        # Default to same interval as monitor unless user already customized monitorChange
        "intervalSeconds": float(existing_change.get("intervalSeconds", monitor["intervalSeconds"])),
        "differenceThreshold": float(
            existing_change.get(
                "differenceThreshold",
                DEFAULT_MONITOR_CHANGE["differenceThreshold"],
            )
        ),
    }

    print("\nCurrent change-watch settings (for change-watch mode):")
    print(f"  intervalSeconds: {change_defaults['intervalSeconds']}")
    print(f"  differenceThreshold: {change_defaults['differenceThreshold']}")

    use_change_defaults = _yes_no("Keep these change-watch settings?", default=True)
    if use_change_defaults:
        monitor_change = dict(change_defaults)
    else:
        monitor_change = {
            "intervalSeconds": _input_float(
                "intervalSeconds for change-watch (seconds between checks)",
                change_defaults["intervalSeconds"],
            ),
            "differenceThreshold": _input_float(
                "differenceThreshold for change-watch (pixel change sensitivity; higher = less sensitive)",
                change_defaults["differenceThreshold"],
            ),
        }

    # Notifications
    print("\nNotification channels:")
    existing_notifications = existing.get("notifications", {})
    enable_telegram = _yes_no(
        "Enable Telegram notifications?",
        default=bool(existing_notifications.get("useTelegram", False)),
    )
    enable_email = _yes_no(
        "Enable email notifications?",
        default=bool(existing_notifications.get("useEmail", False)),
    )
    
    # Platform-appropriate local notifications
    current_os = platform.system()
    if current_os == "Darwin":
        local_prompt = "Enable macOS local notifications?"
    elif current_os == "Windows":
        local_prompt = "Enable Windows local notifications?"
    else:
        local_prompt = "Enable local notifications?"
    enable_local = _yes_no(local_prompt, default=(current_os in ("Darwin", "Windows")))

    include_screenshot_telegram = bool(
        existing_notifications.get("includeScreenshotInTelegram", False)
    )
    if enable_telegram:
        include_screenshot_telegram = _yes_no(
            "Include a screenshot in Telegram notifications?",
            default=include_screenshot_telegram,
        )

    telegram = existing.get("telegram", {}) if enable_telegram else {}
    email = existing.get("email", {}) if enable_email else {}

    if enable_telegram:
        print("\nTelegram setup helper:")
        print("We recommend using Telegram Desktop for easier setup.")

        input(
            "  Step 1: Install and open Telegram Desktop, then log in to your account. "
            "Press Enter here once you are logged in..."
        )

        print("\n  Step 2: In Telegram, start a chat with @BotFather.")
        print("          Send /newbot, then choose:")
        print("            - A bot name, e.g. 'AI Task Watcher'")
        print("            - A bot username, e.g. 'ai_task_watcher_bot'")
        input("  Press Enter once BotFather has created the bot and shown you the HTTP API token...")

        default_token = telegram.get("botToken", "")
        print("\n  BotFather will show a line like 'Use this token to access the HTTP API: <TOKEN>'.")
        print("  Step 3 expects exactly that HTTP API token string. Keep it private – it controls your bot.")
        print("  This tool stores it only in your local config.txt and uses it solely to call Telegram's API ")
        print("  to send you notifications; it is not uploaded anywhere else.")

        bot_token_prompt = f"  Step 3: Paste your HTTP API token from BotFather [{default_token}]: "
        bot_token = input(bot_token_prompt).strip() or default_token
        telegram["botToken"] = bot_token

        print("\n  Step 4: In Telegram, open a chat with your new bot.")
        print("          Easiest is to click the t.me/<bot-username> link BotFather showed (e.g. t.me/ai_task_watcher_bot),")
        print("          which will open a chat with the bot, then send a short message like 'hi'.")
        input("  Press Enter once you have sent a message to your bot...")

        print("\n  Step 5: In a browser, open this URL (you can Cmd+Click it in many terminals):")
        print(f"          https://api.telegram.org/bot{bot_token}/getUpdates")
        print("          In the JSON response, look for 'chat': { 'id': ... } – that 'id' is your chat ID.")
        print("          If you only see an empty 'result': [] or no chat id yet, send another message to your bot and")
        print("          refresh the page until a 'chat': { 'id': ... } entry appears.")

        default_chat = telegram.get("chatID", "")
        chat_prompt = f"  Step 6: Paste your chat ID [{default_chat}]: "
        telegram["chatID"] = input(chat_prompt).strip() or default_chat

    if enable_email:
        print("\nEmail setup (you can leave fields empty to configure later):")
        email["smtp_server"] = input(f"  smtp_server [{email.get('smtp_server', '')}]: ").strip() or email.get("smtp_server", "")
        email["smtp_port"] = input(f"  smtp_port [{email.get('smtp_port', '465')}]: ").strip() or email.get("smtp_port", "465")
        email["mail"] = input(f"  sender mail address [{email.get('mail', '')}]: ").strip() or email.get("mail", "")
        email["password"] = input(f"  sender password [{email.get('password', '')}]: ").strip() or email.get("password", "")
        email["receiver"] = input(f"  receiver mail address [{email.get('receiver', '')}]: ").strip() or email.get("receiver", "")

    notifications = {
        "useTelegram": bool(enable_telegram),
        "useEmail": bool(enable_email),
        "useLocalNotifications": bool(enable_local),
        "includeScreenshotInTelegram": bool(include_screenshot_telegram),
    }

    # Preserve any existing regions
    regions = existing.get("regions", {})

    cfg: Dict[str, Any] = {
        "monitor": monitor,
        "monitorChange": monitor_change,
        "telegram": telegram,
        "email": email,
        "notifications": notifications,
        "regions": regions,
    }
    return cfg


def run_interactive() -> None:
    # Mirror ConfigLoader base_dir resolution: three levels up from this file
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_dir = os.path.join(project_root, "config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.txt")

    existing: Dict[str, Any] = {}
    if os.path.exists(config_path):
        try:
            # Use utf-8-sig to tolerate a UTF-8 BOM written by external tools
            with open(config_path, "r", encoding="utf-8-sig") as f:
                existing = json.load(f)
        except Exception:
            print(f"Existing config at {config_path} could not be parsed; starting from defaults.")
            existing = {}

        print(f"Existing config found at: {config_path}")
        choice = input("[K]eep as is, [R]erun guided setup, or [E]dit manually? [k/r/e]: ").strip().lower() or "k"
        if choice.startswith("k"):
            print("Keeping existing config unchanged.")
            return
        if choice.startswith("e"):
            if platform.system() == "Darwin":
                os.system(f'open "{config_path}"')
            elif platform.system() == "Windows":
                os.system(f'notepad "{config_path}"')
            else:
                print(f"Please edit the config manually at: {config_path}")
            return
        # If 'r' or anything else: continue to guided setup and overwrite

    new_cfg = _build_config_interactive(existing)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(new_cfg, f, indent=2)

    print(f"\nConfig written to {config_path}")
    print("You can rerun the guided setup anytime using 'python main.py setup-config' or edit the file directly.")
