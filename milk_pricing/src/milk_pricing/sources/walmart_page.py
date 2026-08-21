"""Fetch a Walmart product page through Bright Data and read its shelf price.

The subtle failure this module exists to prevent:

Walmart serves the requested product URL even when the resolved local store
does not carry the item — but it fills the page with a **third-party
marketplace offer** under the same product title. That offer is a national
shipped price, not a store shelf price. In sampling it showed up as an
identical $9.97 across four different states while the genuine shelf price
ranged $2.16–$3.52.

It survives the obvious sanity checks: the price is internally consistent
with the stated cents-per-fl-oz, availability reads IN_STOCK, and the page
title is the product you asked for. The only reliable discriminator is item
identity — the page's primary `usItemId` must equal the SKU requested.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

_PRICE_RE = re.compile(r'"priceString"\s*:\s*"\$([\d.]+)"')
_UNIT_RE = re.compile(r'"priceString"\s*:\s*"([\d.]+)\s*¢/fl oz"')
_ITEM_RE = re.compile(r'"usItemId"\s*:\s*"(\d+)"')
_STORE_RE = re.compile(r'"storeId"\s*:\s*"?(\d+)')
_CITY_RE = re.compile(r'"city"\s*:\s*"([^"]{2,24})"')
_STATE_RE = re.compile(r'"stateOrProvinceCode"\s*:\s*"([A-Z]{2})"')
_ZIP_RE = re.compile(r'"postalCode"\s*:\s*"(\d+)"')

# Tolerance between the shelf price and the price implied by cents/fl oz.
# Walmart rounds the unit price to one decimal, so exact equality never holds.
_UNIT_TOLERANCE = 0.06


class Rejected(Exception):
    """The page did not describe the SKU we asked for."""


def fetch_page(url: str, token: str, zone: str = "unblocker",
               timeout: int = 150) -> str:
    payload = {"zone": zone, "url": url, "format": "raw", "country": "us"}
    req = urllib.request.Request(
        "https://api.brightdata.com/request",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", "replace")


def read_shelf_price(html: str, expect_sku: str, size_fl_oz: float = 128.0) -> dict:
    """Return the store shelf price for `expect_sku`, or raise Rejected.

    Rejects, in order: an empty/blocked response, a page whose primary item is
    not the requested SKU (the marketplace substitution above), and a price
    that the stated unit price fails to corroborate.
    """
    if not html or len(html) < 600:
        raise Rejected("empty or blocked response")

    items = _ITEM_RE.findall(html)
    if not items:
        raise Rejected("no usItemId on page")
    # On a genuine store page the requested SKU is the page's primary item and
    # appears first. When Walmart substitutes a marketplace offer, the seller's
    # item id takes that slot and the canonical SKU is merely referenced later
    # — so "appears somewhere on the page" is not good enough.
    if items[0] != expect_sku:
        raise Rejected(f"page primary item is {items[0]}, not {expect_sku}")

    pm = _PRICE_RE.search(html)
    if not pm:
        raise Rejected("no price on page")
    price = float(pm.group(1))

    um = _UNIT_RE.search(html)
    if um:
        implied = float(um.group(1)) * size_fl_oz / 100
        if abs(implied - price) / price > _UNIT_TOLERANCE:
            raise Rejected(f"price ${price} contradicts unit price (${implied:.2f})")

    first = lambda rx: (m.group(1) if (m := rx.search(html)) else None)
    return {
        "sku": expect_sku,
        "price": price,
        "store_id": first(_STORE_RE),
        "city": first(_CITY_RE),
        "state": first(_STATE_RE),
        "zip": first(_ZIP_RE),
        "price_per_gal": round(price * 128.0 / size_fl_oz, 2),
    }
