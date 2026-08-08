"""Run the seasonal-deviation ('own-baseline') money-market test for ANY crisis.

This is the Agadir New-York-control method (`ny_control_agadir.py`) made reusable: pick a
treatment year, a set of clean baseline years, a window, and the cities (Neal-Weidenmier
slugs), and it prints each city's deviation from its own seasonal norm over the window —
the peak tightening, the largest deviation, and the baseline dispersion. Descriptive only:
no premium estimation, no significance tests. Verify anything odd against the source.

Examples
--------
Agadir 1911 (the default cities, a different way in)::

    python crisis_deviation.py --treatment 1911 --baselines 1909,1910,1912,1913 \\
        --window 06-01:11-30 --cities new_york_call,berlin_openmkt,paris_openmkt,amsterdam_openmkt

First Moroccan crisis / Algeciras, spring 1906 (Paris vs Berlin/London/Vienna)::

    python crisis_deviation.py --treatment 1906 --baselines 1904,1905,1907,1908 \\
        --window 01-01:06-30 --cities paris_openmkt,berlin_openmkt,vienna_openmkt

Balkan winter, autumn 1912 (does Berlin's autumn stand out?)::

    python crisis_deviation.py --treatment 1912 --baselines 1909,1910,1913 \\
        --window 09-01:12-31 --cities berlin_openmkt,vienna_openmkt,paris_openmkt

Available slugs: run with --list. 1907 (panic) makes a poor baseline -- exclude it, as
the Agadir analysis does, and say so.
"""

from __future__ import annotations

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "neal_weidenmier", "src"))
sys.path.insert(0, _HERE)

import ny_control_agadir as nc  # reuse analyse() + format_table()


def _md(s):
    m, d = s.split("-")
    return (int(m), int(d))


def _cities(arg):
    """Accept 'slug,slug' or 'Label:slug,Label:slug'; derive a label from the slug."""
    out = []
    for tok in arg.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if ":" in tok:
            label, slug = tok.split(":", 1)
        else:
            slug = tok
            label = tok.replace("_openmkt", "").replace("_call", "").replace("_market", "") \
                       .replace("_", " ").title()
        out.append((label, slug, ""))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Seasonal-deviation money-market test for any crisis.")
    ap.add_argument("--treatment", type=int, help="crisis year")
    ap.add_argument("--baselines", type=lambda s: [int(x) for x in s.split(",")],
                    help="comma-separated clean baseline years (exclude 1907)")
    ap.add_argument("--window", type=lambda s: tuple(_md(p) for p in s.split(":")),
                    help="MM-DD:MM-DD, e.g. 06-01:11-30")
    ap.add_argument("--cities", type=_cities, help="comma-separated NW slugs (or Label:slug)")
    ap.add_argument("--short", default=nc.SHORT, help="path to stinterestrates.xls")
    ap.add_argument("--list", action="store_true", help="list available city slugs and exit")
    ap.add_argument("--detrend", action="store_true",
                    help="centre each year's window at its own mean (remove the cyclical "
                         "rate level; compare only the within-window shape)")
    a = ap.parse_args(argv)

    from neal_weidenmier.load import load_short_rates, to_series_map
    smap = to_series_map(load_short_rates(a.short))
    if a.list:
        for k in sorted(smap):
            print(k)
        return 0

    win = a.window or (nc.WIN_START, nc.WIN_END)
    rows = nc.analyse(smap, treatment=a.treatment, baselines=a.baselines,
                      win_start=win[0], win_end=win[1], cities=a.cities, detrend=a.detrend)
    treatment = a.treatment or nc.TREATMENT_YEAR
    baselines = a.baselines or list(nc.BASELINE_YEARS)
    print("Seasonal-deviation test -- treatment %d vs baselines %s, window %02d-%02d..%02d-%02d%s"
          % (treatment, ",".join(map(str, baselines)), win[0][0], win[0][1], win[1][0], win[1][1],
             "  [DETRENDED: level removed]" if a.detrend else ""))
    print(nc.format_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
