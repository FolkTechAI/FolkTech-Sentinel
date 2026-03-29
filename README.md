# FolkTech Sentinel

A local-only transparency tool that helps you see when desktop applications — especially AI agents — use screen recording, audio input, or network access on your personal computer.

> **⚠️ Important Notice — Please Read Before Using**
>
> **FolkTech Sentinel is intended exclusively for use on devices you personally own and fully control.**
>
> - This tool requires elevated system permissions to function. On macOS, your terminal emulator may need **Full Disk Access** to read the system's permission database. These are the same permissions used by legitimate screen-sharing, accessibility, and AI tools. Sentinel uses them solely to *read* permission records — it never captures your screen, audio, or keyboard input.
> - **You are solely responsible** for complying with all applicable laws in your jurisdiction regarding system monitoring, privacy, and consent.
> - **Do not install or run this tool** on shared, workplace, family, or any third-party computer without explicit, informed authorization from every person who uses that device.
> - This is an **educational and personal-use project**. It is provided as-is, without warranty of any kind. See [LICENSE](LICENSE) for full terms.

---

## What Is FolkTech Sentinel?

Sentinel is a lightweight, local-only Python tool that gives you visibility into how applications on your computer are using system-level capabilities like screen capture, microphone access, and outbound network connections.

It runs entirely on your machine. It has no cloud backend, collects no telemetry, and sends nothing over the network. It simply reads information that your operating system already tracks — and presents it to you in a clear, structured way.

---

## Why It Exists

AI desktop agents — including Claude's Computer Use mode, Perplexity Comet, ChatGPT Desktop, Cursor, and others — request broad system permissions when installed. These typically include Screen Recording, Accessibility, Camera, and Microphone access. Once granted, these permissions allow background processes to capture screen content, record audio, and transmit data to remote endpoints — often with no visible indicator to the user.

Sentinel was created after a routine investigation revealed that a desktop AI application had spawned a background process with screen capture capabilities and was transmitting session data at a 100% recording rate to a third-party analytics provider, with no user-facing disclosure. The affected machine was being used for proprietary software development.

This tool exists to close that visibility gap — so you can **understand what is happening on your own computer** and decide for yourself which applications deserve the access they've been granted.

---

## Key Features

| Capability | Description |
|-----------|-------------|
| **Process Visibility** | Identifies running processes that are actively using screen capture, video recording, or audio input APIs. Covers macOS, Windows, and Linux patterns. |
| **Network Visibility** | Shows where watched applications are connecting. Resolves destination IPs to hostnames and organizations using reverse DNS and WHOIS lookups. |
| **Permission Reporting** (macOS) | Lists which applications currently hold Screen Recording, Camera, Microphone, Accessibility, and Input Monitoring permissions by reading the macOS TCC database. |
| **Baseline Comparison** | Establishes a snapshot of known network connections. New or unexpected destinations are highlighted on subsequent scans. |
| **Cross-Platform** | Core process and network monitoring works on macOS, Windows, and Linux. Permission reporting is macOS-specific. |
| **Auto-Start** | Installer configures your OS to run Sentinel at login — LaunchAgent (macOS), Task Scheduler (Windows), or systemd (Linux). |

### Notification Levels

| Level | Meaning | Delivery |
|-------|---------|----------|
| **Red** | A process is actively using screen or audio capture APIs, or data is being sent to an unidentified destination | OS notification + sound + log file |
| **Yellow** | A connection to a known analytics or telemetry service was observed, or a new privacy permission was granted | OS notification + sound + log file |
| **Green** | Informational — scan completed, baseline saved | Log file only |

---

## What This Tool Does NOT Do

This section is important for clarity:

- **Does not record your screen or audio.** Sentinel detects when *other* applications do — it never captures content itself.
- **Does not block, intercept, or modify network traffic.** It reads connection metadata (IP addresses, ports, process names) and reports what it finds.
- **Does not transmit any data from your machine.** There is no analytics, no telemetry, no phone-home behavior. WHOIS lookups (used to identify who owns an IP address) are the only outbound requests, and they are optional.
- **Does not require root or administrator privileges.** It runs as your normal user account.
- **Does not operate as a firewall, antivirus, or endpoint detection tool.** It is a transparency and awareness utility.

---

## Installation

### From PyPI (recommended)

```bash
pip install folktech-sentinel
```

This installs two commands:

| Command | Purpose |
|---------|---------|
| `sentinel` | Run the monitor (continuous, one-time scan, or report) |
| `sentinel-install` | Configure auto-start at login for your operating system |

### From Source

```bash
git clone https://github.com/FolkTechAI/FolkTech-Sentinel.git
cd FolkTech-Sentinel
python install.py
```

The source installer creates a virtual environment, installs dependencies, and configures auto-start in one step.

---

## Quick Start

```bash
# 1. See what's on your machine right now
sentinel --report

# 2. Review the output — especially the permissions list.
#    Revoke anything you don't recognize in System Settings → Privacy & Security.

# 3. Save the current state as your known-good baseline
sentinel --baseline

# 4. Run continuously in a dedicated terminal (or let the installer auto-start it)
sentinel
```

### All Commands

