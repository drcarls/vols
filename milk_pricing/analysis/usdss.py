"""Is the Class I differential surface the transport-cost surface? Exhibit MIG-16A.

Backs reports/usdss.md. Closes the open item in reports/counterfactual.md section E:
the USDSS county values, previously reported unobtainable, are in the hearing record.

    python3 analysis/usdss.py

Inputs, all public:
  * Exhibit MIG-16A, FMMO_MIG_16A.xlsx -- "Shadow Price Values for Class I, Class III,
    and Price Difference for March, 2016, USDSS Model Run."  3,085 counties x
    {FIPS, Class I shadow price, Class III shadow price, difference}.  Sponsored by
    Dr. Mark Stephenson (Exhibit MIG-16), a caretaker of the model.  ADMITTED into
    evidence: Ruling: Record Exhibits, 2024-03-22, exhibits 1-74.
  * DairyFMMO_USDADifferentialsCurrentvsProposedforFD.xlsx -- current and adopted
    section 1000.52 differentials by county (same file as analysis/counterfactual.py).
  * ACS 2023 table B03002 by county via the Census Reporter API.

WHY NO RESCALING IS NEEDED.  USDSS duals are "price relatives" with an arbitrary
zero -- MIG-16 at 9: "There will be one or more locations in the country where that
value is $0.00."  Only additive shifts of such a surface are meaningful.  The
statistic used throughout, the person-weighted Black mean minus the person-weighted
White mean, is exactly invariant to an additive shift.  So the cost surface and the
regulatory surfaces are compared on the one scale they share: distributional shape.
Levels are reported but never differenced across surfaces.

WHICH USDSS COLUMN IS THE RIGHT COMPARATOR.  Two defensible readings, both run:
  * Class I dual -- what MIG-16 at 10 says "AMS has only asked for."
  * Class I minus Class III -- what MIG-16 at 10 calls the "'incentive' value or
    'give up' charge for delivering milk to a fluid plant instead of a manufacturing
    plant", i.e. the economic quantity a Class I differential is meant to cover.

LIMITS, on the record.  The run is March 2016, a single month; MIG-16 at 9 notes the
model "represents a snapshot in time" and that a flush and a short month are usually
run as a pair -- only one month was filed.  The 2025 schedule was set on 2021 input
data (NMPF-38 at 7), not 2016, so some divergence is vintage, not method.  That cuts
one way only: vintage cannot explain a gradient in county %Black unless milk haulage
costs themselves moved with racial composition between 2016 and 2021.
"""
import json
import subprocess
import sys

import numpy as np

GAL_PER_CWT = 11.6289
BASE = "https://www.ams.usda.gov/sites/default/files/media/"
HEARING = ("https://www.ams.usda.gov/rules-regulations/moa/dairy/hearings/"
           "national-fmmo-pricing-hearing")
USDSS_XLSX, USDA_XLSX = "/tmp/FMMO_MIG_16A.xlsx", "/tmp/DairyFMMO_USDA_cvp.xlsx"
CR_URL = ("https://api.censusreporter.org/1.0/data/show/latest"
          "?table_ids=B03002&geo_ids=050|01000US")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def fetch(url, path):
    subprocess.run(["curl", "-sSL", "-o", path, "-A", UA, "-H", f"Referer: {HEARING}",
                    url], check=True, timeout=300)


