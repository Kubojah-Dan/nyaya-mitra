"""
NyayaMitra SSRF Protection & URL Allowlist Utility
Validates external URLs to prevent Server-Side Request Forgery (SSRF),
blocking internal IPs, cloud metadata endpoints, and non-whitelisted domains.
"""

import ipaddress
import re
from urllib.parse import urlparse

# Allowed official domains for outbound retrieval
ALLOWED_DOMAIN_PATTERNS = [
    r"^([a-zA-Z0-9\-_]+\.)*gov\.in$",
    r"^([a-zA-Z0-9\-_]+\.)*nic\.in$",
    r"^indiacode\.nic\.in$",
    r"^nalsa\.gov\.in$",
    r"^ecourts\.gov\.in$",
    r"^tele-law\.in$",
    r"^www\.tele-law\.in$",
    r"^judgments\.ecourts\.gov\.in$",
    r"^highcourtchd\.gov\.in$",
    r"^delhihighcourt\.nic\.in$",
]

# Blocked private and link-local IP ranges
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private class C
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata (AWS/GCP/Azure)
    ipaddress.ip_network("0.0.0.0/8"),        # Current network
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
]


class SSRFSecurityError(ValueError):
    """Raised when an outbound URL violates SSRF safety rules."""
    pass


class SSRFValidator:
    """Validates URLs against allowlists and private network blocks."""

    @classmethod
    def is_url_safe(cls, url: str) -> tuple[bool, str]:
        """
        Validates URL scheme, hostname, IP resolution, and allowlist.
        Returns: (is_safe: bool, reason_or_error: str)
        """
        if not url or not isinstance(url, str):
            return False, "URL is empty or invalid type."

        try:
            parsed = urlparse(url.strip())
        except Exception as e:
            return False, f"Malformed URL syntax: {e}"

        # 1. Scheme validation (only HTTP/HTTPS)
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Forbidden URL scheme '{parsed.scheme}'. Only http and https are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "URL does not specify a valid hostname."

        hostname_clean = hostname.lower().strip("[]").strip(".")

        # 2. Block direct localhost / internal names
        if hostname_clean in ("localhost", "0.0.0.0", "metadata.google.internal"):
            return False, "Access to localhost or internal metadata hostname is forbidden."

        # 3. Check if hostname is an IP literal
        try:
            ip_obj = ipaddress.ip_address(hostname_clean)
            for blocked_net in BLOCKED_IP_NETWORKS:
                if ip_obj in blocked_net:
                    return False, f"Direct IP '{hostname_clean}' is inside blocked private network '{blocked_net}'."
            return False, f"Direct IP '{hostname_clean}' access is not permitted; must use verified government domain."
        except ValueError:
            # Not an IP literal, proceed to hostname check
            pass

        # 4. Check if hostname matches official government allowlist
        matches_allowlist = any(
            re.match(pattern, hostname_clean, re.IGNORECASE)
            for pattern in ALLOWED_DOMAIN_PATTERNS
        )

        if not matches_allowlist:
            return False, f"Domain '{hostname_clean}' is not on the official government allowlist (*.gov.in, *.nic.in)."

        return True, "URL is safe and verified on allowlist."

    @classmethod
    def validate_and_enforce(cls, url: str) -> str:
        """Enforces URL safety, raising SSRFSecurityError if unsafe."""
        is_safe, reason = cls.is_url_safe(url)
        if not is_safe:
            raise SSRFSecurityError(f"SSRF Protection blocked request: {reason}")
        return url
