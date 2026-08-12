from __future__ import annotations

"""Passive procurement supply-chain mapping via TED (Tenders Electronic Daily).

Public bodies and utilities (LOU/LUF) must publish above-threshold contracts
to the EU's TED. Its v3 search API returns each notice's CPV classification,
type, and date — so we can profile *what a utility outsources* and flag the
NIS2-relevant categories (ICT, telecom, OT/control, security), even though
individual winner names are served through TED's async viewer and aren't in
the search index. The category-level dependency profile is itself a strong
NIS2 Art. 21(2)(d) supply-chain signal; winner names are a per-notice
enrichment left to the analyst (each notice is linked).

Zero-auth, read-only queries against a public API — no scraping of the target.
"""

import json
from urllib.request import Request, urlopen

TED_API = "https://api.ted.europa.eu/v3/notices/search"


def _categorize(cpv: str) -> tuple[str, str, bool]:
    """cpv code -> (category, criticality, nis2_critical)."""
    c = (cpv or "").strip()
    table = [
        ("48", ("Software & information systems", "high", True)),
        ("72", ("IT services", "high", True)),
        ("5031", ("Computer-equipment maintenance", "high", True)),
        ("302", ("Computer equipment", "high", True)),
        ("32", ("Comms / electronic equipment", "high", True)),
        ("642", ("Telecom services", "high", True)),
        ("64", ("Postal / telecom", "medium", True)),
        ("35", ("Security & safety", "high", True)),
        ("79714", ("Security services", "high", True)),
        ("31", ("Electrical equipment (OT-adjacent)", "medium", True)),
        ("38", ("Measuring / control instruments", "medium", True)),
        ("71", ("Engineering / consulting", "low", False)),
        ("73", ("R&D services", "low", False)),
        ("79", ("Business / consulting services", "low", False)),
        ("45", ("Construction", "low", False)),
        ("90", ("Environmental / facilities", "low", False)),
        ("65", ("Utility services", "low", False)),
        ("66", ("Financial / insurance", "low", False)),
    ]
    for prefix, info in table:
        if c.startswith(prefix):
            return info
    return ("Other", "low", False)


def _ted_search(buyer: str, limit: int = 100, award_only: bool = True) -> list[dict]:
    q = f'buyer-name="{buyer}"'
    if award_only:
        q += ' AND notice-type="can-standard"'
    body = json.dumps({
        "query": q,
        "fields": ["publication-number", "publication-date", "notice-type", "classification-cpv"],
        "limit": limit, "scope": "ALL",
    }).encode()
    req = Request(TED_API, data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=40) as resp:
            return json.load(resp).get("notices", [])
    except Exception:
        return []


def profile(buyer: str, limit: int = 100) -> dict:
    """Return a procurement-dependency profile for a buyer name."""
    notices = _ted_search(buyer, limit=limit)
    records = []
    for n in notices:
        cpv_list = n.get("classification-cpv") or []
        cat, crit, nis2 = _categorize(cpv_list[0] if cpv_list else "")
        records.append(dict(
            publication=n.get("publication-number"),
            date=(n.get("publication-date") or "")[:10],
            cpv=cpv_list[0] if cpv_list else "",
            category=cat, criticality=crit, nis2_critical=nis2,
            url=f"https://ted.europa.eu/en/notice/-/detail/{n.get('publication-number')}",
        ))
    critical = [r for r in records if r["nis2_critical"]]
    cats = sorted({r["category"] for r in critical})
    return dict(
        buyer=buyer, total_awards=len(records), critical_awards=len(critical),
        critical_categories=cats, records=records,
        latest=max((r["date"] for r in records), default=""),
    )


def scan_buyer(buyer: str) -> list[tuple[str, str]]:
    """Collector interface: emit a context-map finding code if the buyer
    outsources NIS2-critical categories via public procurement."""
    p = profile(buyer)
    if p["critical_awards"]:
        ev = (f"{p['critical_awards']} of {p['total_awards']} public award notices in NIS2-critical "
              f"categories ({', '.join(p['critical_categories'])}); latest {p['latest']} (source: TED)")
        return [("SUPPLY_PROCUREMENT_CRITICAL", ev)]
    return []
