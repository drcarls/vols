from __future__ import annotations

"""Passive web checks: security headers + software version disclosure.

Performs a single ordinary HTTPS GET of the homepage (normal browsing, not
scanning) and reads the response headers. Returns bare (code, evidence) pairs.
"""

import re
from urllib.request import Request, urlopen

# components whose disclosed version is end-of-life as of this build (Aug 2026).
_EOL_HINTS = [
    (re.compile(r"php/?\s*([0-7]\.|8\.0|8\.1)", re.I), "PHP < 8.2 (8.1 branch EOL Dec 2025)"),
    (re.compile(r"apache/?\s*2\.[0-2]\.", re.I), "Apache httpd 2.2/2.0 (EOL)"),
    (re.compile(r"nginx/?\s*1\.1[0-8]\.", re.I), "nginx < 1.20 (old)"),
    (re.compile(r"openssl/?\s*1\.", re.I), "OpenSSL 1.x (EOL)"),
]
_VERSION_RE = re.compile(r"\d+\.\d+")


def _fetch_headers(domain: str, timeout: int = 20):
    url = f"https://{domain.strip().lower()}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; presales-scout/0.1)"})
    with urlopen(req, timeout=timeout) as resp:
        return {k.lower(): v for k, v in resp.headers.items()}


def scan(domain: str) -> list[tuple[str, str]]:
    try:
        h = _fetch_headers(domain)
    except Exception as exc:
        return []  # site unreachable over the proxy — skip rather than false-flag
    findings: list[tuple[str, str]] = []

    if "strict-transport-security" not in h:
        findings.append(("WEB_HSTS_MISSING", "No Strict-Transport-Security header"))
    if "content-security-policy" not in h:
        findings.append(("WEB_CSP_MISSING", "No Content-Security-Policy header"))
    if "x-frame-options" not in h and "content-security-policy" not in h:
        findings.append(("WEB_SECURITY_HEADERS_WEAK", "No X-Frame-Options / clickjacking protection"))

    banner = " ".join(v for k, v in h.items() if k in ("server", "x-powered-by"))
    if banner and _VERSION_RE.search(banner):
        findings.append(("WEB_VERSION_DISCLOSURE", f"Version disclosed: {banner.strip()}"))
        for rx, label in _EOL_HINTS:
            if rx.search(banner):
                findings.append(("WEB_COMPONENT_EOL", f"{label} — disclosed as: {banner.strip()}"))
                break

    return findings
