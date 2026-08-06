"""FRED CSV parsing — pure, offline (real CSV shape, no network)."""

from fred_nber.client import parse_csv

SAMPLE = (
    "observation_date,M13027FRM156NNBR\n"
    "1911-06-01,3.79\n"
    "1911-07-01,3.80\n"
    "1911-08-01,.\n"          # documented gap -> dropped
    "1911-09-01,3.82\n"
)


def test_parse_basic():
    ys = parse_csv(SAMPLE)
    assert ys["1911-06"] == 3.79
    assert ys["1911-07"] == 3.80
    assert ys["1911-09"] == 3.82


def test_missing_value_dropped_not_imputed():
    ys = parse_csv(SAMPLE)
    assert "1911-08" not in ys


def test_month_key_is_yyyy_mm():
    ys = parse_csv(SAMPLE)
    assert all(len(k) == 7 and k[4] == "-" for k in ys)


def test_empty_and_headise_only():
    assert parse_csv("observation_date,X\n") == {}
    assert parse_csv("") == {}
