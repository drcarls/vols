"""Expand the retailer catalogues to SKU level.

build_dataset.py keeps one row per product, which is the right grain for
comparing model prices. Merchandising questions need the finer grain: a
retailer stocks individual SKUs at individual price points, and it is the SKU
that sits on a shelf next to a competitor's.
"""

import csv
import json
import argparse
from pathlib import Path

from build_dataset import (
    TAG_RE, DEPARTMENT_RE, FOCUS_SET,
    resolve_brand, resolve_form, classify_material, MOTION_RE, POWER_RE,
)


def rows_for(retailer, products, categories=None):
    out = []
    for p in products:
        vendor = (p.get("vendor") or "").strip()
        brand = resolve_brand(retailer, vendor)
        if not brand:
            continue

        handle = p.get("handle", "")
        title = p.get("title", "")
        category = (categories or {}).get(str(p.get("id")), "")
        body = TAG_RE.sub(" ", p.get("body_html") or "")
        motion_text = " ".join(filter(None, [
            title, category, DEPARTMENT_RE.sub(" ", handle).replace("-", " ")]))
        context = " ".join(filter(None, [title, category, motion_text]))
        form = resolve_form(title, category, handle, p.get("product_type"))
        motion = "Motion" if MOTION_RE.search(motion_text) else "Stationary"

        for v in p.get("variants", []):
            try:
                price = float(v.get("price") or 0)
            except (TypeError, ValueError):
                continue
            if price <= 0:
                continue
            try:
                list_price = float(v.get("compare_at_price") or 0) or None
            except (TypeError, ValueError):
                list_price = None

            # Material varies by SKU: the variant name is the colourway.
            out.append({
                "retailer": retailer,
                "brand": brand,
                "focus_set": "Y" if brand in FOCUS_SET else "",
                "sku": v.get("sku") or "",
                "product_id": p.get("id"),
                "product": title,
                "variant": v.get("title") or "",
                "form": form,
                "motion": motion,
                "power": "Power" if POWER_RE.search(context) else "",
                "material": classify_material(
                    " ".join([context, body, v.get("title") or ""])),
                "price": round(price, 2),
                "list_price": round(list_price, 2) if list_price else "",
                "discount_pct": (round((1 - price / list_price) * 100, 1)
                                 if list_price and list_price > price else ""),
                "available": "Y" if v.get("available") else "N",
            })
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="data/skus.csv")
    args = ap.parse_args()
    d = Path(args.data)

    cats = json.loads((d / "steinhafels_categories.json").read_text())
    rows = []
    rows += rows_for("slumberland",
                     json.loads((d / "slumberland_products.json").read_text()))
    rows += rows_for("steinhafels",
                     json.loads((d / "steinhafels_products.json").read_text()), cats)

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} SKU rows -> {args.out}")
