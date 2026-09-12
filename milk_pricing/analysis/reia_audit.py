"""Audit USDA's Regulatory Economic Impact Analysis for the 2025 FMMO amendments.

Backs reports/reia_audit.md. AMS-DA-23-0031-0003, July 2024, 8 pages.

    python3 analysis/reia_audit.py

Establishes three things from the document itself: the size of the transfer USDA
quantified, USDA's stated reason for not running its own econometric model, and
the complete absence of any consumer or distributional analysis.
"""
import re
import subprocess
import sys

URL = ("https://downloads.regulations.gov/AMS-DA-23-0031-0003/content.pdf"
       "?api_key=DEMO_KEY")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.4 Safari/605.1.15")
PATH = "/tmp/reia.pdf"

# Increases by order, $M, from Table 3 — kept here so the arithmetic is checkable.
BY_ORDER = {"Northeast": 874.1, "Mideast": 747.4, "Appalachian": 470.1, "Central": 410.4,
            "Southeast": 328.9, "California": 302.6, "Southwest": 276.2,
            "Upper Midwest": 225.6, "Florida": 204.9, "Pacific Northwest": 111.2,
            "Arizona": 58.2}
SOUTHEASTERN = ("Appalachian", "Southeast", "Florida")

ABSENT = [(r"consum\w*", "consumer"), (r"retail\w*", "retail"), (r"household\w*", "household"),
          (r"school\w*", "school"), (r"\bWIC\b", "WIC"), (r"\bSNAP\b", "SNAP"),
          (r"nutrition\w*", "nutrition"), (r"low[- ]?income", "low-income"),
          (r"\bincidence\b", "incidence"), (r"distributional", "distributional"),
          (r"\bpublic\b", "public"), (r"\bbenefit\w*", "benefit")]
PRESENT = [(r"\bproducer\w*", "producer"), (r"\bhandler\w*", "handler"),
           (r"\bprocessor\w*", "processor"), (r"Class I differential", "Class I differential")]


def text():
    from pypdf import PdfReader
    subprocess.run(["curl", "-sSL", "-o", PATH, "-A", UA, "-H",
                    "Referer: https://www.regulations.gov/document/AMS-DA-23-0031-0003", URL],
                   check=True, timeout=180)
    rd = PdfReader(PATH)
    return len(rd.pages), re.sub(r"\s+", " ", "\n".join((p.extract_text() or "")
                                                        for p in rd.pages))


def main():
    try:
        pages, t = text()
    except Exception as e:
        sys.exit(f"could not retrieve the REIA: {e}")
    print(f"REIA: {pages} pages, {len(t):,} characters\n")

    print("=== 1. The transfer USDA quantified ===")
    tot = sum(BY_ORDER.values())
    print(f"  Class I revenue increase, 2019-2023: ${tot/1000:.2f}bn")
    se = sum(BY_ORDER[k] for k in SOUTHEASTERN)
    print(f"  three Southeastern orders: ${se/1000:.2f}bn = {100*se/tot:.0f}% of the national increase")
    for pat in (r"total Class I revenue with the recommended amendments is calculated to be [^.]+\.",
                r"The value, however, increases \$[\d.]+ billion over the 5-year period[^.]*\.",
                r"Total Pool Value \(\$\)[^A-Za-z]{0,80}"):
        m = re.search(pat, t)
        if m:
            print(f"  verbatim: {m.group(0).strip()}")

    print("\n=== 2. Why USDA did not model the impacts ===")
    m = re.search(r"The dynamic AMS regional econometric model was not used.{0,1250}", t)
    if m:
        print("  " + m.group(0).strip())

    print("\n=== 3. Who the analysis is about ===")
    print("  absent entirely:")
    for pat, lab in ABSENT:
        print(f"    {lab:<16}{len(re.findall(pat, t, re.I)):>4}")
    print("  present:")
    for pat, lab in PRESENT:
        print(f"    {lab:<16}{len(re.findall(pat, t, re.I)):>4}")

    print("\n=== 4. The static premise ===")
    m = re.search(r"This static analysis operates using several key assumptions:.{0,420}", t)
    if m:
        print("  " + m.group(0).strip())

    print("\n  QUALIFICATION: a pool-level transfer is not a consumer burden. Class I")
    print("  pass-through into Walmart shelf price measured here is 0.37x within state")
    print("  (t 1.68, n.s.) — see reports/walmart_pricing_geography.md. The argument is")
    print("  failure to analyse incidence, not a damages figure.")


if __name__ == "__main__":
    main()
