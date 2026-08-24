"""Collect a multi-SKU basket from store-pinned Walmart pages via Bright Data.

Extends `walmart_page` from one SKU to many, and adds the piece that module
lacks: **store pinning with verification**.

The defect this exists to prevent is documented in this project's history. A
Walmart product page served through a proxy resolves whichever store the proxy
exit happens to sit near. An earlier sample came back with 5 of 7 ZIPs equal to
the proxy's ZIP rather than the store's, and a later catalogue pull returned 295
SKUs all attributed to store 3081 in Sacramento. Both looked like clean data.

So this module never trusts a returned page. It asks for a ZIP, reads the ZIP the
page actually resolved to, and raises `StoreMismatch` when they differ. A row that
cannot be verified is dropped, not recorded — an unpinned price is worse than a
missing one, because a dispersion comparison built on proxy-exit stores measures
the proxy.

STATUS, tested 2026-08-24 against the project's Bright Data account
--------------------------------------------------------------------
**No pinning strategy in `_strategies` works on that account, so `fetch_pinned`
raises StoreMismatch for every ZIP.** The account holds one zone (`unblocker`,
no geo targeting) and the serving store is decided by the scraper's exit IP:

  * `zip` / `state` in the Web Unlocker payload -> empty response (not valid
    fields for this zone)
  * `?storeId=`, `?athstid=`, `?location=` -> ignored; successive requests
    resolved to Sacramento, Nashville and Ashburn
  * `locGuestData` / `ASSORTMENT_STORE_ID` cookies -> ignored; still Sacramento
  * the Dataset API's `zipcode` input field -> silently dropped, not echoed back

The module is kept because the *verification* is the durable part: it is what
turns that failure into a visible error instead of a file full of proxy-exit
prices. Give it a geo-targeted zone (residential/ISP with `country-state-city`
in the proxy username) and the same guard makes the result trustworthy.

For the collection that did work without pinning — a random national sample,
which supports a cross-product dispersion comparison but not a geographic one —
see `analysis/walmart_basket_national.py`.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from .walmart_page import Rejected, _ITEM_RE, _PRICE_RE, _UNIT_RE, read_shelf_price

_STORE_ID_RE = re.compile(r'"storeId"\s*:\s*"?(\d+)')
_POSTAL_RE = re.compile(r'"postalCode"\s*:\s*"(\d{5})')
_CITY_RE = re.compile(r'"city"\s*:\s*"([^"]{2,32})"')
_STATE_RE = re.compile(r'"stateOrProvinceCode"\s*:\s*"([A-Z]{2})"')
_SEARCH_ITEM_RE = re.compile(r'"usItemId"\s*:\s*"(\d+)"[^}]{0,4000}?"name"\s*:\s*"([^"]{4,120})"')

BD_ENDPOINT = "https://api.brightdata.com/request"


class StoreMismatch(Exception):
    """The page resolved to a different store than the one requested."""


def _post(payload: dict, token: str, timeout: int) -> str:
    req = urllib.request.Request(
        BD_ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", "replace")


# Store-pinning strategies, tried in order. Each returns a URL and any extra
# Bright Data geo parameters. All four were tested on 2026-08-24 and none pinned
# the store (see the module docstring); they are kept so a future account with a
# geo-targeted zone can be tried against the same verification path.
def _strategies(sku: str, zip_code: str) -> list[tuple[str, dict]]:
    base = f"https://www.walmart.com/ip/{sku}"
    return [
        (f"{base}?athstid=&fulfillmentIntent=In-Store", {"zip": zip_code}),
        (f"{base}", {"zip": zip_code}),
        (f"{base}?location={zip_code}", {}),
        (f"{base}", {}),  # last resort: unpinned, still verified (will usually fail)
    ]


def store_context(html: str) -> dict:
    first = lambda rx: (m.group(1) if (m := rx.search(html)) else None)
    return {"store_id": first(_STORE_ID_RE), "zip": first(_POSTAL_RE),
            "city": first(_CITY_RE), "state": first(_STATE_RE)}


def fetch_pinned(sku: str, zip_code: str, token: str, *, size_fl_oz: float = 128.0,
                 zone: str = "unblocker", timeout: int = 150,
                 verify: bool = True) -> dict:
    """Shelf price for `sku` at the store serving `zip_code`.

    Raises StoreMismatch if no strategy resolves to the requested ZIP, or
    Rejected if every attempt returned an unusable page.
    """
    last = None
    for url, geo in _strategies(sku, zip_code):
        payload = {"zone": zone, "url": url, "format": "raw", "country": "us", **geo}
        html = _post(payload, token, timeout)
        try:
            row = read_shelf_price(html, sku, size_fl_oz=size_fl_oz)
        except Rejected as e:
            last = e
            continue
        ctx = store_context(html)
        row.update({k: v for k, v in ctx.items() if v})
        row["requested_zip"] = zip_code
        row["pinned_via"] = url.split("?", 1)[1] if "?" in url else ("geo" if geo else "none")
        if not verify or ctx.get("zip") == zip_code:
            row["verified"] = True
            return row
        last = StoreMismatch(f"asked {zip_code}, page resolved {ctx.get('zip')} "
                             f"(store {ctx.get('store_id')})")
    raise last or Rejected("no strategy produced a usable page")


def resolve_skus(query: str, token: str, *, zone: str = "unblocker",
                 timeout: int = 150, limit: int = 8) -> list[tuple[str, str]]:
    """Search walmart.com and return [(sku, name)] candidates for a query.

    Needed because item ids for non-milk staples are not in any file we hold.
    Review the candidates before collecting — a search for a private-label
    staple returns third-party listings alongside the shelf item.
    """
    url = "https://www.walmart.com/search?q=" + urllib.parse.quote(query)
    html = _post({"zone": zone, "url": url, "format": "raw", "country": "us"},
                 token, timeout)
    out, seen = [], set()
    for sku, name in _SEARCH_ITEM_RE.findall(html):
        if sku in seen:
            continue
        seen.add(sku)
        out.append((sku, name))
        if len(out) >= limit:
            break
    return out


def collect(skus: dict[str, dict], zips: list[str], token: str, *,
            pause: float = 1.0, on_row=None, on_error=None) -> list[dict]:
    """Cross `skus` x `zips`. `skus` maps a short column name to
    {"sku": ..., "size_fl_oz": ...} (size only matters for fluid items).

    Every row is store-verified. Failures are reported through `on_error` and
    omitted from the result rather than filled with an unpinned price.
    """
    rows = []
    for z in zips:
        for col, spec in skus.items():
            try:
                r = fetch_pinned(spec["sku"], z, token,
                                 size_fl_oz=spec.get("size_fl_oz", 128.0))
                r["item"] = col
                rows.append(r)
                if on_row:
                    on_row(r)
            except (Rejected, StoreMismatch) as e:
                if on_error:
                    on_error(z, col, e)
            time.sleep(pause)
    return rows
