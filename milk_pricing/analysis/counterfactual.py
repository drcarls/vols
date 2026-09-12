"""The section 6 counterfactual: does the 2025 Class I amendment widen the racial
gap, and is a revenue-neutral alternative available?

Backs reports/counterfactual.md. County universe, 3,100 counties, 329M people.

    python3 analysis/counterfactual.py

Inputs, both public:
  * USDA's own county table, AMS national FMMO pricing hearing page —
    DairyFMMO_USDADifferentialsCurrentvsProposedforFD.xlsx, sheet 'Current vs. Proposed'.
    Columns: county, state, FIPS, 2000 base differential, FO 5/6/7 adjustment (the
    2008 southeastern update), current effective differential, Recommended Decision
    value, Final Decision value, change.
  * ACS 2023 table B03002 by county, via the Census Reporter API. The Census
    Bureau's own API now returns "Missing Key" without a registered key;
    Census Reporter needs none.

NOTE on "revenue-neutral": the aggregate held constant here is the
POPULATION-weighted mean increase, not USDA's Class I VOLUME-weighted figure
(REIA Table 1). Per-capita fluid consumption varies regionally, so this is a
proxy. Direction and rough magnitude are robust; the exact figure would move
under proper volume weights.
"""
import json
import subprocess
import sys

import numpy as np

GAL_PER_CWT = 11.6289
XLSX = "/tmp/DairyFMMO_USDADifferentialsCurrentvsProposedforFD.xlsx"
XLSX_URL = ("https://www.ams.usda.gov/sites/default/files/media/"
            "DairyFMMO_USDADifferentialsCurrentvsProposedforFD.xlsx")
CR_URL = ("https://api.censusreporter.org/1.0/data/show/latest"
          "?table_ids=B03002&geo_ids=050|01000US")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.4 Safari/605.1.15")


def fetch(url, path, referer=None):
    cmd = ["curl", "-sSL", "-o", path, "-A", UA]
    if referer:
        cmd += ["-H", f"Referer: {referer}"]
    subprocess.run(cmd + [url], check=True, timeout=300)


def load():
    import openpyxl
    fetch(XLSX_URL, XLSX, referer="https://www.ams.usda.gov/")
    ws = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)["Current vs. Proposed"]
    diffs = {}
    for r in ws.iter_rows(min_row=5, values_only=True):
        if not r or r[2] in (None, ""):
            continue
        try:
            fips = str(int(float(r[2]))).zfill(5)
            diffs[fips] = {"county": r[0], "st": r[1], "adj": float(r[4] or 0),
                           "cur": float(r[5]), "new": float(r[7])}
        except (TypeError, ValueError):
            continue

    fetch(CR_URL, "/tmp/cr.json")
    cr = json.load(open("/tmp/cr.json"))["data"]
    rows = []
    for geo, v in cr.items():
        est = v["B03002"]["estimate"]
        fips = geo[-5:]
        tot = est.get("B03002001") or 0
        if not tot or fips not in diffs:
            continue
        rows.append({**diffs[fips], "fips": fips, "tot": tot,
                     "blk": est.get("B03002004") or 0,
                     "wht": est.get("B03002003") or 0})
    for r in rows:
        r["chg"] = r["new"] - r["cur"]
        r["base2000"] = r["cur"] - r["adj"]
        r["pctblk"] = 100 * r["blk"] / r["tot"]
    return rows, len(diffs)


def wm(rows, key, w):
    return sum(r[key] * r[w] for r in rows) / sum(r[w] for r in rows)


def gap_cents(rows, key):
    return 100 * (wm(rows, key, "blk") - wm(rows, key, "wht")) / GAL_PER_CWT


