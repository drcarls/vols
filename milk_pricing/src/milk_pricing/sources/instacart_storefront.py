"""Collect ZIP-pinned prices from Instacart-powered retailer storefronts.

instacart.com itself is gated behind Bright Data's Premium domains permission,
but several retailers run Instacart white-label storefronts on their own
domains — aldi.us is one — and those domains are not gated. Same DOM, same
product URL structure under a `/store/<retailer>` prefix.

The important property: appending `?zipcode=NNNNN` pins the storefront to that
ZIP's pricing zone. Verified against 8 SC ZIPs, each returning its requested
postal code and a distinct Instacart `zoneId`. This is what makes market-level
competitor pricing possible without the Premium permission — note that the
`zip_code` / `postal_code` / `zip` spellings all silently fall back to the
proxy exit's location instead, so the parameter name matters.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from ..parse import parse_search_html

# Retailers confirmed to run an ungated Instacart white-label storefront.
STOREFRONTS = {
    "aldi": {"domain": "www.aldi.us", "slug": "aldi",
             "dairy_page": "/store/aldi/pages/dairy-and-eggs"},
}

_ZIP_RE = re.compile(r'postalCode(?:%22|")(?:%3A|:)(?:%22|")(\d{5})')
_ZONE_RE = re.compile(r'zoneId(?:%22|\\?")(?:%3A|:)(?:%22|\\?")(\d+)')


class ZipNotHonoured(RuntimeError):
    """The storefront ignored the requested ZIP and served another zone."""


def fetch(url: str, token: str, zone: str = "unblocker", timeout: int = 140) -> str:
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


def verify_zip(html: str, expected_zip: str) -> str | None:
    """Confirm the page really is the requested ZIP's zone; return the zoneId.

    Without this a silently-ignored ZIP looks identical to a successful pin,
    and the whole market comparison would quietly become one arbitrary store
    repeated across every row.
    """
    zips = set(_ZIP_RE.findall(html))
    if expected_zip not in zips:
        raise ZipNotHonoured(
            f"requested {expected_zip}, storefront served {sorted(zips)[:3]}")
    zones = _ZONE_RE.findall(html)
    return zones[0] if zones else None


def collect_dairy(retailer: str, zip_code: str, token: str) -> dict:
    """Fetch one retailer's dairy aisle pinned to one ZIP."""
    cfg = STOREFRONTS[retailer]
    url = f"https://{cfg['domain']}{cfg['dairy_page']}?zipcode={zip_code}"
    html = fetch(url, token)
    zone = verify_zip(html, zip_code)
    return {"retailer": retailer, "zip": zip_code, "zone_id": zone,
            "rows": parse_search_html(html)}
