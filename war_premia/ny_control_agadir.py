"""Does the New York control hold for Agadir? -- a descriptive seasonal check.

During the Agadir crisis (roughly 1 July -- 4 November 1911) Berlin's money market
tightened. The question is whether that tightening was a *war-risk* signal or just
the ordinary European autumn seasonal -- and whether **New York**, outside the
European alliance system, showed any of it. New York is the control: if the Agadir
tightening is war-risk, a market insulated from a European war should not share it.

This is a DESCRIPTIVE check -- no premium estimation, no significance testing. For
each city we compare its 1911 weekly open-market path against *its own* seasonal
baseline (the mean of the same calendar weeks across 1909, 1910, 1912, 1913). 1907
is **excluded** -- deliberately, not silently: it carries the 1907 panic (New York
call money hit 20%), which would swamp every other year and manufacture a spurious
"calm 1911". The deviation (1911 minus own-seasonal-mean) strips the common autumn
seasonal out, so what remains is the year-specific, Agadir-specific movement.

Cities (weekly, Neal-Weidenmier short rates), window 1 June -- 30 November:
  - New York -- the control. NB: NW carries no NY *open-market/discount* series;
    the NY money-market rate is **call money**, which is the analogue used here.
    Call money is more seasonal (crop-moving demand) and more volatile than a
    European discount rate, which makes a *flat* 1911 the more striking, not less.
  - Berlin -- the market said to have tightened during Agadir.
  - Amsterdam -- a neutral European reference.
  - Paris -- the power directly opposed to Germany in the crisis.

Markers: 1 Jul 1911 (the gunboat *Panther* reaches Agadir) and 4 Nov 1911 (the
Franco-German convention settles the crisis).

    python ny_control_agadir.py           # prints the table, writes the SVG chart
"""

from __future__ import annotations

import datetime
import os
import statistics
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
SHORT = os.path.join(_HERE, "..", "neal_weidenmier", "data", "stinterestrates.xls")
CHART = os.path.join(_HERE, "results", "ny_control_agadir.svg")
sys.path.insert(0, os.path.join(_HERE, "..", "neal_weidenmier", "src"))

TREATMENT_YEAR = 1911
BASELINE_YEARS = (1909, 1910, 1912, 1913)
EXCLUDED_YEARS = (1907,)  # 1907 panic -- excluded on purpose (see module docstring)
WIN_START = (6, 1)   # 1 June
WIN_END = (11, 30)   # 30 November

# (label, slug, note); order fixes the plotting/legend order.
CITIES = [
    ("New York", "new_york_call", "control (call money -- NW has no NY discount rate)"),
    ("Berlin", "berlin_openmkt", "said to have tightened during Agadir"),
    ("Amsterdam", "amsterdam_openmkt", "neutral European reference"),
    ("Paris", "paris_openmkt", "power opposed to Germany"),
]

# Crisis markers, as (label, date).
MARKERS = [
    ("Panther -> Agadir (1 Jul)", datetime.date(1911, 7, 1)),
    ("Convention (4 Nov)", datetime.date(1911, 11, 4)),
]


def _window(smap, slug, year, win_start=WIN_START, win_end=WIN_END):
    """{iso_week: value} for the ``win_start``..``win_end`` window of ``year``."""
    lo = datetime.date(year, *win_start)
    hi = datetime.date(year, *win_end)
    return {d.isocalendar()[1]: v for d, v in smap[slug] if lo <= d <= hi}


