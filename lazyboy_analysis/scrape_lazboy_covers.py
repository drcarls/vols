"""Scrape La-Z-Boy.com's per-cover price ladder.

La-Z-Boy product pages carry a data-cover-* attribute block for each upholstery
option, each with its own price. That gives the price of one identical frame
across many covers -- the cleanest possible read on the leather premium, since
the frame is held constant and only the cover varies.

Category pages render 36 products before handing off to JS pagination, so this
samples the first 36 per category rather than claiming full coverage.
"""

import re
import csv
import json
import time
import gzip
import argparse
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://www.la-z-boy.com"

CATEGORIES = [
    "furniture/recliners",
    "furniture/sofas",
    "furniture/loveseats",
    "furniture/sectionals",
    "furniture/chairs",
]

COVER_TAG_RE = re.compile(r"<[^>]*data-cover-price=\"[^\"]*\"[^>]*>")
ATTR_RE = re.compile(r"data-cover-([a-z-]+)=\"([^\"]*)\"")
LINK_RE = re.compile(r'href="(/p/[^"]*)"')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)

def fetch(url, retries=4):
    for attempt in range(retries):
        try:
            # La-Z-Boy serves a challenge page to thin clients, so send the
            # header set a real browser would.
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                          "image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Connection": "keep-alive",
            })
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


def product_urls(category):
    html = fetch(f"{BASE}/c/{category}/")
    if not html:
        return []
    seen = []
    for href in LINK_RE.findall(html):
        clean = href.split("?")[0]
        if clean not in seen:
            seen.append(clean)
    return seen


def covers_for(url):
    html = fetch(BASE + url)
    if not html:
        return []
    tm = TITLE_RE.search(html)
    title = re.sub(r"\s+", " ", tm.group(1)).split("|")[0].strip() if tm else ""

    rows = []
    for tag in COVER_TAG_RE.findall(html):
        a = dict(ATTR_RE.findall(tag))
        try:
            price = float(a.get("price", 0))
        except ValueError:
            continue
        if price <= 0:
            continue
        rows.append({
            "product_url": url,
            "product": title,
            "cover_id": a.get("id", ""),
            "cover_name": a.get("name", ""),
            "cover_pattern": a.get("pattern", ""),
            "price": price,
        })
    # One row per distinct cover.
    uniq = {r["cover_id"]: r for r in rows if r["cover_id"]}
    return list(uniq.values())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/lazboy_covers.csv")
    ap.add_argument("--delay", type=float, default=1.5)
    args = ap.parse_args()

    all_rows, seen = [], set()
    for cat in CATEGORIES:
        urls = product_urls(cat)
        print(f"== {cat}: {len(urls)} products ==", flush=True)
        time.sleep(args.delay)
        for i, u in enumerate(urls, 1):
            if u in seen:
                continue
            seen.add(u)
            rows = covers_for(u)
            for r in rows:
                r["category"] = cat.split("/")[-1]
            all_rows += rows
            if i % 12 == 0:
                print(f"   {i}/{len(urls)}  covers so far {len(all_rows)}", flush=True)
            time.sleep(args.delay)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "category", "product", "product_url", "cover_id",
            "cover_name", "cover_pattern", "price"])
        w.writeheader()
        w.writerows(all_rows)
    print(f"wrote {len(all_rows)} cover rows across {len(seen)} products -> {args.out}")
