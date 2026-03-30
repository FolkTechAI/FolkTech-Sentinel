#!/usr/bin/env python3
"""
Sentinel Installer — sets up everything and configures auto-start.

Works on macOS, Windows, and Linux.

Usage:
    python install.py           # Install and configure auto-start
    python install.py --remove  # Remove auto-start (keeps Sentinel files)
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path


PLATFORM = platform.system()
SENTINEL_DIR = Path(os.path.dirname(os.path.abspath(__file__)))


def get_python_path() -> str:
    """Get the Python that has sentinel installed.

    Prefers the currently running interpreter (which is the one
    that has the package installed, whether via pip or editable install).
    Falls back to a local venv for from-source installs.
    """
    # If we're running inside a venv/pip install, use that Python
    # (it already has sentinel installed)
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        return sys.executable

    # Fall back to local venv for from-source installs
    if PLATFORM == "Windows":
        venv_python = SENTINEL_DIR / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = SENTINEL_DIR / "venv" / "bin" / "python3"

    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def setup_venv():
    """Create virtual environment and install dependencies.

    Only needed for from-source installs. When installed via pip,
    dependencies are already satisfied and this step is skipped.
    """
    requirements_file = SENTINEL_DIR / "requirements.txt"

    # If no requirements.txt, we're running as a pip-installed package.
    # Dependencies are already installed — nothing to do.
    if not requirements_file.exists():
        print("Dependencies already satisfied (pip-installed package).")
        return

    venv_dir = SENTINEL_DIR / "venv"

    if not venv_dir.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    python = get_python_path()
    print("Installing dependencies...")
    subprocess.run(
        [python, "-m", "pip", "install", "-r", str(requirements_file), "-q"],
        check=True,
    )
    print("Dependencies installed.")


# ─────────────────────────────────────────────────────────────────────
# macOS — LaunchAgent
# ─────────────────────────────────────────────────────────────────────

MACOS_PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / "com.folktech.sentinel.plist"

MACOS_PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.folktech.sentinel</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>sentinel.sentinel</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{logdir}/sentinel-daemon.out</string>
    <key>StandardErrorPath</key>
    <string>{logdir}/sentinel-daemon.err</string>
</dict>
</plist>
"""


def install_macos():
    """Install macOS LaunchAgent for auto-start."""
    python = get_python_path()
    log_dir = SENTINEL_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    plist_content = MACOS_PLIST_TEMPLATE.format(
        python=python,
        logdir=str(log_dir),
    )

    MACOS_PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MACOS_PLIST_PATH.write_text(plist_content)

    # Load the agent
    subprocess.run(["launchctl", "load", str(MACOS_PLIST_PATH)], capture_output=True)
    print(f"macOS LaunchAgent installed: {MACOS_PLIST_PATH}")
    print("Sentinel will start automatically at login and restart if it crashes.")


def remove_macos():
    """Remove macOS LaunchAgent."""
    if MACOS_PLIST_PATH.exists():
        subprocess.run(["launchctl", "unload", str(MACOS_PLIST_PATH)], capture_output=True)
        MACOS_PLIST_PATH.unlink()
        print("macOS LaunchAgent removed.")
    else:
        print("No LaunchAgent found.")


# ─────────────────────────────────────────────────────────────────────
# Windows — Task Scheduler
# ─────────────────────────────────────────────────────────────────────

