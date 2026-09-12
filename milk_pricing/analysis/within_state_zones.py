"""Audit memo section 2: do the within-state racial gradients survive zone clustering?

The memo reports t = 14.0 (AR), 13.5 (PA), 9.3 (AL), 9.0 (VA), 7.4 (NY, TX) for the
%Black coefficient on the Class I differential WITHIN each state. The differential is
not a county-level variable: it is a step function taking a handful of distinct values
per state. Counties sharing a value are one observation for inference purposes, so
county-level OLS treats ~10 zones as ~75 independent draws.
"""
import importlib.util, numpy as np
spec = importlib.util.spec_from_file_location("u", "analysis/usdss.py")
u = importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
rows, _, _ = u.load()

MEMO = {"AR": 14.0, "PA": 13.5, "AL": 9.3, "VA": 9.0, "NY": 7.4, "TX": 7.4, "MS": None}

def ols_t(y, x, w, cluster=None):
    s = np.sqrt(w); X = np.column_stack([np.ones(len(x)), x]) * s[:, None]; Y = y * s
    b, *_ = np.linalg.lstsq(X, Y, rcond=None); r = Y - X @ b
    xi = np.linalg.pinv(X.T @ X)
    if cluster is None:
        V = xi * (r @ r / max(len(y) - 2, 1))
    else:
        meat = np.zeros((2, 2))
        for c in np.unique(cluster):
            m = cluster == c; xu = X[m].T @ r[m]; meat += np.outer(xu, xu)
        g = len(np.unique(cluster))
        if g < 3: return b[1], float("nan"), g
        V = xi @ meat @ xi * (g / (g - 1))
    se = np.sqrt(np.diag(V))
    return b[1], b[1] / se[1], (len(np.unique(cluster)) if cluster is not None else len(y))

print("Memo section 2 -- within-state %Black gradient on the 2025 differential")
print("Unweighted county OLS (what reproduces the memo) vs SEs clustered on differential zone\n")
print(f"  {'st':<4}{'counties':>9}{'zones':>7}{'coef $/cwt':>12}{'t naive':>9}{'t zone-clust':>14}{'memo t':>8}{'c/gal':>8}")
tot_flip = 0
for st in ["AR", "PA", "AL", "VA", "NY", "TX", "MS", "SC", "LA", "GA"]:
    g = [r for r in rows if r["st"] == st]
    if len(g) < 8: continue
    y = np.array([r["new"] for r in g]); x = np.array([r["pctblk"] for r in g])
    w = np.ones(len(g))
    zone = np.array([round(r["new"], 2) for r in g])
    b, t0, _ = ols_t(y, x, w)
    _, t1, nz = ols_t(y, x, w, cluster=zone)
    memo = MEMO.get(st)
    flag = ""
    if not np.isnan(t1) and abs(t1) < 1.96 <= abs(t0): flag = "  <- loses significance"; tot_flip += 1
    print(f"  {st:<4}{len(g):>9}{nz:>7}{b:>+12.4f}{t0:>+9.2f}{t1:>+14.2f}"
          f"{(f'{memo:.1f}' if memo else '--'):>8}{100*b/u.GAL_PER_CWT:>+8.2f}{flag}")
print(f"\n  {tot_flip} of the listed states lose conventional significance under zone clustering.")
print("  'zones' is the count of DISTINCT differential values in the state -- the true")
print("  number of independent observations the regression has to work with.")
