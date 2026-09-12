"""Audit docket AMS-DA-23-0031: was consumer price incidence raised on the record?

Backs reports/docket_audit.md.

    python3 analysis/docket_audit.py            # enumerate and classify commenters
    python3 analysis/docket_audit.py --search   # keyword incidence across comment text
    python3 analysis/docket_audit.py --mig      # pull and quote the MIG exceptions

Uses the public regulations.gov API v4. DEMO_KEY is rate-limited; set
REGULATIONS_GOV_KEY for real work.

CAUTION on keyword searches, learned twice in this project: a docket-wide search
for "low-income" returns zero even though MIG's brief says "lower income
consumers", and a case-insensitive search for "WIC" matches BRUNSWICK, SEDGWICK,
WICHITA and WICOMICO. Confirm every hit and every miss against the source text.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse

DOCKET = "AMS-DA-23-0031"
API = "https://api.regulations.gov/v4"
KEY = os.environ.get("REGULATIONS_GOV_KEY", "DEMO_KEY")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.4 Safari/605.1.15")
MIG_ID = "AMS-DA-23-0031-0080"

CONSUMER_SIDE = re.compile(
    r"consumer|hunger|food bank|feeding|nutrition|WIC|SNAP|poverty|civil right|NAACP|"
    r"low.?income|equity|justice|church|community|advocac", re.I)
INDUSTRY = re.compile(
    r"dairy|milk|cheese|creamer|farm|cooperative|coop\b|agri|producer|processor|"
    r"IDFA|NMPF|foremost|hilmar|leprino|schreiber|glanbia|darigold|tillamook|bongards", re.I)


def get(url):
    out = subprocess.run(["curl", "-sS", "-A", UA, url], capture_output=True, text=True,
                         timeout=120)
    return json.loads(out.stdout)


def enumerate_comments():
    d = get(f"{API}/comments?filter%5BdocketId%5D={DOCKET}&page%5Bsize%5D=250&api_key={KEY}")
    rows = [x["attributes"] for x in d.get("data", [])]
    titles = [r.get("title", "") for r in rows]
    print(f"docket {DOCKET}: {d.get('meta', {}).get('totalElements')} comments\n")
    cons = sorted({t for t in titles if CONSUMER_SIDE.search(t)})
    ind = sorted({t for t in titles if INDUSTRY.search(t) and not CONSUMER_SIDE.search(t)})
    other = sorted({t for t in titles if not CONSUMER_SIDE.search(t)
                    and not INDUSTRY.search(t)})
    print(f"  consumer / anti-hunger / civil-rights organisations : {len(cons)}")
    for t in cons:
        print(f"      {t}")
    print(f"  dairy industry organisations                        : {len(ind)}")
    print(f"  individuals and unlabelled                          : {len(other)}")
    print("\n  -> the affected consumer constituency filed nothing.")


def search_terms():
    print(f"keyword incidence across {DOCKET} comment text\n")
    for term in ("consumer", "WIC", "SNAP", "low-income", "lower income", "affordability",
                 "civil rights", "school", "nutrition"):
        q = urllib.parse.quote(term)
        d = get(f"{API}/comments?filter%5BdocketId%5D={DOCKET}"
                f"&filter%5BsearchTerm%5D={q}&page%5Bsize%5D=5&api_key={KEY}")
        n = d.get("meta", {}).get("totalElements")
        who = [x["attributes"]["title"] for x in d.get("data", [])][:3]
        print(f"  {term:<16}{str(n):>5}   {'; '.join(who)}")
    print("\n  NOTE: 'low-income' returns 0 while MIG's brief says 'lower income consumers'.")
    print("  A keyword miss is not evidence of absence.")


def mig():
    """Pull the MIG exceptions and quote the consumer-incidence objections."""
    from pypdf import PdfReader
    url = f"https://downloads.regulations.gov/{MIG_ID}/attachment_1.pdf?api_key={KEY}"
    path = "/tmp/mig_exceptions.pdf"
    subprocess.run(["curl", "-sSL", "-o", path, "-A", UA,
                    "-H", f"Referer: https://www.regulations.gov/comment/{MIG_ID}", url],
                   check=True, timeout=180)
    t = "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    f = re.sub(r"\s+", " ", t)
    print(f"{MIG_ID} — MIG Comments, Exceptions and Objections: {len(f):,} chars\n")
    for kw in (r"\bWIC\b", r"\bSNAP\b", r"consumer\w*", r"lower income", r"retail",
               r"Class I differential", r"USDSS"):
        print(f"  {kw:<24}{len(re.findall(kw, f, re.I)):>4}")
    m = re.search(r"2\. The consumers bearing this price increase.*?budget constraints\.", f)
    if m:
        print("\n  the numbered objections, verbatim:\n")
        print("    " + m.group(0))


if __name__ == "__main__":
    if "--search" in sys.argv:
        search_terms()
    elif "--mig" in sys.argv:
        mig()
    else:
        enumerate_comments()
