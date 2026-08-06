"""The Kokovtsov event test — asserts the runnable finding is stable.

Not synthetic: these assertions read the real recovered NW St Petersburg column.
"""

import datetime
import os

from war_premia.kokovtsov import EVENT_NS, kokovtsov_test

_DATA = os.path.join(os.path.dirname(__file__), "..", "..", "neal_weidenmier", "data")
SHORT = os.path.join(_DATA, "stinterestrates.xls")
BONDS = os.path.join(_DATA, "longtermbonds.xls")


def _res():
    return kokovtsov_test(SHORT, BONDS)


def test_bank_rate_is_flat_across_the_dismissal():
    res = _res()
    assert res.bracket, "no bank-rate observations bracket the event"
    # every weekly obs within +/-10 days of 12 Feb 1914 is the same 5.5%
    assert {o.value for o in res.bracket} == {5.5}


def test_the_event_sits_inside_a_long_plateau():
    p = _res().bank_plateau
    assert p is not None
    assert p.level == 5.5
    assert p.start <= EVENT_NS <= p.end
    # the plateau is long — it is not a coincidental one-week flat
    assert (p.end - p.start).days >= 300


def test_next_move_is_a_cut_after_the_event():
    p = _res().bank_plateau
    assert p.next_change_date is not None
    assert p.next_change_date > EVENT_NS          # after, not before
    assert p.next_change_level < p.level          # a cut, opposite sign to stress


def test_market_rate_is_missing_in_1914():
    res = _res()
    assert res.market_in_1914 is False
    assert res.market_last is not None and res.market_last.year <= 1900


def test_russian_bonds_are_weekly_and_span_the_event():
    bonds = {b.label: b for b in _res().bonds}
    assert bonds, "no Russian bond series loaded"
    for b in bonds.values():
        # quotes both before and after the event exist (it is bracketed)
        assert b.before is not None and b.after is not None
        # the +/-28-day window carries multiple weekly quotes, not one monthly point
        assert len(b.window) >= 5


def test_russian_bonds_are_flat_across_the_dismissal():
    bonds = {b.label: b for b in _res().bonds}
    for b in bonds.values():
        assert b.pct is not None
        assert abs(b.pct) < 1.0          # bracket move well under 1%
        assert b.within_normal is True   # within trailing-12-month weekly variation


def test_the_new_4pct_holds_89_across_four_weeks():
    b = {x.label: x for x in _res().bonds}["Russian New 4% (London)"]
    wk = {d: v for d, v in b.window}
    for day in (datetime.date(1914, 1, 30), datetime.date(1914, 2, 13),
                datetime.date(1914, 2, 20), datetime.date(1914, 2, 27)):
        assert wk[day] == 89.0
