from __future__ import annotations

"""Named-supplier resolution via openprocurements.com (Swedish procurement aggregator).

TED gives the procurement *categories* but not winner names. openprocurements
publishes, per buyer, the tenders and the suppliers named in each award
decision — and it aggregates national portals, so it also covers
below-threshold contracts TED never sees. This resolves the actual supplier
companies (#1) with national coverage (#2); aggregating them across buyers
feeds the supplier-as-leads funnel (#3).

Read-only fetches of a public aggregator — no scraping of the target.
"""

import html
import re
from urllib.request import Request, urlopen

BASE = "https://se.openprocurements.com"

# Swedish keyword -> (category, nis2_critical) for classifying a tender by title
_CATS = [
    (("scada", "styr", "reglerteknik", "transformator", "ställverk", "mät", "elnät", "pann"), ("ot_control", True)),
    (("säkerhet", "brandskydd", "passersystem", "larm", "bevakning"), ("security", True)),
    (("telefoni", "telekom", "fiber", "kommunikation"), ("telecom", True)),
    (("it-", "it ", "system", "programvara", "mjukvara", "licens", "server", "dator",
      "digital", "konsult", "drift", "support", "moln"), ("ict", True)),
]


def _get(url: str, timeout: int = 22) -> str:
    return urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 (presales-scout/0.1)"}),
                   timeout=timeout).read().decode("utf-8", "replace")


def _translit(name: str) -> str:
    s = name.lower()
    for a, b in (("å", "a"), ("ä", "a"), ("ö", "o"), ("é", "e"), ("ü", "u")):
        s = s.replace(a, b)
    s = s.replace("(publ)", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _slug_candidates(name: str) -> list[str]:
    base = _translit(name)
    cands = [base]
    if base.endswith("-ab"):
        stem = base[:-3]
        cands += [stem + "-aktiebolag", stem + "-ab-publ", stem]
    else:
        cands += [base + "-ab", base + "-aktiebolag"]
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c); out.append(c)
    return out


def resolve_buyer(name: str) -> str | None:
    for slug in _slug_candidates(name):
        try:
            page = _get(f"{BASE}/buyer/{slug}/")
        except Exception:
            continue
        if "/tender/" in page:
            return slug
    return None


def buyer_tenders(slug: str) -> list[str]:
    try:
        page = _get(f"{BASE}/buyer/{slug}/")
    except Exception:
        return []
    return sorted(set(re.findall(r'/tender/([a-z0-9\-]{5,80})/', page)))


def _categorize(title: str) -> tuple[str, bool]:
    low = title.lower()
    for keys, info in _CATS:
        if any(k in low for k in keys):
            return info
    return ("other", False)


def tender_suppliers(tender_slug: str) -> dict:
    try:
        page = _get(f"{BASE}/tender/{tender_slug}/")
    except Exception:
        return {}
    m = re.search(r"<title>(.*?)</title>", page, re.S)
    title = html.unescape(m.group(1)).strip() if m else tender_slug
    pairs = re.findall(r'href="/supplier/([a-z0-9\-]+)/"[^>]*>\s*([^<]{2,90})</a>', page)
    suppliers = []
    seen = set()
    for slug, nm in pairs:
        nm = html.unescape(nm).strip()
        if slug not in seen and nm:
            seen.add(slug)
            suppliers.append({"slug": slug, "name": nm})
    cat, crit = _categorize(title)
    return {"tender": tender_slug, "title": title, "category": cat,
            "nis2_critical": crit, "suppliers": suppliers}


def map_named_suppliers(buyer_name: str, max_tenders: int = 40) -> dict:
    slug = resolve_buyer(buyer_name)
    if not slug:
        return {"buyer": buyer_name, "slug": None, "tenders": [], "suppliers": []}
    tenders = buyer_tenders(slug)[:max_tenders]
    records, supplier_index = [], {}
    for t in tenders:
        info = tender_suppliers(t)
        if not info or not info.get("suppliers"):
            continue
        records.append(info)
        for s in info["suppliers"]:
            key = s["slug"]
            entry = supplier_index.setdefault(key, {"name": s["name"], "slug": key,
                                                     "tenders": [], "categories": set(), "nis2_critical": False})
            entry["tenders"].append(info["title"][:60])
            entry["categories"].add(info["category"])
            entry["nis2_critical"] = entry["nis2_critical"] or info["nis2_critical"]
    suppliers = [{**v, "categories": sorted(v["categories"])} for v in supplier_index.values()]
    return {"buyer": buyer_name, "slug": slug, "tenders": records, "suppliers": suppliers}
