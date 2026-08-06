"""Spread-over-London construction and the tidy CSV crisis_lag reads."""

import csv
import datetime

from hfs_rates.spreads import LONG_FIELDS, coverage, to_spread_rows, write_long_csv

D = datetime.date
POWER = {D(1911, 7, 1): 3.50, D(1911, 7, 8): 2.50, D(1911, 7, 15): 4.00}
LONDON = {D(1911, 7, 1): 3.00, D(1911, 7, 8): 2.75}  # no 07-15


def test_spread_bp_and_overlap_only():
    rows = to_spread_rows("germany", POWER, LONDON)
    assert [r.date for r in rows] == ["1911-07-01", "1911-07-08"]
    assert rows[0].value == "50.00"    # (3.50-3.00)*100
    assert rows[1].value == "-25.00"   # (2.50-2.75)*100
    assert rows[0].series == "germany" and rows[0].unit == "bp"
    assert rows[0].source == "hfs" and rows[0].power_rate == "3.500"


def test_coverage():
    assert coverage(POWER, LONDON) == (3, 2, 2)


def test_write_and_reload(tmp_path):
    rows = to_spread_rows("germany", POWER, LONDON)
    out = tmp_path / "w.csv"
    assert write_long_csv(rows, str(out)) == 2
    with open(out, newline="", encoding="utf-8") as fh:
        got = list(csv.DictReader(fh))
    assert set(LONG_FIELDS).issubset(got[0].keys())
    for r in got:
        float(r["value"])
        assert r["date"].count("-") == 2  # weekly YYYY-MM-DD dates


def test_crisis_lag_loads_weekly_output(tmp_path):
    try:
        from crisis_lag import series as cls  # type: ignore
    except Exception:
        import pytest

        pytest.skip("crisis_lag not importable here")
    out = tmp_path / "w.csv"
    write_long_csv(to_spread_rows("germany", POWER, LONDON), str(out))
    smap = cls.load_long_csv(str(out))
    assert "germany" in smap and len(smap["germany"]) == 2
