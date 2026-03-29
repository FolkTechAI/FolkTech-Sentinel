"""
Process Monitor — watches for screen capture, audio capture, and suspicious activity.

How it works:
- Every scan cycle, it walks the entire process table
- For each process, it checks the command line arguments against known patterns
- If a process matches screen capture or audio capture patterns, it's flagged
- If a process has dangerous flags (like --allow-dangerously-skip-permissions), it's flagged

This is what would have caught the Claude desktop app spawning a background
agent with --allowedTools mcp__computer-use before we found it manually.
"""

import psutil
from alerts import AlertManager, Severity
from config import (
    SCREEN_CAPTURE_PATTERNS,
    AUDIO_CAPTURE_PATTERNS,
    SUSPICIOUS_PROCESS_NAMES,
    DANGEROUS_FLAGS,
)


class ProcessMonitor:
    """Monitors running processes for screen capture and suspicious activity."""

    def __init__(self, alerts: AlertManager):
        self.alerts = alerts
        # Track PIDs we've already alerted on (avoid repeats within session)
        self._alerted_pids: dict[int, str] = {}

    def scan(self):
        """
        Scan all running processes for suspicious activity.
        Called every scan cycle by the main daemon.
        """
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                pid = proc.info["pid"]
                name = proc.info["name"] or ""
                cmdline = proc.info["cmdline"] or []
                cmdline_str = " ".join(cmdline)

                # Skip our own process
                if "sentinel" in name.lower():
                    continue

                # Check for screen capture patterns in command line
                self._check_screen_capture(pid, name, cmdline_str)

                # Check for audio capture patterns in command line
                self._check_audio_capture(pid, name, cmdline_str)

                # Check for dangerous flags
                self._check_dangerous_flags(pid, name, cmdline_str)

                # Check for suspicious process names
                self._check_suspicious_names(pid, name)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def _check_screen_capture(self, pid: int, name: str, cmdline: str):
        """Check if a process is using screen capture APIs."""
        for pattern in SCREEN_CAPTURE_PATTERNS:
            if pattern.lower() in cmdline.lower():
                alert_key = f"screencap:{pid}:{pattern}"
                if alert_key in self._alerted_pids:
                    return

                self._alerted_pids[alert_key] = pattern
                self.alerts.red(
                    f"Screen capture detected: {name} (PID {pid})",
                    f"Pattern matched: '{pattern}' in command: {cmdline[:200]}",
                    source="process",
                )
                return  # One alert per process per scan

    def _check_audio_capture(self, pid: int, name: str, cmdline: str):
        """Check if a process is using audio/microphone capture APIs."""
        for pattern in AUDIO_CAPTURE_PATTERNS:
            if pattern.lower() in cmdline.lower():
                alert_key = f"audiocap:{pid}:{pattern}"
                if alert_key in self._alerted_pids:
                    return

                self._alerted_pids[alert_key] = pattern
                self.alerts.red(
                    f"Audio capture detected: {name} (PID {pid})",
                    f"Pattern matched: '{pattern}' in command: {cmdline[:200]}",
                    source="process",
                )
                return

    def _check_dangerous_flags(self, pid: int, name: str, cmdline: str):
        """Check if a process was launched with dangerous permission flags."""
        for flag in DANGEROUS_FLAGS:
            if flag.lower() in cmdline.lower():
                alert_key = f"danger:{pid}:{flag}"
                if alert_key in self._alerted_pids:
                    return

                self._alerted_pids[alert_key] = flag
                self.alerts.red(
                    f"Dangerous permissions: {name} (PID {pid})",
                    f"Flag: '{flag}' — This process bypasses normal permission checks",
                    source="process",
                )
                return

    def _check_suspicious_names(self, pid: int, name: str):
        """Check if a process name matches known suspicious patterns."""
        for pattern in SUSPICIOUS_PROCESS_NAMES:
            if pattern.lower() in name.lower():
                alert_key = f"suspname:{pid}:{pattern}"
                if alert_key in self._alerted_pids:
                    return

                self._alerted_pids[alert_key] = pattern
                self.alerts.yellow(
                    f"Suspicious process: {name} (PID {pid})",
                    f"Matched suspicious name pattern: '{pattern}'",
                    source="process",
                )
                return

    def cleanup_stale_pids(self):
        """Remove PIDs from alert tracking if the process has exited."""
        stale = []
        for alert_key in self._alerted_pids:
            # Extract PID from key format "type:pid:pattern"
            parts = alert_key.split(":")
            if len(parts) >= 2:
                try:
                    pid = int(parts[1])
                    if not psutil.pid_exists(pid):
                        stale.append(alert_key)
                except ValueError:
                    pass

        for key in stale:
            del self._alerted_pids[key]
