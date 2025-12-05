import subprocess
from typing import Optional


class WindowsNotifier:
    """Send native Windows toast notifications via PowerShell.

    Uses PowerShell's built-in toast notification capability.
    Works on Windows 10 and later.
    """

    def __init__(self, title: str = "Task Completion Detector") -> None:
        self._title = title

    def send_notification(self, body: str, subtitle: Optional[str] = None) -> None:
        # Escape single quotes for PowerShell
        title_esc = self._title.replace("'", "''")
        body_esc = body.replace("'", "''")
        
        if subtitle:
            full_body = f"{subtitle}\n{body_esc}"
        else:
            full_body = body_esc
        
        full_body = full_body.replace("'", "''")
        
        # Use BurntToast module if available, otherwise fall back to basic notification
        ps_script = f'''
$ErrorActionPreference = 'SilentlyContinue'
if (Get-Module -ListAvailable -Name BurntToast) {{
    Import-Module BurntToast
    New-BurntToastNotification -Text '{title_esc}', '{full_body}'
}} else {{
    # Fallback using Windows.UI.Notifications
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

    $template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">{title_esc}</text>
            <text id="2">{full_body}</text>
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.Default"/>
</toast>
"@

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Task Completion Detector")
    $notifier.Show($toast)
}}
'''
        try:
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                check=False,
                capture_output=True,
            )
        except Exception:
            # Best-effort only; ignore failures.
            pass
