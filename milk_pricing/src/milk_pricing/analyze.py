"""Milk price analysis for Walmart's SC position.

Milk is a KVI (known value item): a low-margin, high-frequency purchase whose
shelf price drives store-level price perception well beyond the category's own
P&L contribution. So the analysis deliberately does NOT optimise category
margin. It measures one thing precisely — where Walmart's private-label whole
gallon sits against the local competitive floor, market by market — and flags
where that position is off.

Comparability rules enforced here:
  * private label vs private label (Great Value vs Publix vs Friendly Farms)
  * same butterfat tier (whole vs whole)
  * same normalised unit ($/gal)
Anything else is noise dressed up as a price gap.
"""

from __future__ import annotations

import statistics
from collections import defaultdict

from .markets import BY_SLUG

# Cents/gal. Inside this band of the local benchmark, Walmart's position is
# treated as intentional rather than as drift worth acting on.
HOLD_BAND = 0.10

# Channels that set the price a Walmart shopper can actually compare against
# on the same trip. Club is excluded because its $/gal only exists behind a
# membership fee and a two-gallon commitment, and drug because a 64 oz
# fill-in carton serves a different mission at a structurally higher $/gal.
# Both are still reported as context — they just cannot set the floor.
FLOOR_CHANNELS = ("mass", "conventional", "hard_discount")


def comparable_set(observations: list[dict], fat: str = "whole",
                   private_label_only: bool = True) -> list[dict]:
    """Filter to rows that can honestly be compared on price."""
    out = []
    for o in observations:
        if o.get("category") != "dairy_white":
            continue
        if o.get("fat") != fat:
            continue
        if o.get("price_per_gal") is None or o.get("price_per_gal") <= 0:
            continue
        if o.get("is_organic") or o.get("is_lactose_free") or o.get("is_ultrafiltered"):
            continue  # premium tiers are a different shopper decision
        if private_label_only and not o.get("is_private_label"):
            continue
        if not o.get("in_stock", True):
            continue
        out.append(o)
    return out


def _cheapest_by(rows: list[dict], key) -> dict:
    """Lowest $/gal per group — the shelf price a shopper actually anchors on."""
    best: dict = {}
    for r in rows:
        k = key(r)
        if k not in best or r["price_per_gal"] < best[k]["price_per_gal"]:
            best[k] = r
    return best


def market_table(observations: list[dict], fat: str = "whole") -> dict:
    """Per market: each retailer's benchmark price and Walmart's position."""
    rows = comparable_set(observations, fat=fat)
    by_market: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_market[r["market"]].append(r)

    results = {}
    for market, mrows in sorted(by_market.items()):
        best = _cheapest_by(mrows, lambda r: r["retailer"])
        prices = {slug: r["price_per_gal"] for slug, r in best.items()}
        wm = prices.get("walmart")

        competitors = {s: p for s, p in prices.items() if s != "walmart"}
        conventional = {s: p for s, p in competitors.items()
                        if best[s]["channel"] == "conventional"}
        discount = {s: p for s, p in competitors.items()
                    if best[s]["channel"] == "hard_discount"}
        # Context-only channels, reported but never used to set the floor.
        club = {s: p for s, p in competitors.items() if best[s]["channel"] == "club"}
        drug = {s: p for s, p in competitors.items() if best[s]["channel"] == "drug"}

        shoppable = {s: p for s, p in competitors.items()
                     if best[s]["channel"] in FLOOR_CHANNELS}
        floor_slug = min(shoppable, key=shoppable.get) if shoppable else None

        results[market] = {
            "prices": prices,
            "walmart": wm,
            "floor_slug": floor_slug,
            "floor_price": shoppable.get(floor_slug) if floor_slug else None,
            "cheapest_conventional": min(conventional.values()) if conventional else None,
            "cheapest_discount": min(discount.values()) if discount else None,
            "cheapest_club": min(club.values()) if club else None,
            "cheapest_drug": min(drug.values()) if drug else None,
            "gap_to_floor": (round(wm - shoppable[floor_slug], 2)
                             if wm and floor_slug else None),
            # Indexed against the shoppable set only, so a club warehouse
            # cannot drag the index into looking like a Walmart problem.
            "index_vs_market": (round(100 * wm / statistics.mean(shoppable.values()), 1)
                                if wm and shoppable else None),
            "n_retailers": len(prices),
        }
    return results