def load():
    import openpyxl
    fetch(BASE + "FMMO_MIG_16A.xlsx", USDSS_XLSX)
    ws = openpyxl.load_workbook(USDSS_XLSX, read_only=True, data_only=True).worksheets[0]
    usdss = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r or r[2] in (None, ""):
            continue
        try:
            usdss[str(int(float(r[2]))).zfill(5)] = {
                "c1": float(r[3]), "c3": float(r[4]), "gu": float(r[5])}
        except (TypeError, ValueError):
            continue

    fetch(BASE + "DairyFMMO_USDADifferentialsCurrentvsProposedforFD.xlsx", USDA_XLSX)
    ws = openpyxl.load_workbook(USDA_XLSX, read_only=True, data_only=True)["Current vs. Proposed"]
    reg = {}
    for r in ws.iter_rows(min_row=5, values_only=True):
        if not r or r[2] in (None, ""):
            continue
        try:
            reg[str(int(float(r[2]))).zfill(5)] = {
                "county": r[0], "st": r[1], "adj": float(r[4] or 0),
                "cur": float(r[5]), "new": float(r[7])}
        except (TypeError, ValueError):
            continue

    fetch(CR_URL, "/tmp/cr.json")
    cr = json.load(open("/tmp/cr.json"))["data"]
    rows = []
    for geo, v in cr.items():
        fips = geo[-5:]
        if fips not in usdss or fips not in reg:
            continue
        est = v["B03002"]["estimate"]
        tot = est.get("B03002001") or 0
        if not tot:
            continue
        rows.append({**reg[fips], **usdss[fips], "fips": fips, "tot": tot,
                     "blk": est.get("B03002004") or 0,
                     "wht": est.get("B03002003") or 0})
    for r in rows:
        r["pctblk"] = 100 * r["blk"] / r["tot"]
        r["base2000"] = r["cur"] - r["adj"]
    return rows, len(usdss), len(reg)


def wm(rows, key, w):
    return sum(r[key] * r[w] for r in rows) / sum(r[w] for r in rows)


def gap(rows, key):
    """Person-weighted Black mean minus White mean, cents per gallon.
    Invariant to an additive shift of `key`, which is why cost and regulatory
    surfaces can be compared on it despite USDSS's arbitrary zero."""
    return 100 * (wm(rows, key, "blk") - wm(rows, key, "wht")) / GAL_PER_CWT


def wls_clustered(y, x, w, cluster):
    """Population-weighted slope of y on x with SEs clustered on state.
    Counties within a state share a pricing zone and a hauling network, so
    unclustered SEs are not credible here -- the same correction that moved
    Finding A's region-FE t from 13.29 to 2.17."""
    s = np.sqrt(w)
    X = np.column_stack([np.ones(len(x)), x]) * s[:, None]
    Y = y * s
    b, *_ = np.linalg.lstsq(X, Y, rcond=None)
    u = Y - X @ b
    xtx_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((2, 2))
    for c in np.unique(cluster):
        m = cluster == c
        Xu = X[m].T @ u[m]
        meat += np.outer(Xu, Xu)
    g = len(np.unique(cluster))
    V = xtx_inv @ meat @ xtx_inv * (g / (g - 1))
    se = np.sqrt(np.diag(V))
    return b[1], se[1], b[1] / se[1], g


