"""Collect ZIP-pinned Aldi prices from the aldi.us Instacart white-label storefront.

Supersedes the HTML-scraping path in `instacart_storefront.py` for Aldi. As of
2026-09-16 the dairy page ships NO prices in its rendered HTML -- zero "$" literals,
no __NEXT_DATA__ -- because the product grid is client-rendered. The data is still
in the document, inside the `node-apollo-state` script tag as URL-encoded JSON.

Two properties make this worth having, and they are exactly what the Walmart routes
lack (see reports/brightdata_zipcode_trap.md section 9):

  * `?zipcode=NNNNN` genuinely pins the pricing zone, server-side. Verified against
    the August 2026 collection: every ZIP re-tested returned its previously recorded
    zoneId.
  * aldi.us serves this container directly. No proxy, no unblocker, no credential.

WHY THE PARSER WALKS THE JSON INSTEAD OF REGEXING THE PAGE. A first attempt paired
each item name with the next `priceString` within a fixed character window. That
produced two different prices for two ZIPs sharing zone 348, which is impossible --
Aldi prices by zone. Item records are not fixed-width and the window ran into
neighbouring items. Every price here is read from inside the same object as the name
it is attributed to.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
PAGE = "https://www.aldi.us/store/aldi/pages/dairy-and-eggs?zipcode={zip}"
_APOLLO = re.compile(r'id="node-apollo-state"[^>]*>(.*?)</script>', re.S)
_ZIP = re.compile(r'postalCode(?:%22|")(?:%3A|:)(?:%22|")(\d{5})')
_PRICE = re.compile(r'^\$(\d+\.\d\d)$')


class ZipNotHonoured(RuntimeError):
    """The storefront ignored the requested ZIP and served another zone."""


def fetch(zip_code: str, timeout: int = 70) -> str:
    req = urllib.request.Request(PAGE.format(zip=zip_code),
                                 headers={"User-Agent": UA,
                                          "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _price_of(item: dict) -> float | None:
    """The item's own price, read from within the item object only."""
    vs = (item.get("price") or {}).get("viewSection") or {}
    s = vs.get("priceString")
    m = _PRICE.match(s) if isinstance(s, str) else None
    return float(m.group(1)) if m else None


def parse(html: str, expected_zip: str) -> dict:
    """{'zip','zone','shop','items': {(name, size): price}} for one pinned ZIP."""
    zips = set(_ZIP.findall(html))
    if expected_zip not in zips:
        raise ZipNotHonoured(f"asked {expected_zip}, storefront served {sorted(zips)[:3]}")
    m = _APOLLO.search(html)
    if not m:
        raise RuntimeError("node-apollo-state not present")
    state = json.loads(urllib.parse.unquote(m.group(1)))

    items: dict[tuple[str, str], float] = {}
    zone = shop = None

    def walk(o):
        nonlocal zone, shop
        if isinstance(o, dict):
            name, size = o.get("name"), o.get("size")
            if isinstance(name, str) and isinstance(size, str) and "price" in o:
                p = _price_of(o)
                if p is not None:
                    items.setdefault((name, size), p)
            for k, v in o.items():
                # the Apollo cache key carries the resolved zone and store
                if zone is None and isinstance(k, str) and '"zoneId"' in k:
                    try:
                        meta = json.loads(k[k.index("{"):])
                        zone, shop = meta.get("zoneId"), meta.get("shopId")
                    except Exception:
                        pass
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(state)
    return {"zip": expected_zip, "zone": zone, "shop": shop, "items": items}


WHOLE_GAL = (re.compile(r"whole milk", re.I), re.compile(r"^1 gal$", re.I))


def whole_milk_gallon(items: dict) -> tuple[str, float] | None:
    """Aldi's own-label whole milk gallon — the series used across this project."""
    for (name, size), price in items.items():
        if WHOLE_GAL[0].search(name) and WHOLE_GAL[1].match(size.strip()) \
           and "lactose" not in name.lower():
            return name, price
    return None
