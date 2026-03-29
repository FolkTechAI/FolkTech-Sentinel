"""
TCC Monitor — watches macOS privacy permission changes.

TCC (Transparency, Consent, and Control) is macOS's permission system.
The TCC database stores which apps have been granted Screen Recording,
Camera, Microphone, Accessibility, and other sensitive permissions.

This monitor:
1. On first run, snapshots all current permissions
2. On subsequent runs, detects any NEW permissions granted
3. Alerts when an app gets Screen Recording or other sensitive access

This is what would have caught Claude.app or any other app silently
getting Screen Recording permission.

Note: Reading the system TCC database requires Full Disk Access.
The user-level database is readable without special permissions.
"""

import sqlite3
import os
import platform
from dataclasses import dataclass
from typing import Optional

from sentinel.alerts import AlertManager, Severity
from sentinel.config import TCC_WATCHED_SERVICES, TCC_DB_SYSTEM, TCC_DB_USER

IS_MACOS = platform.system() == "Darwin"


# Human-readable names for TCC services
SERVICE_NAMES = {
    "kTCCServiceScreenCapture": "Screen Recording",
    "kTCCServiceAccessibility": "Accessibility",
    "kTCCServiceListenEvent": "Input Monitoring",
    "kTCCServiceCamera": "Camera",
    "kTCCServiceMicrophone": "Microphone",
}

# auth_value meanings in TCC database
AUTH_VALUES = {
    0: "DENIED",
    1: "UNKNOWN",
    2: "ALLOWED",
    3: "LIMITED",
}


@dataclass
class TCCEntry:
    """A single TCC permission entry."""
    client: str          # App bundle ID (e.g., "com.anthropic.claude")
    service: str         # TCC service (e.g., "kTCCServiceScreenCapture")
    auth_value: int      # 0=denied, 2=allowed
    auth_reason: int     # Why it was granted


class TCCMonitor:
    """Monitors macOS TCC database for permission changes."""

    def __init__(self, alerts: AlertManager):
        self.alerts = alerts
        # Snapshot of known permissions: set of "client:service" strings
        self._known_permissions: set[str] = set()
        self._initialized = False

    def scan(self):
        """
        Scan TCC databases for permission changes.
        Called every scan cycle by the main daemon.
        Skips gracefully on Windows/Linux (no TCC on those platforms).
        """
        if not IS_MACOS:
            return
        current_permissions = self._read_tcc_permissions()

        if not self._initialized:
            # First run — establish baseline
            self._known_permissions = {
                f"{e.client}:{e.service}" for e in current_permissions
            }
            self._initialized = True

            # Report what we found
            screen_recording_apps = [
                e for e in current_permissions
                if e.service == "kTCCServiceScreenCapture" and e.auth_value == 2
            ]
            if screen_recording_apps:
                app_list = ", ".join(e.client for e in screen_recording_apps)
                self.alerts.yellow(
                    f"Apps with Screen Recording permission: {len(screen_recording_apps)}",
                    f"{app_list}",
                    source="tcc",
                )
            return

        # Check for NEW permissions
        for entry in current_permissions:
            key = f"{entry.client}:{entry.service}"
            if key not in self._known_permissions and entry.auth_value == 2:
                # New permission granted!
                service_name = SERVICE_NAMES.get(entry.service, entry.service)
                self.alerts.red(
                    f"NEW permission granted: {entry.client}",
                    f"{service_name} access was just granted to {entry.client}",
                    source="tcc",
                )
                self._known_permissions.add(key)

    def _read_tcc_permissions(self) -> list[TCCEntry]:
        """Read permissions from TCC databases."""
        entries = []

        for db_path in [TCC_DB_SYSTEM, TCC_DB_USER]:
            if not os.path.exists(db_path):
                continue

            try:
                # Connect read-only to avoid any modification
                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                cursor = conn.cursor()

                # Build service filter
                placeholders = ",".join("?" for _ in TCC_WATCHED_SERVICES)
                query = f"""
                    SELECT client, service, auth_value, auth_reason
                    FROM access
                    WHERE service IN ({placeholders})
                """
                cursor.execute(query, TCC_WATCHED_SERVICES)

                for row in cursor.fetchall():
                    entries.append(TCCEntry(
                        client=row[0],
                        service=row[1],
                        auth_value=row[2],
                        auth_reason=row[3],
                    ))

                conn.close()
            except (sqlite3.OperationalError, sqlite3.DatabaseError):
                # Can't read this database — likely SIP protected
                # The system DB requires Full Disk Access
                continue

        return entries

    def get_permissions_report(self) -> list[str]:
        """Get a human-readable report of all watched permissions."""
        if not IS_MACOS:
            return ["  (TCC permission monitoring is macOS only)"]
        entries = self._read_tcc_permissions()
        lines = []

        for service in TCC_WATCHED_SERVICES:
            service_name = SERVICE_NAMES.get(service, service)
            service_entries = [e for e in entries if e.service == service]
            allowed = [e for e in service_entries if e.auth_value == 2]

            if allowed:
                lines.append(f"\n  {service_name}:")
                for e in allowed:
                    lines.append(f"    ✓ {e.client}")

        return lines
