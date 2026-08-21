"""Normalise both retailer catalogues into one comparable table.

The two sites describe products differently -- Slumberland carries real brand
names and a usable product_type, Steinhafels carries four-letter vendor codes
and a warehouse status -- so both get mapped onto a shared vocabulary of
brand / form / motion / material before anything is compared.
"""

import csv
import json
import re
import argparse
from pathlib import Path

# Steinhafels vendor codes, resolved by reading its own brand collections.
STEINHAFELS_BRANDS = {
    "LAZB": "La-Z-Boy",
    "FLEX": "Flexsteel",
    "FLXD": "Flexsteel",
    "HGTV": "Bassett",          # HGTV Home Design Studio is Bassett's licensed line
    "BSCH": "Best Home Furnishings",
    "NATU": "Natuzzi",
    "SOMO": "Southern Motion",
    "JACK": "Jackson/Catnapper",
    "ASHY": "Ashley",
}

# Slumberland publishes brand names directly; only aliasing is needed.
SLUMBERLAND_BRANDS = {
    "La-Z-Boy": "La-Z-Boy",
    "Flexsteel": "Flexsteel",
    "Ashley Furniture": "Ashley",
    "Southern Motion": "Southern Motion",
    "Best Home Furnishings": "Best Home Furnishings",
    "Bassett": "Bassett",
    "Natuzzi": "Natuzzi",
    "Catnapper": "Jackson/Catnapper",
    "Jackson Furniture": "Jackson/Catnapper",
    "Palliser": "Palliser",
    "Stressless": "Stressless",
    "Ekornes": "Stressless",
}

# Order matters: the first form that matches wins, so "reclining sectional"
# is classified as a sectional rather than a recliner.
FORM_RULES = [
    ("Sectional", r"sectional"),
    ("Sleeper",   r"sleeper|sofa bed|hide-?a-?bed"),
    ("Loveseat",  r"loveseat|love seat"),
    ("Sofa",      r"\bsofa\b|davenport"),
    ("Recliner",  r"recliner|rocker recliner|lift chair"),
    ("Chair",     r"\bchair\b|glider|swivel|accent"),
    ("Ottoman",   r"ottoman|footstool"),
]

# Steinhafels handles carry a department path ("living-room-sofas-sectionals-")
# whose own name contains category words. Left in place it makes every living
# room seat look like a sectional, so it is stripped before any matching.
DEPARTMENT_RE = re.compile(
    r"living-room-sofas-sectionals|living-room-chairs-ottomans|"
    r"living-room-accents|sofas-sectionals|chairs-ottomans", re.I)

# Steinhafels' own collection taxonomy, which is authoritative where present.
CATEGORY_FORM = {
    "recliners": "Recliner",
    "reclining-sectionals": "Sectional",
    "sectionals": "Sectional",
    "sofas": "Sofa",
    "loveseats": "Loveseat",
    "accent-chairs": "Chair",
    # "reclining-sofas-loveseats" is ambiguous and resolved from the title.
}

MOTION_RE = re.compile(r"reclin|power|motion|glide|lift chair|zecliner", re.I)
POWER_RE = re.compile(r"\bpower\b|\bp[23]\b|powerrecline", re.I)
LEATHER_RE = re.compile(r"leather", re.I)
FABRIC_RE = re.compile(
    r"fabric|chenille|linen|velvet|boucle|bouclé|microfiber|polyester|tweed|weave", re.I)
TAG_RE = re.compile(r"<[^>]+>")


def classify_form(text):
    for name, pattern in FORM_RULES:
        if re.search(pattern, text, re.I):
            return name
    return "Other"


def resolve_form(title, category, handle, product_type):
    """Form, most trustworthy signal first.

    The retailer's own category beats the title, and the title beats the URL
    handle -- the handle is only a fallback because its department prefix
    describes a whole floor of the store, not this product.
    """
    if category:
        if category == "reclining-sofas-loveseats":
            return "Loveseat" if re.search(r"loveseat", title or "", re.I) else "Sofa"
        if category in CATEGORY_FORM:
            return CATEGORY_FORM[category]

    by_title = classify_form(title or "")
    if by_title != "Other":
        return by_title

    tail = DEPARTMENT_RE.sub(" ", handle or "").replace("-", " ")
    return classify_form(" ".join([tail, product_type or ""]))


def classify_material(text):
    # Leather wins ties: "leather match" upholstery is still sold as leather.
    if LEATHER_RE.search(text):
        return "Leather"
    if FABRIC_RE.search(text):
        return "Fabric"
    return "Unspecified"


def price_of(product):
    """Lowest available variant price, with its list price for discount depth."""
    best = None
    for v in product.get("variants", []):
        try:
            p = float(v.get("price") or 0)
        except (TypeError, ValueError):
            continue
        if p <= 0:
            continue
        try:
            cmp_at = float(v.get("compare_at_price") or 0) or None
        except (TypeError, ValueError):
            cmp_at = None
        if best is None or p < best[0]:
            best = (p, cmp_at, v.get("sku"))
    return best


def rows_for(retailer, products, categories=None):
    out = []
    for p in products:
        vendor = (p.get("vendor") or "").strip()
        if retailer == "steinhafels":
            brand = STEINHAFELS_BRANDS.get(vendor)
        else:
            brand = SLUMBERLAND_BRANDS.get(vendor)
        if not brand:
            continue

        priced = price_of(p)
        if not priced:
            continue
        price, list_price, sku = priced

        title = p.get("title", "")
        handle = p.get("handle", "")
        # Steinhafels titles are terse, so the handle's category path and the
        # collection it sits in both feed the classifier.
        category = (categories or {}).get(str(p.get("id")), "")
        motion_text = " ".join(filter(None, [
            title, category, DEPARTMENT_RE.sub(" ", handle).replace("-", " ")]))
        context = " ".join(filter(None, [title, category, motion_text]))
        # Form and motion read cleanly off the title; material usually does not,
        # since upholstery is named in the description or the colourway.
        material_text = " ".join(filter(None, [
            context,
            TAG_RE.sub(" ", p.get("body_html") or ""),
            " ".join((v.get("title") or "") for v in p.get("variants", [])),
        ]))

        out.append({
            "retailer": retailer,
            "brand": brand,
            "vendor_raw": vendor,
            "title": title,
            "sku": sku or "",
            "form": resolve_form(title, (categories or {}).get(str(p.get("id"))),
                                 handle, p.get("product_type")),
            "motion": "Motion" if MOTION_RE.search(motion_text) else "Stationary",
            "power": "Power" if POWER_RE.search(context) else "",
            "material": classify_material(material_text),
            "price": round(price, 2),
            "list_price": round(list_price, 2) if list_price else "",
            "discount_pct": (round((1 - price / list_price) * 100, 1)
                             if list_price and list_price > price else ""),
            "url": f"https://www.{retailer}.com/products/{handle}",
        })
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="data/catalog.csv")
    args = ap.parse_args()
    d = Path(args.data)

    cats = json.loads((d / "steinhafels_categories.json").read_text())
    rows = []
    rows += rows_for("slumberland", json.loads((d / "slumberland_products.json").read_text()))
    rows += rows_for("steinhafels", json.loads((d / "steinhafels_products.json").read_text()), cats)

    fields = list(rows[0].keys())
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {args.out}")
