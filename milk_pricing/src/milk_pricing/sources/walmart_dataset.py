"""Adapter: Bright Data 'Walmart - products' records -> pipeline rows.

Keyword discovery against walmart.com returns the full marketplace long tail,
not a grocery shelf: shelf-stable powder, #10 survival cans, bulk multipacks
from third-party sellers. Those carry real prices, so nothing upstream filters
them out, and left in they destroy every per-gallon statistic. The guards here
are the ones that matter.
"""

from __future__ import annotations

import re

FL_OZ_PER_GAL = 128.0

# Marketplace tells. A "milk" keyword search surfaces all of these.
_MARKETPLACE = (
    "powder", "dry milk", "instant nonfat", "long shelf life", "survival",
    "food storage", "#10 can", "emergency", "drink mix", "freeze dried",
    "freeze-dried", "condensed", "evaporated", "creamer", "formula",
)

# A refrigerated gallon of milk has never cost $60. Anything outside this
# per-gallon band is a bulk or marketplace listing wearing a milk name.
MIN_PPG, MAX_PPG = 1.00, 20.00


def _looks_marketplace(name: str) -> bool:
    n = name.lower()
    return any(t in n for t in _MARKETPLACE)


def to_rows(records: list[dict]) -> list[dict]:
    """Map dataset records into the {name, brand, size, price} shape the
    normaliser expects, dropping what cannot be a grocery milk purchase."""
    rows = []
    for r in records:
        price = r.get("final_price")
        name = (r.get("product_name") or "").strip()
        if price is None or not name:
            continue
        if _looks_marketplace(name):
            continue

        # Prefer the size stated in the title. Back-solving from unit_price
        # (which Walmart rounds to 3dp) turns a 128 oz gallon into "130.0 fl
        # oz" and quietly biases every $/gal figure, so it is only a fallback.
        size = ""
        if m := re.search(r"(\d+(?:\.\d+)?)\s*(fl oz|oz)\b", name, re.I):
            size = f"{m.group(1)} {m.group(2)}"
        elif re.search(r"\bhalf[- ]gallon\b", name, re.I):
            size = "64 fl oz"
        elif re.search(r"\bgallon\b", name, re.I):
            size = "128 fl oz"
        elif m := re.search(r"(\d+(?:\.\d+)?)\s*(gal|qt|pt)\b", name, re.I):
            size = f"{m.group(1)} {m.group(2)}"
        else:
            unit = r.get("unit_price")
            if unit and 0 < unit < 1:
                size = f"{round(price / unit, 1)} fl oz"

        rows.append({
            "id": str(r.get("sku") or r.get("product_id") or ""),
            "name": name,
            "brand": (r.get("brand") or "").strip(),
            "size": size,
            "price": float(price),
            "in_stock": bool(r.get("in_stock", True)),
            "store_id": str(r.get("store_id") or ""),
            "category_name": r.get("category_name") or "",
        })
    return rows


def plausible(observation: dict) -> bool:
    """Final per-gallon sanity gate, applied after normalisation."""
    ppg = observation.get("price_per_gal")
    return ppg is not None and MIN_PPG <= ppg <= MAX_PPG
