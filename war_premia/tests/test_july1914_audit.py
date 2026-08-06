"""The bond-quote audit: the corrected July-1914 reading.

Confirms the two data-integrity findings that withdrew the earlier cross-section:
the June-3 baseline is ex-dividend, and the post-closure quotes are not genuine
(belligerent bonds 'rise' during the war). Runs against the mirrored workbook."""

import os

import pytest

import datetime

from war_premia.july1914 import (
    bond_feasibility,
    bond_quote_audit,
    short_rate_feasibility,
    war_week_bond_decline,
)

BONDS = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier",
                     "data", "longtermbonds.xls")
SHORT = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier",
                     "data", "stinterestrates.xls")

pytestmark = pytest.mark.skipif(
    not os.path.exists(BONDS), reason="mirrored bond workbook not present"
)


def test_consols_baseline_is_ex_dividend():
    audit = {a.sovereign: a for a in bond_quote_audit(BONDS)}
    c = audit["UK Consols 3%"]
    assert c.exdiv_flag is True
    # the coupon drop: cum-dividend Jun 2 is higher than ex-dividend Jun 3
    assert c.clean_pre > c.exdiv_pre


def test_belligerent_post_closure_quotes_are_not_genuine():
    audit = {a.sovereign: a for a in bond_quote_audit(BONDS)}
    for name in ("Russian 1822 5%", "Austrian Gold 4%", "Russian New 4%"):
        a = audit[name]
        assert a.genuine is False
        assert a.post_sept > a.post_stale   # rises during the war -> nominal


def test_prices_not_yields_magnitudes():
    # Values are par-relative prices (tens), not yields (single digits).
    for a in bond_quote_audit(BONDS):
        if a.clean_pre is not None:
            assert a.clean_pre > 60  # ~70s-120s, i.e. prices


def test_neither_asset_is_estimable():
    assert short_rate_feasibility(SHORT).estimable is False
    bf = bond_feasibility(BONDS)
    assert bf.estimable is False


def test_bonds_are_weekly_and_the_gap_is_the_closure_not_a_data_gap():
    # After the text-date parse fix the real gap is the 31 Jul -> 5 Aug closure
    # (5 days), NOT the old serial-only artifact of 63 days.
    bf = bond_feasibility(BONDS)
    assert bf.gap_across_crisis_days == 5
    assert "weekly" in bf.reason.lower()


def test_pre_closure_decline_is_observable_and_broad():
    decl = {w.sovereign: w for w in war_week_bond_decline(BONDS)}
    # The whole complex fell; Consols and the German/Austrian bonds all clearly down.
    for name in ("UK Consols 3%", "German Imperial 3%", "Austrian Gold 4%"):
        w = decl[name]
        assert w.pct_clean is not None and w.pct_clean < -3.0


def test_russian_31july_print_is_flagged_and_excluded_from_clean_decline():
    w = {x.sovereign: x for x in war_week_bond_decline(BONDS)}["Russian New 4%"]
    # 31 Jul carries a numeric footnote (col 14 = 1.0), so the clean decline
    # stops at the last unflagged quote (24 Jul), not the footnoted 31 Jul print.
    assert w.final_flagged is True
    assert w.last_clean_date == datetime.date(1914, 7, 24)
    assert -6.0 < w.pct_clean < -3.0   # ~-4.5%, not the raw -10%
