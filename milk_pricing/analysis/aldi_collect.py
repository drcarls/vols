"""Re-collect the Aldi panel, this time recording the shop.

    python3 analysis/aldi_collect.py [--zips N] [--workers N]

The August 2026 collection recorded a `zone` for each ZIP and treated it as the pricing
unit. It is not -- see reports/aldi_comparison.md section 4. The pricing unit is the
SHOP, and two ZIPs sharing a zone can resolve to different shops and different prices.
This run records zip, zone, shop and the whole 26-item dairy basket, so the pricing unit
can be identified from the data rather than assumed.

Output: data/aldi_2026_09.jsonl, one JSON object per ZIP, appended as it goes. Re-running
skips ZIPs already present, so the job is resumable after an interruption.

Politeness: a small worker pool with a per-request delay. aldi.us serves this container
directly; there is no proxy or credential involved.
"""
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "src")
from milk_pricing.sources import aldi_storefront as A

OUT = "data/aldi_2026_09.jsonl"
DELAY = 0.45
_lock = threading.Lock()


def done_zips():
    if not os.path.exists(OUT):
        return set()
    out = set()
    for line in open(OUT):
        try:
            out.add(json.loads(line)["zip"])
        except Exception:
            pass
    return out


def one(z):
    for attempt in (1, 2):
        try:
            time.sleep(DELAY)
            r = A.parse(A.fetch(z), z)
            w = A.whole_milk_gallon(r["items"])
            return {"zip": z, "zone": r["zone"], "shop": r["shop"],
                    "zones": r["zones"], "shops": r["shops"],
                    "whole": w[1] if w else None, "whole_name": w[0] if w else None,
                    "items": {f"{n}|{s}": p for (n, s), p in r["items"].items()},
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        except A.ZipNotHonoured as e:
            return {"zip": z, "error": f"zip_not_honoured: {e}"}
        except Exception as e:
            if attempt == 2:
                return {"zip": z, "error": str(e)[:120]}
            time.sleep(2.0)


def main():
    args = sys.argv[1:]
    limit = int(args[args.index("--zips") + 1]) if "--zips" in args else None
    workers = int(args[args.index("--workers") + 1]) if "--workers" in args else 4

    todo = [z.zfill(5) for z in json.load(open("data/aldi_pooled.json"))]
    have = done_zips()
    todo = [z for z in todo if z not in have]
    if limit:
        todo = todo[:limit]
    print(f"{len(have)} already collected, {len(todo)} to go, {workers} workers", flush=True)

    n = ok = 0
    t0 = time.time()
    with open(OUT, "a") as fh, ThreadPoolExecutor(max_workers=workers) as ex:
        for rec in ex.map(one, todo):
            with _lock:
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
            n += 1
            ok += 1 if rec.get("whole") is not None else 0
            if n % 100 == 0:
                el = time.time() - t0
                print(f"  {n}/{len(todo)}  priced {ok}  {el/n:.2f}s/zip  "
                      f"eta {(len(todo)-n)*el/n/60:.0f}m", flush=True)
    print(f"done: {n} fetched, {ok} with a whole-milk gallon price, "
          f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
