"""Parse Harris Teeter (Kroger platform) search results.

Two behaviours worth knowing before using this:

* **Rate limiting.** harristeeter.com returns a 77-byte "global adaptive rate
  limit" body far more often than it returns a page. It is not a permission
  error and retrying with backoff clears it, so callers must retry on a short
  body rather than treating it as a failure.
* **Store follows the proxy exit.** There is no working ZIP or store URL
  parameter — `zipcode`, `zip`, `storeCode` and `locationId` were all tested
  and none pins the store. The page names its store in "Pickup at <store>",
  which is the only reliable way to know which store a price belongs to, so
  every row must carry it.

Products render as a flat run of text rather than discrete tiles:

    $2.99 Discounted From Harris Teeter 2% Reduced Fat Milk 1 gal SNAP EBT

so entries are recovered by splitting on the "Sign In to Add" terminator that
closes each tile.
"""

from __future__ import annotations

import html
import re

_TILE_SPLIT = re.compile(r"Sign In to Add")
_PRICE = re.compile(r"\$(\d+\.\d{2})")
_SIZE = re.compile(r"(\d+(?:\.\d+)?\s*(?:fl oz|oz|gal|ct)|1/2\s*gal|half gallon)", re.I)
_STORE = re.compile(r"Pickup at (.{5,60}?) (?:Weekly|Shop|Cart|$)")
_NOISE = re.compile(
    r"\b(Discounted From|SNAP EBT|Sponsored|Featured|Add to List|Buy \d)\b", re.I)

# Harris Teeter's own labels. Kroger's Simple Truth is a sibling private label
# but an organic tier, so it is not the conventional benchmark.
PRIVATE_LABEL = ("harris teeter", "ht traders", "highland crest")


def visible_text(page_html: str) -> str:
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", page_html)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def store_name(page_html: str) -> str | None:
    m = _STORE.search(visible_text(page_html))
    return m.group(1).strip() if m else None


def parse_search(page_html: str) -> list[dict]:
    """Return {name, size, price} rows from a rendered HT search page."""
    text = visible_text(page_html)
    rows: list[dict] = []
    for chunk in _TILE_SPLIT.split(text):
        pm = _PRICE.search(chunk)
        if not pm:
            continue
        # The tile's own price is the first one; a following "Discounted From
        # $X" is the struck-through was-price and must not be picked up.
        price = float(pm.group(1))

        tail = chunk[pm.end():]
        sm = _SIZE.search(tail)
        size = sm.group(1).strip() if sm else ""

        name = tail[:sm.start()] if sm else tail
        name = _NOISE.sub(" ", name)
        name = re.sub(r"\$\d+\.\d{2}", " ", name)
        name = re.sub(r"\s+", " ", name).strip(" -–—|")
        if not name or len(name) < 4:
            continue
        rows.append({"name": name, "size": size, "price": price,
                     "brand": "", "in_stock": True, "id": f"{name}|{size}"})
    return rows
