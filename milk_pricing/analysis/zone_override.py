"""Split Walmart's shelf price into its centrally-set zone component and its
locally-discretionary override component, and test each for a racial gradient.

Architecture (client, who designed the zones; 2014): ~57 national zones, plus
store-level overrides and discretionary competitor adjustments. No zone map is
available, so state (51 groups) and ZIP2 prefix (98 groups) bracket it as proxies.

Backs reports/zone_vs_override.md. Run from the milk_pricing/ package root.
"""
import csv
import numpy as np
from collections import Counter, defaultdict

DEEP_SOUTH = {"SC", "LA", "MS", "AL", "GA", "AR", "NC", "TN"}


def load():
    out = []
    for r in csv.DictReader(open("data/national_walmart_official.csv")):
        if not (r["store_id"] and r["whole_milk"] and r["state"] and r["county"]
                and r["zip"] and r["pct_black"] and r["median_income"] and r["population"]):
            continue
        out.append({
            "st": r["state"], "cty": r["county"], "zip": r["zip"].zfill(5),
            "z2": r["zip"].zfill(5)[:2], "geo": r["geo"], "p": float(r["whole_milk"]),
            "blk": float(r["pct_black"]), "inc": float(r["median_income"]),
            "pop": float(r["population"]),
        })
    return out


def ols(cols, y, of_interest=1):
    X = np.column_stack([np.ones(len(y))] + cols)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    k = np.linalg.matrix_rank(X)
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / max(len(y) - k, 1)))
    return b[of_interest], b[of_interest] / se[of_interest]


def controls(W):
    return [np.array([s["inc"] for s in W]) / 1000, np.log(np.array([s["pop"] for s in W]))]


def section_not_a_zone_map(S):
    """Backs report section 1: the structure cannot be a contiguous zone map."""
    print("=== Is this a contiguous zone map? (no testimony required) ===")
    byc = defaultdict(list)
    for s in S:
        byc[(s["st"], s["cty"])].append(s["p"])
    multi = {k: v for k, v in byc.items() if len(v) > 1}
    print(f"  multi-store counties: {len(multi)}")
    for thr in (0.25, 0.50, 1.00):
        n = sum(1 for v in multi.values() if max(v) - min(v) > thr)
        print(f"    internal spread > ${thr:.2f}: {n:>3} ({100 * n / len(multi):.0f}%)")
    worst = sorted(multi.items(), key=lambda kv: -(max(kv[1]) - min(kv[1])))[:5]
    for (st, c), v in worst:
        print(f"    {st} {c:<16} n={len(v):>2}  ${min(v):.2f}..${max(v):.2f}  spread ${max(v) - min(v):.2f}")
    by4 = defaultdict(list)
    for s in S:
        by4[(s["st"], s["zip"][:4])].append(s["p"])
    m4 = [v for v in by4.values() if len(v) > 1]
    d = [max(v) - min(v) for v in m4]
    print(f"  ZIP4-adjacent groups: {len(m4)}  identical {100 * np.mean([x < 0.005 for x in d]):.0f}%"
          f"  spread > $0.50 {100 * np.mean([x > 0.5 for x in d]):.0f}%  max ${max(d):.2f}")
    print("\n  do the common price points recur across non-adjacent states?")
    byp = defaultdict(set)
    for s in S:
        byp[s["p"]].add(s["st"])
    for p_, n in Counter(s["p"] for s in S).most_common(6):
        sts = sorted(byp[p_])
        print(f"    ${p_:.2f}: {n:>3} stores across {len(sts):>2} states  {','.join(sts)}")
    print("  -> a national ladder of price points assigned per store, not a contiguous zone map.")
    print("     ($3.64 across FL/TN/VA is the exception: Virginia's regulated price.)")


def section_split(S):
    print("=== Zone (central) vs override (local discretion) ===")
    for zone, lbl in ((lambda s: s["st"], "state"), (lambda s: s["z2"], "ZIP2")):
        g = defaultdict(list)
        for s in S:
            g[zone(s)].append(s)
        zm = {k: np.mean([x["p"] for x in v]) for k, v in g.items()}
        between = np.array([zm[zone(s)] for s in S])
        within = np.array([s["p"] - zm[zone(s)] for s in S])
        tot = np.array([s["p"] for s in S])
        print(f"\n  zone proxy = {lbl} ({len(g)} groups)")
        print(f"    zone component {100 * np.var(between) / np.var(tot):5.1f}%   "
              f"override component {100 * np.var(within) / np.var(tot):5.1f}%   "
              f"override sd ${np.std(within):.3f}   mean |override| ${np.mean(np.abs(within)):.3f}")
        # (a) central component: zone mean price on zone mean %Black
        zp = np.array([np.mean([x["p"] for x in v]) for v in g.values()])
        zb = np.array([np.mean([x["blk"] for x in v]) for v in g.values()])
        zi = np.array([np.mean([x["inc"] for x in v]) for v in g.values()]) / 1000
        b1, t1 = ols([zb], zp)
        b2, t2 = ols([zb, zi], zp)
        print(f"    (a) ZONE price on ZONE %Black (n={len(zp)}): "
              f"raw {b1:+.5f} (t {t1:+.2f})   +income {b2:+.5f} (t {t2:+.2f})")
        # (b) override: store deviation on store %Black, zone FE
        D = [np.array([1.0 if zone(s) == k else 0.0 for s in S]) for k in list(g)[1:]]
        b3, t3 = ols([np.array([s["blk"] for s in S])] + controls(S) + D,
                     np.array([s["p"] for s in S]))
        print(f"    (b) OVERRIDE on store %Black (n={len(S)}): {b3:+.5f} (t {t3:+.2f})")


