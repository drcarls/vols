"""Was Berlin's spot-versus-to-arrive gap unusual in autumn 1911?

The check that decides Chapter III. The mirrored Neal-Weidenmier data carries a single
open-market rate per city, so it CANNOT see an intra-market spread; this has to come
off the Commercial & Financial Chronicle's weekly Berlin money paragraph, one figure
per autumn. Anchor: each year's early-October (Oct-1 quarter-end settlement) issue,
1908-1913; 1907 excluded (panic). Every figure carries its verbatim OCR quote in
data/berlin_spot_to_arrive_autumn.csv.

"Spot versus to-arrive" is the Chronicle's own wording: it quotes Berlin's open-market
rate for "spot bills" and, separately, for "bills to arrive". The gap is
    to_arrive - spot   (a positive gap = forward money dearer than spot).

Finding: Berlin drew a spot/to-arrive gap in exactly ONE of the six autumns -- 1911
(+0.5 pp). In 1910 and 1912 the Chronicle states spot and to-arrive were equal ("for
both", "all maturities"); in 1908, 1909, 1913 it gives a single undivided rate/range.
1910 is the control that matters: a FIRMER autumn in level (official 5%, private 4.5%)
with ZERO gap -- so the 1911 gap is not a by-product of a high rate. The gap was
unusual; the scene stands.

    python spot_to_arrive.py     # prints the table + verdict, writes the SVG
"""

from __future__ import annotations

import csv
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(_HERE, "data", "berlin_spot_to_arrive_autumn.csv")
CRISES_CSV = os.path.join(_HERE, "data", "spot_to_arrive_crises.csv")
WEEKLY_CSV = os.path.join(_HERE, "data", "spot_to_arrive_weekly.csv")
CHART = os.path.join(_HERE, "results", "berlin_spot_to_arrive.svg")
CHART_CRISES = os.path.join(_HERE, "results", "spot_to_arrive_crises.svg")
CHART_WEEKLY = os.path.join(_HERE, "results", "spot_to_arrive_weekly.svg")


