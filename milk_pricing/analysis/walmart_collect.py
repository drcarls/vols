"""Per-store Walmart milk collection via a Bright Data Scraping Browser zone.

    python3 analysis/walmart_collect.py --zone <browser_zone_name> [--stores N]

STATUS: WRITTEN BUT NEVER RUN. The account this project uses holds one zone
(`unblocker`, no JavaScript execution), so this code has not executed end to end even
once. Treat every claim below as a design intention, not a verified result, until the
preflight and the three-store verification in `--verify` both pass.

WHY A BROWSER ZONE IS REQUIRED, established by testing (reports/brightdata_zipcode_trap.md
section 9, re-confirmed 2026-09-16):

  * `/ip/{sku}` is server-rendered and carries a REAL shelf price, but the store is
    decided by the proxy exit IP. `?athStoreId=`, `?storeId=` and a Cookie header are
    all ignored. Three consecutive calls resolved to St. Petersburg, Sacramento and
    Idaho Falls.
  * `/store/{id}` DOES honour the store id server-side -- requests for 634, 5378 and
    4440 returned Camden, Cayce and Irmo -- but no sub-path of it can be queried. Every
    search and browse variant returns the same store landing page, because those grids
    are client-rendered and a raw fetch returns the pre-JavaScript document.
  * There is no store-scoped product URL. The store page contains no `/store/{id}/ip/`
    links and no `athStoreId` parameters; its only `/ip/` reference is the Next.js route
    template `/ip/[...itemParams]`.
  * Direct access from outside a proxy is blocked by PerimeterX: `/ip/{sku}` returns
    307 to `/blocked` with a `_pxhd` cookie.

So the two halves -- store control and a real shelf price -- exist on different routes
and cannot be joined by fetching. A browser can join them: load `/store/{id}` to put the
store into session state, then navigate to `/ip/{sku}` in the SAME context and read the
server-rendered price. That is the one combination never tested, and it is untestable
without a JS-executing zone.

TO PROVISION: in the Bright Data dashboard create a zone of type "Scraping Browser".
This is a billable change and costs materially more than Unblocker; it is the user's
decision, not this script's. Then pass its name with --zone.

CREDENTIALS: never hard-code them. The script reads BRIGHTDATA_API_TOKEN from the
environment and asks the API for the customer id and zone password at run time.
"""
import argparse
import json
import os
import subprocess
import sys
import time

API = "https://api.brightdata.com"
OUT = "data/walmart_2026_09.jsonl"
# Known SC stores with a shelf price already on file, for --verify.
VERIFY = [("634", 3.82, "Camden"), ("5378", 2.72, "Cayce"), ("4440", 2.70, "Irmo")]
SKU = "10450114"          # Great Value whole milk, 1 gal


def api(path):
    tok = os.environ.get("BRIGHTDATA_API_TOKEN")
    if not tok:
        sys.exit("BRIGHTDATA_API_TOKEN is not set (environment only, never a flag).")
    out = subprocess.run(["curl", "-sS", "--http1.1", "-m", "40",
                          "-H", f"Authorization: Bearer {tok}", f"{API}/{path}"],
                         capture_output=True, text=True, timeout=60).stdout
    try:
        return json.loads(out)
    except Exception:
        sys.exit(f"unexpected response from /{path}: {out[:120]}")


def preflight(zone):
    """Confirm a browser-capable zone exists before doing anything else."""
    zones = api("zone/get_active_zones")
    names = {z.get("name"): z.get("type") for z in zones}
    print(f"zones on the account: {names}")
    if zone not in names:
        sys.exit(f"\nzone {zone!r} does not exist. Create a 'Scraping Browser' zone in the\n"
                 f"Bright Data dashboard and re-run with --zone <its name>. This is a\n"
                 f"billable change and is deliberately not automated here.")
    if "browser" not in str(names[zone]).lower():
        print(f"WARNING: zone {zone!r} has type {names[zone]!r}, which does not look like a\n"
              f"Scraping Browser zone. If it cannot execute JavaScript this will fail at the\n"
              f"first store-pin step, which is the correct behaviour -- see the guard below.")
    cust = api("status").get("customer")
    pw = (api(f"zone/passwords?zone={zone}").get("passwords") or [None])[0]
    if not (cust and pw):
        sys.exit("could not resolve customer id or zone password from the API")
    return f"wss://brd-customer-{cust}-zone-{zone}:{pw}@brd.superproxy.io:9222"


