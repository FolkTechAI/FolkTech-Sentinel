"""
Alert system — how Sentinel tells you something is wrong.

Cross-platform: works on macOS, Windows, and Linux.

Two channels:
1. Native OS notifications (macOS banners, Windows toast, Linux notify-send)
2. Log file with timestamps and severity levels

Severity levels:
  RED    — Active threat: screen capture, audio capture, unknown data exfiltration
  YELLOW — Suspicious: new permissions granted, known telemetry/analytics
  GREEN  — Informational: baseline established, normal scan complete
"""

import os
import sys
import subprocess
import logging
import platform
from datetime import datetime
from enum import Enum
from pathlib import Path


PLATFORM = platform.system()  # "Darwin", "Windows", "Linux"


class Severity(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


# Map severity to terminal colors for console output
SEVERITY_COLORS = {
    Severity.RED: "\033[91m",     # bright red
    Severity.YELLOW: "\033[93m",  # bright yellow
    Severity.GREEN: "\033[92m",   # bright green
}
COLOR_RESET = "\033[0m"

SEVERITY_ICONS = {
    Severity.RED: "RED ALERT",
    Severity.YELLOW: "WARNING",
    Severity.GREEN: "OK",
}


class AlertManager:
    """Manages all alert output — notifications, console, and log file."""

    def __init__(self, log_dir: str = None):
        # Set up log directory — platform-aware default
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up file logger
        log_file = self.log_dir / f"sentinel-{datetime.now().strftime('%Y-%m-%d')}.log"
        self.logger = logging.getLogger("sentinel")
        self.logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers if AlertManager is re-created
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self.logger.addHandler(file_handler)

        # Track alerts to avoid spamming the same notification
        self._recent_alerts: dict[str, datetime] = {}
        self._cooldown_seconds = 60  # Don't repeat same alert within 60s

    def alert(self, severity: Severity, title: str, message: str, source: str = ""):
        """Send an alert through all channels."""
        # Deduplicate — don't spam the same alert
        alert_key = f"{severity.value}:{title}"
        now = datetime.now()
        if alert_key in self._recent_alerts:
            elapsed = (now - self._recent_alerts[alert_key]).total_seconds()
            if elapsed < self._cooldown_seconds:
                return
        self._recent_alerts[alert_key] = now

        # Format the log line
        source_tag = f"[{source}] " if source else ""
        log_line = f"[{severity.value}] {source_tag}{title} — {message}"

        # 1. Log to file (always)
        self.logger.info(log_line)

        # 2. Print to console with color
        color = SEVERITY_COLORS[severity]
        print(f"{color}[{severity.value}]{COLOR_RESET} {source_tag}{title}")
        if severity in (Severity.RED, Severity.YELLOW):
            print(f"         {message}")

        # 3. OS notification for RED and YELLOW
        if severity in (Severity.RED, Severity.YELLOW):
            self._send_notification(severity, title, message)

    def _send_notification(self, severity: Severity, title: str, message: str):
        """Send a native OS notification. Adapts to macOS, Windows, and Linux."""
        icon = SEVERITY_ICONS[severity]
        try:
            if PLATFORM == "Darwin":
                self._notify_macos(icon, title, message)
            elif PLATFORM == "Windows":
                self._notify_windows(icon, title, message)
            elif PLATFORM == "Linux":
                self._notify_linux(icon, title, message)
        except Exception:
            pass  # Never let notification failure crash the daemon

    def _notify_macos(self, icon: str, title: str, message: str):
        """macOS notification via osascript."""
        safe_title = title.replace('"', '\\"')
        safe_message = message.replace('"', '\\"')
        script = (
            f'display notification "{icon}: {safe_message}" '
            f'with title "Sentinel" '
            f'subtitle "{safe_title}" '
            f'sound name "Basso"'
        )
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)

    def _notify_windows(self, icon: str, title: str, message: str):
        """Windows notification via plyer (cross-platform notification library)."""
        try:
            from plyer import notification
            notification.notify(
                title=f"Sentinel — {icon}",
                message=f"{title}: {message[:200]}",
                app_name="Sentinel",
                timeout=10,
            )
        except ImportError:
            pass  # plyer not installed — notifications won't work, but logs still capture everything

    def _notify_linux(self, icon: str, title: str, message: str):
        """Linux notification via notify-send."""
        urgency = "critical" if icon == "RED ALERT" else "normal"
        subprocess.run(
            ["notify-send", "-u", urgency, f"Sentinel: {title}", message[:200]],
            capture_output=True, timeout=5,
        )

    def red(self, title: str, message: str, source: str = ""):
        self.alert(Severity.RED, title, message, source)

    def yellow(self, title: str, message: str, source: str = ""):
        self.alert(Severity.YELLOW, title, message, source)

    def green(self, title: str, message: str, source: str = ""):
        self.alert(Severity.GREEN, title, message, source)
