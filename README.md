# FolkTech Sentinel

Local security monitor that watches your machine for unauthorized screen capture, data exfiltration, and suspicious app behavior. No cloud dependency — everything runs locally.

## What It Does

- **Process Monitor** — Detects apps using screen capture APIs, video recording, or running with dangerous permissions
- **Network Monitor** — Tracks outbound connections from watched apps, resolves where data is going (IP → hostname → organization)
- **TCC Monitor** (macOS) — Watches for privacy permission changes (Screen Recording, Camera, Microphone, Accessibility)

## Alert Levels

| Level | Meaning | Notification |
|-------|---------|-------------|
| RED | Active threat — screen capture detected, unknown destination receiving data | macOS banner + sound + log |
| YELLOW | Suspicious — known telemetry/analytics, new permission granted | macOS banner + sound + log |
| GREEN | Informational — normal traffic, scan complete | Log file only |

---

## Setup

### macOS

```bash
cd ~/Developer/sentinel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows

```cmd
cd C:\path\to\sentinel
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux

```bash
cd /path/to/sentinel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Commands

### Run Continuously (Daemon Mode)

Scans every 5 seconds. Alerts pop up in real time. Press Ctrl+C to stop.

```bash
python sentinel.py
```

Saves baseline automatically on shutdown.

### One-Time Scan

Run all monitors once and exit. Good for a quick check.

```bash
python sentinel.py --scan
```

### Full Report

Shows current privacy permissions and all active network connections from watched apps.

```bash
python sentinel.py --report
```

### Establish Baseline

Snapshots current network connections as "normal." Future scans flag anything new.

```bash
python sentinel.py --baseline
```

Run this once when you're confident your system is clean.

---

## Log Files

Logs are written to `sentinel/logs/` with one file per day:

```
logs/sentinel-2026-03-29.log
```

Format:
```
2026-03-29 14:51:30 | [RED] [process] Screen capture detected: Comet Helper (PID 896) — Pattern matched: 'video_capture.mojom'
```

---

## Configuration

Edit `config.py` to customize:

- **SCAN_INTERVAL** — How often to scan (default: 5 seconds)
- **WATCHED_APPS** — Which apps to monitor network connections for
- **SCREEN_CAPTURE_PATTERNS** — Process patterns that indicate screen capture
- **KNOWN_TELEMETRY** — Known analytics services (flagged YELLOW instead of RED)
- **KNOWN_FIRST_PARTY** — Expected API endpoints (flagged GREEN)

### Adding a watched app

Open `config.py` and add to the `WATCHED_APPS` list:

```python
WATCHED_APPS = [
    "claude",
    "Comet",        # Perplexity
    "ChatGPT",
    "YourNewApp",   # ← add here
]
```

### Marking a destination as safe

Add to `KNOWN_FIRST_PARTY` in `config.py`:

```python
KNOWN_FIRST_PARTY = {
    "anthropic": "Anthropic API",
    "github.com": "GitHub",   # ← add here
}
```

---

## Cross-Platform Notes

| Feature | macOS | Windows | Linux |
|---------|-------|---------|-------|
| Process Monitor | Full support | Full support (psutil) | Full support (psutil) |
| Network Monitor | Full support | Full support (psutil) | Full support (psutil) |
| TCC Monitor | Full support | N/A (no TCC on Windows) | N/A (no TCC on Linux) |
| WHOIS Lookups | Built-in `whois` | Needs `whois` installed | Needs `whois` installed |
| Notifications | macOS banners (osascript) | Needs adaptation (win10toast or plyer) | Needs adaptation (notify-send) |
| Reverse DNS | Full support | Full support | Full support |

### Windows/Linux Adaptations Needed

1. **Notifications** — Replace `osascript` in `alerts.py`:
   - Windows: use `plyer` or `win10toast` package
   - Linux: use `notify-send` command
2. **TCC Monitor** — Only works on macOS. On Windows/Linux, the TCC monitor will simply skip (no crash).
3. **WHOIS** — Install `whois` command or use Python `ipwhois` package.

---

## Recommended First Steps

1. Run `python sentinel.py --report` to see what's on your machine right now
2. Review the permissions list — revoke anything you don't recognize
3. Run `python sentinel.py --baseline` to establish what's normal
4. Run `python sentinel.py` in a dedicated terminal to monitor continuously

---

## Built by FolkTech AI
