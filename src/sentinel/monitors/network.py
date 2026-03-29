"""
Network Monitor — watches outbound connections from watched apps.

How it works:
- Uses psutil to get all network connections (like lsof -i but faster)
- Filters for connections from apps we care about (Claude, Perplexity, etc.)
- Sends each destination to the intel engine for classification
- Flags UNKNOWN destinations as RED, telemetry as YELLOW

This is what would have caught Statsig session recording traffic
and the multiple Anthropic connections we found earlier.
"""

import psutil
from sentinel.alerts import AlertManager, Severity
from sentinel.intel import IntelEngine
from sentinel.config import WATCHED_APPS


class NetworkMonitor:
    """Monitors outbound network connections from watched applications."""

    def __init__(self, alerts: AlertManager, intel: IntelEngine):
        self.alerts = alerts
        self.intel = intel
        # Track connections we've already reported
        self._reported: set[str] = set()

    def scan(self):
        """
        Scan all network connections for watched apps.
        Called every scan cycle by the main daemon.
        """
        # Get all processes and their connections
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = proc.info["name"] or ""

                # Only watch apps we care about
                if not self._is_watched(name):
                    continue

                connections = proc.net_connections()
                for conn in connections:
                    self._analyze_connection(name, proc.info["pid"], conn)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def _is_watched(self, process_name: str) -> bool:
        """Check if this process is in our watch list."""
        name_lower = process_name.lower()
        for watched in WATCHED_APPS:
            if watched.lower() in name_lower:
                return True
        return False

    def _analyze_connection(self, app_name: str, pid: int, conn):
        """Analyze a single network connection."""
        # Only care about established outbound connections
        if conn.status != "ESTABLISHED":
            return

        # Must have a remote address
        if not conn.raddr:
            return

        remote_ip = conn.raddr.ip
        remote_port = conn.raddr.port

        # Skip local connections
        if remote_ip.startswith(("127.", "::1", "fe80")):
            return

        # Create a unique key for this connection
        conn_key = f"{app_name}:{remote_ip}:{remote_port}"

        # Analyze the destination
        dest = self.intel.analyze(remote_ip, remote_port, app_name)
        is_new = self.intel.is_new_destination(remote_ip, remote_port)

        # Only report each unique connection once per session
        if conn_key in self._reported:
            return
        self._reported.add(conn_key)

        summary = self.intel.get_summary(dest)

        if dest.classification == "UNKNOWN":
            # Unknown destination — could be exfiltration
            severity = Severity.RED if is_new else Severity.YELLOW
            self.alerts.alert(
                severity,
                f"{app_name} (PID {pid}) → UNKNOWN destination",
                f"{summary}",
                source="network",
            )
        elif dest.classification == "TELEMETRY":
            self.alerts.yellow(
                f"{app_name} (PID {pid}) → telemetry/analytics",
                f"{summary}",
                source="network",
            )
        elif dest.classification == "KNOWN_API":
            # Identified API — still flagged YELLOW. No free passes.
            self.alerts.yellow(
                f"{app_name} (PID {pid}) → {dest.organization or dest.hostname}",
                f"{summary}",
                source="network",
            )

    def get_active_connections_summary(self) -> list[str]:
        """Get a summary of all currently active watched connections."""
        summaries = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = proc.info["name"] or ""
                if not self._is_watched(name):
                    continue

                for conn in proc.net_connections():
                    if conn.status != "ESTABLISHED" or not conn.raddr:
                        continue
                    if conn.raddr.ip.startswith(("127.", "::1", "fe80")):
                        continue

                    dest = self.intel.analyze(conn.raddr.ip, conn.raddr.port)
                    summaries.append(
                        f"  {name} (PID {proc.info['pid']}) → {self.intel.get_summary(dest)}"
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return summaries
