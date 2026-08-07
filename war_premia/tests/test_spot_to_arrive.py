"""Chapter-III check: Berlin's autumn spot-vs-to-arrive gap, from the C&F Chronicle.

The WEEKLY panel overturns the single-snapshot result: 1910 (a war-free firm autumn)
carries the same +0.5 gap as 1911 in the weeks flanking its one 'for both' reading,
so the gap is a quarter-end forward premium, not an Agadir fingerprint. These tests
pin the corrected finding (and keep the raw snapshot/crisis facts as data).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import spot_to_arrive as sta

pytestmark = pytest.mark.skipif(not os.path.exists(sta.CSV), reason="gap CSV absent")


# --- the raw single-snapshot facts (still true for those specific Oct-1 weeks) -----

def test_snapshot_1911_shows_a_gap():
    y1911 = next(r for r in sta.load() if r["year"] == 1911)
    assert y1911["gap"] == 0.5                       # spot 4.0, to-arrive 4.5


def test_every_figure_carries_a_source_quote():
    for r in sta.load():
        assert r["source_quote"].strip()
        assert r["issue"].startswith("cfc_1")


# --- the weekly panel, which OVERTURNS the snapshot ------------------------------

@pytest.mark.skipif(not os.path.exists(sta.WEEKLY_CSV), reason="weekly CSV absent")
def test_weekly_1910_also_carries_the_gap():
    mx = sta.weekly_max_gap_by_year(sta.load_weekly())
    # a war-FREE firm autumn shows a gap at least as large as Agadir's
    assert mx[1910] >= 0.5
    assert mx[1910] >= mx[1911] - 0.001


@pytest.mark.skipif(not os.path.exists(sta.WEEKLY_CSV), reason="weekly CSV absent")
def test_weekly_verdict_is_not_unusual():
    is_unusual, mx = sta.verdict(sta.load_weekly())
    assert is_unusual is False                       # the snapshot 'uniqueness' does not survive


@pytest.mark.skipif(not os.path.exists(sta.WEEKLY_CSV), reason="weekly CSV absent")
def test_weekly_easy_money_years_have_no_gap():
    mx = sta.weekly_max_gap_by_year(sta.load_weekly())
    assert mx[1908] == 0.0 and mx[1909] == 0.0       # easy money -> no forward premium


@pytest.mark.skipif(not os.path.exists(sta.WEEKLY_CSV), reason="weekly CSV absent")
def test_weekly_every_obs_has_a_quote():
    for r in sta.load_weekly():
        assert r["source_quote"].strip()
        assert r["issue"].startswith("cfc_1")


# --- cross-crisis weeks: real facts for those specific weeks ---------------------

@pytest.mark.skipif(not os.path.exists(sta.CRISES_CSV), reason="crises CSV absent")
def test_crisis_week_snapshots():
    berlin = {r["crisis"]: r for r in sta.load_crises() if r["centre"] == "Berlin"}
    # Bosnian (easy money) and Balkan-winter ('for both') crisis weeks show no gap
    assert berlin["Bosnian annexation"]["gap"] == 0.0
    assert berlin["Balkan winter"]["gap"] == 0.0


@pytest.mark.skipif(not os.path.exists(sta.CRISES_CSV), reason="crises CSV absent")
def test_only_london_and_berlin_ever_split():
    # the crises CSV only carries London/Berlin because Vienna/Paris/Amsterdam/Brussels
    # are quoted as single rates throughout -- they never split spot vs to-arrive
    centres = {r["centre"] for r in sta.load_crises()}
    assert centres == {"Berlin", "London"}
