"""Sample Walmart shelf prices across random proxy exits.

Exits cannot be pinned to a state: the Web Unlocker `/request` API accepts
only `country`, and this zone holds country-level permission. Passing city,
state or zip returns an empty body, and Walmart's own URL store parameters
(athStoreId, storeId, selectedStoreId) are ignored — the store follows the
exit IP.

So rather than target a state, sample the national pool and keep the hits.
Roughly 2-3% of exits land in South Carolina, and about half of all fetches
are discarded as marketplace substitutions, so expect ~1 usable SC store per
70 fetches. Inefficient, but it needs no account change.
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import os
from pathlib import Path

from .sources.walmart_page import fetch_page, read_shelf_price, Rejected

BENCHMARK_SKU = "10450114"
BENCHMARK_URL = (
    "https://www.walmart.com/ip/"
    f"Great-Value-Whole-Vitamin-D-Milk-Gallon-128-fl-oz/{BENCHMARK_SKU}"
)


def harvest(n: int = 120, sku: str = BENCHMARK_SKU, url: str = BENCHMARK_URL,
            workers: int = 16, out: str = "data/national_store_prices.json",
            token: str | None = None) -> dict:
    """Fetch `n` times, keep verified shelf prices, merge with prior runs."""
    tok = token or os.environ.get("BRIGHTDATA_API_TOKEN", "")
    if not tok:
        raise RuntimeError("BRIGHTDATA_API_TOKEN is not set")

    def one(_):
        try:
            return read_shelf_price(fetch_page(url, tok), sku)
        except Rejected as e:
            return {"rejected": str(e)}
        except Exception as e:                      # network, timeout
            return {"error": str(e)[:60]}

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(one, range(n)))

    ok = [r for r in res if "price" in r]
    rejected = sum(1 for r in res if "rejected" in r)

    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    prior = json.loads(p.read_text()) if p.exists() else []
    # Keyed by store so repeat draws of the same store collapse.
    stores = {r["store_id"]: r for r in prior + ok}
    p.write_text(json.dumps(list(stores.values()), indent=2))

    return {"fetched": n, "valid": len(ok), "rejected": rejected,
            "distinct_stores": len(stores)}
