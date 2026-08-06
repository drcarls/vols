"""The bond-quote audit: the corrected July-1914 reading.

Confirms the two data-integrity findings that withdrew the earlier cross-section:
the June-3 baseline is ex-dividend, and the post-closure quotes are not genuine
(belligerent bonds 'rise' during the war). Runs against the mirrored workbook."""

import os

import pytest

from war_premia.july1914 import (
    bond_feasibility,
    bond_quote_audit,
    short_rate_feasibility,
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
    assert bf.gap_across_crisis_days == 63   # 1914-06-03 -> 1914-08-05
