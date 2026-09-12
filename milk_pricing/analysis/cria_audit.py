"""Audit the 2025 FMMO final rule and its Civil Rights Impact Analysis.

Backs reports/cria_audit.md. Downloads both public PDFs and reproduces every
count and quotation in that report.

    python3 analysis/cria_audit.py

Method note: keyword counts use WORD BOUNDARIES. A plain case-insensitive
substring search for "WIC" returns 7 false hits in the final rule from
BRUNSWICK, SEDGWICK, WICHITA and WICOMICO; the true count is zero. Counts here
also probe for hyphen-split and letter-spaced variants, because a PDF text
layer can break a word across a line.
"""
import io
import re
import sys
import urllib.request
from collections import Counter

RULE = ("https://www.govinfo.gov/content/pkg/FR-2025-01-17/pdf/2025-00563.pdf",
        "2025 FMMO final rule (90 Fed. Reg., Jan. 17, 2025)")
FOR_CRIA = ("https://www.ams.usda.gov/sites/default/files/media/"
            "FOR%20Civil%20Rights%20Impact%20Analysis.pdf",
            "AMS CRIA of Federal Milk Marketing Order Reform (c. 1999-2000)")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def text_of(url):
    from pypdf import PdfReader
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read()
    rd = PdfReader(io.BytesIO(raw))
    t = "\n".join((p.extract_text() or "") for p in rd.pages)
    return len(rd.pages), re.sub(r"\s+", " ", t)


TERMS = [
    (r"\bconsum\w*", "consumer / consumption"),
    (r"con-\s*sum\w*", "  (hyphen-split variant)"),
    (r"\bretail\w*", "retail"),
    (r"\bhousehold\w*", "household"),
    (r"\bbuyer\w*|\bshopper\w*", "buyer / shopper"),
    (r"\bWIC\b", "WIC (word-boundary)"),
    (r"\bSNAP\b|food stamp\w*|nutrition assistance", "SNAP / food stamps"),
    (r"\bincidence\b|\bdistributional\b", "incidence / distributional"),
    (r"low[- ]income", "low-income"),
    (r"public assistance", '"public assistance"'),
    (r"\bminorit\w*", "minority"),
    (r"\bproducer\w*", "producer"),
    (r"\bhandler\w*", "handler"),
    (r"Class I differential", "Class I differential"),
]


def main():
    for url, label in (RULE, FOR_CRIA):
        try:
            pages, t = text_of(url)
        except Exception as e:
            print(f"\n{label}\n  could not fetch/parse: {e}")
            continue
        print(f"\n=== {label} ===")
        print(f"  {pages} pages, {len(t):,} characters\n")
        for pat, lab in TERMS:
            print(f"  {lab:<30}{len(re.findall(pat, t, re.I)):>5}")

        if url == RULE[0]:
            m = re.search(r"Civil Rights Impact Analysis AMS has reviewed.*?"
                          r"No major civil rights impact is likely to result from this final rule\.", t)
            if m:
                print(f"\n  CRIA section: {len(m.group(0))} characters, "
                      f"{len(re.findall(r'[.]', m.group(0)))} sentences")
                print(f"  verbatim:\n    {m.group(0)}")
            rfa = re.search(r"Regulatory Flexibility Act and Paperwork Reduction Act.{0,20000}", t)
            if rfa:
                print(f"\n  Regulatory Flexibility Act analysis, same rule: "
                      f"{len(rfa.group(0)):,}+ characters")
        else:
            print("\n  What are the 'minority' mentions about?")
            ctx = Counter()
            for m in re.finditer(r"minorit\w*", t, re.I):
                w = t[max(0, m.start() - 90):m.end() + 90].lower()
                if any(k in w for k in ("producer", "farmer", "dairy farm", "operator")):
                    ctx["minority producers / dairy operators"] += 1
                elif any(k in w for k in ("consum", "beneficiar")):
                    ctx["consumers / beneficiaries"] += 1
                else:
                    ctx["unclassified"] += 1
            for k, v in ctx.most_common():
                print(f"    {k:<40}{v:>5}")
            print("\n  -> the comparator is far more rigorous but is ALSO industry-scoped;")
            print("     it contains no consumer incidence analysis either.")


if __name__ == "__main__":
    main()
