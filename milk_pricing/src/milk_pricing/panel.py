"""The canonical national panel, and the exclusions applied to it.

Excluded states and why:

  PA, NJ  minimum RETAIL milk price. New Jersey's Milk Control Act sets a
          presumptive retail price; Pennsylvania's Milk Marketing Board sets a
          minimum retail price by marketing area. In these states the shelf
          price is set by statute, not by the retailer.
  ME, ND, VA, MT
          USDA-listed classified pricing programs whose effect reaches retail:
          all four sit at 0-3% coefficient of variation, against 12% where no
          regime applies.
  AK, HI  non-contiguous. Freight dominates: HI averages $6.28/gal on a single
          statewide price, the highest in the country, and AK $4.98.

NOT excluded: the ~24 states with general below-cost / minimum-markup statutes.
Those floor price at cost plus a few percent, milk is rarely sold below cost, and
the floor does not bind - the four least compressed states in the country (SC,
MA, NC, TN) all have one. See reports/state_pricing_laws.md.
"""

from __future__ import annotations

import csv

RETAIL_PRICE_FIX = {"PA", "NJ"}
CLASSIFIED_REACHING_RETAIL = {"ME", "ND", "VA", "MT"}
NON_CONTIGUOUS = {"AK", "HI"}
EXCLUDED = RETAIL_PRICE_FIX | CLASSIFIED_REACHING_RETAIL | NON_CONTIGUOUS

DEFAULT_PATH = "data/national_walmart_official.csv"


def load(path: str = DEFAULT_PATH, *, exclude: bool = True) -> list[dict]:
    """Rows with a whole-milk price and complete demographics.

    `exclude=False` returns the raw panel, for before/after comparison.
    """
    out = []
    for r in csv.DictReader(open(path)):
        if not (r["whole_milk"] and r["state"] and r["county"] and r["zip"]
                and r["pct_black"] and r["median_income"] and r["population"]):
            continue
        if float(r["median_income"]) <= 0 or float(r["population"]) <= 0:
            continue
        if exclude and r["state"] in EXCLUDED:
            continue
        out.append({
            "st": r["state"], "cty": r["county"], "zip": r["zip"].zfill(5),
            "z3": r["zip"].zfill(5)[:3], "geo": r["geo"],
            "p": float(r["whole_milk"]),
            "blk": float(r["pct_black"]),
            "hisp": float(r["pct_hisp"]) if r["pct_hisp"] else 0.0,
            "inc": float(r["median_income"]),
            "pop": float(r["population"]),
            "cls": float(r["class_I_diff_cwt"]) if r["class_I_diff_cwt"] else None,
        })
    return out
