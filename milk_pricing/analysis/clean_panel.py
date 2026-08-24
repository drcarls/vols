"""Re-run every headline number on the exclusion-cleaned national panel.

Excludes PA, NJ (minimum retail price), ME, ND, VA, MT (classified pricing that
reaches retail) and AK, HI (non-contiguous). See src/milk_pricing/panel.py.

Prints each result RAW then CLEAN so any change is visible. The question this
answers is not "what are the numbers" but "does excluding regulated states
change any conclusion".
"""
import math
import os
import statistics
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from milk_pricing.panel import EXCLUDED, load  # noqa: E402

GAL_PER_CWT = 11.6289
GAL_PER_YEAR = 104.0


def ols(cols, y, of=1):
    X = np.column_stack([np.ones(len(y))] + cols)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    k = np.linalg.matrix_rank(X)
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / max(len(y) - k, 1)))
    return b[of], b[of] / se[of]


def ctrls(S):
    return [np.array([s["inc"] for s in S]) / 1000, np.log(np.array([s["pop"] for s in S]))]


def fe(S, key):
    gs = sorted({key(s) for s in S})
    return [np.array([1.0 if key(s) == g else 0.0 for s in S]) for g in gs[1:]]


def row(label, raw, clean):
    print(f"  {label:<44}{raw:>26}{clean:>26}")


def main():
    R = load(exclude=False)
    C = load(exclude=True)
    print(f"excluded states: {', '.join(sorted(EXCLUDED))}")
    print(f"raw panel {len(R)} stores / {len({s['st'] for s in R})} states   ->   "
          f"clean {len(C)} stores / {len({s['st'] for s in C})} states "
          f"({len(R)-len(C)} dropped, {100*(len(R)-len(C))/len(R):.1f}%)\n")
    print(f"  {'':<44}{'RAW':>26}{'CLEAN':>26}")
    print("  " + "-" * 94)

    def both(f):
        return f(R), f(C)

    # --- price level and dispersion
    a, b = both(lambda S: f"${np.mean([s['p'] for s in S]):.2f}")
    row("mean price", a, b)
    a, b = both(lambda S: f"${np.std([s['p'] for s in S]):.3f}")
    row("sd of price", a, b)

    # --- Finding A: Class I differential on %Black
    def findA(S, with_ctrl):
        V = [s for s in S if s["cls"] is not None]
        y = np.array([s["cls"] for s in V])
        cols = [np.array([s["blk"] for s in V])] + (ctrls(V) if with_ctrl else [])
        c, t = ols(cols, y)
        return f"{c:+.4f} (t {t:+.2f})"
    row("FINDING A: Class I diff on %Black, raw", *both(lambda S: findA(S, False)))
    row("FINDING A: + income, log(pop)", *both(lambda S: findA(S, True)))

    # --- price on %Black
    def pblk(S, statefe):
        y = np.array([s["p"] for s in S])
        cols = [np.array([s["blk"] for s in S])] + ctrls(S) + (fe(S, lambda s: s["st"]) if statefe else [])
        c, t = ols(cols, y)
        return f"{c:+.5f} (t {t:+.2f})"
    row("price on %Black, no FE", *both(lambda S: pblk(S, False)))
    row("price on %Black, state FE (the override layer)", *both(lambda S: pblk(S, True)))

    # --- zone vs override split
    def split(S):
        g = defaultdict(list)
        for s in S:
            g[s["st"]].append(s["p"])
        zm = {k: np.mean(v) for k, v in g.items()}
        bet = np.array([zm[s["st"]] for s in S])
        tot = np.array([s["p"] for s in S])
        return f"{100*np.var(bet)/np.var(tot):.1f}% / {100*(1-np.var(bet)/np.var(tot)):.1f}%"
    row("zone / override variance split", *both(split))

    # --- burden decomposition
    def burden(S):
        y = np.array([100 * GAL_PER_YEAR * s["p"] / s["inc"] for s in S])
        c, t = ols([np.array([s["blk"] for s in S])] + fe(S, lambda s: s["st"]), y)
        return f"{c:+.5f} (t {t:+.2f})"
    row("BURDEN (cost/income) on %Black, state FE", *both(burden))

    def income(S):
        y = np.array([s["inc"] for s in S]) / 1000
        c, t = ols([np.array([s["blk"] for s in S])] + fe(S, lambda s: s["st"]), y)
        return f"{c:+.4f} (t {t:+.2f})"
    row("median income on %Black, state FE", *both(income))

    # --- Class I pass-through
    def passthru(S):
        V = [s for s in S if s["cls"] is not None]
        y = np.array([s["p"] for s in V])
        c, t = ols([np.array([s["cls"] for s in V])] + fe(V, lambda s: s["st"]), y)
        return f"{c*GAL_PER_CWT:.2f}x (t {t:+.2f})"
    row("Class I pass-through, within state", *both(passthru))

    # --- partition R^2
    def part(S, key):
        y = np.log(np.array([s["p"] for s in S]))
        g = defaultdict(list)
        for s, v in zip(S, y):
            g[key(s)].append(v)
        gm = {k: np.mean(v) for k, v in g.items()}
        wss = sum(sum((np.array(v) - gm[k]) ** 2) for k, v in g.items())
        return f"{100*(1-wss/sum((y-y.mean())**2)):.1f}% ({len(g)} groups)"
    row("state explains (ln price)", *both(lambda S: part(S, lambda s: s["st"])))
    row("county explains (ln price)", *both(lambda S: part(S, lambda s: (s["st"], s["cty"]))))

    # --- Finding B, memo design, per state
    print("\n=== FINDING B (memo design) — states in the clean panel ===")
    print("  (PA, NJ, ME, ND, VA, MT, AK, HI are gone; no test state is affected)")
    for st in ("SC", "LA", "MS", "AR", "NC", "AL", "GA", "TN", "TX"):
        V = [s for s in C if s["st"] == st and s["geo"] == "rural"]
        if len(V) < 25:
            continue
        y = np.array([s["p"] for s in V])
        c, t = ols([np.array([s["blk"] for s in V])] + ctrls(V), y)
        c2, t2 = ols([np.array([s["blk"] for s in V])] + ctrls(V) + fe(V, lambda s: s["z3"]), y)
        print(f"  {st:<4} n={len(V):>4}   no FE {c:+.5f} (t {t:+.2f})    "
              f"ZIP3-region FE {c2:+.5f} (t {t2:+.2f})")

    print("\n=== Which states left, and what they contributed ===")
    for st in sorted(EXCLUDED):
        V = [s for s in R if s["st"] == st]
        if V:
            print(f"  {st}: {len(V):>3} stores, mean ${np.mean([s['p'] for s in V]):.2f}, "
                  f"{len(set(s['p'] for s in V))} distinct prices, "
                  f"mean %Black {np.mean([s['blk'] for s in V]):.1f}")


if __name__ == "__main__":
    main()
