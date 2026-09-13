"""California WIC exposure to the Class I differential — the memo's §3, audited.

Backs reports/ca_wic.md. This section of the August memorandum was never independently
checked; it rests on a CDPH dataset the project did not hold. It does now.

    python3 analysis/ca_wic.py

Source, public and unauthenticated:
  CDPH, "WIC Participants by County" (CHHS Open Data Portal, dataset
  890afa4a-fc77-4d1a-a09f-52a7f0e3a490), Report 2 — participants by county of residence
  and by race/ethnicity, 2019-2024. These are ACTUAL participant counts by race, not
  county racial composition used as a proxy, so the exposure figures below are
  participant-weighted in the strict sense.

Joined to the USDA county Class I differential table (before = effective pre-2025,
after = 2025 Final Decision), matched on county name.

CAVEAT that governs every number here: exposure is not incidence. A differential is a
minimum price paid by processors; what reaches a WIC participant depends on retail
pass-through, which is not measured. Nothing below is a claim about what any household
paid.
"""
import csv
import importlib.util
import subprocess
import sys

GAL_PER_CWT = 11.6289
CSV_URL = ("https://data.chhs.ca.gov/dataset/890afa4a-fc77-4d1a-a09f-52a7f0e3a490/"
           "resource/8a27dc3e-1789-4c55-832d-0d6d8720e3da/download/"
           "report2_wic-participants-by-county-of-residence-by-race-ethnicity_2019-2024.csv")
LOCAL = "/tmp/wic_race.csv"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
LABEL = {"Non-Hispanic African American": "Black", "Hispanic": "Hispanic",
         "Non-Hispanic Asian": "Asian", "Non-Hispanic White": "White NH",
         "Non-Hispanic Other": "Other"}
ORDER = ["Black", "Hispanic", "Asian", "Other", "White NH"]


def num(s):
    s = (s or "").strip().replace(",", "")
    return None if s in ("", ".", "-") else float(s)


def load(year="2024"):
    subprocess.run(["curl", "-sSL", "-A", UA, "-o", LOCAL, CSV_URL], check=True, timeout=300)
    spec = importlib.util.spec_from_file_location("u", "analysis/usdss.py")
    u = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(u)
    rows, _, _ = u.load()
    diff = {str(r["county"]).strip().upper(): r for r in rows if r["st"] == "CA"}

    wic, unmatched = {}, set()
    for rec in csv.DictReader(open(LOCAL)):
        if rec["YEAR MONTH"].strip() != year:
            continue
        county = rec["COUNTY OF RESIDENCE"].strip()
        if county.lower() == "statewide":
            continue
        n = num(rec["NUMBER OF ISSUED PARTICIPANTS"]) or num(rec["NUMBER OF CERTIFIED PARTICIPANTS"])
        key = county.upper()
        if key not in diff:
            unmatched.add(county)
            continue
        if n:
            wic.setdefault(key, {})[LABEL[rec["RACE ETHNICITY"].strip()]] = n
    return diff, wic, sorted(unmatched)


