from __future__ import annotations

"""Passive maturity check: presence of a security.txt (RFC 9116)."""

from urllib.request import Request, urlopen


def scan(domain: str) -> list[tuple[str, str]]:
    d = domain.strip().lower()
    for path in (f"https://{d}/.well-known/security.txt", f"https://{d}/security.txt"):
        try:
            req = Request(path, headers={"User-Agent": "presales-scout/0.1"})
            with urlopen(req, timeout=15) as resp:
                body = resp.read(2048).decode("utf-8", "replace").lower()
                if resp.status == 200 and ("contact:" in body):
                    return []  # present and valid — no finding
        except Exception:
            continue
    return [("MATURITY_SECURITYTXT_MISSING", "No valid /.well-known/security.txt found")]
