"""The tidy long emitter — schema and values crisis_lag will read back."""

import csv

from imm_yale.series import (
    LONG_FIELDS,
    merge_series,
    spreads_to_points,
    write_long_csv,
)
from imm_yale.spread import to_spreads


def _spreads():
    issuer = {"1911-07": 4.20, "1911-08": 4.50}
    bench = {"1911-07": 2.50, "1911-08": 2.55}
    return to_spreads(issuer, bench)


def test_points_dated_to_first_of_month():
    pts = spreads_to_points("germany", _spreads(), security_id="10500")
    assert pts[0].date == "1911-07-01"
    assert pts[0].series == "germany"
    assert pts[0].value == "170.00"
    assert pts[0].unit == "bp"
    assert pts[0].source == "imm_yale"
    assert pts[0].security_id == "10500"


def test_write_long_csv_roundtrip(tmp_path):
    pts = merge_series(
        spreads_to_points("germany", _spreads()),
        spreads_to_points("france", _spreads()),
    )
    out = tmp_path / "spreads_long.csv"
    n = write_long_csv(pts, str(out))
    assert n == 4

    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # Header carries the canonical long schema.
    assert set(LONG_FIELDS).issubset(rows[0].keys())
    # crisis_lag reads date/series/value — all present and parseable.
    for r in rows:
        assert r["date"].count("-") == 2
        assert r["series"] in {"germany", "france"}
        float(r["value"])
    # Sorted by (date, series): france before germany within a month.
    assert (rows[0]["date"], rows[0]["series"]) == ("1911-07-01", "france")


def test_crisis_lag_can_load_it(tmp_path):
    # The whole point: the output is consumable by crisis_lag.series.
    crisis_lag_series = _import_crisis_lag_series()
    if crisis_lag_series is None:
        import pytest

        pytest.skip("crisis_lag not importable in this environment")
    pts = spreads_to_points("germany", _spreads())
    out = tmp_path / "s.csv"
    write_long_csv(pts, str(out))
    smap = crisis_lag_series.load_long_csv(str(out))
    assert "germany" in smap
    assert len(smap["germany"]) == 2


def _import_crisis_lag_series():
    try:
        from crisis_lag import series as s  # type: ignore

        return s
    except Exception:
        return None