def main():
    try:
        rows, n_diff = load()
    except Exception as e:
        sys.exit(f"could not assemble inputs: {e}")
    tot = sum(r["tot"] for r in rows)
    print(f"counties matched: {len(rows)} of {n_diff}   population {tot:,.0f}   "
          f"Black {100*sum(r['blk'] for r in rows)/tot:.1f}%   "
          f"White non-Hisp {100*sum(r['wht'] for r in rows)/tot:.1f}%\n")

    print("=== 1. Person-weighted mean differential ===")
    print(f"  {'schedule':<28}{'Black-wtd':>12}{'White-wtd':>12}{'gap $/cwt':>12}{'gap c/gal':>12}")
    for lab, key in (("current (pre-2025)", "cur"), ("adopted (2025)", "new")):
        b, w = wm(rows, key, "blk"), wm(rows, key, "wht")
        print(f"  {lab:<28}{b:>12.4f}{w:>12.4f}{b-w:>12.4f}{100*(b-w)/GAL_PER_CWT:>11.2f}c")
    g0, g1 = gap_cents(rows, "cur"), gap_cents(rows, "new")
    print(f"  -> widened {g0:.2f}c to {g1:.2f}c  (+{g1-g0:.2f}c, {100*(g1-g0)/g0:+.0f}%)")

    x = np.array([r["pctblk"] for r in rows])
    y = np.array([r["chg"] for r in rows])
    sw = np.sqrt(np.array([r["tot"] for r in rows]))
    X = np.column_stack([np.ones(len(x)), x]) * sw[:, None]
    b, *_ = np.linalg.lstsq(X, y * sw, rcond=None)
    res = y * sw - X @ b
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / (len(y) - 2)))
    print(f"  change on %Black, population-weighted: {b[1]:+.5f}/cwt per point "
          f"(t {b[1]/se[1]:+.2f}) = {100*b[1]/GAL_PER_CWT:+.4f}c/gal per point")

    print("\n=== 2. The gap was built in discrete actions ===")
    for lab, key in (("2000 base differentials", "base2000"),
                     ("+ 2008 adjustment, orders 5/6/7", "cur"),
                     ("+ 2025 amendment", "new")):
        print(f"  {lab:<36}{gap_cents(rows, key):>7.2f}c")

    print("\n=== 3. Revenue-neutral counterfactuals (same aggregate increase) ===")
    agg = sum(r["chg"] * r["tot"] for r in rows) / tot
    print(f"  adopted population-weighted mean increase: {agg:.4f}/cwt "
          f"({100*agg/GAL_PER_CWT:.2f}c/gal)\n")
    for r in rows:
        r["cf_flat"] = r["cur"] + agg
    scale = agg / (sum(r["cur"] * r["tot"] for r in rows) / tot)
    for r in rows:
        r["cf_prop"] = r["cur"] * (1 + scale)
    excess = sum(max(r["chg"] - agg, 0) * r["tot"] for r in rows) / tot
    short = sum(r["tot"] for r in rows if r["chg"] < agg) / tot
    for r in rows:
        r["cf_cap"] = r["cur"] + min(r["chg"], agg) + (excess / short if r["chg"] < agg else 0)
    print(f"  {'schedule':<46}{'gap c/gal':>11}{'vs adopted':>12}{'mean inc':>11}")
    print(f"  {'adopted (2025 Final Decision)':<46}{g1:>10.2f}c{'':>12}{agg:>11.4f}")
    for lab, key in (("(1) flat national increase", "cf_flat"),
                     ("(2) proportional to current differential", "cf_prop"),
                     ("(3) cap at the mean, redistribute excess", "cf_cap")):
        g = gap_cents(rows, key)
        chk = sum((r[key] - r["cur"]) * r["tot"] for r in rows) / tot
        print(f"  {lab:<46}{g:>10.2f}c{g-g1:>11.2f}c{chk:>11.4f}")
    print(f"\n  removable at constant aggregate cost: up to {g1-gap_cents(rows,'cf_flat'):.2f}c of "
          f"{g1:.2f}c = {100*(g1-gap_cents(rows,'cf_flat'))/g1:.0f}% of the gap, "
          f"100% of the 2025 widening.")
    print("  CAVEAT: a flat increase sends no locational signal and defeats the rule's stated")
    print("  purpose. Counterfactual (3) preserves the geographic slope and is the defensible one.")
    print("  NOT TESTED: the memo's own counterfactual, tracking the USDSS model. Those county")
    print("  values are hearing exhibits and were not obtainable from the published record.")


if __name__ == "__main__":
    main()
