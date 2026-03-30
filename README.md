# FolkTech Sentinel

A read-only, local-only visibility tool that shows you what your operating system already knows about how desktop applications use screen, audio, and network access — presented in a clear, structured way.

> **⚠️ Important Notice**
>
> FolkTech Sentinel is intended **only for use on computers you personally own and fully control.**
> Do not install or run it on shared, workplace, family, or third-party devices without explicit, informed consent from every person who uses that device.
> You are solely responsible for complying with all applicable laws in your jurisdiction regarding system monitoring, privacy, and consent.
> This is an educational and personal-use project provided as-is without any warranty. See [LICENSE](LICENSE) for details.

---

## What Is FolkTech Sentinel?

Sentinel is a lightweight Python utility that reads system information already tracked by your operating system — the process table, active network connections, and (on macOS) the permission database — and presents it in a clear, human-readable format.

It runs entirely locally with no cloud component, no telemetry, and no data collection. It does not modify, block, or intercept anything on your system.

---

## Why It Exists

Modern AI desktop applications (such as Claude, Perplexity, ChatGPT Desktop, Cursor, and others) often request broad system permissions including Screen Recording, Accessibility, Camera, and Microphone access. Once granted, these permissions can be used by background processes with little ongoing visibility to the user.

Sentinel helps you periodically review which applications hold these permissions, when processes appear to be using them, and where watched applications are connecting on the network. It is a **personal awareness utility**, not a security product.

---

## Key Features

| Capability | Description |
|-----------|-------------|
| **Process Visibility** | Identifies processes matching known patterns associated with screen capture, video recording, or audio input APIs (macOS, Windows, Linux). |
| **Network Visibility** | Shows outbound network connections from applications you choose to watch. Optionally resolves IPs to hostnames and organizations via reverse DNS and WHOIS. |
| **Permission Reporting** (macOS only) | Reads the macOS TCC database to list applications that currently hold Screen Recording, Camera, Microphone, Accessibility, or Input Monitoring permissions. |
| **Baseline Comparison** | Lets you save a snapshot of observed connections for easier comparison on future runs. |
| **Cross-Platform** | Core functionality works on macOS, Windows, and Linux. Permission reporting is macOS-specific. |
| **Optional Auto-Start** | Installer can configure the tool to run at login — LaunchAgent (macOS), Task Scheduler (Windows), or systemd (Linux). |

### Observation Levels

For easier reading, Sentinel uses three simple categories:

| Level | Description | Output |
|-------|-------------|--------|
| **High** | A process is using screen or audio capture patterns, or a connection to an unidentified destination was observed | Desktop notification + log |
| **Notable** | A connection to a recognized analytics or telemetry service was observed, or a permission change was noted | Desktop notification + log |
| **Info** | Routine scan information | Log file only |

---

## What This Tool Does NOT Do

- It does **not** record your screen or audio — it only notes when other applications appear to be using related APIs.
- It does **not** block, intercept, or modify network traffic.
- It does **not** transmit any data from your machine (optional WHOIS lookups for IP identification are the only external requests).
- It does **not** require root or administrator privileges.
- It is **not** a firewall, antivirus, or security enforcement tool — it is purely a read-only visibility utility.
- It does **not** make security guarantees or certify any application as safe or unsafe. It surfaces information so you can make your own informed decisions.

---

## Installation

### From PyPI

```bash
pip install folktech-sentinel
```

This installs two commands:

| Command | Purpose |
|---------|---------|
| `sentinel` | Run the visibility tool (continuous, one-time, or report mode) |
| `sentinel-install` | Optionally configure auto-start at login |

### From Source

```bash
git clone https://github.com/FolkTechAI/FolkTech-Sentinel.git
cd FolkTech-Sentinel
python install.py
```

The source installer creates a virtual environment, installs dependencies, and optionally configures auto-start.

---

## Quick Start

```bash
# See current permissions and active connections
sentinel --report

# Save current state as your baseline
sentinel --baseline

# Run continuously (scans every 5 seconds, Ctrl+C to stop)
sentinel
```

### All Commands

| Command | Description |
|---------|-------------|
| `sentinel` | Run continuously. Press `Ctrl+C` to stop. |
| `sentinel --scan` | Run once and exit. |
| `sentinel --report` | Display current permissions and connections. |
| `sentinel --baseline` | Save current connections as your baseline. |
| `sentinel-install` | Configure auto-start at login. |
| `sentinel-install --remove` | Remove auto-start configuration. |

---

## Configuration

Edit `src/sentinel/config.py` to customize:

| Setting | Description | Default |
|---------|-------------|---------|
| `SCAN_INTERVAL` | Seconds between scan cycles | `5` |
| `WATCHED_APPS` | Applications whose network connections are reported | Claude, Perplexity, ChatGPT, Cursor, VS Code, Electron, Node |
| `SCREEN_CAPTURE_PATTERNS` | Process patterns associated with screen capture | macOS, Windows, and Linux patterns included |
| `AUDIO_CAPTURE_PATTERNS` | Process patterns associated with audio input | macOS, Windows, and Linux patterns included |
| `KNOWN_TELEMETRY` | Recognized analytics services (labeled for identification) | Statsig, Sentry, Amplitude, Mixpanel, and others |
| `KNOWN_API_ENDPOINTS` | Recognized API destinations (labeled — **never suppressed**) | Anthropic, OpenAI, GitHub, Hugging Face |

All observations are always reported. Labeling a destination helps you identify it — it does not hide or filter it.

---

## Required Permissions

### macOS

To read the TCC permission database, your terminal application may need **Full Disk Access** (System Settings → Privacy & Security → Full Disk Access).

Sentinel reads the database that records which apps hold permissions. It **does not request or exercise** Screen Recording, Camera, or Microphone access itself.

### Windows and Linux

No elevated permissions required. Process and network visibility use standard `psutil` APIs available to any user-level process.

---

## Limitations

- **Polling-based.** Sentinel reads the process table at a configurable interval (default: 5 seconds). A process that starts and exits between scans would not be observed.
- **Pattern-based.** Identification relies on known command-line strings and process names. Processes that obscure their command lines may not be recognized.
- **macOS-only permission reporting.** The TCC database is a macOS feature. Windows and Linux lack a centralized equivalent.
- **WHOIS rate limits.** Lookups are cached locally, but querying many new IPs quickly may trigger rate limiting from WHOIS servers.
- **Not a security product.** Sentinel is an awareness tool. It does not prevent, block, or remediate anything. It presents information so you can make your own decisions.

---

## Uninstall

```bash
# Remove auto-start only
sentinel-install --remove

# Full removal
pip uninstall folktech-sentinel
```

If installed from source, delete the project directory and any auto-start entry created by the installer.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contributing

Issues, feature requests, and pull requests are welcome at [GitHub Issues](https://github.com/FolkTechAI/FolkTech-Sentinel/issues).

If you encounter a process pattern or network destination that Sentinel should recognize, please open an issue or submit a PR updating `config.py`.

---

[PyPI](https://pypi.org/project/folktech-sentinel/) · [GitHub](https://github.com/FolkTechAI/FolkTech-Sentinel) · [Issues](https://github.com/FolkTechAI/FolkTech-Sentinel/issues)

Built by [FolkTech AI](https://github.com/FolkTechAI)
