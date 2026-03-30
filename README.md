# FolkTech Sentinel

A read-only, local-only visibility tool that shows you what your operating system already knows about how desktop applications use screen, audio, and network access — presented in a clear, structured way.

> **⚠️ Important Notice**
>
> FolkTech Sentinel is for use **only on computers you personally own and fully control.** Do not install or run it on shared, workplace, family, or third-party devices without explicit, informed consent from every person who uses that device. You are solely responsible for complying with all applicable laws in your jurisdiction. This is an educational and personal-use project provided as-is without warranty. See [LICENSE](LICENSE).

---

## What Is FolkTech Sentinel?

Sentinel is a lightweight Python utility that reads publicly available system information — the process table, active network connections, and (on macOS) the operating system's own permission database — and presents it to you in a structured, human-readable format.

It runs entirely on your machine. It has no cloud backend, no telemetry, and no analytics. It does not modify, block, or intercept anything. It simply surfaces information your OS already tracks but does not make easily visible.

---

## Why It Exists

AI desktop applications — including Claude, Perplexity, ChatGPT Desktop, Cursor, and others — typically request broad system permissions during setup: Screen Recording, Accessibility, Camera, and Microphone. Once granted, these permissions persist and can be exercised by background processes without any visible indicator.

Most users grant these permissions during onboarding and never revisit them. Sentinel was built to make that information accessible again — so you can periodically review which applications hold sensitive permissions, which processes are exercising them, and where those applications are connecting.

It is a **personal awareness utility**, not a security product.

---

## Key Features

| Capability | Description |
|-----------|-------------|
| **Process Visibility** | Lists running processes that match known screen-capture, video-recording, or audio-input API patterns across macOS, Windows, and Linux. |
| **Network Visibility** | Shows active outbound connections from applications you choose to watch. Optionally resolves destination IPs to hostnames and organizations via reverse DNS and WHOIS. |
| **Permission Reporting** (macOS) | Reads the macOS TCC (Transparency, Consent, and Control) database to list which applications currently hold Screen Recording, Camera, Microphone, Accessibility, and Input Monitoring permissions. |
| **Baseline Comparison** | Saves a snapshot of observed network connections. Subsequent runs note any destinations not present in the baseline. |
| **Cross-Platform** | Process and network visibility work on macOS, Windows, and Linux. Permission reporting is macOS-specific. |
| **Auto-Start** | Optional installer configures your OS to run Sentinel at login — LaunchAgent (macOS), Task Scheduler (Windows), or systemd (Linux). |

### Status Levels

Sentinel categorizes observations into three levels for readability:

| Level | Meaning | Output |
|-------|---------|--------|
| **High** | A process is actively exercising screen or audio capture APIs, or a connection was observed to a destination not yet identified | Desktop notification + log file |
| **Notable** | A connection to a recognized analytics or telemetry service was observed, or a permission change was noted | Desktop notification + log file |
| **Info** | Routine — scan completed, baseline saved | Log file only |

---

## What This Tool Does NOT Do

- **Does not record your screen or audio.** It reads process metadata to note when other applications appear to be doing so. It never captures content.
- **Does not block, intercept, or modify any network traffic.** It reads connection metadata (IP addresses, ports, process names) from the OS and reports what it finds.
- **Does not transmit any of your data.** There is no analytics, no telemetry, no cloud component. The only outbound requests are optional WHOIS lookups used to identify IP address ownership.
- **Does not require root or administrator privileges.** It runs under your normal user account.
- **Does not function as a firewall, antivirus, or endpoint protection tool.** It is a read-only visibility and awareness utility.
- **Does not make security guarantees.** It surfaces OS-level information to help you make informed decisions. It does not certify that any application is safe or unsafe.

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
- **WHOIS rate limits.** Lookups are cached locally, but scanning many new IPs quickly may trigger rate limiting from WHOIS servers.
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

MIT License. See [LICENSE](LICENSE).

---

## Contributing

Issues, feature requests, and pull requests are welcome at [GitHub Issues](https://github.com/FolkTechAI/FolkTech-Sentinel/issues).

If you encounter a process pattern or network destination that Sentinel should recognize, please open an issue or submit a PR updating `config.py`.

---

[PyPI](https://pypi.org/project/folktech-sentinel/) · [GitHub](https://github.com/FolkTechAI/FolkTech-Sentinel) · [Issues](https://github.com/FolkTechAI/FolkTech-Sentinel/issues)

Built by [FolkTech AI](https://github.com/FolkTechAI)
