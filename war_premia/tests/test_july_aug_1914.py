"""The descriptive July-Aug 1914 money-market series (from the Chronicle).

These are hand-read from OCR'd primary source; each row carries its source quote.
The test guards structure and the headline figures, not a model."""

import csv
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "july_aug_1914_money.csv")


def _rows():
    with open(DATA, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_every_figure_has_a_source_quote():
    for r in _rows():
        assert r["source_quote"].strip(), f"{r['series']} {r['week_ending']} missing source quote"
        assert r["issue"].startswith("cfc_1914")


def test_bank_of_england_spike_trajectory():
    boe = {r["week_ending"]: r["value"] for r in _rows() if r["series"] == "bank_of_england_rate"}
    # 3% through July -> 4 -> 8 -> 10 (peak) -> 6
    assert boe["1914-07-25"] == "3.0"
    assert boe["1914-07-30"] == "4.0"
    assert boe["1914-08-01"] == "8.0"
    assert boe["1914-08-03"] == "10.0"


def test_london_bills_calm_then_frozen():
    bills = {r["week_ending"]: r["value"] for r in _rows() if r["series"] == "london_3mo_bank_bills"}
    assert float(bills["1914-07-11"]) == 2.375           # calm summer firming
    assert bills["1914-08-01"] == ""                      # market froze (LSE closed)


def test_values_parse_or_are_blank():
    for r in _rows():
        if r["value"]:
            float(r["value"])
