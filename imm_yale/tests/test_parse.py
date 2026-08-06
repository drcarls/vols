"""Response parsing: sentinels, header-matched columns, and £-s-d reduction.

The data-bearing fixture is synthetic — built from the documented Yale column
labels — because the live backend served no rows during development (RECON.md).
The sentinel/empty cases below are taken verbatim from real responses observed.
"""

from imm_yale.parse import parse_response, rows_to_yields

# Verbatim from a live "no data" response.
NO_RECORDS_HTML = (
    "<html><body>There are no records matching your selection(s). "
    "Please try again</body></html>"
)

# Synthetic populated table using the documented column labels.
DATA_HTML = """
<html><body>
<table>
  <tr>
    <th>Year</th><th>Month</th>
    <th>YieldInvtLatePricePound</th>
    <th>YieldInvtLatePriceShilling</th>
    <th>YieldInvtLatePricePence</th>
    <th>PriceMonthLate</th>
  </tr>
  <tr><td>1911</td><td>7</td><td>4</td><td>3</td><td>6</td><td>95.5</td></tr>
  <tr><td>1911</td><td>8</td><td>4</td><td>10</td><td>0</td><td>94.0</td></tr>
</table>
</body></html>
"""


def test_no_records_sentinel():
    r = parse_response(NO_RECORDS_HTML)
    assert r.status == "no_records"
    assert not r.rows


def test_empty_body():
    r = parse_response("")
    assert r.status == "empty"


def test_populated_table_parses_by_header():
    r = parse_response(DATA_HTML)
    assert r.status == "ok"
    assert len(r.rows) == 2
    assert r.rows[0]["year"] == "1911"
    assert r.rows[0]["yield_pound"] == "4"
    assert r.rows[0]["price_late"] == "95.5"


def test_rows_to_yields_converts_lsd():
    r = parse_response(DATA_HTML)
    ys = rows_to_yields(r.rows)
    # £4 3s 6d = 4.175 ; £4 10s 0d = 4.5
    assert ys["1911-07"] == __import__("pytest").approx(4.175)
    assert ys["1911-08"] == __import__("pytest").approx(4.5)


def test_named_month_supported():
    html = DATA_HTML.replace("<td>7</td>", "<td>Jul</td>").replace("<td>8</td>", "<td>Aug</td>")
    ys = rows_to_yields(parse_response(html).rows)
    assert set(ys) == {"1911-07", "1911-08"}


def test_unknown_table_is_empty_status():
    html = "<table><tr><th>Foo</th><th>Bar</th></tr><tr><td>1</td><td>2</td></tr></table>"
    assert parse_response(html).status == "empty"