def analyse(smap, treatment=None, baselines=None, win_start=None, win_end=None, cities=None,
            detrend=False):
    """Per city: week-by-week treatment value, own-seasonal baseline, deviation, dispersion.

    Alignment is by ISO week (cities share the same survey date each week, and the years
    drift only a few days), so the same calendar week is compared across years. A week is
    used only where >= 2 baseline years supply a value. The five keyword arguments make
    this reusable for *any* crisis window (see ``crisis_deviation.py``); the defaults
    reproduce the Agadir-1911 analysis.
    """
    treatment = TREATMENT_YEAR if treatment is None else treatment
    baselines = BASELINE_YEARS if baselines is None else tuple(baselines)
    win_start = WIN_START if win_start is None else win_start
    win_end = WIN_END if win_end is None else win_end
    cities = CITIES if cities is None else cities
    # representative treatment-year date for each iso week (union across the cities, so
    # every week has a label regardless of which city is listed first)
    lo, hi = datetime.date(treatment, *win_start), datetime.date(treatment, *win_end)
    dates = {}
    for _, slug, _ in cities:
        for d, _v in smap.get(slug, []):
            if lo <= d <= hi:
                dates.setdefault(d.isocalendar()[1], d)
    out = []
    for label, slug, note in cities:
        treat = _window(smap, slug, treatment, win_start, win_end)
        base = {y: _window(smap, slug, y, win_start, win_end) for y in baselines}
        if detrend:
            # centre each year's window at its own mean, so only the within-window
            # *shape* is compared -- removes the cyclical rate LEVEL confound.
            if treat:
                tm = statistics.mean(treat.values())
                treat = {w: v - tm for w, v in treat.items()}
            for y in list(base):
                if base[y]:
                    bm = statistics.mean(base[y].values())
                    base[y] = {w: v - bm for w, v in base[y].items()}
        weeks = []
        for w in sorted(treat):
            bvals = [base[y][w] for y in baselines if w in base[y]]
            if len(bvals) < 2:
                continue
            bmean = statistics.mean(bvals)
            weeks.append({
                "week": w,
                "date": dates.get(w),
                "value": treat[w],
                "base_mean": bmean,
                "base_sd": statistics.pstdev(bvals),
                "dev": treat[w] - bmean,
            })
        if not weeks:                                # no week with >=2 baseline years
            continue                                 # (city absent/short in this window)
        devs = [wk["dev"] for wk in weeks]
        pos = max(weeks, key=lambda wk: wk["dev"])   # peak tightening above seasonal
        absmax = max(weeks, key=lambda wk: abs(wk["dev"]))
        out.append({
            "label": label, "slug": slug, "note": note, "weeks": weeks,
            "peak_pos": pos, "peak_abs": absmax,
            "dev_min": min(devs), "dev_max": max(devs),
            "base_disp": statistics.mean(wk["base_sd"] for wk in weeks),
        })
    return out


def format_table(rows):
    out = []
    out.append("Deviation from each city's own seasonal baseline (same calendar weeks across")
    out.append("the baseline years). Positive tightening = above the city's own seasonal norm.")
    out.append("")
    hdr = "%-10s | %-28s | %-24s | %s" % (
        "city", "peak tightening (dev>0)", "largest deviation (|dev|)", "baseline")
    out.append(hdr)
    out.append("%-10s | %-28s | %-24s | %s" % (
        "", "  above own seasonal norm", "  any direction", "dispersion"))
    out.append("-" * len(hdr))
    for r in rows:
        pp, pa = r["peak_pos"], r["peak_abs"]
        out.append("%-10s | %+5.2f pts  %s | %+5.2f pts  %s | SD %.2f" % (
            r["label"],
            pp["dev"], pp["date"].isoformat(),
            pa["dev"], pa["date"].isoformat(),
            r["base_disp"],
        ))
    out.append("")
    out.append("Reading: 'peak tightening' is the largest week the treatment year sat ABOVE")
    out.append("its own seasonal norm. 'baseline dispersion' is the typical week-to-week")
    out.append("scatter of the baseline years: a deviation smaller than it sits inside normal")
    out.append("year-to-year noise. NB when the treatment year's cyclical rate LEVEL differs")
    out.append("from the baselines', the deviation conflates the crisis with that level --")
    out.append("trust synchronized TIMING over absolute magnitude.")
    return "\n".join(out)


# ---------------------------------------------------------------- SVG chart ----

