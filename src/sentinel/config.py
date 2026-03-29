"""
Sentinel configuration — defines what to watch and what's suspicious.

This is the brain's knowledge base. It knows:
- Which process patterns indicate screen capture
- Which destinations are known analytics/telemetry
- Which apps to watch closely
- What the scan interval should be
"""

# How often each monitor runs (in seconds)
SCAN_INTERVAL = 5

# ─────────────────────────────────────────────────────────────────────
# PROCESS MONITOR CONFIG
# ─────────────────────────────────────────────────────────────────────

# Process argument patterns that indicate screen/video capture activity.
# If ANY running process has these in its command line, it's flagged.
# Covers macOS, Windows, and Linux patterns.
SCREEN_CAPTURE_PATTERNS = [
    # ── macOS ──
    "ScreenCaptureKit",
    "CGWindowListCreateImage",
    "CGDisplayStream",
    "SCStream",
    "SCScreenshotManager",
    "screencapture",            # macOS built-in screenshot tool
    # ── Windows ──
    "Desktop Duplication",      # Windows Desktop Duplication API
    "BitBlt",                   # GDI screen capture
    "PrintWindow",              # Windows window capture
    "Snipping Tool",
    "SnippingTool",
    "ShareX",                   # Popular screen capture tool
    "OBS",                      # Open Broadcaster (screen recording)
    "obs64",
    "ffmpeg.*gdigrab",          # FFmpeg screen capture on Windows
    "ffmpeg.*x11grab",          # FFmpeg screen capture on Linux
    "dxgi",                     # DirectX screen capture
    # ── Linux ──
    "xdotool",
    "xwd",                      # X Window Dump
    "scrot",                    # Linux screenshot tool
    "gnome-screenshot",
    "spectacle",                # KDE screenshot
    "PipeWire.*screen",         # PipeWire screen sharing
    "xdg-desktop-portal",       # Desktop portal screen capture
    # ── Cross-platform (Chromium/Electron) ──
    "video_capture.mojom",      # Chromium/Electron video capture service
    "Page.captureScreenshot",   # Chrome DevTools Protocol
    "console.screenshot",
    "mcp__computer-use",        # Claude computer-use tool
    "screen.record",
]

# Audio/microphone capture patterns — cross-platform
AUDIO_CAPTURE_PATTERNS = [
    # ── Cross-platform (Chromium/Electron) ──
    "audio.mojom.AudioService",     # Chromium/Electron audio service
    "AudioCapture",
    # ── macOS ──
    "coreaudiod",                   # macOS Core Audio daemon interaction
    "AVAudioRecorder",              # Apple audio recording API
    "AVCaptureSession",             # Apple capture session (audio + video)
    "AudioQueue",                   # Low-level audio recording
    "SFSpeechRecognizer",           # Speech recognition (listens to mic)
    "VoiceProcessingIO",            # Voice processing unit
    "kAudioDevicePropertyDeviceIsRunningSomewhere",
    # ── Windows ──
    "WASAPI",                       # Windows Audio Session API
    "waveInOpen",                   # Legacy Windows audio capture
    "AudioClient",                  # Windows Core Audio
    "MediaCapture",                 # UWP media capture
    "SpeechRecognizer",             # Windows speech recognition
    # ── Linux ──
    "PulseAudio.*record",           # PulseAudio recording
    "parecord",                     # PulseAudio CLI recorder
    "arecord",                      # ALSA recorder
    "PipeWire.*audio",              # PipeWire audio capture
]

# Process name patterns that are suspicious when running
SUSPICIOUS_PROCESS_NAMES = [
    "screencapture",
    "ScreenCaptureKit",
    "AudioCapture",
    "SnippingTool",
    "ShareX",
    "obs64",
    "scrot",
    "parecord",
    "arecord",
]

# Flags that indicate elevated/dangerous permissions
DANGEROUS_FLAGS = [
    "--allow-dangerously-skip-permissions",
    "--allowedTools mcp__computer-use",
    "--disable-features=LocalNetworkAccessChecks",  # Chromium network bypass
]

# ─────────────────────────────────────────────────────────────────────
# NETWORK MONITOR CONFIG
# ─────────────────────────────────────────────────────────────────────

# Apps to monitor all outbound connections for.
# These are apps that COULD exfiltrate your proprietary code.
WATCHED_APPS = [
    "claude",
    "Claude",
    "Claude Helper",
    "Comet",              # Perplexity
    "ChatGPT",
    "openai",
    "copilot",
    "Cursor",
    "code",               # VS Code
    "Electron",
    "node",               # MCP servers, extensions
]

# Known analytics/telemetry services — flagged YELLOW, not RED.
# Format: partial domain match → organization name
KNOWN_TELEMETRY = {
    "statsig": "Statsig (A/B testing & analytics)",
    "sentry": "Sentry (error tracking)",
    "amplitude": "Amplitude (analytics)",
    "mixpanel": "Mixpanel (analytics)",
    "segment": "Segment (data pipeline)",
    "google-analytics": "Google Analytics",
    "googletagmanager": "Google Tag Manager",
    "doubleclick": "Google Ads",
    "hotjar": "Hotjar (session recording)",
    "fullstory": "FullStory (session recording)",
    "logrocket": "LogRocket (session recording)",
    "datadog": "Datadog (monitoring)",
    "newrelic": "New Relic (monitoring)",
    "intercom": "Intercom (messaging)",
    "crashpad": "Crashpad (crash reporting)",
}

# Known API endpoints — these are IDENTIFIED but NOT whitelisted.
# Sentinel still flags them YELLOW so you see every connection.
# Nothing gets a free pass. You decide what's acceptable.
KNOWN_API_ENDPOINTS = {
    "anthropic": "Anthropic API",
    "openai": "OpenAI API",
    "api.github.com": "GitHub API",
    "huggingface": "Hugging Face",
}

# ─────────────────────────────────────────────────────────────────────
# TCC MONITOR CONFIG
# ─────────────────────────────────────────────────────────────────────

# macOS TCC services to watch for permission changes.
# These are the privacy permissions that matter most.
TCC_WATCHED_SERVICES = [
    "kTCCServiceScreenCapture",      # Screen Recording
    "kTCCServiceAccessibility",       # Accessibility (can read screen)
    "kTCCServiceListenEvent",         # Input Monitoring (keylogger risk)
    "kTCCServiceCamera",              # Camera
    "kTCCServiceMicrophone",          # Microphone
]

# ─────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────

import os

SENTINEL_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SENTINEL_DIR, "logs")
BASELINE_FILE = os.path.join(SENTINEL_DIR, "baseline.json")

# System TCC database (requires Full Disk Access to read)
TCC_DB_SYSTEM = "/Library/Application Support/com.apple.TCC/TCC.db"
# User TCC database
TCC_DB_USER = os.path.expanduser("~/Library/Application Support/com.apple.TCC/TCC.db")
