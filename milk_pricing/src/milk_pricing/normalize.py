"""Turn raw Instacart product rows into comparable milk price observations.

Everything downstream depends on this module getting three things right:
  1. Excluding non-milk that a "milk" search returns (creamers, cream, plant).
  2. Resolving pack size to fluid ounces so prices become $/gal.
  3. Splitting private label from national brand, since Walmart's milk price
     position is really a Great-Value-vs-their-private-label question.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict

from .markets import BY_SLUG, MARKET_OF_ZIP, private_label_brands

FL_OZ_PER_GAL = 128.0

# --- size parsing -----------------------------------------------------------

_UNIT_FL_OZ = {
    "gal": 128.0, "gallon": 128.0, "gallons": 128.0,
    "qt": 32.0, "quart": 32.0, "quarts": 32.0,
    "pt": 16.0, "pint": 16.0, "pints": 16.0,
    "l": 33.814, "liter": 33.814, "litre": 33.814,
    "ml": 0.033814,
    "fl oz": 1.0, "floz": 1.0, "oz": 1.0,
}
_UNIT_RE = "|".join(sorted((re.escape(u) for u in _UNIT_FL_OZ), key=len, reverse=True))

# "40 x 16.9 fl oz", "12 x 8 fl oz"
_MULTI_RE = re.compile(rf"(\d+)\s*(?:x|×)\s*(\d+(?:\.\d+)?)\s*({_UNIT_RE})\b", re.I)
# "1 gal", "0.5 gal", "64 fl oz", "1.89 L"
_SINGLE_RE = re.compile(rf"(\d+(?:\.\d+)?)\s*({_UNIT_RE})\b", re.I)
# "half gallon", "1/2 gal"
_FRACTION_RE = re.compile(r"(?:half|1/2)\s*(gal|gallon)\b", re.I)
# A bare unit with no leading quantity ("gallon", "quart") means one of it.
# Instacart uses this form freely, so it is not an edge case.
_BARE_RE = re.compile(rf"\b({_UNIT_RE})\b", re.I)


def parse_size_fl_oz(size_text: str | None) -> tuple[float | None, int]:
    """Return (total fluid ounces, pack count). (None, 1) if unparseable."""
    if not size_text:
        return None, 1
    s = size_text.lower().replace(",", "")

    if m := _MULTI_RE.search(s):
        count, each, unit = int(m.group(1)), float(m.group(2)), m.group(3)
        return count * each * _UNIT_FL_OZ[unit], count

    if _FRACTION_RE.search(s):
        return 64.0, 1

    if m := _SINGLE_RE.search(s):
        qty, unit = float(m.group(1)), m.group(2)
        return qty * _UNIT_FL_OZ[unit], 1

    # Bare "gallon"/"quart" implies quantity 1. Guard against a bare "oz"/"ml"
    # match, which without a number carries no quantity information at all.
    if m := _BARE_RE.search(s):
        unit = m.group(1).lower()
        if unit not in ("oz", "fl oz", "floz", "ml", "l"):
            return _UNIT_FL_OZ[unit], 1

    return None, 1


# --- classification ---------------------------------------------------------

# A "milk" search is mostly not milk. Order matters: exclusions run first.
_PLANT = ("almond", "oat", "soy", "coconut", "cashew", "rice milk", "pea ",
          "hemp", "macadamia", "pistachio", "flax", "banana milk")
# Dairy products whose names legitimately contain "whole milk" — ricotta is
# literally "Whole Milk Ricotta Cheese" — and which a fat/size classifier will
# otherwise wave straight through into the milk benchmark. One such item priced
# a 15 oz tub at $23.47/gal and became a market's benchmark before this guard.
_NOT_MILK = ("creamer", "half and half", "half & half", "heavy cream",
             "whipping cream", "sour cream", "condensed", "evaporated",
             "buttermilk", "eggnog", "milkshake", "milk chocolate",
             "powdered milk", "dry milk", "milk bone", "coconut cream",
             "cream cheese", "ice cream", "milk duds",
             "ricotta", "mozzarella", "cheese", "yogurt", "yoghurt",
             "cottage", "kefir", "butter", "pudding", "custard")
# Walmart lists the same SKU in English and Spanish, so the flavour tells have
# to cover both or a chocolate gallon lands in the white-milk benchmark.
_FLAVORED = ("chocolate", "strawberry", "vanilla", "banana", "cookies",
             "chocolatada", "chocolatado", "fresa", "sabor")


@dataclass
class MilkObservation:
    retailer: str
    retailer_name: str
    channel: str
    zip_code: str
    market: str
    product_id: str
    name: str
    brand: str
    size_text: str
    price: float
    fl_oz: float | None
    pack_count: int
    price_per_gal: float | None
    fat: str | None
    category: str          # dairy_white | dairy_flavored | plant | excluded
    is_private_label: bool
    is_organic: bool
    is_lactose_free: bool
    is_ultrafiltered: bool
    in_stock: bool = True
    reason: str = ""       # why excluded, when category == "excluded"


def classify_category(name: str) -> tuple[str, str]:
    n = name.lower()
    for bad in _NOT_MILK:
        if bad in n:
            return "excluded", f"non-milk item ({bad})"
    for p in _PLANT:
        if p in n:
            return "plant", ""
    for f in _FLAVORED:
        if f in n:
            return "dairy_flavored", ""
    return "dairy_white", ""


def classify_fat(name: str) -> str | None:
    """Butterfat tier. This is the single most important comparability key:
    a whole-gallon price means nothing next to a skim-gallon price."""
    n = name.lower()
    if re.search(r"\b(whole|vitamin d|homogenized)\b", n):
        return "whole"
    if re.search(r"\b2\s*%|reduced[- ]fat\b", n):
        return "2%"
    if re.search(r"\b1\s*%|low[- ]?fat\b", n):
        return "1%"
    if re.search(r"\b(skim|fat[- ]free|nonfat|non[- ]fat|0\s*%)\b", n):
        return "skim"
    return None


def normalize_row(raw: dict, retailer_slug: str, zip_code: str) -> MilkObservation:
    """Map one scraped product dict into a comparable observation."""
    name = (raw.get("name") or "").strip()
    brand = (raw.get("brand") or "").strip()
    size_text = (raw.get("size") or "").strip()
    price = raw.get("price")

    fl_oz, pack = parse_size_fl_oz(size_text or name)
    category, reason = classify_category(name)

    ppg = None
    if price and fl_oz:
        ppg = round(float(price) * FL_OZ_PER_GAL / fl_oz, 4)

    r = BY_SLUG.get(retailer_slug)
    pl_brands = private_label_brands()
    hay = f"{brand} {name}".lower()
    n = name.lower()

    return MilkObservation(
        retailer=retailer_slug,
        retailer_name=r.name if r else retailer_slug,
        channel=r.channel if r else "unknown",
        zip_code=zip_code,
        market=MARKET_OF_ZIP.get(zip_code, "unknown"),
        product_id=str(raw.get("id") or raw.get("product_id") or ""),
        name=name,
        brand=brand,
        size_text=size_text,
        price=float(price) if price else 0.0,
        fl_oz=fl_oz,
        pack_count=pack,
        price_per_gal=ppg,
        fat=classify_fat(name),
        category=category,
        is_private_label=any(pl in hay for pl in pl_brands),
        is_organic="organic" in hay,
        is_lactose_free=("lactose" in n or "lactaid" in hay),
        is_ultrafiltered=("fairlife" in hay or "ultra-filtered" in n
                          or "ultrafiltered" in n),
        in_stock=raw.get("in_stock", True),
        reason=reason,
    )


def normalize_all(rows: list[dict], retailer_slug: str, zip_code: str) -> list[dict]:
    return [asdict(normalize_row(r, retailer_slug, zip_code)) for r in rows]