| Command | Description |
|---------|-------------|
| `sentinel` | Run continuously, scanning every 5 seconds. Press `Ctrl+C` to stop. |
| `sentinel --scan` | Run all monitors once and exit. |
| `sentinel --report` | Display current permissions and active connections from watched apps. |
| `sentinel --baseline` | Snapshot current connections as your known-good state. |
| `sentinel-install` | Set up auto-start at login. |
| `sentinel-install --remove` | Remove auto-start (keeps all files). |

---

## Configuration

Edit `src/sentinel/config.py` to customize:

| Setting | Description | Default |
|---------|-------------|---------|
| `SCAN_INTERVAL` | Seconds between scan cycles | `5` |
| `WATCHED_APPS` | Applications whose network activity is tracked | Claude, Perplexity, ChatGPT, Cursor, VS Code, Electron, Node |
| `SCREEN_CAPTURE_PATTERNS` | Command-line patterns indicating screen capture | macOS, Windows, and Linux patterns included |
| `AUDIO_CAPTURE_PATTERNS` | Command-line patterns indicating audio recording | macOS, Windows, and Linux patterns included |
| `KNOWN_TELEMETRY` | Recognized analytics services (reported as Yellow) | Statsig, Sentry, Amplitude, Mixpanel, and others |
| `KNOWN_API_ENDPOINTS` | Recognized API destinations (reported as Yellow — **not** suppressed) | Anthropic, OpenAI, GitHub, Hugging Face |

All connections are always reported. Adding a destination to `KNOWN_API_ENDPOINTS` labels it for easier identification — it does not hide or suppress it.

---

## Permissions Required

### macOS

To read the TCC permission database, your terminal application (Terminal.app, iTerm2, etc.) may need **Full Disk Access**, configurable in System Settings → Privacy & Security → Full Disk Access.

Sentinel itself **does not request or use** Screen Recording, Camera, or Microphone access. It reads the *database that records which other apps have those permissions* — it does not exercise those permissions itself.

### Windows and Linux

No elevated permissions are required. Process and network monitoring use standard `psutil` APIs available to any user-level process. The TCC monitor is macOS-specific and is automatically skipped on other platforms.

---

## Cross-Platform Support

| Feature | macOS | Windows | Linux |
|---------|-------|---------|-------|
| Process Monitor | Full | Full | Full |
| Network Monitor | Full | Full | Full |
| TCC Permission Monitor | Full | N/A | N/A |
| WHOIS Lookups | Built-in | Requires `whois` CLI | Requires `whois` CLI |
| Desktop Notifications | Native (osascript) | plyer | notify-send |
| Auto-start | LaunchAgent | Task Scheduler | systemd user service |

---

## Log Files

Sentinel writes daily log files to the `logs/` directory:

```
logs/sentinel-2026-03-29.log
```

Example entries:

```
2026-03-29 14:51:30 | [RED] [process] Screen capture activity: Comet Helper (PID 896) — Pattern: 'video_capture.mojom'
2026-03-29 14:51:31 | [YELLOW] [network] claude (PID 11764) → 160.79.104.10:443 (api.anthropic.com) [ANTHROPIC] — KNOWN_API
2026-03-29 14:52:00 | [YELLOW] [tcc] Apps with Screen Recording permission: 10 — ai.perplexity.comet, com.openai.atlas, ...
```

---

## Limitations

- **Polling-based.** Sentinel checks the process table at a configurable interval (default: every 5 seconds). A very short-lived process could start and exit between scans. Event-driven monitoring (e.g., via Apple's Endpoint Security framework) would close this gap but requires system-level entitlements not available to standard applications.
- **Pattern-based detection.** Identification relies on known command-line strings and process names. A process that deliberately obscures its command line could avoid detection.
- **macOS-only permission monitoring.** The TCC database is a macOS feature. Windows and Linux do not have a centralized equivalent, so permission reporting is unavailable on those platforms.
- **WHOIS caching and rate limits.** WHOIS lookups are cached locally to minimize external requests. Scanning a large number of new IPs in a short period may trigger rate limits from WHOIS servers.
- **Not a security product.** Sentinel is an awareness and transparency tool. It does not prevent, block, or remediate any activity. It reports what it observes so you can take action yourself.

---

## Uninstall

```bash
# Remove auto-start only (keeps Sentinel installed)
sentinel-install --remove

# Full removal
pip uninstall folktech-sentinel
```

If installed from source, also delete the project directory and any auto-start entry (LaunchAgent, Task Scheduler task, or systemd service) created by the installer.

---

## License

MIT License. See [LICENSE](LICENSE) for the full text.

---

## Contributing

Issues, feature requests, and pull requests are welcome at [GitHub Issues](https://github.com/FolkTechAI/FolkTech-Sentinel/issues).

If you encounter a new capture pattern, process name, or telemetry endpoint that Sentinel should recognize, please open an issue or submit a PR adding it to `config.py`.

---

**Links:** [PyPI](https://pypi.org/project/folktech-sentinel/) · [GitHub](https://github.com/FolkTechAI/FolkTech-Sentinel) · [Issues](https://github.com/FolkTechAI/FolkTech-Sentinel/issues)

Built by [FolkTech AI](https://github.com/FolkTechAI)
