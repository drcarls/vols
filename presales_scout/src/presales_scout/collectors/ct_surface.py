from __future__ import annotations

"""Passive attack-surface mapping via Certificate Transparency (crt.sh).

Queries the public CT index — never touches the target — for every hostname
ever issued a certificate under the domain. A large or sensitive footprint
(vpn/admin/dev/staging hosts) is a real, actionable finding.
"""

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

SENSITIVE = ("vpn", "remote", "owa", "webmail", "admin", "portal", "citrix", "rdp",
             "dev", "test", "staging", "stage", "git", "jenkins", "jira", "gitlab",
             "sso", "api", "ftp", "backup", "db", "sql")
SURFACE_THRESHOLD = 25


def scan(domain: str) -> list[tuple[str, str]]:
    d = domain.strip().lower()
    url = f"https://crt.sh/?q={quote('%.' + d)}&output=json"
    try:
        req = Request(url, headers={"User-Agent": "presales-scout/0.1"})
        with urlopen(req, timeout=18) as resp:
            rows = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception:
        return []
    names = set()
    for r in rows:
        for n in (r.get("name_value") or "").split("\n"):
            n = n.strip().lower().lstrip("*.")
            if n.endswith(d):
                names.add(n)
    findings: list[tuple[str, str]] = []
    if len(names) >= SURFACE_THRESHOLD:
        findings.append(("SURFACE_SUBDOMAINS", f"{len(names)} distinct hostnames in CT logs"))
    hits = sorted({p for n in names for p in SENSITIVE if n.split(".")[0].startswith(p)})
    if hits:
        findings.append(("SURFACE_SUBDOMAINS",
                         f"{len(names)} hostnames incl. sensitive prefixes: {', '.join(hits[:8])}"))
    return findings[:1]  # one surface finding per company is enough
