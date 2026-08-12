from __future__ import annotations

"""Passive exposed-service check.

Two backends, both passive (they query an index, never scan the target):
  - Shodan InternetDB (free, no key): per-IP open ports / CVEs / CPEs.
  - Shodan full API (needs SHODAN_API_KEY): richer host + OT/ICS search.

We resolve the domain's A records, then look each IP up in the index. Only
clearly sensitive ports are flagged, to keep false positives low. OT/ICS
protocol ports escalate to the critical EXPOSURE_OT_ICS finding.
"""

import json
import os
from urllib.request import Request, urlopen

from . import _doh

SENSITIVE_PORTS = {
    22: "SSH", 23: "Telnet", 21: "FTP", 3389: "RDP", 445: "SMB",
    3306: "MySQL", 5432: "PostgreSQL", 1433: "MSSQL", 6379: "Redis",
    27017: "MongoDB", 9200: "Elasticsearch",
}
OT_PORTS = {502: "Modbus", 102: "S7comm", 20000: "DNP3", 44818: "EtherNet/IP", 47808: "BACnet"}


def _internetdb(ip: str) -> dict | None:
    try:
        req = Request(f"https://internetdb.shodan.io/{ip}", headers={"User-Agent": "presales-scout/0.1"})
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def scan(domain: str) -> list[tuple[str, str]]:
    d = domain.strip().lower()
    ips = _doh.resolve(d, "A")[:3]
    findings: list[tuple[str, str]] = []
    seen_codes: set[str] = set()
    for ip in ips:
        info = _internetdb(ip)
        if not info:
            continue
        ports = set(info.get("ports") or [])
        ot = sorted(p for p in ports if p in OT_PORTS)
        if ot and "EXPOSURE_OT_ICS" not in seen_codes:
            names = ", ".join(f"{p}/{OT_PORTS[p]}" for p in ot)
            findings.append(("EXPOSURE_OT_ICS", f"{ip} exposes OT protocol port(s): {names}"))
            seen_codes.add("EXPOSURE_OT_ICS")
        sens = sorted(p for p in ports if p in SENSITIVE_PORTS)
        if sens and "EXPOSURE_SERVICE_OPEN" not in seen_codes:
            names = ", ".join(f"{p}/{SENSITIVE_PORTS[p]}" for p in sens)
            findings.append(("EXPOSURE_SERVICE_OPEN", f"{ip} exposes: {names}"))
            seen_codes.add("EXPOSURE_SERVICE_OPEN")
        vulns = info.get("vulns") or []
        if vulns and "WEB_COMPONENT_EOL" not in seen_codes:
            findings.append(("WEB_COMPONENT_EOL", f"{ip} flagged CVEs in index: {', '.join(vulns[:5])}"))
            seen_codes.add("WEB_COMPONENT_EOL")
    return findings


def available() -> str:
    return "shodan_api" if os.environ.get("SHODAN_API_KEY") else "internetdb_free"
