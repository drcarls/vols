"""Loader tests — the date decode is pure and unit-tested; the xls read is a
lightweight integration check against the mirrored file."""

import datetime
import os

import pytest

from neal_weidenmier.load import (
    load_short_rates,
    span,
    to_series_map,
    true_date,
)

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "stinterestrates.xls")
D = datetime.date


def test_true_date_undoes_shift():
    # +100-shifted segments (raw >= 1970) go back a century.
    assert true_date(D(1970, 1, 1)) == D(1870, 1, 1)
    assert true_date(D(2012, 6, 29)) == D(1912, 6, 29)
    assert true_date(D(2014, 6, 27)) == D(1914, 6, 27)
    # True-stored middle segment (1912-07 .. 1913-12) is left alone.
    assert true_date(D(1912, 7, 6)) == D(1912, 7, 6)
    assert true_date(D(1913, 12, 27)) == D(1913, 12, 27)


def test_true_date_leap_day_guard():
    # 29 Feb 2000 (leap) -> 1900 (not leap) must not raise.
    assert true_date(D(2000, 2, 29)) == D(1900, 2, 28)


@pytest.mark.skipif(not os.path.exists(DATA), reason="mirrored xls not present")
def test_load_real_file_span_and_continuity():
    obs = load_short_rates(DATA)
    assert obs, "no observations parsed"
    lo, hi = span(obs)
    assert lo == D(1870, 1, 1)
    assert hi == D(1914, 6, 27)   # eve of Sarajevo; ends before the July war weeks
    # All dates in the plausible historical band (decode sanity).
    assert all(D(1870, 1, 1) <= o.date <= D(1914, 6, 27) for o in obs)


@pytest.mark.skipif(not os.path.exists(DATA), reason="mirrored xls not present")
def test_paper_cities_present():
    smap = to_series_map(load_short_rates(DATA))
    keys = " ".join(smap)
    for city in ("london", "paris", "berlin", "vienna", "genoa", "new_york", "petersburg"):
        assert city in keys, f"{city} missing"
    # London 3-month trade bill (the paper's basis asset) is present.
    assert any("london" in k and "trade3mo" in k for k in smap)