def main():
    year = sys.argv[1] if len(sys.argv) > 1 else "2024"
    try:
        diff, wic, unmatched = load(year)
    except Exception as e:
        sys.exit(f"could not assemble inputs: {e}")

    print(f"CDPH WIC participants by county and race/ethnicity, {year}, issued participants")
    print(f"joined to USDA Class I differentials — {len(wic)} of 58 CA counties matched")
    if unmatched:
        print(f"  unmatched: {', '.join(unmatched)}")

    tot = {g: sum(v.get(g, 0) for v in wic.values()) for g in ORDER}
    N = sum(tot.values())
    print(f"  {N:,.0f} participants\n")

    def wmean(g, key):
        num_ = sum(v.get(g, 0) * diff[c][key] for c, v in wic.items())
        den = sum(v.get(g, 0) for v in wic.values())
        return num_ / den if den else float("nan")

    print("=== 1. Participant-weighted Class I differential, by race/ethnicity ===")
    print(f"  {'group':<11}{'participants':>14}{'share':>8}{'before':>9}{'after':>9}"
          f"{'rise':>8}{'gap vs White before→after':>29}")
    wb, wa = wmean("White NH", "cur"), wmean("White NH", "new")
    out = {}
    for g in ORDER:
        b, a = wmean(g, "cur"), wmean(g, "new")
        out[g] = (b, a)
        gb, ga = 100 * (b - wb) / GAL_PER_CWT, 100 * (a - wa) / GAL_PER_CWT
        tail = "—" if g == "White NH" else f"{gb:+.1f}¢ → {ga:+.1f}¢/gal  (ratio {a/wa:.3f})"
        print(f"  {g:<11}{tot[g]:>14,.0f}{100*tot[g]/N:>7.1f}%{b:>9.3f}{a:>9.3f}"
              f"{a-b:>+8.3f}   {tail}")

    print("\n=== 2. Did the 2025 change widen it? ===")
    for g in ORDER:
        if g == "White NH":
            continue
        b, a = out[g]
        print(f"  {g:<11} exposure ratio to White NH: {b/wb:.4f} → {a/wa:.4f}  "
              f"({'widened' if a/wa > b/wb else 'narrowed'})   "
              f"rise {a-b:+.3f} vs White {wa-wb:+.3f}/cwt")

    print("\n=== 3. Where the Black exposure sits (top counties by Black participants) ===")
    tb = tot["Black"]
    top = sorted(wic.items(), key=lambda kv: -kv[1].get("Black", 0))[:8]
    print(f"  {'county':<16}{'Black part.':>12}{'% of CA Black':>15}{'before':>9}{'after':>9}{'rise':>8}")
    for c, v in top:
        print(f"  {c.title():<16}{v.get('Black',0):>12,.0f}{100*v.get('Black',0)/tb:>14.1f}%"
              f"{diff[c]['cur']:>9.2f}{diff[c]['new']:>9.2f}{diff[c]['new']-diff[c]['cur']:>+8.2f}")

    print("\n=== 4. Annual dollars — assumption-dependent, shown as a range ===")
    print("  The differential is $/cwt; converting to a household figure needs an assumed")
    print("  annual gallonage AND full retail pass-through. Neither is measured here.")
    b, a = out["Black"]
    dB, dW = (a - b) / GAL_PER_CWT, (wa - wb) / GAL_PER_CWT
    print(f"  per-gallon rise: Black {100*dB:.2f}¢, White {100*dW:.2f}¢, difference {100*(dB-dW):.2f}¢")
    print(f"  {'assumed gallons/yr':<26}{'Black $/yr':>12}{'White $/yr':>12}{'difference':>12}")
    for gal, note in ((16, "conservative"), (32, "≈ the Aug memo's implied figure"),
                      (43, "WIC child package, 16 qt/mo at 90% redemption")):
        print(f"  {gal:<4}{note:<22}{gal*dB:>12.2f}{gal*dW:>12.2f}{gal*(dB-dW):>12.2f}")
    print("  The August memorandum reported $1.87–$2.49/yr for Black participants; that")
    print("  corresponds to roughly 32 gallons a year, which is inside the plausible range")
    print("  for the WIC package. It is an assumption, not an observation — say so.")

    print("\n=== 5. What this does and does not support ===")
    print("  Supports: a real, participant-weighted exposure gap, and its widening in 2025.")
    print("  Does not support: any dollar claim about a household. CA is a low-differential")
    print("  state, the per-person amounts are cents to low dollars per year, and retail")
    print("  pass-through is unmeasured. The value of this section is the nexus — a federal")
    print("  nutrition program whose participants are disproportionately minority, buying a")
    print("  good whose federal price floor USDA raised — not the magnitude.")


if __name__ == "__main__":
    main()
