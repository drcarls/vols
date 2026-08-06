"""Pure grid->series logic, tested on a synthetic grid shaped like the HFS sheet."""

import datetime

from hfs_rates.parse import find_column, grid_to_series, parse_gregorian

# A miniature of the "Market rates--daily" sheet: header block (label in col D)
# then dated rows (Gregorian date in col D, rates in the country columns).
GRID = [
    ["Market interest rates", None, None, None, None, None],
    ["", None, None, None, None, None],
    [None, None, None, "Country", "Germany", "United Kingdom"],
    [None, None, None, "Category", "Interest rates", "Interest rates"],
    [None, None, None, "Series", "Berlin open market rate", "bank bills, 90 days, bid"],
    [None, None, None, "Unit", "Percent", "Percent"],
    ["Sat", None, "1911.06.24", "1911.07.01", 3.50, 3.00],
    ["Sat", None, "1911.07.01", "1911.07.08", 2.50, 2.75],
    ["Sat", None, "1899.12.30", "1899.12.31", 9.99, 9.99],  # out of range
    ["Sat", None, "bad", "not-a-date", 1.0, 1.0],           # undated -> skipped
]


def test_parse_gregorian():
    assert parse_gregorian("1911.07.01") == datetime.date(1911, 7, 1)
    assert parse_gregorian("bad") is None
    assert parse_gregorian(None) is None
    assert parse_gregorian("1911.13.40") is None


def test_find_column_by_country_and_series():
    assert find_column(GRID, "Germany", "open market rate") == 4
    assert find_column(GRID, "United Kingdom", "bank bills, 90 days, bid") == 5
    assert find_column(GRID, "France", "open market rate") is None


def test_grid_to_series_extracts_dated_rates_in_range():
    de = grid_to_series(GRID, "Germany", "open market rate")
    assert de == {
        datetime.date(1911, 7, 1): 3.50,
        datetime.date(1911, 7, 8): 2.50,
    }


def test_grid_to_series_respects_year_bounds():
    de = grid_to_series(GRID, "Germany", "open market rate", start_year=1912)
    assert de == {}


def test_grid_to_series_missing_column_is_empty():
    assert grid_to_series(GRID, "Russia", "open market rate") == {}