def _svg_chart(rows, path):
    """Hand-write an SVG line chart (no matplotlib in this env)."""
    W, H = 860, 500
    L, R, T, B = 70, 210, 54, 60  # margins (wide right margin for the legend)
    pw, ph = W - L - R, H - T - B
    colors = ["#1a1a1a", "#c0392b", "#2980b9", "#27ae60"]  # NY, Berlin, Amsterdam, Paris

    weeks = [wk["week"] for wk in rows[0]["weeks"]]
    dates = [wk["date"] for wk in rows[0]["weeks"]]
    n = len(weeks)
    all_dev = [wk["dev"] for r in rows for wk in r["weeks"]]
    ymin = min(-3.0, min(all_dev) - 0.3)
    ymax = max(1.0, max(all_dev) + 0.3)

    def x(i):
        return L + pw * i / (n - 1)

    def y(v):
        return T + ph * (ymax - v) / (ymax - ymin)

    s = []
    s.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d" font-family="Helvetica,Arial,sans-serif">' % (W, H, W, H))
    s.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))
    s.append('<text x="%d" y="24" font-size="16" font-weight="bold">Does New York tighten with Agadir? '
             'Deviation from each city\'s own seasonal baseline, 1911</text>' % L)
    s.append('<text x="%d" y="42" font-size="11" fill="#555">Weekly open-market rate minus mean of '
             '1909/1910/1912/1913 same-week rate (1907 excluded). Positive = tighter than a normal '
             'Jun-Nov.</text>' % L)

    # y gridlines / labels at integer points
    yv = int(ymin)
    while yv <= ymax:
        gy = y(yv)
        s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="%s"/>' % (
            L, gy, L + pw, gy, "#888" if yv == 0 else "#e8e8e8", "1.2" if yv == 0 else "1"))
        s.append('<text x="%d" y="%.1f" font-size="10" fill="#555" text-anchor="end">%+d</text>' % (
            L - 6, gy + 3, yv))
        yv += 1
    s.append('<text x="16" y="%d" font-size="11" fill="#555" transform="rotate(-90 16 %d)" '
             'text-anchor="middle">deviation from seasonal norm (pts)</text>' % (T + ph / 2, T + ph / 2))

    # x labels: month starts
    seen = set()
    for i, d in enumerate(dates):
        if d.month not in seen:
            seen.add(d.month)
            s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#e8e8e8"/>' % (
                x(i), T, x(i), T + ph))
            s.append('<text x="%.1f" y="%d" font-size="10" fill="#555" text-anchor="middle">%s</text>' % (
                x(i), T + ph + 16, d.strftime("%b")))

    # crisis markers
    for lab, md in MARKERS:
        # nearest week index
        i = min(range(n), key=lambda k: abs((dates[k] - md).days))
        s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#999" stroke-width="1.2" '
                 'stroke-dasharray="5,4"/>' % (x(i), T, x(i), T + ph))
        s.append('<text x="%.1f" y="%d" font-size="9.5" fill="#666" text-anchor="middle">%s</text>' % (
            x(i), T - 6, lab))

    # city lines
    for r, col in zip(rows, colors):
        pts = " ".join("%.1f,%.1f" % (x(i), y(wk["dev"])) for i, wk in enumerate(r["weeks"]))
        s.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>' % (pts, col))

    # legend
    ly = T + 8
    for r, col in zip(rows, colors):
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2.5"/>' % (
            L + pw + 14, ly, L + pw + 34, ly, col))
        s.append('<text x="%d" y="%d" font-size="11" font-weight="bold">%s</text>' % (
            L + pw + 40, ly + 4, r["label"]))
        s.append('<text x="%d" y="%d" font-size="8.5" fill="#666">%s</text>' % (
            L + pw + 40, ly + 15, r["note"][:26]))
        ly += 34
    s.append('</svg>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(s))
    return path


# ----------------------------------------------- the 1914 contagion extension --

# Aug 1 1914 is ISO week 31; the NY-call seasonal norm for late-Jul/early-Aug uses
# ISO weeks 30-32 of the same baseline years. The July-1914 crisis rate is READ from
# the Commercial & Financial Chronicle (data/july_aug_1914_money.csv), because the
# NW weekly series stops at 1914-06-27 -- the eve of Sarajevo.
GOLD_CSV = os.path.join(_HERE, "data", "july_aug_1914_gold.csv")
MONEY_CSV = os.path.join(_HERE, "data", "july_aug_1914_money.csv")
CHART_1914 = os.path.join(_HERE, "results", "ny_control_1914_flip.svg")


def contagion_1914(smap):
    """The sign-flip test: NY was BELOW its norm for Agadir (localized crisis) but
    FAR ABOVE it in the July-1914 outbreak (the crisis that became a world war).

    Returns the pieces, all descriptive:
      - june_dev: mean deviation of each city over 1-27 Jun 1914 (the last weeks the
        NW data covers) -- the 'no anticipation' check.
      - ny_norm: NY call-money seasonal norm for ISO wk 30-32 (baseline years).
      - ny_1914_high/low: NY call money in the outbreak week (Chronicle, 1914-08-01).
      - flip: (Agadir peak neg dev) vs (Jul-1914 high minus norm).
    """
    import csv

    def win(slug, year, lo, hi):
        return [(d, v) for d, v in smap[slug]
                if d.year == year and lo <= d.isocalendar()[1] <= hi]

    june = {}
    for label, slug, _ in CITIES:
        devs = []
        for d, v in win(slug, 1914, 23, 26):        # ISO wk 23-26 ~ 1-27 Jun
            w = d.isocalendar()[1]
            bvals = [bb for y in BASELINE_YEARS for _, bb in win(slug, y, w, w)]
            if len(bvals) >= 2:
                devs.append(v - statistics.mean(bvals))
        june[label] = statistics.mean(devs) if devs else float("nan")

    ny_norm_vals = [v for y in BASELINE_YEARS for _, v in win("new_york_call", y, 30, 32)]
    ny_norm = statistics.mean(ny_norm_vals)

    ny_high = ny_low = None
    with open(MONEY_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["series"] == "ny_call_money_high":
                ny_high = float(row["value"])
            elif row["series"] == "ny_call_money_low":
                ny_low = float(row["value"])

    gold = []
    with open(GOLD_CSV, newline="", encoding="utf-8") as fh:
        gold = list(csv.DictReader(fh))

    return {
        "june_dev": june,
        "ny_norm": ny_norm,
        "ny_high": ny_high, "ny_low": ny_low,
        "flip_high": ny_high - ny_norm, "flip_low": ny_low - ny_norm,
        "gold": gold,
    }


def format_contagion(c, agadir_ny_peak_neg):
    out = []
    out.append("The 1914 contagion extension -- does New York's sign flip?")
    out.append("(NW weekly rates end 1914-06-27; July-1914 rate from the C&F Chronicle)")
    out.append("")
    out.append("1) No anticipation -- mean deviation from own seasonal norm, 1-27 Jun 1914:")
    for label, _, _ in CITIES:
        out.append("     %-10s %+.2f pts" % (label, c["june_dev"][label]))
    out.append("   Every market at/below its seasonal norm on the eve of Sarajevo -- the")
    out.append("   war was NOT priced in advance (Berlin was actually easy, -1.15).")
    out.append("")
    out.append("2) The flip -- New York call money:")
    out.append("     Agadir 1911 peak deviation ........ %+.2f pts (BELOW norm: insulated)" % agadir_ny_peak_neg)
    out.append("     late-Jul/early-Aug seasonal norm .. %.2f%%" % c["ny_norm"])
    out.append("     outbreak week (Chronicle 08-01) ... %.0f-%.0f%%" % (c["ny_low"], c["ny_high"]))
    out.append("     => outbreak HIGH vs norm .......... %+.1f pts (ABOVE norm: hit)" % c["flip_high"])
    out.append("   New York's sign flips from strongly negative (Agadir, a localized crisis")
    out.append("   that stayed localized) to strongly positive (July 1914, the crisis that")
    out.append("   froze the London-centred system New York was plugged into).")
    out.append("")
    out.append("3) Gold corroboration (C&F Chronicle, cfc_19140808; sourced quotes in CSV):")
    out.append("   - Reichsbank had added ~$100M gold 'since the Morocco [Agadir] incident'")
    out.append("     -- the German war-chest built from the earlier crisis onward.")
    out.append("   - Outbreak week: gold poured OUT of New York toward London -- the")
    out.append("     Kronprinzessin Cecilie's $10M turned back mid-Atlantic; a $100M London")
    out.append("     shipment contemplated; Sub-Treasury+gold-export drain $16.8M on NY banks.")
    out.append("   Gold flowing OUT of New York under stress is the opposite of the")
    out.append("   safe-haven inflow it enjoyed while insulated -- contagion, not refuge.")
    return "\n".join(out)


def _svg_flip(agadir_ny_peak_neg, c, path):
    """A small two-bar SVG: NY deviation from its seasonal norm, Agadir vs Jul 1914."""
    W, H = 560, 380
    L, R, T, B = 70, 30, 70, 70
    pw, ph = W - L - R, H - T - B
    vals = [("Agadir 1911\n(localized crisis)", agadir_ny_peak_neg, "#2980b9"),
            ("July 1914\n(became world war)", c["flip_high"], "#c0392b")]
    ymin, ymax = -3.5, 5.5

    def y(v):
        return T + ph * (ymax - v) / (ymax - ymin)

    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="Helvetica,Arial,sans-serif">' % (W, H, W, H)]
    s.append('<rect width="%d" height="%d" fill="#fff"/>' % (W, H))
    s.append('<text x="%d" y="26" font-size="15" font-weight="bold">New York\'s sign flips: '
             'call-money deviation</text>' % L)
    s.append('<text x="%d" y="44" font-size="11" fill="#555">Peak deviation from NY\'s own '
             'seasonal norm (points). Below 0 = calmer than usual.</text>' % L)
    # zero line + integer grid
    v = int(ymin)
    while v <= ymax:
        gy = y(v)
        s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="%s"/>' % (
            L, gy, L + pw, gy, "#888" if v == 0 else "#ececec", "1.3" if v == 0 else "1"))
        s.append('<text x="%d" y="%.1f" font-size="10" fill="#555" text-anchor="end">%+d</text>' % (
            L - 6, gy + 3, v))
        v += 1
    bw = pw / (len(vals) * 2)
    for i, (lab, val, col) in enumerate(vals):
        cx = L + pw * (i + 0.5) / len(vals)
        y0, y1 = y(0), y(val)
        s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (
            cx - bw / 2, min(y0, y1), bw, abs(y1 - y0), col))
        s.append('<text x="%.1f" y="%.1f" font-size="13" font-weight="bold" fill="%s" '
                 'text-anchor="middle">%+.1f</text>' % (cx, (y1 - 8 if val > 0 else y1 + 18), col, val))
        for k, part in enumerate(lab.split("\n")):
            s.append('<text x="%.1f" y="%d" font-size="10.5" fill="#333" text-anchor="middle">%s</text>' % (
                cx, T + ph + 20 + k * 14, part))
    s.append('</svg>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(s))
    return path


def main():
    from neal_weidenmier.load import load_short_rates, to_series_map
    smap = to_series_map(load_short_rates(SHORT))
    rows = analyse(smap)
    print(format_table(rows))
    _svg_chart(rows, CHART)
    print("\nchart -> %s" % os.path.relpath(CHART, os.getcwd()))

    print("\n" + "=" * 72 + "\n")
    ny_peak_neg = next(r for r in rows if r["label"] == "New York")["peak_abs"]["dev"]
    c = contagion_1914(smap)
    print(format_contagion(c, ny_peak_neg))
    _svg_flip(ny_peak_neg, c, CHART_1914)
    print("\nchart -> %s" % os.path.relpath(CHART_1914, os.getcwd()))


if __name__ == "__main__":
    raise SystemExit(main())
