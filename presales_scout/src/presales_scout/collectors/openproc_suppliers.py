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

from . import _doh

BASE = "https://se.openprocurements.com"

_STOP = {"ab", "aktiebolag", "sverige", "sweden", "group", "holding", "publ", "i", "of",
         "and", "the", "management", "consulting", "konsult", "co", "kommanditbolag",
         "kb", "hb", "norr", "syd", "ost", "vast", "sverige"}

# Swedish keyword -> (category, nis2_critical) for a coarse tender-title guess.
# NOTE: title keywords are a WEAK proxy — they over-match (e.g. "konsult"
# flags every architect). Reliable per-supplier categorisation needs the
# supplier's registered SNI industry code (org number -> Bolagsverket/allabolag),
# not this. Kept deliberately conservative to minimise false positives.
_CATS = [
    (("scada", "reglerteknik", "transformator", "ställverk", "elnät", "fjärrkontroll"), ("ot_control", True)),
    (("passersystem", "inbrottslarm", "cctv", "informationssäker", "cybersäker"), ("security", True)),
    (("telefoni", "telekom", "bredband", "fibernät"), ("telecom", True)),
    (("it-konsult", "it-drift", "it-support", "programvara", "mjukvara", "licens",
      "informationssystem", "affärssystem", "verksamhetssystem", "molntjänst", "datacenter"), ("ict", True)),
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


def supplier_profile(slug: str) -> dict:
    """Enrich a supplier from its own page: org number, full public-sector
    reach (all buyers it supplies), and category aggregated from its tenders.
    """
    try:
        page = _get(f"{BASE}/supplier/{slug}/")
    except Exception:
        return {"slug": slug, "org_number": None, "buyers": [], "reach": 0, "categories": []}
    m = re.search(r"<title>(.*?)</title>", page, re.S)
    name = html.unescape(re.sub(r"(?i)^leverantör:\s*", "", m.group(1).strip())) if m else slug
    org = re.search(r"\b(55\d{4}[-\s]?\d{4})\b", page)
    org = org.group(1).replace(" ", "").replace("-", "") if org else None
    if org:
        org = f"{org[:6]}-{org[6:]}"
    buyers = sorted(set(re.findall(r"/buyer/([a-z0-9\-]+)/", page)))
    titles = re.findall(r'/tender/[a-z0-9\-]+/"[^>]*>\s*([^<]{4,90})</a>', page)
    cats, crit = set(), False
    for t in titles:
        c, k = _categorize(html.unescape(t))
        cats.add(c); crit = crit or k
    return {"slug": slug, "name": name, "org_number": org, "buyers": buyers,
            "reach": len(buyers), "categories": sorted(cats), "nis2_critical": crit}


def map_named_suppliers(buyer_name: str, max_tenders: int | None = 40) -> dict:
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


def _name_tokens(name: str) -> list[str]:
    s = name.lower()
    for a, b in (("å", "a"), ("ä", "a"), ("ö", "o"), ("é", "e"), ("ü", "u"), ("ø", "o"), ("æ", "a")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return [t for t in s.split() if t and t not in _STOP and len(t) > 1]


def resolve_domain(name: str) -> str:
    """Best-effort company domain, VERIFIED by ownership.

    Generates candidate domains from the name's brand tokens, keeps only those
    that (a) have an A record and (b) show the brand on their homepage — so a
    coincidentally-registered domain like 'general.se' is rejected for
    'General Architecture AB'. Returns '' when nothing verifies.
    """
    toks = _name_tokens(name)
    if not toks:
        return ""
    # only distinctive brands (>=4 chars) are trustworthy for ownership matching;
    # 2-3 char fragments ('af', 'al') match almost any page as a substring.
    brands = {t for t in toks[:3] if len(t) >= 4}
    if len(toks) >= 2:
        brands.add("".join(toks[:2]))
    if not brands:
        return ""
    cands = []
    for t in toks[:3]:
        cands += [t + ".se", t + ".com"]
    if len(toks) >= 2:
        cands += ["".join(toks[:2]) + ".se", "".join(toks[:2]) + ".com"]
    seen = set()
    for cand in [c for c in cands if not (c in seen or seen.add(c))]:
        if not _doh.has_record(cand, "A"):
            continue
        try:
            body = _get("https://" + cand, timeout=12)[:6000].lower()
        except Exception:
            continue
        # brand must appear as a whole word, not an incidental substring
        if any(re.search(r"\b" + re.escape(b) + r"\b", body) for b in brands):
            return cand
    return ""