def install_windows():
    """Install Windows Task Scheduler task for auto-start."""
    python = get_python_path()

    # Create a scheduled task that runs at logon
    result = subprocess.run(
        [
            "schtasks", "/create",
            "/tn", "FolkTechSentinel",
            "/tr", f'"{python}" -m sentinel.sentinel',
            "/sc", "onlogon",
            "/rl", "highest",
            "/f",  # Force overwrite if exists
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("Windows Task Scheduler task created: FolkTechSentinel")
        print("Sentinel will start automatically at login.")

        # Also start it now
        subprocess.run(
            ["schtasks", "/run", "/tn", "FolkTechSentinel"],
            capture_output=True,
        )
        print("Sentinel started.")
    else:
        print(f"Failed to create task: {result.stderr}")
        print("You may need to run this as Administrator.")


def remove_windows():
    """Remove Windows Task Scheduler task."""
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", "FolkTechSentinel", "/f"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("Windows scheduled task removed.")
    else:
        print("No scheduled task found.")


# ─────────────────────────────────────────────────────────────────────
# Linux — systemd user service
# ─────────────────────────────────────────────────────────────────────

LINUX_SERVICE_DIR = Path.home() / ".config" / "systemd" / "user"
LINUX_SERVICE_PATH = LINUX_SERVICE_DIR / "sentinel.service"

LINUX_SERVICE_TEMPLATE = """[Unit]
Description=FolkTech Sentinel — Local Visibility Tool
After=network.target

[Service]
Type=simple
ExecStart={python} -m sentinel.sentinel
Restart=always
RestartSec=10
StandardOutput=append:{logdir}/sentinel-daemon.out
StandardError=append:{logdir}/sentinel-daemon.err

[Install]
WantedBy=default.target
"""


def install_linux():
    """Install systemd user service for auto-start."""
    python = get_python_path()
    log_dir = SENTINEL_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    service_content = LINUX_SERVICE_TEMPLATE.format(
        python=python,
        logdir=str(log_dir),
    )

    LINUX_SERVICE_DIR.mkdir(parents=True, exist_ok=True)
    LINUX_SERVICE_PATH.write_text(service_content)

    # Enable and start the service
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    subprocess.run(["systemctl", "--user", "enable", "sentinel.service"], capture_output=True)
    subprocess.run(["systemctl", "--user", "start", "sentinel.service"], capture_output=True)

    print(f"systemd user service installed: {LINUX_SERVICE_PATH}")
    print("Sentinel will start automatically at login and restart if it crashes.")


def remove_linux():
    """Remove systemd user service."""
    subprocess.run(["systemctl", "--user", "stop", "sentinel.service"], capture_output=True)
    subprocess.run(["systemctl", "--user", "disable", "sentinel.service"], capture_output=True)
    if LINUX_SERVICE_PATH.exists():
        LINUX_SERVICE_PATH.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        print("systemd service removed.")
    else:
        print("No systemd service found.")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sentinel Installer")
    parser.add_argument("--remove", action="store_true", help="Remove auto-start")
    args = parser.parse_args()

    print(f"\n  FolkTech Sentinel Installer")
    print(f"  Platform: {PLATFORM}")
    print(f"  Directory: {SENTINEL_DIR}\n")

    if args.remove:
        if PLATFORM == "Darwin":
            remove_macos()
        elif PLATFORM == "Windows":
            remove_windows()
        elif PLATFORM == "Linux":
            remove_linux()
        print("\nSentinel auto-start removed. Files are still in place.")
        return

    # Step 1: Set up venv and deps
    setup_venv()

    # Step 2: Create logs directory
    (SENTINEL_DIR / "logs").mkdir(parents=True, exist_ok=True)

    # Step 3: Install platform-specific auto-start
    print()
    if PLATFORM == "Darwin":
        install_macos()
    elif PLATFORM == "Windows":
        install_windows()
    elif PLATFORM == "Linux":
        install_linux()
    else:
        print(f"Unknown platform: {PLATFORM}. Auto-start not configured.")
        print("You can still run Sentinel manually: sentinel")

    print(f"\nInstallation complete.")
    print(f"Logs: {SENTINEL_DIR / 'logs'}")
    print(f"\nCommands:")
    print(f"  sentinel              # Run in foreground")
    print(f"  sentinel --report     # Show current status")
    print(f"  sentinel --baseline   # Establish baseline")
    print(f"  sentinel-install --remove  # Remove auto-start")


if __name__ == "__main__":
    main()
