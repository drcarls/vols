"""The Kokovtsov event test — asserts the runnable finding is stable.

Not synthetic: these assertions read the real recovered NW St Petersburg column.
"""

import datetime
import os

from war_premia.kokovtsov import EVENT_NS, kokovtsov_test

SHORT = os.path.join(
    os.path.dirname(__file__), "..", "..", "neal_weidenmier", "data", "stinterestrates.xls"
)


def _res():
    return kokovtsov_test(SHORT)


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
