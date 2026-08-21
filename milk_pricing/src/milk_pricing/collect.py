"""Orchestrate the SC milk pull across the retailer x ZIP matrix."""

from __future__ import annotations

import json
import time
from pathlib import Path

from .brightdata import WebUnlocker, BrightDataError
from .markets import RETAILERS, SC_MARKETS, BY_SLUG
from .normalize import normalize_all
from .parse import parse_search_html

SEARCH_URL = "https://www.instacart.com/store/{slug}/s?k={kw}"


def collect_one(unlocker: WebUnlocker, slug: str, zip_code: str,
                keyword: str = "milk") -> list[dict]:
    """Fetch and normalise one retailer x ZIP cell."""
    url = SEARCH_URL.format(slug=slug, kw=keyword)
    page = unlocker.fetch(url)
    raw = parse_search_html(page)
    return normalize_all(raw, slug, zip_code)


def collect_all(retailer_slugs: list[str] | None = None,
                zips: list[str] | None = None,
                keyword: str = "milk",
                out_dir: str = "data",
                raw_dir: str | None = "data/raw",
                sleep: float = 1.0,
                verbose: bool = True) -> dict:
    """Walk the matrix, writing observations plus a per-cell status log.

    Cells fail independently: one blocked retailer must never take down the
    run, so failures are recorded and the walk continues.
    """
    slugs = retailer_slugs or [r.slug for r in RETAILERS]
    zip_list = zips or [z for m in SC_MARKETS for z in m.zips]

    unlocker = WebUnlocker()
    observations: list[dict] = []
    status: list[dict] = []

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    if raw_dir:
        Path(raw_dir).mkdir(parents=True, exist_ok=True)

    total = len(slugs) * len(zip_list)
    n = 0
    for slug in slugs:
        for z in zip_list:
            n += 1
            label = f"[{n}/{total}] {slug} @ {z}"
            try:
                rows = collect_one(unlocker, slug, z, keyword)
                observations.extend(rows)
                status.append({"retailer": slug, "zip": z, "ok": True,
                               "rows": len(rows)})
                if verbose:
                    print(f"{label}: {len(rows)} rows")
                if raw_dir:
                    Path(f"{raw_dir}/{slug}_{z}.json").write_text(
                        json.dumps(rows, indent=2))
            except BrightDataError as e:
                status.append({"retailer": slug, "zip": z, "ok": False,
                               "error": str(e)[:200]})
                if verbose:
                    print(f"{label}: FAILED {str(e)[:120]}")
            time.sleep(sleep)

    Path(f"{out_dir}/observations.json").write_text(json.dumps(observations, indent=2))
    Path(f"{out_dir}/collection_status.json").write_text(json.dumps(status, indent=2))

    ok = sum(1 for s in status if s["ok"])
    if verbose:
        print(f"\n{ok}/{total} cells succeeded; "
              f"{len(observations)} observations -> {out_dir}/observations.json")
    return {"observations": observations, "status": status}
