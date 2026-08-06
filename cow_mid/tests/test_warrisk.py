"""Continuous great-power war-risk series."""

import csv
import datetime

from cow_mid.parse import Dispute
from cow_mid.warrisk import (
    pseudo_probability,
    war_risk_series,
    write_long_csv,
)

D = datetime.date


def _disputes():
    return {
        # Agadir: Germany vs France+UK (great powers both sides), display (3).
        "315": Dispute("315", D(1911, 7, 1), D(1911, 10, 1), 3, 0, [255], [220, 200]),
        # July 1914: war (5), great powers both sides.
        "257": Dispute("257", D(1914, 7, 23), D(1918, 11, 11), 5, 6, [300, 255], [365, 220]),
        # Colonial: France vs a non-great-power (600) — great power only one side.
        "86": Dispute("86", D(1907, 3, 25), D(1907, 4, 1), 4, None, [220], [600]),
    }


def test_both_sides_ignores_colonial_and_lights_up_confrontations():
    s = war_risk_series(_disputes(), D(1907, 1, 1), D(1914, 12, 31), both_sides=True)
    by = {p.date: p for p in s}
    # A week inside Agadir -> hostlev 3.
    wk_agadir = next(p for p in s if D(1911, 7, 1) <= p.date <= D(1911, 9, 1))
    assert wk_agadir.max_hostlev == 3 and "315" in wk_agadir.dispnums
    # A week inside July 1914 -> hostlev 5.
    wk_war = next(p for p in s if D(1914, 8, 1) <= p.date <= D(1914, 9, 1))
    assert wk_war.max_hostlev == 5
    # The colonial dispute (one-sided) never contributes under both_sides.
    assert all("86" not in p.dispnums for p in s)


def test_any_side_includes_colonial():
    s = war_risk_series(_disputes(), D(1907, 1, 1), D(1907, 12, 31), both_sides=False)
    wk = next(p for p in s if D(1907, 3, 25) <= p.date <= D(1907, 4, 1))
    assert wk.max_hostlev == 4 and "86" in wk.dispnums


def test_quiet_weeks_are_zero():
    s = war_risk_series(_disputes(), D(1909, 1, 1), D(1909, 12, 31), both_sides=True)
    assert all(p.max_hostlev == 0 and p.n_active == 0 for p in s)


def test_pseudo_probability_monotone():
    assert pseudo_probability(0) == 0.0
    assert pseudo_probability(3) < pseudo_probability(4) < pseudo_probability(5)
    assert pseudo_probability(5) == 1.0


def test_write_long_csv_two_series(tmp_path):
    s = war_risk_series(_disputes(), D(1911, 1, 1), D(1911, 12, 31), both_sides=True)
    out = tmp_path / "wr.csv"
    n = write_long_csv(s, str(out))
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert n == len(rows)
    assert {r["series"] for r in rows} == {"war_risk", "war_risk_pprob"}
    # every value parses as a number; dates are ISO
    for r in rows:
        float(r["value"])
        assert r["date"].count("-") == 2