def walmart_zone_dispersion(observations: list[dict], fat: str = "whole") -> dict:
    """Walmart's own spread across SC. Wide dispersion is only a problem when
    it fails to track local competition — that is what `misaligned` reports."""
    rows = [r for r in comparable_set(observations, fat=fat)
            if r["retailer"] == "walmart"]
    if not rows:
        return {}
    best = _cheapest_by(rows, lambda r: r["market"])
    prices = {m: r["price_per_gal"] for m, r in best.items()}
    vals = list(prices.values())
    return {
        "by_market": dict(sorted(prices.items(), key=lambda kv: kv[1])),
        "min": min(vals),
        "max": max(vals),
        "spread": round(max(vals) - min(vals), 2),
        "median": round(statistics.median(vals), 2),
        "n_markets": len(vals),
    }


def recommendations(observations: list[dict], fat: str = "whole",
                    hold_band: float = HOLD_BAND) -> list[dict]:
    """Classify each market into an action. Deliberately conservative: the
    default verdict is HOLD, and a move must clear the band to be proposed."""
    table = market_table(observations, fat=fat)
    recs = []
    for market, t in table.items():
        wm, floor = t["walmart"], t["floor_price"]
        if wm is None:
            recs.append({"market": market, "action": "NO_DATA",
                         "detail": "No comparable Walmart benchmark item found."})
            continue
        if floor is None:
            recs.append({"market": market, "action": "NO_COMPARISON",
                         "detail": "No shoppable (mass/conventional/discount) "
                                   "competitor benchmark in this market."})
            continue

        gap = round(wm - floor, 2)
        floor_name = BY_SLUG[t["floor_slug"]].name if t.get("floor_slug") else "the floor"
        entry = {
            "market": market, "walmart_price": wm, "floor_price": floor,
            "floor_retailer": t["floor_slug"], "gap": gap,
            "index": t["index_vs_market"],
        }
        if gap > hold_band:
            entry |= {
                "action": "EXPOSED",
                "detail": (f"Walmart is ${gap:.2f}/gal above {floor_name}. "
                           f"On a KVI this is visible to shoppers; closing to "
                           f"${floor:.2f} costs ~${gap:.2f}/gal on milk volume "
                           f"and defends trip frequency."),
                "suggested_price": floor,
            }
        elif gap < -hold_band:
            entry |= {
                "action": "MARGIN_LEFT",
                "detail": (f"Walmart is ${abs(gap):.2f}/gal below {floor_name} — "
                           f"deeper than price leadership requires. Holding "
                           f"${floor - hold_band:.2f} keeps the lead and recovers "
                           f"~${abs(gap) - hold_band:.2f}/gal."),
                "suggested_price": round(floor - hold_band, 2),
            }
        else:
            entry |= {"action": "HOLD",
                      "detail": f"Within ${hold_band:.2f}/gal of the local floor."}
        recs.append(entry)

    order = {"EXPOSED": 0, "MARGIN_LEFT": 1, "HOLD": 2,
             "NO_COMPARISON": 3, "NO_DATA": 4}
    return sorted(recs, key=lambda r: (order[r["action"]], -abs(r.get("gap") or 0)))


def coverage_report(observations: list[dict]) -> dict:
    """What the pull actually captured. Reported alongside every result so a
    thin market is never mistaken for a confident finding."""
    total = len(observations)
    by_cat: dict[str, int] = defaultdict(int)
    for o in observations:
        by_cat[o.get("category", "unknown")] += 1
    comparable = comparable_set(observations)
    return {
        "rows_collected": total,
        "by_category": dict(by_cat),
        "comparable_benchmark_rows": len(comparable),
        "markets_covered": len({o["market"] for o in comparable}),
        "retailers_covered": len({o["retailer"] for o in comparable}),
        "unparsed_size_rows": sum(1 for o in observations
                                  if o.get("price_per_gal") is None),
    }
