"""Probe Bright Data's Walmart scrapers for usable store-pinned shelf prices.

Backs reports/brightdata_zipcode_trap.md. Requires BRIGHTDATA_API_TOKEN in the
environment (env var only — never a flag or a file).

    python3 analysis/bd_zipcode_probe.py --list       # Walmart scrapers on the account
    python3 analysis/bd_zipcode_probe.py --schema     # discover input fields via validation errors
    python3 analysis/bd_zipcode_probe.py --validate   # the decisive test (costs a live pull)
    python3 analysis/bd_zipcode_probe.py --matrix     # which scraper honours which field

Finding: `Walmart - products zipcodes` (gd_m693oc1r1gebnayxq) takes a `zip_code`
field and resolves a real local store, but returns Walmart's NATIONAL ONLINE
price ("Price when purchased online"), not the shelf price. Proof: it reports
$3.52 for Pennsylvania stores, below the Pennsylvania Milk Marketing Board's
legal minimum retail price.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.brightdata.com"
ZIPCODES_DS = "gd_m693oc1r1gebnayxq"
PRODUCTS_DS = "gd_l95fol7l1ru6rlo116"

# ZIPs whose Walmart shelf price is already known from data/*_walmart_official.csv
KNOWN_SHELF = {
    "29306": 2.32,  # Spartanburg SC
    "29607": 2.50,  # Greenville SC
    "29926": 3.86,  # Hilton Head SC
    "29566": 3.97,  # N Myrtle Beach SC
    "17055": 4.63,  # Camp Hill PA   -- PA has a regulated minimum retail price
    "16335": 4.94,  # Meadville PA
    "15227": 5.17,  # Brentwood PA
    "95829": 3.52,  # Sacramento CA
}
WHOLE_MILK = "10450114"


def token():
    t = os.environ.get("BRIGHTDATA_API_TOKEN")
    if not t:
        sys.exit("BRIGHTDATA_API_TOKEN is not set (env var only).")
    return t


def call(url, data=None, timeout=180):
    h = {"Authorization": f"Bearer {token()}"}
    if data is not None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                               headers=h, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.read().decode()


def list_scrapers():
    ds = json.loads(call(f"{API}/datasets/v3/scrapers"))
    wm = [d for d in ds if "walmart" in d.get("name", "").lower()]
    print(f"{len(ds)} scrapers on the account; {len(wm)} Walmart:")
    for d in wm:
        print(f"  {d['id']:<26} {d['name']!r}")


def schema():
    """The trigger endpoint's validation error names the required fields."""
    for label, ds, probe in (("zipcodes", ZIPCODES_DS, [{"_": "x"}]),
                             ("zipcodes wrong field", ZIPCODES_DS,
                              [{"url": f"https://www.walmart.com/ip/{WHOLE_MILK}", "zipcode": "29201"}]),
                             ("search", "gd_m7khey0wb7wviejgj",
                              [{"url": "https://www.walmart.com/search?q=milk", "zip_code": "29306"}])):
        b = call(f"{API}/datasets/v3/trigger?dataset_id={ds}&include_errors=true", probe)
        print(f"  {label:<22} {b[:240]}")


def run(ds, payload, poll=15, tries=32):
    snap = json.loads(call(f"{API}/datasets/v3/trigger?dataset_id={ds}&include_errors=true",
                           payload)).get("snapshot_id")
    if not snap:
        sys.exit("trigger failed")
    print(f"  snapshot {snap} ({len(payload)} inputs)")
    for _ in range(tries):
        st = json.loads(call(f"{API}/datasets/v3/progress/{snap}"))
        if st.get("status") in ("ready", "failed"):
            print(f"  {st.get('status')} records={st.get('records')} errors={st.get('errors')}")
            break
        time.sleep(poll)
    for _ in range(8):  # the snapshot builds after the run reports ready
        b = call(f"{API}/datasets/v3/snapshot/{snap}?format=json")
        if len(b) > 1500:
            return json.loads(b)
        time.sleep(20)
    sys.exit("snapshot never built")


def matrix():
    """Which scraper accepts and which HONOURS zip_code / store_id."""
    u = f"https://www.walmart.com/ip/{WHOLE_MILK}"
    print("Walmart - products (real prices) — does it take geography?")
    for probe in ({"url": u, "zip_code": "29607"}, {"url": u, "store_id": "640"}):
        b = call(f"{API}/datasets/v3/trigger?dataset_id={PRODUCTS_DS}&include_errors=true", [probe])
        verdict = "ACCEPTED" if "snapshot_id" in b else "rejected"
        print(f"  {json.dumps(probe)[:58]:<60} {verdict}")
    print("  NOTE: store_id is accepted by validation but IGNORED at run time —")
    print("  requesting store_id 640 (Greenville SC) returned store 3081, Sacramento.")
    print("\nWalmart products search — takes url only:")
    b = call(f"{API}/datasets/v3/trigger?dataset_id=gd_m7khey0wb7wviejgj&include_errors=true",
             [{"url": u, "zip_code": "29607"}])
    print(f"  {b[:170]}")


def validate():
    print("Does the zipcodes scraper return SHELF prices? Compare to known values.")
    d = run(ZIPCODES_DS, [{"url": f"https://www.walmart.com/ip/{WHOLE_MILK}", "zip_code": z}
                          for z in KNOWN_SHELF])
    print(f"\n  {'zip':<8}{'template':>10}{'known shelf':>13}{'match':>8}   store resolved")
    hits = 0
    for x in sorted(d, key=lambda r: str(r.get("zip_code"))):
        z, bd = str(x.get("zip_code")), x.get("final_price")
        kn = KNOWN_SHELF.get(z)
        ok = bool(kn and bd and abs(bd - kn) < 0.02)
        hits += ok
        print(f"  {z:<8}{('$%.2f' % bd) if bd else '—':>10}{('$%.2f' % kn):>13}"
              f"{'YES' if ok else 'no':>8}   {str(x.get('pickup_address'))[:38]}")
    print(f"\n  matches: {hits}/{len(KNOWN_SHELF)}")
    pa = [x for x in d if str(x.get("zip_code")) in ("15227", "16335", "17055")]
    if pa:
        print(f"  Pennsylvania returned: {sorted({x.get('final_price') for x in pa})}")
        print("  PA's Milk Marketing Board sets a MINIMUM retail price; observed PA shelf prices")
        print("  are $4.63-$5.48, so this cannot be a PA shelf price.")
        print(f"  promotion_fulltext: {pa[0].get('promotion_fulltext')!r}  <- the explanation")


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--list" in a:
        list_scrapers()
    elif "--schema" in a:
        schema()
    elif "--validate" in a:
        validate()
    elif "--matrix" in a:
        matrix()
    else:
        sys.exit(__doc__)
