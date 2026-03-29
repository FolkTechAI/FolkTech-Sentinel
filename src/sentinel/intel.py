"""
Intelligence module — turns raw data into understanding.

Responsibilities:
1. Resolve IPs to hostnames and organizations
2. Classify destinations (first-party API, known telemetry, unknown)
3. Manage a baseline of "normal" connections
4. Cache lookups so we don't hammer DNS/WHOIS on every scan
"""

import json
import socket
import subprocess
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional

from sentinel.config import KNOWN_TELEMETRY, KNOWN_API_ENDPOINTS, BASELINE_FILE


@dataclass
class Destination:
    """Everything we know about a network destination."""
    ip: str
    port: int
    hostname: Optional[str] = None
    organization: Optional[str] = None
    classification: str = "UNKNOWN"  # FIRST_PARTY, TELEMETRY, UNKNOWN
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    seen_count: int = 0


class IntelEngine:
    """
    Resolves and classifies network destinations.

    On first run, everything is new — it builds a baseline.
    On subsequent runs, it flags anything that wasn't in the baseline.
    """

    def __init__(self):
        # Cache: IP:port → Destination
        self._cache: dict[str, Destination] = {}
        # DNS cache: IP → hostname (avoid repeated lookups)
        self._dns_cache: dict[str, Optional[str]] = {}
        # WHOIS cache: IP → org name
        self._whois_cache: dict[str, Optional[str]] = {}
        # Baseline: known-good connections from first run
        self._baseline: set[str] = set()
        # Load saved baseline if it exists
        self._load_baseline()

    def analyze(self, ip: str, port: int, app: str = "") -> Destination:
        """
        Analyze a destination. Returns a Destination with classification.

        This is the main entry point — give it an IP:port and it tells
        you everything it can figure out about where that data is going.
        """
        key = f"{ip}:{port}"
        now = datetime.now().isoformat()

        # Check cache first
        if key in self._cache:
            dest = self._cache[key]
            dest.last_seen = now
            dest.seen_count += 1
            return dest

        # New destination — resolve it
        hostname = self._resolve_hostname(ip)
        org = self._resolve_org(ip)
        classification = self._classify(ip, hostname, org)

        dest = Destination(
            ip=ip,
            port=port,
            hostname=hostname,
            organization=org,
            classification=classification,
            first_seen=now,
            last_seen=now,
            seen_count=1,
        )

        self._cache[key] = dest
        return dest

    def is_new_destination(self, ip: str, port: int) -> bool:
        """Check if this destination was NOT in the baseline."""
        return f"{ip}:{port}" not in self._baseline

    def save_baseline(self):
        """Save current known destinations as the baseline."""
        baseline_data = {
            "created": datetime.now().isoformat(),
            "destinations": {
                key: asdict(dest) for key, dest in self._cache.items()
            }
        }
        with open(BASELINE_FILE, "w") as f:
            json.dump(baseline_data, f, indent=2)

    def _load_baseline(self):
        """Load baseline from disk if it exists."""
        if not os.path.exists(BASELINE_FILE):
            return
        try:
            with open(BASELINE_FILE, "r") as f:
                data = json.load(f)
            self._baseline = set(data.get("destinations", {}).keys())
            # Pre-populate cache from baseline
            for key, dest_data in data.get("destinations", {}).items():
                self._cache[key] = Destination(**dest_data)
        except (json.JSONDecodeError, TypeError):
            pass  # Corrupted baseline — start fresh

    def _resolve_hostname(self, ip: str) -> Optional[str]:
        """Reverse DNS lookup — IP to hostname."""
        if ip in self._dns_cache:
            return self._dns_cache[ip]

        try:
            hostname = socket.gethostbyaddr(ip)[0]
            self._dns_cache[ip] = hostname
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            self._dns_cache[ip] = None
            return None

    def _resolve_org(self, ip: str) -> Optional[str]:
        """
        Use WHOIS to find the organization that owns this IP.
        Falls back to nslookup if whois is slow.
        """
        if ip in self._whois_cache:
            return self._whois_cache[ip]

        # Skip private/local IPs
        if ip.startswith(("10.", "172.16.", "192.168.", "127.", "fe80", "::1")):
            self._whois_cache[ip] = "Local Network"
            return "Local Network"

        try:
            result = subprocess.run(
                ["whois", ip],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout.lower()

            # Extract org name from WHOIS output
            for line in result.stdout.splitlines():
                lower = line.lower().strip()
                if lower.startswith(("orgname:", "org-name:", "organization:")):
                    org = line.split(":", 1)[1].strip()
                    self._whois_cache[ip] = org
                    return org
                if lower.startswith("netname:"):
                    org = line.split(":", 1)[1].strip()
                    self._whois_cache[ip] = org
                    return org

            self._whois_cache[ip] = None
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._whois_cache[ip] = None
            return None

    def _classify(self, ip: str, hostname: Optional[str], org: Optional[str]) -> str:
        """
        Classify a destination based on what we know about it.

        Returns: KNOWN_API, TELEMETRY, or UNKNOWN

        IMPORTANT: No classification gets a free pass. KNOWN_API and TELEMETRY
        are still flagged (YELLOW). They just tell you WHO is receiving data.
        UNKNOWN is flagged RED because we can't even identify the destination.
        """
        searchable = " ".join(filter(None, [hostname, org, ip])).lower()

        # Check known API endpoints — identified but NOT whitelisted
        for pattern, name in KNOWN_API_ENDPOINTS.items():
            if pattern.lower() in searchable:
                return "KNOWN_API"

        # Check known telemetry/analytics
        for pattern, name in KNOWN_TELEMETRY.items():
            if pattern.lower() in searchable:
                return "TELEMETRY"

        return "UNKNOWN"

    def get_summary(self, dest: Destination) -> str:
        """Human-readable summary of a destination."""
        parts = [f"{dest.ip}:{dest.port}"]
        if dest.hostname:
            parts.append(f"({dest.hostname})")
        if dest.organization:
            parts.append(f"[{dest.organization}]")
        parts.append(f"— {dest.classification}")
        return " ".join(parts)
