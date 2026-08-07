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


def _window(smap, slug, year):
    """{iso_week: value} for the 1 Jun -- 30 Nov window of `year`."""
    lo = datetime.date(year, *WIN_START)
    hi = datetime.date(year, *WIN_END)
    return {d.isocalendar()[1]: v for d, v in smap[slug] if lo <= d <= hi}


def analyse(smap):
    """Per city: week-by-week 1911 value, own-seasonal baseline, deviation, dispersion.

    Alignment is by ISO week (all four cities share the same survey date each week,
    and the years drift only a few days), so the same calendar week is compared
    across years. A week is used only where >= 2 baseline years supply a value.
    """
    # representative 1911 date for each iso week (for the x-axis / labels)
    dates = {
        d.isocalendar()[1]: d
        for d, _ in smap["berlin_openmkt"]
        if datetime.date(1911, *WIN_START) <= d <= datetime.date(1911, *WIN_END)
    }
    out = []
    for label, slug, note in CITIES:
        treat = _window(smap, slug, TREATMENT_YEAR)
        base = {y: _window(smap, slug, y) for y in BASELINE_YEARS}
        weeks = []
        for w in sorted(treat):
            bvals = [base[y][w] for y in BASELINE_YEARS if w in base[y]]
            if len(bvals) < 2:
                continue
            bmean = statistics.mean(bvals)
            weeks.append({
                "week": w,
                "date": dates[w],
                "value": treat[w],
                "base_mean": bmean,
                "base_sd": statistics.pstdev(bvals),
                "dev": treat[w] - bmean,
            })
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
    out.append("New York control for Agadir -- deviation of 1911 from own-seasonal baseline")
    out.append("(baseline = mean of 1909, 1910, 1912, 1913; 1907 excluded; 1 Jun - 30 Nov)")
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
    out.append("Reading: 'peak tightening' is the largest week 1911 sat ABOVE its own")
    out.append("seasonal norm -- the Agadir-specific signal. 'baseline dispersion' is the")
    out.append("typical week-to-week scatter of the baseline years: a deviation smaller")
    out.append("than it is inside normal year-to-year noise.")
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


def main():
    from neal_weidenmier.load import load_short_rates, to_series_map
    smap = to_series_map(load_short_rates(SHORT))
    rows = analyse(smap)
    print(format_table(rows))
    _svg_chart(rows, CHART)
    print("\nchart -> %s" % os.path.relpath(CHART, os.getcwd()))


if __name__ == "__main__":
    raise SystemExit(main())
