"""Count what each manufacturer lists on its own site.

The dealer feeds say what a shop chose to stock. This says what the maker
offers, which is the denominator that makes the dealer number mean something.

Coverage is uneven by design of the sites, not by choice: Flexsteel runs
Shopify and exposes a full product feed; Southern Motion and Franklin run
WordPress and expose product sitemaps; Ashley returns 403 to every request,
including robots.txt and its sitemaps, so it is absent rather than estimated.
Best Home Furnishings and Catnapper publish no machine-readable index.
"""

import re
import json
import time
import gzip
import argparse
import urllib.request
from pathlib import Path
from collections import Counter

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept": "text/xml,text/html,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip"}

SHOPIFY = {"Flexsteel": "https://www.flexsteel.com"}
SITEMAPS = {
    "Southern Motion": "https://www.southernmotion.com/product-sitemap.xml",
    "Franklin": "https://franklincorp.com/wp-sitemap-posts-product-1.xml",
}
# Ashley hard-blocks this environment (403 on every request, sitemaps and
# robots.txt included), so its catalogue comes from a file supplied by the
# user, collected through a residential-proxy scraper. Its own material labels
# are carried through rather than re-inferred from text.
LOCAL_FILES = {
    "Ashley": [("data/ashley_own_recliners.csv", "user-supplied scrape"),
               ("data/ashley_own_motion_sofas_catalog.csv", "constructor.io browse")],
}

BLOCKED = {
    "Best Home Furnishings": "no machine-readable product index",
    "Catnapper": "no machine-readable product index",
    "Bassett": "Salesforce Commerce, no open product feed",
}

LOC_RE = re.compile(r"<loc>([^<]+)</loc>")

# An "Ashley recliner" listing is a department, not a category: it carries
# third-party nursery gliders, massage chairs and battery packs alongside the
# furniture. Counting those against a dealer's recliner wall would overstate
# the maker's line by a third.
NOT_FURNITURE = re.compile(r"massage chair|osaki|titan .*vibe|amamedic|power pack", re.I)
NOT_CATEGORY = {"Nursery Gliders", "Chaise Lounge"}

# Whether a source discloses motion-vs-stationary for upholstered seating.
# Flexsteel names the action in its product titles. Southern Motion builds
# nothing else -- two product pages were checked and both sofas are power
# reclining, despite slugs that say only "sofa". Franklin makes both and its
# slugs do not say which, so its seating is reported as one figure rather than
# split on a guess.
MOTION_POLICY = {
    "Flexsteel": "from-title",
    "Southern Motion": "all-motion",
    "Franklin": "undisclosed",
}


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="ignore")
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def categorise(text, policy="from-title"):
    """The same two categories, read from a product name or slug."""
    if re.search(r"sectional|sofa|loveseat|console", text, re.I):
        if policy == "all-motion":
            return "Motion sofas"
        if policy == "undisclosed":
            return "Sofas (action undisclosed)"
        if re.search(r"reclin|power|motion|zecliner|duo", text, re.I):
            return "Motion sofas"
        return "Stationary sofas"
    if re.search(r"recliner|reclining chair|lift.chair|lift.recliner", text, re.I):
        return "Recliners"
    return "Other"


def from_shopify(base, policy):
    products, page = [], 1
    while True:
        raw = fetch(f"{base}/products.json?limit=250&page={page}")
        batch = json.loads(raw).get("products", []) if raw else []
        if not batch:
            break
        products.extend(batch)
        page += 1
        time.sleep(1)
    counts, skus = Counter(), Counter()
    for p in products:
        c = categorise(p.get("title", ""), policy)
        counts[c] += 1
        skus[c] += len(p.get("variants", []))
    return counts, skus, len(products)


def from_sitemap(url, policy):
    xml = fetch(url)
    if not xml:
        return Counter(), Counter(), 0
    locs = LOC_RE.findall(xml)
    counts = Counter(categorise(u.rstrip("/").rsplit("/", 1)[-1], policy) for u in locs)
    # A sitemap lists pages, so models only -- colourway SKUs are not exposed.
    return counts, Counter(), len(locs)


def from_local_csv(path):
    """A supplied catalogue export, filtered to the same footing as the rest."""
    import csv as _csv
    models, skus, dropped = Counter(), Counter(), 0
    materials = Counter()
    for r in _csv.DictReader(open(path)):
        if not r.get("product_id"):
            continue
        if NOT_FURNITURE.search(r.get("name", "")) or r.get("subcategory") in NOT_CATEGORY:
            dropped += 1
            continue
        cat = (r["subcategory"] if r.get("subcategory") in ("Motion sofas", "Recliners")
               else categorise(r.get("name", "") + " " + r.get("subcategory", "")))
        if cat == "Other":
            cat = "Recliners"
        models[cat] += 1
        skus[cat] += 1
        materials[r.get("material", "unknown")] += 1
    return models, skus, sum(models.values()), dropped, materials


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/manufacturers.json")
    args = ap.parse_args()

    out = {}
    for brand, base in SHOPIFY.items():
        counts, skus, total = from_shopify(base, MOTION_POLICY.get(brand, "from-title"))
        out[brand] = {"source": "shopify product feed", "total": total,
                      "motion_split": MOTION_POLICY.get(brand, "from-title"),
                      "models": dict(counts), "skus": dict(skus)}
        print(f"  {brand:<22} {total:>5} products  {dict(counts)}", flush=True)
        time.sleep(1)
    for brand, url in SITEMAPS.items():
        counts, skus, total = from_sitemap(url, MOTION_POLICY.get(brand, "from-title"))
        out[brand] = {"source": "product sitemap", "total": total,
                      "motion_split": MOTION_POLICY.get(brand, "from-title"),
                      "models": dict(counts), "skus": {}}
        print(f"  {brand:<22} {total:>5} products  {dict(counts)}", flush=True)
        time.sleep(1)
    for brand, files in LOCAL_FILES.items():
        counts, skus, mats = Counter(), Counter(), Counter()
        dropped, notes = 0, []
        for path, note in files:
            c, sk, _, dr, mt = from_local_csv(path)
            counts += c; skus += sk; mats += mt; dropped += dr
            notes.append(note)
        out[brand] = {"source": " + ".join(sorted(set(notes))),
                      "total": sum(counts.values()), "motion_split": "n/a",
                      "models": dict(counts), "skus": dict(skus),
                      "materials": dict(mats), "excluded_non_furniture": dropped}
        print(f"  {brand:<22} {sum(counts.values()):>5} products  {dict(counts)}"
              f"   (excluded {dropped} non-furniture)", flush=True)

    for brand, why in BLOCKED.items():
        out[brand] = {"source": "unavailable", "reason": why}
        print(f"  {brand:<22}    -- unavailable: {why}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(f"\nwrote {args.out}")
