from __future__ import annotations

"""Tiny DNS-over-HTTPS helper (Google JSON API), shared by collectors.

DoH works where UDP/53 is blocked but HTTPS is open (sandboxes, proxies).
"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_ENDPOINT = "https://dns.google/resolve"

# numeric TXT/record type codes we care about
_TYPES = {"A": 1, "NS": 2, "TXT": 16, "CAA": 257, "DNSKEY": 48, "DS": 43, "MX": 15}


def resolve(name: str, rtype: str, timeout: int = 15) -> list[str]:
    """Return the record data strings for name/rtype, or [] if none."""
    url = _ENDPOINT + "?" + urlencode({"name": name, "type": rtype})
    req = Request(url, headers={"accept": "application/dns-json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []
    want = _TYPES.get(rtype)
    out = []
    for ans in data.get("Answer", []):
        if want is None or ans.get("type") == want:
            out.append((ans.get("data") or "").strip('"'))
    return out


def has_record(name: str, rtype: str) -> bool:
    return bool(resolve(name, rtype))
