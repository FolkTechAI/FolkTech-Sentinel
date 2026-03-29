# FolkTech Sentinel

A local-only transparency tool that helps you understand what desktop applications — especially AI agents — are doing with screen, audio, and network access on your personal computer.

---

> **Important Notice**
>
> **This tool is intended for use only on devices you personally own and fully control.**
>
> - Sentinel requires elevated system permissions to function (Screen Recording and Accessibility on macOS). These permissions are used solely to *read* the system's permission database — Sentinel itself never captures your screen, audio, or input.
> - You are solely responsible for complying with all applicable laws regarding monitoring, privacy, and consent in your jurisdiction.
> - This tool is **not intended** for use on shared, workplace, family, or third-party computers without explicit, informed authorization from all affected parties.
> - FolkTech Sentinel is an educational and personal-use tool. It is provided as-is with no warranty. See [LICENSE](LICENSE) for details.

---

## Why This Exists

Modern AI desktop agents — Claude Computer Use, Perplexity Comet, ChatGPT Desktop, Cursor, and others — routinely request broad system permissions including Screen Recording, Accessibility, Camera, and Microphone access. Once granted, these permissions allow background processes to capture your screen, record audio, and transmit data to remote servers with little or no indication to the user.

Sentinel was built after discovering that a desktop AI application had silently spawned a background process with screen capture capabilities and bypassed permission checks — on a machine used for proprietary software development. The process was sending telemetry data at a 100% session recording rate to a third-party analytics service without any user-facing disclosure.

This tool exists so you can **see what is happening on your own machine** and make informed decisions about which applications to trust.

---

## What It Does

Sentinel runs locally on your computer and periodically checks three things:

| Monitor | What It Observes | How |
|---------|-----------------|-----|
| **Process** | Which running processes are using screen capture, audio recording, or video capture APIs | Scans the process table for known API patterns across macOS, Windows, and Linux |
| **Network** | Where watched applications are sending data | Maps outbound connections to hostnames and organizations via reverse DNS and WHOIS |
| **Permissions** (macOS) | Which apps hold Screen Recording, Camera, Microphone, Accessibility, and Input Monitoring permissions | Reads the macOS TCC (Transparency, Consent, and Control) database |

### What This Tool Does NOT Do

- **Does not capture your screen or audio.** It only detects when other applications do.
- **Does not block or modify network traffic.** It observes and reports.
- **Does not send any data off your machine.** There is no telemetry, no analytics, no cloud component.
- **Does not require an internet connection to function.** WHOIS lookups are optional and used only to identify IP ownership.
- **Does not run with root/admin privileges.** It runs as your user account.

---

## Alert Levels

| Level | Meaning | Notification |
|-------|---------|-------------|
| **RED** | A process is actively using screen or audio capture APIs, or data is being sent to an unidentified destination | OS notification + sound + log |
| **YELLOW** | A connection to a known analytics/telemetry service was observed, or a new privacy permission was granted | OS notification + sound + log |
| **GREEN** | Informational — scan completed, baseline saved | Log file only |

---

## Installation

### From PyPI (recommended)

```bash
pip install folktech-sentinel
```

This installs two commands:

- `sentinel` — the monitor itself
- `sentinel-install` — configures auto-start on boot

### From Source

```bash
git clone https://github.com/FolkTechAI/FolkTech-Sentinel.git
cd FolkTech-Sentinel
python install.py
```

The installer creates a virtual environment, installs dependencies, and configures your operating system to start Sentinel automatically at login.

---

## Usage

### Run Continuously

Scans every 5 seconds. Alerts appear in real time. Press `Ctrl+C` to stop.

```bash
sentinel
```

Saves a connection baseline automatically on shutdown.

### One-Time Scan

Run all monitors once and exit.

```bash
sentinel --scan
```

### Full Report

Display current privacy permissions and all active outbound connections from watched applications.

```bash
sentinel --report
```

### Establish Baseline

Snapshot current network connections as your known-good state. Future scans will flag any new destinations not present in this baseline.

```bash
sentinel --baseline
```

Run this once after reviewing your report and confirming the current state is acceptable.

---

## Log Files

Sentinel writes one log file per day to the `logs/` directory:

```
logs/sentinel-2026-03-29.log
```

Log format:
```
2026-03-29 14:51:30 | [RED] [process] Screen capture activity: Comet Helper (PID 896) — Pattern: 'video_capture.mojom'
2026-03-29 14:51:31 | [YELLOW] [tcc] Apps with Screen Recording permission: 10 — ai.perplexity.comet, com.openai.atlas, ...
```

