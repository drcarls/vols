"""Extract product rows from a rendered Instacart page.

Instacart's class names are emotion-hashed (`e-1gh06cz`) and rotate on every
deploy, so nothing here keys on them. The anchors used are the semantic ones
that have to stay put for the page to remain accessible and linkable:

  * `data-testid="item_list_item_..."`   tile boundary
  * `href="/products/<id>-<slug>"`       product id and slug
  * `<span class="screen-reader-only">Current price: $X</span>`
  * `<h3>`                               display name
  * "... in stock" / "Out of stock"      availability
"""

from __future__ import annotations

import html
import re

_TILE_RE = re.compile(r'<li[^>]*data-testid="item_list_item[^"]*"', re.I)
# instacart.com uses /products/<id>-<slug>; the white-label storefronts
# (aldi.us, lidl.com and friends, all Instacart-powered) prefix it with
# /store/<retailer>. Same DOM otherwise, so one pattern serves both.
_PRODUCT_HREF_RE = re.compile(
    r'href="(?:/store/[a-z0-9-]+)?/products/(\d+)-([^"?]+)', re.I)
# The screen-reader node is the authoritative current price: it is the one the
# page guarantees reflects the promo price rather than the struck-through was-price.
_SR_PRICE_RE = re.compile(
    r'screen-reader-only[^>]*>\s*Current price:\s*\$([\d,]+\.?\d*)', re.I)
_ANY_PRICE_RE = re.compile(r'\$([\d,]+\.\d{2})')
_H3_RE = re.compile(r"<h3[^>]*>(.*?)</h3>", re.I | re.S)
_STOCK_RE = re.compile(r">\s*(Out of stock|Many in stock|\d+\s+in stock)\s*<", re.I)
_WAS_PRICE_RE = re.compile(r"Original Price:\s*\$([\d,]+\.?\d*)", re.I)
_PROMO_RE = re.compile(r">\s*(Rollback|Spend \$[\d.]+, save \$[\d.]+|\d+% off)\s*<", re.I)
# Size appears as its own small text node after the title: "14 oz", "1 gal".
_SIZE_TEXT_RE = re.compile(
    r">\s*((?:about\s+)?[\d.]+\s*(?:x|×)?\s*[\d.]*\s*"
    r"(?:fl oz|floz|oz|gal|gallon|qt|quart|pt|pint|ml|l|lb|ct|each)\b[^<]{0,12})\s*<",
    re.I)


def _text(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", fragment)).strip()


def _slug_to_size(slug: str) -> str:
    """Fall back to the URL slug when no size node rendered.
    'great-value-whole-milk-1-gal' -> '1 gal'."""
    m = re.search(
        r"-((?:\d+-)*\d+(?:-\d+)?)-(fl-oz|oz|gal|gallon|qt|quart|pt|pint|ml|l)$",
        slug, re.I)
    if not m:
        return ""
    return f"{m.group(1).replace('-', '.')} {m.group(2).replace('-', ' ')}"


def parse_search_html(page_html: str) -> list[dict]:
    """Return one dict per product tile found on a rendered search/aisle page."""
    if not page_html:
        return []

    bounds = [m.start() for m in _TILE_RE.finditer(page_html)]
    if not bounds:
        return []
    bounds.append(len(page_html))

    rows: list[dict] = []
    for i in range(len(bounds) - 1):
        tile = page_html[bounds[i]:bounds[i + 1]]

        href = _PRODUCT_HREF_RE.search(tile)
        if not href:
            continue
        pid, slug = href.group(1), href.group(2)

        pm = _SR_PRICE_RE.search(tile) or _ANY_PRICE_RE.search(tile)
        if not pm:
            continue
        price = float(pm.group(1).replace(",", ""))

        h3 = _H3_RE.search(tile)
        name = _text(h3.group(1)) if h3 else slug.replace("-", " ")

        size = ""
        if sm := _SIZE_TEXT_RE.search(tile):
            size = sm.group(1).strip()
        if not size:
            size = _slug_to_size(slug)

        stock = _STOCK_RE.search(tile)
        was = _WAS_PRICE_RE.search(tile)
        promo = _PROMO_RE.search(tile)

        rows.append({
            "id": pid,
            "slug": slug,
            "name": name,
            "brand": "",          # resolved from name downstream
            "size": size,
            "price": price,
            "was_price": float(was.group(1).replace(",", "")) if was else None,
            "promo": promo.group(1) if promo else None,
            "in_stock": not (stock and stock.group(1).lower() == "out of stock"),
        })

    # A search page can repeat a product across carousels; keep the first.
    seen, unique = set(), []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        unique.append(r)
    return unique
