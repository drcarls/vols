"""Spread construction: issuer yield over benchmark, in basis points."""

import pytest

from imm_yale.spread import coverage, month_key, to_spreads


def test_month_key():
    assert month_key(1911, 7) == "1911-07"
    assert month_key(1911, 12) == "1911-12"


def test_basic_spread_in_bp():
    issuer = {"1911-07": 4.20, "1911-08": 4.50}
    bench = {"1911-07": 2.50, "1911-08": 2.55}
    pts = to_spreads(issuer, bench)
    assert [p.month for p in pts] == ["1911-07", "1911-08"]
    assert pts[0].spread_bp == pytest.approx(170.0)  # (4.20-2.50)*100
    assert pts[1].spread_bp == pytest.approx(195.0)


def test_only_overlapping_months_kept():
    issuer = {"1911-06": 4.0, "1911-07": 4.2}
    bench = {"1911-07": 2.5, "1911-08": 2.6}
    pts = to_spreads(issuer, bench)
    assert [p.month for p in pts] == ["1911-07"]


def test_result_is_month_sorted():
    issuer = {"1911-08": 4.5, "1911-07": 4.2, "1911-09": 4.6}
    bench = {"1911-07": 2.5, "1911-08": 2.5, "1911-09": 2.5}
    pts = to_spreads(issuer, bench)
    assert [p.month for p in pts] == ["1911-07", "1911-08", "1911-09"]


def test_negative_spread_allowed():
    # A safer-than-benchmark quote is a real (if rare) observation, not an error.
    pts = to_spreads({"1911-07": 2.3}, {"1911-07": 2.5})
    assert pts[0].spread_bp == pytest.approx(-20.0)


def test_coverage_counts():
    issuer = {"1911-06": 4.0, "1911-07": 4.2}
    bench = {"1911-07": 2.5, "1911-08": 2.6}
    assert coverage(issuer, bench) == (2, 2, 1)