def main():
    try:
        rows, n_usdss, n_reg = load()
    except Exception as e:
        sys.exit(f"could not assemble inputs: {e}")
    tot = sum(r["tot"] for r in rows)
    st = np.array([r["st"] for r in rows])
    w = np.array([float(r["tot"]) for r in rows])
    pb = np.array([r["pctblk"] for r in rows])
    print(f"counties: {len(rows)} matched  (USDSS {n_usdss}, USDA table {n_reg})")
    print(f"population {tot:,.0f}   Black {100*sum(r['blk'] for r in rows)/tot:.1f}%   "
          f"White non-Hisp {100*sum(r['wht'] for r in rows)/tot:.1f}%   states {len(set(st))}\n")

    SURF = (("USDSS Class I dual", "c1"),
            ("USDSS Class I minus Class III", "gu"),
            ("2000 base differentials", "base2000"),
            ("current (pre-2025) differentials", "cur"),
            ("adopted 2025 differentials", "new"))

    print("=== 1. Racial grading of each surface (level-invariant) ===")
    print(f"  {'surface':<34}{'mean':>9}{'Black-wtd':>11}{'White-wtd':>11}{'gap c/gal':>11}")
    for lab, k in SURF:
        print(f"  {lab:<34}{wm(rows,k,'tot'):>9.3f}{wm(rows,k,'blk'):>11.3f}"
              f"{wm(rows,k,'wht'):>11.3f}{gap(rows,k):>10.2f}c")

    print("\n=== 2. Slope on county %Black, person-weighted, SEs clustered on state ===")
    print(f"  {'surface':<34}{'$/cwt per pt':>14}{'c/gal per pt':>14}{'t':>8}")
    for lab, k in SURF:
        b, se, t, g = wls_clustered(np.array([r[k] for r in rows]), pb, w, st)
        print(f"  {lab:<34}{b:>+14.5f}{100*b/GAL_PER_CWT:>+14.4f}{t:>+8.2f}")
    print(f"  ({g} state clusters)")

    print("\n=== 3. How much of the adopted surface is the cost surface? ===")
    for lab, k in (("Class I dual", "c1"), ("Class I minus Class III", "gu")):
        c = np.array([r[k] for r in rows])
        for tgt_lab, tgt in (("current", "cur"), ("adopted", "new")):
            y = np.array([r[tgt] for r in rows])
            s = np.sqrt(w)
            X = np.column_stack([np.ones(len(c)), c]) * s[:, None]
            b, *_ = np.linalg.lstsq(X, y * s, rcond=None)
            fit = b[0] + b[1] * c
            r2 = 1 - (w * (y - fit) ** 2).sum() / (w * (y - wm(rows, tgt, "tot")) ** 2).sum()
            for i, rr in enumerate(rows):
                rr["_res"] = y[i] - fit[i]
            rb, rse, rt, _ = wls_clustered(np.array([rr["_res"] for rr in rows]), pb, w, st)
            print(f"  {tgt_lab:<9} on USDSS {lab:<24} R2 {r2:>5.2f}   "
                  f"residual gap {gap(rows,'_res'):>+6.2f}c   "
                  f"residual slope on %Black {rb:>+8.5f} (t {rt:>+6.2f})")

    print("\n=== 4. Where USDA departed from the cost surface ===")
    for lab, k in (("Class I dual", "c1"), ("Class I minus Class III", "gu")):
        # additive shift to a common mean: the only meaningful renormalisation of a
        # price-relative surface, and it leaves every gap statistic unchanged.
        shift = wm(rows, "new", "tot") - wm(rows, k, "tot")
        for r in rows:
            r["_dev"] = r["new"] - (r[k] + shift)
        b, se, t, _ = wls_clustered(np.array([r["_dev"] for r in rows]), pb, w, st)
        above = sum(1 for r in rows if r["_dev"] > 0.25)
        below = sum(1 for r in rows if r["_dev"] < -0.25)
        print(f"  vs {lab:<24} shift {shift:+.3f}  "
              f"above cost by >$0.25 in {above} counties, below in {below}")
        print(f"  {'':<27}deviation on %Black {b:+.5f}/cwt per pt (t {t:+.2f}), "
              f"gap {gap(rows,'_dev'):+.2f}c")

    print("\n=== 5. Counterfactual: adopt the cost surface at the adopted level ===")
    g_new = gap(rows, "new")
    print(f"  {'schedule':<44}{'gap c/gal':>11}{'vs adopted':>12}{'mean $/cwt':>12}")
    print(f"  {'adopted (2025 Final Decision)':<44}{g_new:>10.2f}c{'':>12}"
          f"{wm(rows,'new','tot'):>12.3f}")
    for lab, k in (("USDSS Class I dual, shifted to adopted mean", "c1"),
                   ("USDSS Class I minus III, shifted to adopted mean", "gu")):
        shift = wm(rows, "new", "tot") - wm(rows, k, "tot")
        for r in rows:
            r["_cf"] = r[k] + shift
        g = gap(rows, "_cf")
        print(f"  {lab:<44}{g:>10.2f}c{g-g_new:>11.2f}c{wm(rows,'_cf','tot'):>12.3f}")

    print("\n=== 6. Decomposing the 2025 widening ===")
    g_cur, g_new = gap(rows, "cur"), gap(rows, "new")
    for lab, k in (("Class I dual", "c1"), ("Class I minus Class III", "gu")):
        g_cost = gap(rows, k)
        conv, beyond = g_cost - g_cur, g_new - g_cost
        print(f"  against USDSS {lab}:")
        print(f"    current {g_cur:.2f}c -> cost surface {g_cost:.2f}c -> adopted {g_new:.2f}c")
        print(f"    of the {g_new-g_cur:+.2f}c widening: {conv:+.2f}c ({100*conv/(g_new-g_cur):.0f}%) "
              f"converges toward the cost surface, {beyond:+.2f}c ({100*beyond/(g_new-g_cur):.0f}%) goes beyond it")

    print("\n=== 7. Sensitivity on the section-4 departure regressions ===")
    rng = np.random.default_rng(20250912)
    for lab, k in (("Class I dual", "c1"), ("Class I minus Class III", "gu")):
        shift = wm(rows, "new", "tot") - wm(rows, k, "tot")
        dev = np.array([r["new"] - (r[k] + shift) for r in rows])
        b0, _, t0, _ = wls_clustered(dev, pb, w, st)
        # leave one state out
        los = []
        for c in np.unique(st):
            m = st != c
            bb, _, tt, _ = wls_clustered(dev[m], pb[m], w[m], st[m])
            los.append((bb, tt, c))
        bs = [x[0] for x in los]
        ts = [x[1] for x in los]
        worst = min(los, key=lambda x: x[1])
        sign_flips = sum(1 for x in bs if x <= 0)
        # permutation: reassign %Black across states, preserving within-state structure
        null = []
        states = list(np.unique(st))
        for _ in range(2000):
            perm = dict(zip(states, rng.permutation(states)))
            idx = {c: np.where(st == c)[0] for c in states}
            newpb = np.empty_like(pb)
            for c in states:
                src, dst = idx[perm[c]], idx[c]
                take = np.resize(pb[src], len(dst))
                newpb[dst] = take
            bb, _, _, _ = wls_clustered(dev, newpb, w, st)
            null.append(bb)
        null = np.array(null)
        pval = (np.abs(null) >= abs(b0)).mean()
        print(f"  vs {lab}: b {b0:+.5f} (t {t0:+.2f})")
        print(f"    leave-one-state-out: b in [{min(bs):+.5f}, {max(bs):+.5f}], "
              f"t in [{min(ts):+.2f}, {max(ts):+.2f}], sign flips {sign_flips}/48")
        print(f"    weakest when dropping {worst[2]} (t {worst[1]:+.2f})")
        print(f"    state-block permutation (2000 draws): two-sided p {pval:.3f}")


    print("\n=== 8. Permutation inference on the gap statistics themselves ===")
    print("  Section 7 tests whether the county-level departure is GRADED on %Black.")
    print("  The disparate-impact claim rests on a different quantity: whether the")
    print("  departure LANDS more on Black people in aggregate.  Same state-block")
    print("  permutation, applied to the gap.")
    states = list(np.unique(st))
    idx = {c: np.where(st == c)[0] for c in states}
    blk = np.array([float(r["blk"]) for r in rows])
    wht = np.array([float(r["wht"]) for r in rows])

    def gap_arr(v, b, h):
        return 100 * ((v * b).sum() / b.sum() - (v * h).sum() / h.sum()) / GAL_PER_CWT

    rng2 = np.random.default_rng(20250913)
    def perm_p(v, obs, n=2000):
        hits = 0
        for _ in range(n):
            pm = dict(zip(states, rng2.permutation(states)))
            nb, nh = np.empty_like(blk), np.empty_like(wht)
            for c in states:
                src, dst = idx[pm[c]], idx[c]
                nb[dst] = np.resize(blk[src], len(dst))
                nh[dst] = np.resize(wht[src], len(dst))
            if abs(gap_arr(v, nb, nh)) >= abs(obs):
                hits += 1
        return hits / n

    tests = [("current differentials", np.array([r["cur"] for r in rows])),
             ("adopted differentials", np.array([r["new"] for r in rows])),
             ("USDSS Class I dual", np.array([r["c1"] for r in rows])),
             ("USDSS Class I minus III", np.array([r["gu"] for r in rows]))]
    for lab, k in (("Class I dual", "c1"), ("Class I minus Class III", "gu")):
        shift = wm(rows, "new", "tot") - wm(rows, k, "tot")
        tests.append((f"adopted MINUS cost ({lab})",
                      np.array([r["new"] - (r[k] + shift) for r in rows])))
    print(f"  {'surface':<40}{'gap c/gal':>11}{'perm p':>9}")
    for lab, v in tests:
        o = gap_arr(v, blk, wht)
        print(f"  {lab:<40}{o:>10.2f}c{perm_p(v, o):>9.3f}")

    print("\n  A surface is racially graded here only through where people live relative to")
    print("  milk. Any gap the cost surface itself carries is the part a least-cost")
    print("  transport model cannot avoid; the excess over it is the part USDA chose.")


if __name__ == "__main__":
    main()
