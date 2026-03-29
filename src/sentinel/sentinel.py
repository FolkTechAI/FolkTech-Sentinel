#!/usr/bin/env python3
"""
FolkTech Sentinel — Local Security Monitor

A daemon that watches your machine for:
- Unauthorized screen capture and video recording
- Suspicious outbound network connections
- Data exfiltration to unknown destinations
- macOS permission changes (TCC)

Usage:
    python sentinel.py              # Run the daemon
    python sentinel.py --scan       # Run a single scan and exit
    python sentinel.py --baseline   # Establish a network baseline
    python sentinel.py --report     # Show current permissions and connections
"""

import sys
import os
import time
import signal
import argparse
from datetime import datetime

from sentinel.alerts import AlertManager, Severity
from sentinel.intel import IntelEngine
from sentinel.config import SCAN_INTERVAL, LOG_DIR
from sentinel.monitors.process import ProcessMonitor
from sentinel.monitors.network import NetworkMonitor
from sentinel.monitors.tcc import TCCMonitor


# ─────────────────────────────────────────────────────────────────────
# ASCII Banner
# ─────────────────────────────────────────────────────────────────────

BANNER = """
\033[96m
  ____            _   _            _
 / ___|  ___ _ __ | |_(_)_ __   ___| |
 \\___ \\ / _ \\ '_ \\| __| | '_ \\ / _ \\ |
  ___) |  __/ | | | |_| | | | |  __/ |
 |____/ \\___|_| |_|\\__|_|_| |_|\\___|_|

\033[0m FolkTech Security Monitor v1.0
 Watching for unauthorized access...
"""


class Sentinel:
    """Main daemon that orchestrates all monitors."""

    def __init__(self):
        self.alerts = AlertManager(log_dir=LOG_DIR)
        self.intel = IntelEngine()
        self.process_monitor = ProcessMonitor(self.alerts)
        self.network_monitor = NetworkMonitor(self.alerts, self.intel)
        self.tcc_monitor = TCCMonitor(self.alerts)
        self._running = False
        self._scan_count = 0

    def run_single_scan(self):
        """Run all monitors once."""
        self._scan_count += 1

        # Process monitor — check for screen capture, dangerous flags
        self.process_monitor.scan()

        # Network monitor — check outbound connections
        self.network_monitor.scan()

        # TCC monitor — check permission changes
        self.tcc_monitor.scan()

        # Periodic cleanup of stale PID tracking
        if self._scan_count % 12 == 0:  # Every ~60s at 5s interval
            self.process_monitor.cleanup_stale_pids()

    def run_daemon(self):
        """Run continuously, scanning at the configured interval."""
        print(BANNER)
        print(f" Scan interval: {SCAN_INTERVAL}s")
        print(f" Log directory: {LOG_DIR}")
        print(f" Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" Press Ctrl+C to stop\n")

        self._running = True

        # Handle graceful shutdown
        def shutdown(signum, frame):
            print(f"\n\033[93mShutting down Sentinel...\033[0m")
            self._running = False

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        # Initial scan
        self.alerts.green("Sentinel started", "Running initial scan...", source="daemon")

        while self._running:
            try:
                self.run_single_scan()
                time.sleep(SCAN_INTERVAL)
            except Exception as e:
                self.alerts.yellow(
                    "Scan error",
                    f"Error during scan cycle: {e}",
                    source="daemon",
                )
                time.sleep(SCAN_INTERVAL)

        # Save baseline on shutdown
        self.intel.save_baseline()
        self.alerts.green("Sentinel stopped", "Baseline saved.", source="daemon")

    def establish_baseline(self):
        """Run a scan and save the results as the baseline."""
        print(BANNER)
        print(" Establishing network baseline...\n")

        # Run scans to populate intel cache
        self.run_single_scan()

        # Get connection summary
        connections = self.network_monitor.get_active_connections_summary()
        if connections:
            print("\n Current connections:")
            for line in connections:
                print(line)

        # Save baseline
        self.intel.save_baseline()
        print(f"\n\033[92mBaseline saved.\033[0m")
        print(f" Future scans will flag any NEW destinations not in this baseline.")

    def show_report(self):
        """Show current state — permissions and connections."""
        print(BANNER)

        # TCC permissions
        print("\n\033[96m── macOS Privacy Permissions ──\033[0m")
        permissions = self.tcc_monitor.get_permissions_report()
        if permissions:
            for line in permissions:
                print(line)
        else:
            print("  (Could not read TCC database — may need Full Disk Access)")

        # Active connections
        print("\n\033[96m── Active Watched Connections ──\033[0m")
        # Run a quick scan to populate data
        self.network_monitor.scan()
        connections = self.network_monitor.get_active_connections_summary()
        if connections:
            for line in connections:
                print(line)
        else:
            print("  No watched apps have active connections")

        # Process scan
        print("\n\033[96m── Process Scan ──\033[0m")
        self.process_monitor.scan()
        print("  Process scan complete (alerts shown above if any found)")

        print()


def main():
    parser = argparse.ArgumentParser(
        description="FolkTech Sentinel — Local Security Monitor"
    )
    parser.add_argument(
        "--scan", action="store_true",
        help="Run a single scan and exit"
    )
    parser.add_argument(
        "--baseline", action="store_true",
        help="Establish a network baseline"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Show current permissions and connections"
    )

    args = parser.parse_args()
    sentinel = Sentinel()

    if args.scan:
        sentinel.run_single_scan()
    elif args.baseline:
        sentinel.establish_baseline()
    elif args.report:
        sentinel.show_report()
    else:
        sentinel.run_daemon()


if __name__ == "__main__":
    main()
