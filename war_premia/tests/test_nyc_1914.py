"""The NYC 1914 bond panel (Chronicle) — every figure sourced to an OCR quote."""

import csv
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "nyc_1914_bonds.csv")


def _rows():
    with open(DATA, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_every_figure_has_a_source_quote_and_issue():
    for r in _rows():
        assert r["source_quote"].strip(), f"{r['bond']} missing source quote"
        assert r["issue"] in ("cfc_19140801", "cfc_19141205")


def test_reopening_high_grades_are_near_par():
    reop = {r["bond"]: r for r in _rows() if r["phase"].startswith("reopening")}
    steel = reop["US Steel s f g 5s 1963"]
    assert 99.0 <= float(steel["low"]) <= 101.0 and float(steel["high"]) <= 101.0
    rubber = reop["US Rubber 10-yr coll tr 6s 1918"]
    assert float(rubber["low"]) > 100.0   # above par


def test_pre_closure_us_governments_present():
    pre = {r["bond"]: r for r in _rows() if r["phase"] == "pre_closure"}
    assert "97" in pre["US Government 2s (coupon)"]["source_quote"]
    assert float(pre["US Government Panama 3s (coupon)"]["last_or_sale"]) == 101.75


def test_actual_first_day_trade_is_recorded():
    sale = [r for r in _rows() if r["phase"] == "reopening_sale"][0]
    assert "Nov. 28" in sale["source_quote"]
    assert 98.0 <= float(sale["last_or_sale"]) <= 98.5


def test_numeric_fields_parse():
    for r in _rows():
        for f in ("low", "high", "last_or_sale"):
            if r[f]:
                float(r[f])