---

## Configuration

Edit `src/sentinel/config.py` to customize behavior:

| Setting | Description | Default |
|---------|-------------|---------|
| `SCAN_INTERVAL` | Seconds between scan cycles | `5` |
| `WATCHED_APPS` | Applications whose network connections are monitored | Claude, Perplexity, ChatGPT, Cursor, VS Code, Electron, Node |
| `SCREEN_CAPTURE_PATTERNS` | Process command-line patterns that indicate screen capture | macOS, Windows, and Linux patterns included |
| `AUDIO_CAPTURE_PATTERNS` | Process command-line patterns that indicate audio recording | macOS, Windows, and Linux patterns included |
| `KNOWN_TELEMETRY` | Known analytics services (classified YELLOW) | Statsig, Sentry, Amplitude, Mixpanel, and others |
| `KNOWN_API_ENDPOINTS` | Identified API destinations (classified YELLOW — not whitelisted) | Anthropic, OpenAI, GitHub, Hugging Face |

### Adding a watched application

```python
WATCHED_APPS = [
    "claude",
    "Comet",        # Perplexity
    "ChatGPT",
    "YourApp",      # add here
]
```

### Identifying a known destination

Adding a destination to `KNOWN_API_ENDPOINTS` classifies it as **identified** but does **not** suppress alerts. All connections are reported.

```python
KNOWN_API_ENDPOINTS = {
    "anthropic": "Anthropic API",
    "github.com": "GitHub",   # add here
}
```

---

## Cross-Platform Support

| Feature | macOS | Windows | Linux |
|---------|-------|---------|-------|
| Process Monitor | Full | Full | Full |
| Network Monitor | Full | Full | Full |
| TCC Permission Monitor | Full | N/A | N/A |
| WHOIS Lookups | Built-in | Requires `whois` | Requires `whois` |
| Desktop Notifications | Native (osascript) | plyer | notify-send |
| Auto-start | LaunchAgent | Task Scheduler | systemd |

On Windows and Linux, the TCC monitor is automatically skipped — no errors, no configuration needed. All other monitors function identically across platforms.

---

## Permissions Required

### macOS

Sentinel reads the TCC database to report which apps hold sensitive permissions. To access this data, **Terminal.app** (or your terminal emulator) may need **Full Disk Access** in System Settings → Privacy & Security.

Sentinel itself does not request or use Screen Recording, Camera, or Microphone access.

### Windows / Linux

No special permissions are required. Process and network monitoring use standard `psutil` APIs available to any user-level process.

---

## Limitations

- **Polling-based detection.** Sentinel checks the process table every few seconds. A very short-lived capture process could complete between scans. Event-driven monitoring (e.g., via Apple's Endpoint Security framework) would catch these but requires kernel-level entitlements.
- **Pattern matching.** Detection relies on known command-line patterns and process names. A deliberately obfuscated process could evade detection.
- **No TCC on Windows/Linux.** Permission monitoring is macOS-specific. Windows and Linux lack a centralized equivalent.
- **WHOIS rate limits.** Rapid scans of many new IPs may trigger rate limiting from WHOIS servers. Results are cached to minimize lookups.

---

## Recommended First Steps

1. **Review your permissions.** Run `sentinel --report` to see which apps currently hold Screen Recording, Camera, Microphone, and Accessibility access on your machine.
2. **Revoke what you don't recognize.** Open System Settings → Privacy & Security and disable access for apps you no longer use or don't trust.
3. **Establish a baseline.** Run `sentinel --baseline` to snapshot your current network connections as known-good.
4. **Run continuously.** Start `sentinel` in a dedicated terminal or let the installer configure it to run at login.

---

## Uninstall

### Remove auto-start only (keeps files)

```bash
sentinel-install --remove
```

### Full removal

```bash
pip uninstall folktech-sentinel
```

If installed from source, also delete the project directory and the LaunchAgent/systemd service/Task Scheduler entry created by the installer.

---

## License

MIT License. See [LICENSE](LICENSE) for the full text.

---

## Links

- **PyPI:** [folktech-sentinel](https://pypi.org/project/folktech-sentinel/)
- **GitHub:** [FolkTechAI/FolkTech-Sentinel](https://github.com/FolkTechAI/FolkTech-Sentinel)
- **Issues:** [Report a bug or request a feature](https://github.com/FolkTechAI/FolkTech-Sentinel/issues)

Built by [FolkTech AI](https://github.com/FolkTechAI)
