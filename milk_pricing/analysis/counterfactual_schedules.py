"""Compare the racial incidence of every Class I differential schedule that was
before USDA at the 2023-24 national hearing.

Backs reports/counterfactual.md addendum.

    python3 analysis/counterfactual_schedules.py

Four county-level schedules, all public:
  * current effective       - USDA's own table, 'Current vs. Proposed' sheet
  * USDA adopted            - same table, Final Decision column
  * NMPF proposal           - Appendix A, NationalHearingNMPFProposedDifferentials.pdf
  * MIG proposal            - Appendix B, NationalHearingMIGProposedDifferentials.pdf
joined by FIPS to ACS 2023 B03002 via Census Reporter.

Two things to know about the inputs:
  * MIG quotes the BASE 1000.52 differential; USDA's "current effective" adds the
    2008 FO 5/6/7 southeastern adjustment. NMPF quotes the effective value.
  * MIG's proposal is a uniform -$1.60 in every county, so its level and its
    distribution separate exactly. That is what makes the rescaled comparison
    below meaningful rather than a fudge.
"""
import json
import re
import subprocess
import sys
from collections import Counter

import numpy as np

GAL_PER_CWT = 11.6289
BASE = "https://www.ams.usda.gov/sites/default/files/media/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.4 Safari/605.1.15")
APPENDICES = {"mig": "NationalHearingMIGProposedDifferentials.pdf",
              "nmpf": "NationalHearingNMPFProposedDifferentials.pdf"}
ROW = re.compile(r"([A-Za-z][A-Za-z .'\-]{1,34}?)\s+([A-Z]{2})\s+(\d{4,5})"
                 r"\s+(\d+\.\d{1,2})\s+(\d+\.\d{1,2})")


def fetch(name):
    path = f"/tmp/{name}"
    subprocess.run(["curl", "-sSL", "-o", path, "-A", UA, "-H",
                    "Referer: https://www.ams.usda.gov/", BASE + name],
                   check=True, timeout=300)
    return path


def parse_appendix(name):
    from pypdf import PdfReader
    t = "\n".join((p.extract_text() or "") for p in PdfReader(fetch(name)).pages)
    flat = re.sub(r"\s+", " ", t)
    return {m.group(3).zfill(5): {"cur": float(m.group(4)), "prop": float(m.group(5))}
            for m in ROW.finditer(flat)}


def main():
    try:
        import counterfactual as cf
    except ImportError:
        sys.path.insert(0, __file__.rsplit("/", 1)[0])
        import counterfactual as cf
    try:
        base, _ = cf.load()
        sched = {k: parse_appendix(v) for k, v in APPENDICES.items()}
    except Exception as e:
        sys.exit(f"could not assemble inputs: {e}")

    demo = {r["fips"]: r for r in base}
    J = [{**demo[f], "mig": sched["mig"][f]["prop"], "nmpf": sched["nmpf"][f]["prop"],
          "mig_base": sched["mig"][f]["cur"], "nmpf_base": sched["nmpf"][f]["cur"]}
         for f in demo if f in sched["mig"] and f in sched["nmpf"]]
    tot = sum(r["tot"] for r in J)
    print(f"counties across all four schedules: {len(J)}   population {tot:,.0f}\n")

    print("=== MIG's proposal is one number ===")
    print("  changes from base: ",
          Counter(round(v["prop"] - v["cur"], 4) for v in sched["mig"].values()).most_common(4))
    dn = [round(v["prop"] - v["cur"], 4) for v in sched["nmpf"].values()]
    print(f"  NMPF: min {min(dn):+.2f}  max {max(dn):+.2f}  {len(set(dn))} distinct values")
    print("  baseline check, MIG vs USDA effective:",
          Counter(round(r["cur"] - r["mig_base"], 2) for r in J).most_common(3))
    print("  baseline check, NMPF vs USDA effective:",
          Counter(round(r["cur"] - r["nmpf_base"], 2) for r in J).most_common(2))

    def lvl(k):
        return sum(r[k] * r["tot"] for r in J) / tot

    def gap(k):
        b = sum(r[k] * r["blk"] for r in J) / sum(r["blk"] for r in J)
        w = sum(r[k] * r["wht"] for r in J) / sum(r["wht"] for r in J)
        return 100 * (b - w) / GAL_PER_CWT

    LABELS = (("MIG proposal (Appendix B)", "mig"), ("current effective", "cur"),
              ("NMPF proposal (Appendix A)", "nmpf"), ("USDA adopted (Final Decision)", "new"))
    print("\n=== As filed ===")
    print(f"  {'schedule':<34}{'mean $/cwt':>12}{'gap c/gal':>12}")
    for lab, k in LABELS:
        print(f"  {lab:<34}{lvl(k):>12.4f}{gap(k):>11.2f}c")

    print(f"\n=== Same shape, rescaled to the adopted level (${lvl('new'):.4f}) ===")
    for lab, k in LABELS:
        shift = lvl("new") - lvl(k)
        for r in J:
            r[k + "_s"] = r[k] + shift
        print(f"  {lab:<34}{lvl(k+'_s'):>12.4f}{gap(k+'_s'):>11.2f}c")
    red = 100 * (gap("new") - gap("mig")) / gap("new")
    print(f"\n  MIG's shape at the adopted level cuts the gap {red:.0f}%")

    print("\n=== USDA's own departures from NMPF ===")
    for r in J:
        r["over"] = r["new"] - r["nmpf"]
    x = np.array([r["pctblk"] for r in J])
    y = np.array([r["over"] for r in J])
    sw = np.sqrt(np.array([r["tot"] for r in J]))
    X = np.column_stack([np.ones(len(x)), x]) * sw[:, None]
    b, *_ = np.linalg.lstsq(X, y * sw, rcond=None)
    res = y * sw - X @ b
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * (res @ res / (len(y) - 2)))
    above = sum(1 for r in J if r["over"] > 1e-3)
    print(f"  above NMPF in {above} counties, below in {sum(1 for r in J if r['over'] < -1e-3)}")
    print(f"  deviation on %Black: {b[1]:+.5f}/cwt per point (t {b[1]/se[1]:+.2f})")
    print("  -> USDA cut less where the Black share was higher, which is why its gap")
    print("     exceeds NMPF's despite a lower national level.")
    print("\n  CAVEAT: MIG's filing cuts the mean level to $1.00/cwt, which USDA could reject")
    print("  on producer-return grounds. The rescaling isolates distribution from level; it is")
    print("  not a schedule anyone submitted.")


if __name__ == "__main__":
    main()
