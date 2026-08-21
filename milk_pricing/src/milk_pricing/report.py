"""Render the analysis as a markdown briefing."""

from __future__ import annotations

from . import analyze as A
from .markets import BY_SLUG

_ACTION_NOTE = {
    "EXPOSED": "Walmart above the local floor on a KVI",
    "MARGIN_LEFT": "deeper than price leadership requires",
    "HOLD": "within band",
    "NO_COMPARISON": "no competitor benchmark captured",
    "NO_DATA": "no Walmart benchmark captured",
}


def render_report(observations: list[dict], fat: str = "whole") -> str:
    cov = A.coverage_report(observations)
    table = A.market_table(observations, fat=fat)
    disp = A.walmart_zone_dispersion(observations, fat=fat)
    recs = A.recommendations(observations, fat=fat)

    L: list[str] = []
    L.append(f"# Walmart SC milk pricing — private-label {fat} gallon\n")
    L.append("**Benchmark unit:** cheapest in-stock private-label "
             f"{fat}-milk item per retailer per market, normalised to $/gal. "
             "Organic, lactose-free and ultra-filtered tiers are excluded as "
             "separate shopper decisions.\n")

    L.append("## Coverage\n")
    L.append(f"- Rows collected: **{cov['rows_collected']}**")
    L.append(f"- Comparable benchmark rows: **{cov['comparable_benchmark_rows']}**")
    L.append(f"- Markets covered: **{cov['markets_covered']}** · "
             f"retailers: **{cov['retailers_covered']}**")
    L.append(f"- Rows with unparseable size (no $/gal): {cov['unparsed_size_rows']}")
    L.append(f"- Category mix: {cov['by_category']}\n")

    if disp:
        L.append("## Walmart's own SC spread\n")
        L.append(f"Walmart ranges **${disp['min']:.2f}–${disp['max']:.2f}/gal** "
                 f"across {disp['n_markets']} SC markets "
                 f"(spread ${disp['spread']:.2f}, median ${disp['median']:.2f}).\n")

    L.append("## Market-by-market position\n")
    L.append("Floor = cheapest **shoppable** competitor "
             "(mass, conventional, hard discount). Club and drug are shown as "
             "context only: a club $/gal exists behind a membership fee and a "
             "multi-gallon commitment, so it cannot set a supercenter shelf price.\n")
    L.append("| Market | Walmart $/gal | Local floor | Floor retailer | Gap | Index vs mkt | Club | Drug |")
    L.append("|---|---:|---:|---|---:|---:|---:|---:|")
    for market, t in sorted(table.items()):
        wm = f"${t['walmart']:.2f}" if t["walmart"] else "—"
        fl = f"${t['floor_price']:.2f}" if t["floor_price"] else "—"
        fr = BY_SLUG[t["floor_slug"]].name if t.get("floor_slug") else "—"
        gap = f"{t['gap_to_floor']:+.2f}" if t["gap_to_floor"] is not None else "—"
        idx = f"{t['index_vs_market']:.1f}" if t["index_vs_market"] else "—"
        club = f"${t['cheapest_club']:.2f}" if t.get("cheapest_club") else "—"
        drug = f"${t['cheapest_drug']:.2f}" if t.get("cheapest_drug") else "—"
        L.append(f"| {market} | {wm} | {fl} | {fr} | {gap} | {idx} | {club} | {drug} |")
    L.append("")

    L.append("## Recommended actions\n")
    for r in recs:
        if r["action"] in ("HOLD", "NO_DATA", "NO_COMPARISON"):
            continue
        L.append(f"**{r['market']} — {r['action']}** "
                 f"({_ACTION_NOTE[r['action']]})  ")
        L.append(f"{r['detail']}  ")
        L.append(f"Current ${r['walmart_price']:.2f} → "
                 f"suggested ${r['suggested_price']:.2f}/gal\n")

    holds = [r["market"] for r in recs if r["action"] == "HOLD"]
    if holds:
        L.append(f"**Hold ({len(holds)}):** {', '.join(holds)}\n")
    gaps = [r["market"] for r in recs
            if r["action"] in ("NO_DATA", "NO_COMPARISON")]
    if gaps:
        L.append(f"**Insufficient data ({len(gaps)}):** {', '.join(gaps)}\n")

    L.append("---")
    L.append("_Source: Instacart via Bright Data. Walmart's Instacart "
             "storefront is flagged 'No markups', so its prices track shelf "
             "price; conventional and drug-channel retailers may carry an "
             "Instacart markup and should be read as delivered price, not "
             "shelf price._")
    return "\n".join(L)
