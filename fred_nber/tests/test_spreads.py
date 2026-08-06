"""Spread construction and the tidy CSV — offline, and loadable by crisis_lag."""

import csv

from fred_nber.spreads import LONG_FIELDS, coverage, to_spread_rows, write_long_csv


ISSUER = {"1911-06": 3.79, "1911-07": 3.80, "1911-09": 3.82}
BENCH = {"1911-06": 3.13, "1911-07": 3.18, "1911-08": 3.20}


def test_spread_bp_and_overlap_only():
    rows = to_spread_rows("germany", ISSUER, BENCH, fred_id="X", benchmark_id="B")
    # overlap is Jun, Jul (not Aug: no issuer; not Sep: no benchmark)
    assert [r.date for r in rows] == ["1911-06-01", "1911-07-01"]
    assert rows[0].value == "66.00"   # (3.79-3.13)*100
    assert rows[1].value == "62.00"   # (3.80-3.18)*100
    assert rows[0].series == "germany" and rows[0].unit == "bp"
    assert rows[0].source == "fred_nber" and rows[0].fred_id == "X"


def test_coverage():
    assert coverage(ISSUER, BENCH) == (3, 3, 2)


def test_write_and_reload_schema(tmp_path):
    rows = to_spread_rows("germany", ISSUER, BENCH)
    out = tmp_path / "s.csv"
    n = write_long_csv(rows, str(out))
    assert n == 2
    with open(out, newline="", encoding="utf-8") as fh:
        got = list(csv.DictReader(fh))
    assert set(LONG_FIELDS).issubset(got[0].keys())
    for r in got:
        float(r["value"])
        assert r["date"].count("-") == 2


def test_crisis_lag_loads_output(tmp_path):
    try:
        from crisis_lag import series as cls  # type: ignore
    except Exception:
        import pytest

        pytest.skip("crisis_lag not importable here")
    out = tmp_path / "s.csv"
    write_long_csv(to_spread_rows("germany", ISSUER, BENCH), str(out))
    smap = cls.load_long_csv(str(out))
    assert "germany" in smap and len(smap["germany"]) == 2
