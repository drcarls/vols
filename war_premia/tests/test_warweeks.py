"""War-week coding and event->week mapping."""

import datetime

from war_premia.warweeks import (
    CRISES,
    JULY_1914_EVENTS,
    get_crisis,
    nearest_week,
    war_mask,
)

D = datetime.date


def _saturdays(start: D, n: int):
    return [start + datetime.timedelta(days=7 * i) for i in range(n)]


def test_nearest_week_picks_closest_saturday():
    sats = _saturdays(D(1911, 6, 3), 10)  # weekly Saturdays
    # Agadir event 1911-07-01 is itself a Saturday in this grid.
    assert nearest_week(D(1911, 7, 1), sats) == D(1911, 7, 1)
    # A Wednesday maps to the nearest Saturday.
    assert nearest_week(D(1911, 7, 5), sats) in (D(1911, 7, 1), D(1911, 7, 8))


def test_war_mask_flags_event_weeks_only():
    sats = _saturdays(D(1911, 6, 3), 12)
    mask = war_mask(sats, [D(1911, 7, 1), D(1911, 8, 8)])
    flagged = [d for d, m in zip(sats, mask) if m]
    assert D(1911, 7, 1) in flagged
    assert sum(mask) == 2  # exactly the two event weeks


def test_war_mask_respects_max_gap():
    sats = _saturdays(D(1911, 6, 3), 4)
    # An event two months before any observation should flag nothing.
    assert sum(war_mask(sats, [D(1911, 1, 1)])) == 0


def test_all_crises_have_events_and_windows():
    for c in CRISES:
        lo, hi = c.window
        assert lo < hi
        assert c.war_events, f"{c.key} has no war weeks"
        # At least some coded war weeks fall inside the analysis window (the
        # First Moroccan window is the acute phase and omits the 1904 run-up).
        assert any(lo <= e <= hi for e in c.war_events), f"{c.key}: no war week in window"


def test_july1914_events_are_after_short_data_end():
    # Every July-1914 event is on/after Sarajevo (28 June 1914).
    assert min(JULY_1914_EVENTS) == D(1914, 6, 28)


def test_full_sample_unions_war_weeks():
    full = get_crisis("full")
    assert len(full.war_events) >= 20  # union across the four crises
