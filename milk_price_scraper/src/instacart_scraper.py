"""Orchestrates Instacart milk-price collection across ZIP codes.

Two strategies:

  dataset  -> uses Bright Data's managed Instacart Web Scraper API (recommended)
  unlocker -> fetches Instacart search HTML via Web Unlocker and best-effort parses it

The output is always normalized to the same flat schema so downstream analysis
(analyze.py) doesn't care which strategy produced the data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from typing import Any, Iterable
from urllib.parse import quote_plus

from brightdata_client import BrightDataClient, BrightDataError

# Canonical output columns.
FIELDNAMES = [
    "scraped_at",
    "zip",
    "city",
    "county",
    "region",
    "cohort_label",
    "query",
    "retailer",
    "product_name",
    "brand",
    "size",
    "price",
    "unit_price",
    "in_stock",
    "product_url",
    "source_strategy",
]


@dataclass
class PriceRecord:
    scraped_at: str
    zip: str
    city: str = ""
    county: str = ""
    region: str = ""
    cohort_label: str = ""
    query: str = ""
    retailer: str = ""
    product_name: str = ""
    brand: str = ""
    size: str = ""
    price: float | None = None
    unit_price: str = ""
    in_stock: str = ""
    product_url: str = ""
    source_strategy: str = ""

    def as_row(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
_PRICE_RE = re.compile(r"(\d+[\.,]?\d{0,2})")


def _coerce_price(value: Any) -> float | None:
    """Pull a float price out of whatever Instacart/Bright Data hands us."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _PRICE_RE.search(str(value).replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _first(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    """Return the first present, non-empty value among candidate keys."""
    for key in keys:
        if key in row and row[key] not in (None, "", []):
            return row[key]
    return default


# --------------------------------------------------------------------------- #
# Dataset (Web Scraper API) strategy
# --------------------------------------------------------------------------- #
def build_dataset_inputs(
    zips: list[dict[str, str]],
    products: list[dict[str, str]],
    retailers: list[str] | None,
) -> list[dict[str, Any]]:
    """Build the input records for the Bright Data Instacart collector.

    Bright Data's Instacart collectors accept a search URL plus a zip. Exact
    accepted field names vary by dataset; we send both `url` and `zipcode`
    (and `keyword`) which covers the common collector shapes. Adjust to match
    the input schema shown on your dataset's Bright Data page if needed.
    """
    inputs: list[dict[str, Any]] = []
    for z in zips:
        for p in products:
            query = p["query"]
            search_url = f"https://www.instacart.com/store/s?k={quote_plus(query)}"
            record: dict[str, Any] = {
                "url": search_url,
                "keyword": query,
                "zipcode": z["zip"],
            }
            if retailers:
                record["retailers"] = retailers
            inputs.append(record)
    return inputs


def normalize_dataset_row(
    raw: dict[str, Any],
    zip_meta: dict[str, str],
    query: str,
    scraped_at: str,
) -> PriceRecord:
    return PriceRecord(
        scraped_at=scraped_at,
        zip=zip_meta.get("zip", ""),
        city=zip_meta.get("city", ""),
        county=zip_meta.get("county", ""),
        region=zip_meta.get("region", ""),
        cohort_label=zip_meta.get("cohort_label", ""),
        query=query,
        retailer=str(_first(raw, "retailer", "store", "store_name", "shop")),
        product_name=str(_first(raw, "product_name", "name", "title")),
        brand=str(_first(raw, "brand", "brand_name")),
        size=str(_first(raw, "size", "package_size", "unit_size", "weight")),
        price=_coerce_price(_first(raw, "price", "final_price", "current_price", "amount")),
        unit_price=str(_first(raw, "unit_price", "price_per_unit", "pricePerUnit")),
        in_stock=str(_first(raw, "in_stock", "availability", "available")),
        product_url=str(_first(raw, "product_url", "url", "link")),
        source_strategy="dataset",
    )


# --------------------------------------------------------------------------- #
# Unlocker strategy (best-effort HTML/JSON parse)
# --------------------------------------------------------------------------- #
_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def _walk_for_products(node: Any) -> Iterable[dict[str, Any]]:
    """Recursively yield dict nodes that look like product items."""
    if isinstance(node, dict):
        keys = {k.lower() for k in node.keys()}
        looks_like_product = ("name" in keys or "title" in keys) and any(
            k in keys for k in ("price", "pricing", "price_string", "priceperunit")
        )
        if looks_like_product:
            yield node
        for value in node.values():
            yield from _walk_for_products(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_for_products(item)


def parse_unlocker_html(html: str) -> list[dict[str, Any]]:
    """Best-effort extraction of product-like dicts from an Instacart page."""
    products: list[dict[str, Any]] = []
    match = _NEXT_DATA_RE.search(html)
    if match:
        try:
            data = json.loads(match.group(1))
            products.extend(_walk_for_products(data))
        except json.JSONDecodeError:
            pass
    return products


def normalize_unlocker_row(
    raw: dict[str, Any],
    zip_meta: dict[str, str],
    query: str,
    scraped_at: str,
) -> PriceRecord:
    price_val = _first(raw, "price", "pricing", "price_string", "pricePerUnit")
    if isinstance(price_val, dict):
        price_val = _first(price_val, "price", "value", "amount")
    return PriceRecord(
        scraped_at=scraped_at,
        zip=zip_meta.get("zip", ""),
        city=zip_meta.get("city", ""),
        county=zip_meta.get("county", ""),
        region=zip_meta.get("region", ""),
        cohort_label=zip_meta.get("cohort_label", ""),
        query=query,
        retailer=str(_first(raw, "retailer", "store", "shop")),
        product_name=str(_first(raw, "name", "title")),
        brand=str(_first(raw, "brand")),
        size=str(_first(raw, "size", "package_size")),
        price=_coerce_price(price_val),
        unit_price=str(_first(raw, "unit_price", "pricePerUnit")),
        in_stock=str(_first(raw, "in_stock", "available")),
        product_url=str(_first(raw, "product_url", "url")),
        source_strategy="unlocker",
    )