def load():
    with open(CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["year"] = int(r["year"])
        r["gap"] = float(r["gap_pp"]) if r["gap_pp"] else 0.0
        r["spot"] = float(r["spot_pct"]) if r["spot_pct"] else None
        r["to_arrive"] = float(r["to_arrive_pct"]) if r["to_arrive_pct"] else None
    return rows


def load_weekly():
    with open(WEEKLY_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["year"] = int(r["year"])
        r["gap"] = float(r["gap_pp"]) if r["gap_pp"] else 0.0
    return rows


def weekly_max_gap_by_year(weekly):
    """Largest observed Berlin gap per autumn, from the multi-week panel."""
    out = {}
    for r in weekly:
        if r["centre"] != "Berlin":
            continue
        out[r["year"]] = max(out.get(r["year"], 0.0), r["gap"])
    return out


def verdict(weekly):
    """The WEEKLY verdict, which overturns the single-snapshot one.

    The single Oct-1 snapshots suggested 1911 was the only autumn with a gap. The
    multi-week panel shows that is false: 1910 -- a war-FREE firm autumn -- carries
    the SAME +0.5 gap in the weeks flanking its one 'for both' reading, and 1912
    shows a small one. So the gap is a quarter-end forward premium that appears
    whenever Berlin money is firm at the turn; it does NOT single out Agadir.
    Returns (is_unusual, max_gap_by_year).
    """
    mx = weekly_max_gap_by_year(weekly)
    # 'unusual' would require 1911 to stand materially above the firm controls; it does not
    firm_controls = max(mx.get(1910, 0.0), mx.get(1912, 0.0))
    is_unusual = mx.get(1911, 0.0) >= firm_controls + 0.4
    return is_unusual, mx


def format_report(rows, weekly):
    series = sorted(rows, key=lambda r: r["year"])
    is_unusual, mx = verdict(weekly)
    out = []
    out.append("SINGLE Oct-1 snapshot per autumn (the original design):")
    out.append("%-6s | %-8s | %-8s | %-6s | %s" % ("year", "spot", "to-arr", "gap", "what the Chronicle drew"))
    out.append("-" * 74)
    for r in series:
        spot = "%.3g%%" % r["spot"] if r["spot"] is not None else "  --"
        toa = "%.3g%%" % r["to_arrive"] if r["to_arrive"] is not None else "  --"
        tag = {"yes_gap": "SPOT/TO-ARRIVE GAP", "yes_equal": "equal (stated)",
               "no": "single undivided rate/range"}[r["explicit_split"]]
        out.append("%-6d | %-8s | %-8s | %+5.2f | %s" % (r["year"], spot, toa, r["gap"], tag))
    out.append("")
    out.append("WEEKLY panel (4-6 obs per autumn) -- max Berlin gap observed each autumn:")
    for yr in sorted(mx):
        note = {1910: "  <== war-FREE autumn, yet the SAME gap as 1911",
                1911: "  <== Agadir",
                1913: "  (Berlin quoted single private rate -> gap unobservable)"}.get(yr, "")
        out.append("   %d: +%.3f pp%s" % (yr, mx[yr], note))
    out.append("")
    out.append("VERDICT (weekly): %s" % (
        "1911 stands materially above the firm controls." if is_unusual
        else "NOT unusual -- the single-snapshot result does NOT survive."))
    out.append("  The weekly data OVERTURNS the snapshot: 1910 (no war scare) carries the same")
    out.append("  +0.5 gap in the weeks flanking its one 'for both' reading, and 1912 shows a")
    out.append("  smaller one. The gap is a QUARTER-END forward premium that appears whenever")
    out.append("  Berlin money is firm at the turn -- it does not single out Agadir. My earlier")
    out.append("  '1910 firmer yet flat' claim was a sampling artifact and is retracted.")
    out.append("  (1908/1909 easy money -> no gap; 1913 quoted single -> gap unobservable.)")
    return "\n".join(out)


def _svg_weekly(weekly, path):
    """Berlin's weekly gap trajectory, 1910 vs 1911 (both firm autumns)."""
    years = [1910, 1911]
    cols = {1910: "#2980b9", 1911: "#c0392b"}
    # x-axis: week-of-autumn index by issue date (Sep 1 = 0)
    import datetime
    def widx(wk):
        d = datetime.date(*map(int, wk.split("-")))
        return (d - datetime.date(d.year, 9, 1)).days
    W, H, L, R, T, B = 640, 400, 55, 120, 60, 60
    pw, ph = W - L - R, H - T - B
    xmax, ymax = 75, 0.65

    def X(i):
        return L + pw * i / xmax

    def Y(v):
        return T + ph * (ymax - v) / ymax

    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="Helvetica,Arial,sans-serif">' % (W, H, W, H)]
    s.append('<rect width="%d" height="%d" fill="#fff"/>' % (W, H))
    s.append('<text x="%d" y="24" font-size="15" font-weight="bold">The gap is seasonal, not '
             'Agadir-specific</text>' % L)
    s.append('<text x="%d" y="42" font-size="11" fill="#555">Berlin spot-vs-to-arrive gap, week by '
             'week. 1910 (no war) tracks 1911.</text>' % L)
    for gv in (0, 0.25, 0.5):
        s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s"/>' % (
            L, Y(gv), L + pw, Y(gv), "#888" if gv == 0 else "#ececec"))
        s.append('<text x="%d" y="%.1f" font-size="10" fill="#555" text-anchor="end">+%.2f</text>' % (
            L - 6, Y(gv) + 3, gv))
    # month ticks
    for mo, lab in ((0, "Sep"), (30, "Oct"), (61, "Nov")):
        s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#ececec"/>' % (X(mo), T, X(mo), T + ph))
        s.append('<text x="%.1f" y="%d" font-size="10" fill="#555" text-anchor="middle">%s</text>' % (
            X(mo), T + ph + 16, lab))
    # quarter-end marker
    s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#999" stroke-dasharray="4,3"/>' % (
        X(30), T, X(30), T + ph))
    s.append('<text x="%.1f" y="%d" font-size="9" fill="#666" text-anchor="middle">Oct-1 turn</text>' % (X(30), T - 4))
    for yr in years:
        pts = sorted(((widx(r["week"]), r["gap"]) for r in weekly
                      if r["centre"] == "Berlin" and r["year"] == yr), key=lambda p: p[0])
        poly = " ".join("%.1f,%.1f" % (X(i), Y(g)) for i, g in pts)
        s.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.2"/>' % (poly, cols[yr]))
        for i, g in pts:
            s.append('<circle cx="%.1f" cy="%.1f" r="3" fill="%s"/>' % (X(i), Y(g), cols[yr]))
    ly = T + 6
    for yr in years:
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2.5"/>' % (
            L + pw + 16, ly, L + pw + 36, ly, cols[yr]))
        lab = "1910 (no war)" if yr == 1910 else "1911 (Agadir)"
        s.append('<text x="%d" y="%d" font-size="11" font-weight="bold">%s</text>' % (L + pw + 42, ly + 4, lab))
        ly += 22
    s.append('</svg>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(s))
    return path


def _svg(rows, path):
    order = sorted(rows, key=lambda r: r["year"])
    W, H, L, R, T, B = 620, 380, 55, 25, 60, 70
    pw, ph = W - L - R, H - T - B
    ymax = 0.6
    n = len(order)

    def y(v):
        return T + ph * (ymax - v) / ymax

    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="Helvetica,Arial,sans-serif">' % (W, H, W, H)]
    s.append('<rect width="%d" height="%d" fill="#fff"/>' % (W, H))
    s.append('<text x="%d" y="26" font-size="15" font-weight="bold">Berlin\'s spot-vs-to-arrive '
             'bill gap, quarter-end, by autumn</text>' % L)
    s.append('<text x="%d" y="44" font-size="11" fill="#555">To-arrive minus spot (points). '
             '1911 alone shows a gap; 1910 was firmer yet flat.</text>' % L)
    for gv in (0, 0.25, 0.5):
        s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s"/>' % (
            L, y(gv), L + pw, y(gv), "#888" if gv == 0 else "#ececec"))
        s.append('<text x="%d" y="%.1f" font-size="10" fill="#555" text-anchor="end">%+.2f</text>' % (
            L - 6, y(gv) + 3, gv))
    bw = pw / (n * 1.7)
    for i, r in enumerate(order):
        cx = L + pw * (i + 0.5) / n
        is11 = r["year"] == 1911
        col = "#c0392b" if is11 else "#9aa4ad"
        gap = r["gap"]
        if gap > 0:
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (
                cx - bw / 2, y(gap), bw, y(0) - y(gap), col))
        else:
            s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3"/>' % (
                cx - bw / 2, y(0), cx + bw / 2, y(0), col))
        lab = "%+.2f" % gap if gap > 0 else "0"
        s.append('<text x="%.1f" y="%.1f" font-size="11" font-weight="%s" fill="%s" '
                 'text-anchor="middle">%s</text>' % (cx, y(max(gap, 0)) - 6,
                 "bold" if is11 else "normal", col, lab))
        s.append('<text x="%.1f" y="%d" font-size="11" fill="#333" text-anchor="middle" '
                 'font-weight="%s">%d</text>' % (cx, T + ph + 18, "bold" if is11 else "normal", r["year"]))
        # tag firm-autumn control on 1910
        if r["year"] == 1910:
            s.append('<text x="%.1f" y="%d" font-size="8.5" fill="#666" text-anchor="middle">firmer, yet flat</text>' % (
                cx, T + ph + 32))
    s.append('</svg>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(s))
    return path


def load_crises():
    with open(CRISES_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["gap"] = float(r["gap_pp"]) if r["gap_pp"] else 0.0
        r["spot"] = float(r["spot_pct"]) if r["spot_pct"] else None
        r["to_arrive"] = float(r["to_arrive_pct"]) if r["to_arrive_pct"] else None
    return rows


def format_crises(rows):
    """Does the Agadir gap generalize to other crises / other centres? No."""
    out = []
    out.append("Does it generalize? Spot-vs-to-arrive gap across war-scares and centres")
    out.append("(gap = to-arrive minus spot, pp; source: C&F Chronicle crisis-week issues)")
    out.append("")
    out.append("%-20s | %-7s | %-8s | %-8s | %-6s" % ("crisis", "centre", "spot", "to-arr", "gap"))
    out.append("-" * 62)
    for r in rows:
        spot = "%.4g%%" % r["spot"] if r["spot"] is not None else " --"
        toa = "%.4g%%" % r["to_arrive"] if r["to_arrive"] is not None else " --"
        flag = "  <==" if (r["centre"] == "Berlin" and r["gap"] >= 0.5) else ""
        out.append("%-20s | %-7s | %-8s | %-8s | %+5.3f%s" % (
            r["crisis"], r["centre"], spot, toa, r["gap"], flag))
    out.append("")
    out.append("Among these CRISIS WEEKS only Agadir's shows a Berlin gap: the Bosnian week")
    out.append("(Mar 1909) was easy money (single rate) and the Balkan-winter week (Dec 1912)")
    out.append("was not a quarter-end ('for both spot and to arrive'). But NOTE the weekly")
    out.append("panel (load_weekly): the gap is a QUARTER-END forward premium that also")
    out.append("appears in the war-free autumn 1910 -- so this crisis-week contrast is")
    out.append("confounded by timing, and does NOT establish an Agadir-specific war signal.")
    out.append("What is robust here is the CENTRE result: only London and Berlin split their")
    out.append("bills at all (Paris/Amsterdam/Brussels/Vienna quote a single rate), so there")
    out.append("is no Vienna/Paris forward-premium series to compare across crises.")
    return "\n".join(out)


def _svg_crises(rows, path):
    """Grouped bars: Berlin vs London spot/to-arrive gap in three crisis weeks."""
    crises = ["Bosnian annexation", "Agadir", "Balkan winter"]
    labels = {"Bosnian annexation": "Bosnia\nMar 1909", "Agadir": "Agadir\nOct 1911",
              "Balkan winter": "Balkan winter\nDec 1912"}
    by = {(r["crisis"], r["centre"]): r["gap"] for r in rows}
    W, H, L, R, T, B = 620, 400, 55, 120, 60, 78
    pw, ph = W - L - R, H - T - B
    ymax = 0.6
    n = len(crises)

    def y(v):
        return T + ph * (ymax - v) / ymax

    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="Helvetica,Arial,sans-serif">' % (W, H, W, H)]
    s.append('<rect width="%d" height="%d" fill="#fff"/>' % (W, H))
    s.append('<text x="%d" y="26" font-size="15" font-weight="bold">Only London &amp; Berlin split; '
             'Vienna/Paris never do</text>' % L)
    s.append('<text x="%d" y="44" font-size="11" fill="#555">Spot-vs-to-arrive gap at three crisis '
             'weeks (but see weekly panel: it is seasonal).</text>' % L)
    for gv in (0, 0.25, 0.5):
        s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s"/>' % (
            L, y(gv), L + pw, y(gv), "#888" if gv == 0 else "#ececec"))
        s.append('<text x="%d" y="%.1f" font-size="10" fill="#555" text-anchor="end">%+.2f</text>' % (
            L - 6, y(gv) + 3, gv))
    gw = pw / n
    pair = [("Berlin", "#c0392b"), ("London", "#2980b9")]
    bw = gw / 3.2
    for i, cr in enumerate(crises):
        base = L + gw * (i + 0.5)
        for k, (centre, col) in enumerate(pair):
            cx = base + (k - 0.5) * bw * 1.15
            gap = by.get((cr, centre), 0.0)
            if gap > 0.001:
                s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (
                    cx - bw / 2, y(gap), bw, y(0) - y(gap), col))
            else:
                s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3"/>' % (
                    cx - bw / 2, y(0), cx + bw / 2, y(0), col))
            s.append('<text x="%.1f" y="%.1f" font-size="10" fill="%s" text-anchor="middle" '
                     'font-weight="%s">%s</text>' % (cx, y(max(gap, 0)) - 5, col,
                     "bold" if gap >= 0.5 else "normal", ("%+.2f" % gap) if gap > 0.001 else "0"))
        for kk, part in enumerate(labels[cr].split("\n")):
            s.append('<text x="%.1f" y="%d" font-size="10.5" fill="#333" text-anchor="middle" '
                     'font-weight="%s">%s</text>' % (base, T + ph + 18 + kk * 14,
                     "bold" if cr == "Agadir" else "normal", part))
    ly = T + 8
    for centre, col in pair:
        s.append('<rect x="%d" y="%d" width="14" height="12" fill="%s"/>' % (L + pw + 22, ly, col))
        s.append('<text x="%d" y="%d" font-size="11">%s</text>' % (L + pw + 40, ly + 11, centre))
        ly += 22
    s.append('<text x="%d" y="%d" font-size="8.5" fill="#666">Only these two</text>' % (L + pw + 22, ly + 6))
    s.append('<text x="%d" y="%d" font-size="8.5" fill="#666">centres split their</text>' % (L + pw + 22, ly + 18))
    s.append('<text x="%d" y="%d" font-size="8.5" fill="#666">bills at all.</text>' % (L + pw + 22, ly + 30))
    s.append('</svg>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(s))
    return path


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Berlin spot-vs-to-arrive gap (Chronicle-sourced).")
    ap.add_argument("--year", type=int, help="print only this autumn's weekly Berlin gap trajectory")
    a = ap.parse_args(argv)
    if a.year is not None:
        wk = [r for r in load_weekly() if r["centre"] == "Berlin" and r["year"] == a.year]
        if not wk:
            print("no weekly Berlin observations for %d (panel covers 1908-1913)" % a.year)
            return 0
        print("Berlin spot-vs-to-arrive gap, %d (to-arrive minus spot, pp):" % a.year)
        for r in sorted(wk, key=lambda r: r["week"]):
            print("  %s  %+.3f  (%s)" % (r["week"], r["gap"], r["source_quote"][:60]))
        return 0
    rows = load()
    weekly = load_weekly()
    print(format_report(rows, weekly))
    _svg(rows, CHART)
    _svg_weekly(weekly, CHART_WEEKLY)
    print("\ncharts -> %s , %s" % (os.path.relpath(CHART, os.getcwd()),
                                   os.path.relpath(CHART_WEEKLY, os.getcwd())))

    print("\n" + "=" * 72 + "\n")
    crises = load_crises()
    print(format_crises(crises))
    _svg_crises(crises, CHART_CRISES)
    print("\nchart -> %s" % os.path.relpath(CHART_CRISES, os.getcwd()))


if __name__ == "__main__":
    raise SystemExit(main())
