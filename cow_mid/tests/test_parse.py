"""Pure MIDA+MIDB join logic, tested without the CSV files."""

import datetime

from cow_mid.parse import join_disputes

MIDA = [
    {"dispnum": "315", "styear": "1911", "stmon": "7", "stday": "1",
     "endyear": "1911", "endmon": "10", "endday": "-9", "hostlev": "3", "fatality": "0"},
    {"dispnum": "257", "styear": "1914", "stmon": "7", "stday": "23",
     "endyear": "1918", "endmon": "11", "endday": "11", "hostlev": "5", "fatality": "6"},
    {"dispnum": "30", "styear": "1908", "stmon": "10", "stday": "6",
     "endyear": "1909", "endmon": "3", "endday": "-9", "hostlev": "4", "fatality": "-9"},
]
MIDB = [
    {"dispnum": "315", "ccode": "255", "sidea": "1"},   # Germany
    {"dispnum": "315", "ccode": "220", "sidea": "0"},   # France
    {"dispnum": "315", "ccode": "200", "sidea": "0"},   # UK
    {"dispnum": "30", "ccode": "345", "sidea": "1"},    # Serbia
    {"dispnum": "30", "ccode": "300", "sidea": "0"},    # Austria-Hungary
]


def test_join_dates_and_hostlev():
    d = join_disputes(MIDA, MIDB)
    assert d["315"].onset == datetime.date(1911, 7, 1)
    assert d["315"].hostlev == 3 and d["315"].hostlev_label == "display of force"
    assert d["257"].onset == datetime.date(1914, 7, 23)
    assert d["257"].hostlev_label == "war"


def test_missing_day_falls_back_to_first():
    # endday -9 -> day 1
    d = join_disputes(MIDA, MIDB)
    assert d["315"].end == datetime.date(1911, 10, 1)


def test_sides_and_names():
    d = join_disputes(MIDA, MIDB)["315"]
    assert d.side_a == [255] and set(d.side_b) == {220, 200}
    assert d.names(d.side_a) == ["Germany"]
    assert set(d.names(d.side_b)) == {"France", "UK"}


def test_fatality_missing_is_none():
    d = join_disputes(MIDA, MIDB)
    assert d["30"].fatality is None   # "-9" -> None
    assert d["257"].fatality == 6


def test_dispute_without_participants_still_parses():
    d = join_disputes([MIDA[0]], [])  # no MIDB rows
    assert d["315"].side_a == [] and d["315"].onset == datetime.date(1911, 7, 1)