JS_READ = """() => {
  const el = document.getElementById('__NEXT_DATA__');
  if (!el) return {err: 'no __NEXT_DATA__'};
  let j; try { j = JSON.parse(el.textContent); } catch (e) { return {err: 'bad json'}; }
  const p = j?.props?.pageProps?.initialData?.data?.product;
  return {price: p?.priceInfo?.currentPrice?.price ?? null,
          name: p?.name ?? null,
          store: p?.location?.storeId ?? null,
          postal: p?.location?.postalCode ?? null};
}"""


def node_driver(wss, jobs):
    """Drive the remote browser. One context per store so session state cannot leak."""
    script = """
const {chromium} = require('playwright');
(async () => {
  const wss = process.argv[2], jobs = JSON.parse(process.argv[3]), sku = process.argv[4];
  const b = await chromium.connectOverCDP(wss);
  for (const [store] of jobs) {
    const ctx = await b.newContext();
    const pg = await ctx.newPage();
    const rec = {store};
    try {
      await pg.goto('https://www.walmart.com/store/' + store, {waitUntil:'domcontentloaded', timeout:90000});
      await pg.waitForTimeout(1500);
      await pg.goto('https://www.walmart.com/ip/' + sku, {waitUntil:'domcontentloaded', timeout:90000});
      Object.assign(rec, await pg.evaluate(%s));
    } catch (e) { rec.err = String(e).split('\\n')[0].slice(0,120); }
    console.log(JSON.stringify(rec));
    await ctx.close();
  }
  await b.close();
})().catch(e => { console.error(String(e).slice(0,200)); process.exit(1); });
""" % JS_READ
    d = "/tmp/claude-0/wm_driver"
    os.makedirs(d, exist_ok=True)
    open(f"{d}/drive.cjs", "w").write(script)
    r = subprocess.run(["node", f"{d}/drive.cjs", wss, json.dumps(jobs), SKU],
                       capture_output=True, text=True, timeout=120 * max(len(jobs), 1),
                       cwd="/tmp/claude-0/-home-user-vols/fcb83355-2553-53ed-838c-913830ac829f/scratchpad")
    if r.returncode != 0:
        print("driver failed:", r.stderr[:200])
    return [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", required=True)
    ap.add_argument("--verify", action="store_true",
                    help="three known SC stores only; run this before any volume")
    ap.add_argument("--stores", type=int, default=0)
    a = ap.parse_args()

    wss = preflight(a.zone)
    print("preflight passed; browser endpoint resolved\n")

    if a.verify or not a.stores:
        print("VERIFICATION against known shelf prices -- nothing is collected at volume")
        print("until every row here pins the right store and matches its reference price.\n")
        recs = node_driver(wss, [[s] for s, _, _ in VERIFY])
        print(f"  {'asked':<8}{'resolved':<10}{'price':>8}{'known':>8}{'verdict':>12}")
        okall = True
        for (s, known, city), rec in zip(VERIFY, recs + [{}] * len(VERIFY)):
            got, pr = str(rec.get("store")), rec.get("price")
            pin = got == s
            match = pr is not None and abs(pr - known) < 0.005
            okall &= pin and match
            print(f"  {s:<8}{got:<10}{(pr if pr is not None else '-'):>8}{known:>8}"
                  f"{('OK' if pin and match else 'STORE MISMATCH' if not pin else 'PRICE DIFFERS'):>12}"
                  f"   {rec.get('err','')}")
        print("\n" + ("verification passed -- volume collection is safe to run"
                      if okall else
                      "VERIFICATION FAILED -- do not collect at volume. A wrong store looks\n"
                      "exactly like clean data, which is how the earlier Bright Data trap\n"
                      "produced a file that read as 'no store-level variation'."))
        return

    sys.exit("volume collection is intentionally gated behind a passing --verify run.")


if __name__ == "__main__":
    main()
