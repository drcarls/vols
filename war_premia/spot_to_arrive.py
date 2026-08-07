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
CHART = os.path.join(_HERE, "results", "berlin_spot_to_arrive.svg")
CHART_CRISES = os.path.join(_HERE, "results", "spot_to_arrive_crises.svg")


def load():
    with open(CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["year"] = int(r["year"])
        r["gap"] = float(r["gap_pp"]) if r["gap_pp"] else 0.0
        r["spot"] = float(r["spot_pct"]) if r["spot_pct"] else None
        r["to_arrive"] = float(r["to_arrive_pct"]) if r["to_arrive_pct"] else None
    return rows


def verdict(rows):
    """Return (is_unusual, the-1911-row, the sorted gap series)."""
    y1911 = next(r for r in rows if r["year"] == 1911)
    others = [r for r in rows if r["year"] != 1911]
    # 1911 is 'unusual' if its gap is the sole materially-positive one
    max_other = max(r["gap"] for r in others)
    is_unusual = y1911["gap"] >= 0.5 and max_other <= 0.125
    return is_unusual, y1911, sorted(rows, key=lambda r: r["year"])


def format_report(rows):
    is_unusual, y1911, series = verdict(rows)
    out = []
    out.append("Berlin spot-versus-to-arrive gap, early-October (quarter-end) issue, by autumn")
    out.append("(gap = to-arrive minus spot, percentage points; source: C&F Chronicle)")
    out.append("")
    out.append("%-6s | %-8s | %-8s | %-6s | %s" % ("year", "spot", "to-arr", "gap", "what the Chronicle drew"))
    out.append("-" * 78)
    for r in series:
        spot = "%.3g%%" % r["spot"] if r["spot"] is not None else "  --"
        toa = "%.3g%%" % r["to_arrive"] if r["to_arrive"] is not None else "  --"
        tag = {"yes_gap": "SPOT/TO-ARRIVE GAP", "yes_equal": "equal (stated)",
               "no": "single undivided rate/range"}[r["explicit_split"]]
        star = "  <== 1911" if r["year"] == 1911 else ""
        out.append("%-6d | %-8s | %-8s | %+5.2f | %s%s" % (r["year"], spot, toa, r["gap"], tag, star))
    out.append("")
    out.append("VERDICT: %s" % ("UNUSUAL -- keep the scene as written." if is_unusual
                                else "ordinary -- Chapter III drops the rates."))
    out.append("  1911 is the only autumn of the six in which Berlin quoted a spot/to-arrive")
    out.append("  gap (+0.5 pp, to-arrive dearer). 1910 -- a FIRMER autumn in level -- showed")
    out.append("  none, so the gap is not a rate-level artifact. The Agadir anxiety left an")
    out.append("  actual price in the forward bill market, not merely a belief.")
    out.append("  (1913 is a quotation range, not a split; 1908/1909 single undivided rates.)")
    return "\n".join(out)


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
    out.append("Berlin split its bills in AGADIR ALONE (+0.5 pp). In the Bosnian crisis")
    out.append("(Mar 1909, easy money) it quoted a single rate; in the Balkan winter crisis")
    out.append("(Dec 1912) it was explicitly 'for both spot and to arrive' at 5 3/8-6% --")
    out.append("TIGHTER than Agadir, yet no gap. So the gap is not a generic war-scare")
    out.append("signature and not a rate-level effect. Among centres only London and Berlin")
    out.append("split their bills at all (Paris/Amsterdam/Brussels/Vienna quote a single")
    out.append("rate); London's forward premium was also WIDEST in Agadir (+0.25 vs +0.06 in")
    out.append("the tighter Dec-1912 week). Agadir is the one crisis that reached into the")
    out.append("great bill centres' forward pricing -- Berlin's most of all.")
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
    s.append('<text x="%d" y="26" font-size="15" font-weight="bold">The gap is Agadir-specific, '
             'not a war-scare signature</text>' % L)
    s.append('<text x="%d" y="44" font-size="11" fill="#555">Spot-vs-to-arrive bill gap (points) '
             'at three great-power war scares.</text>' % L)
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


def main():
    rows = load()
    print(format_report(rows))
    _svg(rows, CHART)
    print("\nchart -> %s" % os.path.relpath(CHART, os.getcwd()))

    print("\n" + "=" * 72 + "\n")
    crises = load_crises()
    print(format_crises(crises))
    _svg_crises(crises, CHART_CRISES)
    print("\nchart -> %s" % os.path.relpath(CHART_CRISES, os.getcwd()))


if __name__ == "__main__":
    raise SystemExit(main())
