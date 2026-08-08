#!/usr/bin/env python3
"""Iran / Strait of Hormuz live watch.

Keeps the live case in `docs/modern_iran_2026_prediction_markets.md` current between now and
press. Pulls the latest oil tape (FRED WTI) and — best effort — the Hormuz prediction-market
odds (Polymarket/Kalshi), classifies the state, and flags a RESOLUTION when the state changes
(an actual closure, or a durable de-escalation) — the only events the framework says are
informative. Appends a dated line to `war_premia/data/iran_watch_log.csv`.

Discipline: this reports the *state of the price*, not a forecast. A threshold crossing is a
resolution to investigate and write up, not a prediction. Oil thresholds are deliberately blunt
and documented below; adjust with a comment, never silently.

Run:  python3 war_premia/iran_watch.py
Reproducible; pure-stdlib (urllib), no external deps. Respects HTTPS_PROXY.
"""
import csv, io, os, sys, subprocess, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "data", "iran_watch_log.csv")

# Blunt, documented oil-state thresholds (WTI $/bbl). The point is to detect a *change of state*,
# not to price anything. Spring-2026 closure ran oil to ~$100-114; the $57 Jan base was "calm".
ESCALATED = 95.0   # >= this => consistent with an actual Hormuz disruption
CALM      = 72.0   # <  this => consistent with a durable de-escalation
# between the two is ELEVATED / oscillating (a fragile ceasefire) — the Aug-2026 state.

def fetch(url, timeout=20):
    # Prefer curl: the remote environment routes HTTPS through a pre-configured proxy + CA bundle
    # that curl already honours; urllib does not pick those up. Fall back to urllib locally.
    try:
        out = subprocess.run(
            ["curl", "-sS", "--http1.1", "--retry", "3", "--retry-all-errors",
             "--max-time", str(timeout), "-A", "Mozilla/5.0 (iran-watch)", url],
            capture_output=True, timeout=timeout * 4 + 10)
        if out.returncode == 0 and out.stdout:
            return out.stdout.decode("utf-8", "replace")
    except Exception:
        pass
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (iran-watch)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def fred_series(series_id, days=45):
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    url = ("https://fred.stlouisfed.org/graph/fredgraph.csv"
           f"?id={series_id}&cosd={start.isoformat()}&coed={end.isoformat()}")
    out = []
    for row in csv.reader(io.StringIO(fetch(url))):
        if not row or row[0] == "observation_date" or len(row) < 2 or row[1] in (".", ""):
            continue
        try:
            out.append((row[0], float(row[1])))
        except ValueError:
            pass
    return out

def classify(px):
    if px >= ESCALATED:
        return "ESCALATED"      # oil consistent with an actual Hormuz disruption
    if px < CALM:
        return "CALM"           # oil consistent with durable de-escalation
    return "ELEVATED"           # oscillating / fragile ceasefire

def last_state():
    if not os.path.exists(LOG):
        return None
    rows = list(csv.DictReader(open(LOG)))
    return rows[-1]["state"] if rows else None

def append_log(date, wti, chg, state, flag):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "wti", "chg_45d_pct", "state", "resolution_flag"])
        w.writerow([date, f"{wti:.2f}", f"{chg:+.1f}", state, flag])

def main():
    try:
        wti = fred_series("DCOILWTICO")
    except Exception as e:
        wti = None
        print(f"iran-watch: FRED fetch failed: {e}", file=sys.stderr)
    if not wti:
        # Leave a dated trace so a missed week is visible, then exit cleanly for the cron.
        today = datetime.date.today().isoformat()
        append_log(today, float("nan"), float("nan"), "FETCH_FAILED", "")
        print("iran-watch: no WTI observations (network); logged FETCH_FAILED, will retry next run.",
              file=sys.stderr)
        return 2
    date, px = wti[-1]
    base = wti[0][1]
    chg = (px / base - 1.0) * 100.0
    state = classify(px)
    prev = last_state()
    resolution = (prev is not None and prev != state)
    flag = f"RESOLUTION:{prev}->{state}" if resolution else ""
    append_log(date, px, chg, state, flag)

    print(f"iran-watch {date}: WTI ${px:.2f} ({chg:+.1f}% over ~45d) -> state={state}")
    if resolution:
        print(f"  ** RESOLUTION: state changed {prev} -> {state}. "
              f"Investigate (actual closure? durable ceasefire?), update "
              f"docs/modern_iran_2026_prediction_markets.md, and commit.")
    elif prev is None:
        print("  (first run — baseline recorded; no prior state to compare)")
    else:
        print(f"  no state change (still {state}); re-arm silently.")
    print("  Prediction-market odds are not auto-fetched (thin/manipulable, no stable public "
          "time-series endpoint) — check Polymarket/Kalshi Hormuz markets manually when writing up.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
