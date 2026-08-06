from gallica_le_temps.pipeline import ExtractionResult
from gallica_le_temps.series import (
    LONG_FIELDS,
    series_order,
    to_long,
    to_wide,
    write_long_csv,
    write_wide_csv,
)


def _results():
    return [
        ExtractionResult(
            date="1914-07-28", target="rente_3pct", status="ok", ark="bpt6k1",
            ocr_quality=95.4, page=3, region="1,2,3,4",
            crop_url="http://x/1", value="84.25", unit="FRF",
        ),
        ExtractionResult(
            date="1914-07-28", target="bdf", status="ok", ark="bpt6k1",
            page=3, region="5,6,7,8", crop_url="http://x/2",
            value="4100", unit="FRF",
        ),
        # A market-closed / missing day: no value, explicit status.
        ExtractionResult(
            date="1914-07-29", target="rente_3pct", status="no_issue",
            unit="FRF", note="sunday",
        ),
    ]


def test_to_long_shape_and_source():
    points = to_long(_results(), source="le_temps")
    assert len(points) == 3
    assert points[0].source == "le_temps"
    assert points[0].series == "rente_3pct"
    assert points[0].value == "84.25"
    # Missing day is preserved with its status, blank value.
    assert points[2].value is None
    assert points[2].status == "no_issue"


def test_series_order_first_seen():
    assert series_order(_results()) == ["rente_3pct", "bdf"]


def test_to_wide_only_result_dates():
    fields, rows = to_wide(_results())
    assert fields == ["date", "rente_3pct", "bdf"]
    assert rows[0] == {"date": "1914-07-28", "rente_3pct": "84.25", "bdf": "4100"}
    # 29th has no parsed value -> blank cells, but the row exists.
    assert rows[1] == {"date": "1914-07-29", "rente_3pct": "", "bdf": ""}


def test_to_wide_daily_spine_fills_gaps():
    spine = ["1914-07-27", "1914-07-28", "1914-07-29", "1914-07-30"]
    fields, rows = to_wide(_results(), dates=spine)
    assert [r["date"] for r in rows] == spine
    # Days outside the results (27th, 30th) appear as empty rows -> gap-free index.
    assert rows[0] == {"date": "1914-07-27", "rente_3pct": "", "bdf": ""}
    assert rows[1]["rente_3pct"] == "84.25"
    assert rows[3] == {"date": "1914-07-30", "rente_3pct": "", "bdf": ""}


def test_write_long_csv(tmp_path):
    p = tmp_path / "long.csv"
    n = write_long_csv(_results(), str(p), source="le_temps")
    assert n == 3
    lines = p.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(LONG_FIELDS)
    assert "1914-07-28,rente_3pct,84.25,FRF,le_temps,ok" in lines[1]


def test_write_wide_csv_daily(tmp_path):
    p = tmp_path / "wide.csv"
    spine = ["1914-07-28", "1914-07-29"]
    n = write_wide_csv(_results(), str(p), dates=spine)
    assert n == 2
    text = p.read_text(encoding="utf-8").splitlines()
    assert text[0] == "date,rente_3pct,bdf"
    assert text[1] == "1914-07-28,84.25,4100"
    assert text[2] == "1914-07-29,,"
