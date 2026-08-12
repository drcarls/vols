from __future__ import annotations

"""Domain enrichment: company name -> primary web domain.

EDGAR (and most registries) give a legal name but no website. The homepage
AI/chatbot check and cleaner SERP matching both want a domain, so this
collector resolves one via Clearbit's free autocomplete endpoint
(https://autocomplete.clearbit.com/v1/companies/suggest) -- no API key.

The matcher (``pick_domain``) is a pure, conservative function: it only
accepts a suggestion whose name actually matches the company, so we don't
attach a plausible-but-wrong domain to a prospect. It's unit-tested without
the network; the live lookup degrades to ``None`` when unavailable.
"""

import json
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models import Company

CLEARBIT_URL = "https://autocomplete.clearbit.com/v1/companies/suggest"

_SUFFIXES = (
    " incorporated", " inc", " llc", " l l c", " llp", " l l p", " corp",
    " corporation", " co", " ltd", " limited", " plc", " pllc", " pc", " lp",
    " company", " holdings", " group", " partners", " the",
)


def _norm(name: str) -> str:
    n = (name or "").lower()
    n = n.replace("&", " and ")
    n = re.sub(r"[^a-z0-9\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    # strip trailing legal/entity words (repeatedly)
    changed = True
    while changed:
        changed = False
        for suf in _SUFFIXES:
            if n.endswith(suf):
                n = n[: -len(suf)].strip()
                changed = True
    return n


def pick_domain(suggestions: list[dict], company_name: str) -> str | None:
    """Choose the best-matching domain from Clearbit suggestions, or None.

    Conservative: accepts an exact normalized-name match, else a suggestion
    whose normalized name is a prefix of (or equals) the company's -- never a
    loose partial, so we don't mis-attribute a domain.
    """
    target = _norm(company_name)
    if not target:
        return None
    tokens = target.split()
    exact = None
    prefix = None
    for s in suggestions:
        dom = (s.get("domain") or "").strip().lower()
        if not dom:
            continue
        sn = _norm(s.get("name", ""))
        if not sn:
            continue
        if sn == target and exact is None:
            exact = dom
        elif prefix is None and (target.startswith(sn + " ") or sn.startswith(target + " ")):
            prefix = dom
        elif prefix is None and len(tokens) >= 2 and sn == " ".join(tokens[:2]):
            prefix = dom
    return exact or prefix


def suggest(name: str, timeout: int = 15) -> list[dict]:
    """Query Clearbit autocomplete (network). Returns [] on empty, raises on error."""
    url = CLEARBIT_URL + "?" + urlencode({"query": name})
    req = Request(url, headers={"User-Agent": "questa-scout/0.1 (+prospecting)"})
    with urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    return data if isinstance(data, list) else []


def resolve_domain(name: str, timeout: int = 15) -> str | None:
    """Resolve one company name to a domain, degrading to None on any error.

    Queries Clearbit with the *cleaned* name (legal suffixes drop recall
    sharply) but matches suggestions against the original for correctness.
    """
    try:
        query = _norm(name) or name
        return pick_domain(suggest(query, timeout=timeout), name)
    except Exception:  # noqa: BLE001 -- best-effort enrichment
        return None


def enrich_domains(
    companies: list[Company],
    *,
    polite_delay: float = 0.2,
    offline: bool = False,
) -> tuple[int, int]:
    """Fill in ``domain`` for companies missing one. Returns (resolved, attempted).

    offline=True skips the network entirely (leaves domains as-is).
    """
    resolved = attempted = 0
    for c in companies:
        if c.domain or offline:
            continue
        attempted += 1
        dom = resolve_domain(c.name)
        if dom:
            c.domain = dom
            resolved += 1
        if polite_delay:
            time.sleep(polite_delay)
    return resolved, attempted
