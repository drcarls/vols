#!/usr/bin/env python
"""Generate a large synthetic domain CSV for load testing.

SYNTHETIC. These are combinatorial word pairings, not a real inventory feed.
They exist to verify that the pipeline handles 10,000 rows within a sensible
time and memory budget - nothing more. Never score these for a real decision.

Usage:
    python scripts/generate_test_csv.py 10000 data/load_test_SYNTHETIC.csv
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

HEADS = ["fleet", "cloud", "data", "smart", "rapid", "prime", "north", "apex",
         "blue", "iron", "swift", "core", "peak", "nova", "atlas", "vertex",
         "solar", "urban", "quantum", "cyber", "green", "silver", "bright",
         "global", "metro", "delta", "omega", "pioneer", "summit", "harbor"]
TAILS = ["analytics", "logistics", "roofing", "payroll", "security", "insurance",
         "dental", "plumbing", "capital", "robotics", "freight", "staffing",
         "legal", "medical", "energy", "software", "consulting", "trading",
         "storage", "brewing", "fitness", "realty", "lending", "telecom",
         "audit", "leasing", "hosting", "labs", "systems", "works"]
MODIFIERS = ["", "", "", "get", "my", "the", "pro", "online"]
TLDS = ["com"] * 12 + ["net", "org", "io", "co", "ai"]
SOURCES = ["auction", "closeout", "marketplace", "expired"]


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "data/load_test_SYNTHETIC.csv")
    rng = random.Random(20260826)   # fixed seed: the file is reproducible

    seen: set[str] = set()
    rows: list[dict[str, object]] = []
    while len(rows) < count:
        parts = [rng.choice(MODIFIERS), rng.choice(HEADS), rng.choice(TAILS)]
        sld = "".join(p for p in parts if p)
        if rng.random() < 0.06:
            sld += str(rng.randint(1, 99))
        if rng.random() < 0.04:
            sld = "-".join(p for p in parts if p)
        name = f"{sld}.{rng.choice(TLDS)}"
        if name in seen:
            continue
        seen.add(name)
        source = rng.choice(SOURCES)
        price = round(rng.lognormvariate(5.6, 1.1), 2)
        rows.append({
            "domain": name,
            "asking_price": price,
            "source": source,
            "auction_end_date": ("2026-09-%02d" % rng.randint(1, 28)
                                 if source == "auction" else ""),
            "current_bid": (round(price * rng.uniform(0.2, 0.9), 2)
                            if source == "auction" else ""),
            "bid_count": rng.randint(0, 30) if source == "auction" else "",
            "listing_type": source,
        })

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} SYNTHETIC rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
