"""Within-retailer milk price architecture.

`analyze.py` compares retailers across markets. That needs geo-differentiated
collection, which the Bright Data Walmart dataset does not provide (see
README: the `zipcode` input is accepted but never changes store context).

What the data does support is the price ladder inside one retailer: what each
step up the milk hierarchy costs per gallon. That is a real pricing lever —
pack-size penalty, lactose-free premium, organic premium and private-label
gap are all decisions Walmart sets directly.
"""

from __future__ import annotations

import statistics
from collections import defaultdict


def _ppg(rows: list[dict]) -> float | None:
    vals = [r["price_per_gal"] for r in rows if r.get("price_per_gal")]
    return round(statistics.median(vals), 2) if vals else None


def segment(observations: list[dict]) -> dict[str, list[dict]]:
    """Split white milk into the tiers a shopper actually chooses between."""
    white = [o for o in observations
             if o.get("category") == "dairy_white" and o.get("price_per_gal")]
    seg: dict[str, list[dict]] = defaultdict(list)
    for o in white:
        if o["is_organic"]:
            key = "organic"
        elif o["is_lactose_free"]:
            key = "lactose_free"
        elif o["is_ultrafiltered"]:
            key = "ultrafiltered"
        elif o["is_private_label"]:
            key = "private_label"
        else:
            key = "national_brand"
        seg[key].append(o)
    return dict(seg)


def pack_size_penalty(observations: list[dict]) -> dict:
    """What a shopper pays per gallon for buying a smaller container.

    This is the cleanest margin lever in the category: the same milk, priced
    per gallon, costs materially more in a half gallon.
    """
    base = [o for o in observations
            if o.get("category") == "dairy_white" and o.get("price_per_gal")
            and o["is_private_label"] and not (o["is_organic"] or o["is_lactose_free"])]
    by_size: dict[str, list[dict]] = defaultdict(list)
    for o in base:
        oz = o.get("fl_oz")
        if not oz:
            continue
        label = ("gallon" if oz >= 120 else
                 "half gallon" if 56 <= oz < 120 else
                 "quart or smaller")
        by_size[label].append(o)

    out = {k: {"median_ppg": _ppg(v), "n": len(v)} for k, v in by_size.items()}
    gal = out.get("gallon", {}).get("median_ppg")
    half = out.get("half gallon", {}).get("median_ppg")
    if gal and half:
        out["half_gallon_premium_pct"] = round(100 * (half - gal) / gal, 1)
        out["half_gallon_premium_usd"] = round(half - gal, 2)
    return out


def tier_premiums(observations: list[dict]) -> dict:
    """Cost of each step up from the conventional private-label baseline."""
    seg = segment(observations)
    base = _ppg(seg.get("private_label", []))
    out = {"baseline_private_label_ppg": base}
    for tier in ("national_brand", "lactose_free", "organic", "ultrafiltered"):
        p = _ppg(seg.get(tier, []))
        if p is None or base is None:
            continue
        out[tier] = {
            "median_ppg": p,
            "premium_usd": round(p - base, 2),
            "premium_pct": round(100 * (p - base) / base, 1),
            "n": len(seg[tier]),
        }
    return out


def fat_tier_spread(observations: list[dict]) -> dict:
    """Private-label price by butterfat tier at the gallon."""
    rows = [o for o in observations
            if o.get("category") == "dairy_white" and o.get("price_per_gal")
            and o["is_private_label"] and o.get("fat")
            and not (o["is_organic"] or o["is_lactose_free"])
            and (o.get("fl_oz") or 0) >= 120]
    by_fat: dict[str, list[dict]] = defaultdict(list)
    for o in rows:
        by_fat[o["fat"]].append(o)
    return {k: _ppg(v) for k, v in sorted(by_fat.items())}
