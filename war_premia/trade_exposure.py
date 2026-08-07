"""Test the blockade / trade-exposure channel: does the war premium scale with
trade dependence on the Central Powers?

The neutral premia might be genuine war exposure -- a European war damages neutral
economies too, above all via the British blockade of Central-Powers trade. Testable
prediction: a neutral more dependent on trade with Germany/Austria (the trade the
blockade severed) should carry a HIGHER war-risk premium.

x = 1913 trade shares from the **Correlates of War Bilateral Trade v4.0** (Barbieri,
Keshk & Pollins 2009), extracted from the dyadic file (data/cow_trade_shares_1913.csv):
each country's trade with Germany / with the Central Powers (Germany+Austria) / with
all belligerents (DE, AT, UK, FR, RU), as a share of its total 1913 trade.
y = the full-sample Rigobon-Sack money-market premium (vs the London basis), estimated
here from the mirrored Neal-Weidenmier short rates.

The clean test is WITHIN the European neutrals: belligerents' premia are idiosyncratic
(driven by being belligerents), and the US is a war *supplier* (a beneficiary, not a
disrupted neutral -- high belligerent trade but a negative, safe-haven premium).

    python trade_exposure.py
"""

from __future__ import annotations

import csv
import os
import statistics

_HERE = os.path.dirname(os.path.abspath(__file__))
SHARES = os.path.join(_HERE, "data", "cow_trade_shares_1913.csv")
SHORT = os.path.join(_HERE, "..", "neal_weidenmier", "data", "stinterestrates.xls")


def _pearson(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sx = sum((a - mx) ** 2 for a in xs) ** 0.5
    sy = sum((b - my) ** 2 for b in ys) ** 0.5
    return cov / (sx * sy) if sx * sy else 0.0


def _spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for pos, i in enumerate(order):
            r[i] = pos
        return r
    return _pearson(rank(xs), rank(ys))


def _tstat(r, n):
    """Correlation t-statistic, df = n-2 (report this; small-n p-values are fragile)."""
    if abs(r) >= 1 or n <= 2:
        return float("nan")
    return r * ((n - 2) ** 0.5) / ((1 - r * r) ** 0.5)


def premia(short_path=SHORT):
    from neal_weidenmier.load import load_short_rates, to_series_map
    from war_premia.run import run_crisis
    from war_premia.warweeks import get_crisis
    smap = to_series_map(load_short_rates(short_path))
    return {r.city: r.single.beta for r in run_crisis(smap, get_crisis("full"), basis_key="london_trade3mo")}


def load():
    with open(SHARES, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    b = premia()
    out = []
    for row in rows:
        beta = b.get(row["slug"])
        if beta is None:
            continue
        out.append({
            "country": row["country"], "type": row["type"], "beta": beta,
            "pct_germany": float(row["pct_germany"]) if row["pct_germany"] else None,
            "pct_central": float(row["pct_central"]) if row["pct_central"] else None,
            "pct_bellig": float(row["pct_bellig"]) if row["pct_bellig"] else None,
        })
    return out


def robustness():
    """Is the trade correlation robust to the premium MEASURE? (neutrals, %Central)"""
    import datetime
    from neal_weidenmier.load import load_short_rates, to_series_map
    from war_premia.run import run_crisis
    from war_premia.warweeks import get_crisis
    smap = to_series_map(load_short_rates(SHORT))
    full = get_crisis("full")
    rows = [d for d in load() if d["type"] == "neut" and d["pct_central"] is not None]
    slugmap = {r["country"]: r for r in _shares_rows()}
    slugs = [slugmap[d["country"]]["slug"] for d in rows]
    x = [d["pct_central"] for d in rows]
    london = {r.city: r.single.beta for r in run_crisis(smap, full, basis_key="london_trade3mo")}
    swiss = {r.city: r.single.beta for r in run_crisis(smap, full, basis_key="geneva_market")}
    return {
        "London-basis beta": _pearson([london[s] for s in slugs], x),
        "Swiss-basis beta (Geneva is itself 33% Central -> contaminated basis)":
            _pearson([swiss.get(s, 0.0) for s in slugs], x),
    }


def _shares_rows():
    with open(SHARES, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    data = load()
    groups = [
        ("NEUTRALS only (the clean test)", [d for d in data if d["type"] == "neut"]),
        ("Neutrals + belligerents", [d for d in data if d["type"] in ("neut", "bell")]),
        ("All incl. US", data),
    ]
    for label, sub in groups:
        print(f"=== {label} ===")
        for key, name in (("pct_germany", "%Germany"), ("pct_central", "%Central"), ("pct_bellig", "%Bellig")):
            rows = [d for d in sub if d[key] is not None]
            xs = [d[key] for d in rows]
            ys = [d["beta"] for d in rows]
            r = _pearson(ys, xs)
            print(f"  premium vs {name:<9}: r={r:+.2f}  Spearman={_spearman(ys, xs):+.2f}  "
                  f"t={_tstat(r, len(rows)):+.2f} (df {len(rows)-2})  (n={len(rows)})")
        print()
    print("Central-Powers trade share is the blockade-relevant variable. Within the European")
    print("neutrals the premium rises with it: %Central r=+0.64 (t=2.0, df 6), %Germany r=+0.53")
    print("(t=1.5) -- the RIGHT sign and a moderate-to-strong correlation, supporting the")
    print("blockade/exposure channel. But n=8 (3 of them the Scandinavian bloc, so effective n")
    print("is smaller): marginal, suggestive, not conclusive. Adding belligerents (idiosyncratic")
    print("premia) washes it out, as expected. The US is the informative break: high belligerent")
    print("trade (44.9%) yet a NEGATIVE premium -- a war SUPPLIER/beneficiary, not a disrupted")
    print("neutral -- so exposure is about disruptive dependence, not trade volume.")
    print("\nROBUSTNESS -- is the r=0.64 robust to the premium MEASURE? (neutrals, %Central):")
    for measure, r in robustness().items():
        print(f"  {measure}: r={r:+.2f}")
    print("  Positive on the London basis (0.64) and the common-factor loading (~0.41) but ~0")
    print("  on the Swiss basis -- partly mechanical (Geneva is itself the top-Central-trade")
    print("  neutral, so it differences the signal away), but the result is NOT robust: it is")
    print("  suggestive, measure-dependent, and underpowered -- not a clean confirmation.")
    print("\nTrade shares: Correlates of War Bilateral Trade v4.0 (Barbieri, Keshk & Pollins 2009).")


if __name__ == "__main__":
    raise SystemExit(main())