def section_regions(S):
    print("\n=== Is the override gradient different in the Deep South? ===")
    for lab, W in (("Deep South", [s for s in S if s["st"] in DEEP_SOUTH]),
                   ("rest of country", [s for s in S if s["st"] not in DEEP_SOUTH])):
        for geo in ("rural", "urban"):
            G = [s for s in W if s["geo"] == geo]
            sts = sorted({s["st"] for s in G})
            D = [np.array([1.0 if s["st"] == k else 0.0 for s in G]) for k in sts[1:]]
            b, t = ols([np.array([s["blk"] for s in G])] + controls(G) + D,
                       np.array([s["p"] for s in G]))
            print(f"  {lab:<18}{geo:<7} n={len(G):>4}  %Black on override = {b:+.5f} (t {t:+.2f})")


def section_by_state(S):
    print("\n=== Override gradient state by state ===")
    print(f"  {'st':<4}{'stores':>7}{'override sd':>13}{'all stores':>22}{'rural only':>22}")
    bys = defaultdict(list)
    for s in S:
        bys[s["st"]].append(s)
    for st, V in sorted(bys.items()):
        if len(V) < 40:
            continue
        m = np.mean([s["p"] for s in V])
        sd = np.std([s["p"] - m for s in V])

        def run(W):
            if len(W) < 25:
                return "—"
            b, t = ols([np.array([s["blk"] for s in W])] + controls(W),
                       np.array([s["p"] for s in W]))
            return f"{b:+.5f} (t {t:+.2f})"

        print(f"  {st:<4}{len(V):>7}{('$%.3f' % sd):>13}{run(V):>22}"
              f"{run([s for s in V if s['geo'] == 'rural']):>22}")
    print("  note: VA's rural cell is degenerate (override sd $0.028, two prices statewide).")


def section_louisiana(S):
    LA = [s for s in S if s["st"] == "LA"]
    print("\n=== Louisiana: stress test, then restate as block assignment ===")
    for lab, W in (("all LA", LA), ("rural", [s for s in LA if s["geo"] == "rural"])):
        base = np.array([s["blk"] for s in W])
        y = np.array([s["p"] for s in W])
        b, t = ols([base] + controls(W), y)
        rng = np.random.default_rng(5)
        null = np.array([ols([rng.permutation(base)] + controls(W), y)[0] for _ in range(5000)])
        ts = []
        for c in sorted({s["cty"] for s in W}):
            K = [s for s in W if s["cty"] != c]
            if len(K) >= 20:
                ts.append(ols([np.array([s["blk"] for s in K])] + controls(K),
                              np.array([s["p"] for s in K]))[1])
        order = sorted(range(len(W)), key=lambda i: -W[i]["blk"])
        drops = []
        for N in (2, 4, 6, 8):
            K = [W[i] for i in range(len(W)) if i not in set(order[:N])]
            drops.append(ols([np.array([s["blk"] for s in K])] + controls(K),
                             np.array([s["p"] for s in K]))[1])
        print(f"  {lab:<8} n={len(W):>3}  %Black={b:+.5f} (t {t:+.2f})  "
              f"permutation one-sided p={np.mean(null >= b):.4f}  "
              f"leave-one-parish-out t in [{min(ts):+.2f},{max(ts):+.2f}]  "
              f"drop-top-N t in [{min(drops):+.2f},{max(drops):+.2f}]")

    lo = [s for s in LA if s["p"] <= 4.40]
    hi = [s for s in LA if s["p"] > 4.40]
    print("\n  LA is a two-block state:")
    for lab, G in (("LOW  ($4.19-4.32)", lo), ("HIGH ($4.64-4.78)", hi)):
        print(f"    {lab:<20} n={len(G):>3}  mean ${np.mean([s['p'] for s in G]):.3f}  "
              f"%Black {np.mean([s['blk'] for s in G]):5.1f}  "
              f"median inc ${np.median([s['inc'] for s in G]):>7,.0f}  "
              f"urban {100 * np.mean([s['geo'] == 'urban' for s in G]):.0f}%")
    y = np.array([1.0 if s["p"] > 4.40 else 0.0 for s in LA])
    b, t = ols([np.array([s["blk"] for s in LA])] + controls(LA) +
               [np.array([1.0 if s["geo"] == "urban" else 0.0 for s in LA])], y)
    print(f"    P(HIGH block) on %Black, controlling income, log(pop), urban: "
          f"{b:+.5f} (t {t:+.2f}) -> a 20pt %Black gap = {100 * b * 20:+.1f} pp")
    print(f"    parishes: low {len({s['cty'] for s in lo})}, high {len({s['cty'] for s in hi})}, "
          f"both {len({s['cty'] for s in lo} & {s['cty'] for s in hi})} "
          f"-> still a between-region contrast")


if __name__ == "__main__":
    S = load()
    print(f"usable stores: {len(S)}\n")
    section_not_a_zone_map(S)
    section_split(S)
    section_regions(S)
    section_by_state(S)
    section_louisiana(S)
