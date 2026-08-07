"""Pins the Chapter-III check: Berlin's autumn spot-vs-to-arrive gap, 1908-1913.

The decision-relevant facts, read from the Commercial & Financial Chronicle:
1911 is the sole autumn with a spot/to-arrive gap; 1910 (a firmer autumn in level)
shows none, so the gap is not a rate-level artifact.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import spot_to_arrive as sta

pytestmark = pytest.mark.skipif(not os.path.exists(sta.CSV), reason="gap CSV absent")


def test_1911_is_the_only_autumn_with_a_gap():
    rows = sta.load()
    y1911 = next(r for r in rows if r["year"] == 1911)
    assert y1911["gap"] == 0.5                       # spot 4.0, to-arrive 4.5
    others = [r for r in rows if r["year"] != 1911]
    assert all(r["gap"] <= 0.125 for r in others)    # no other autumn shows a real gap


def test_1910_is_the_level_control_firmer_yet_flat():
    rows = {r["year"]: r for r in sta.load()}
    # 1910 was FIRMER in level than 1911 (4.5% vs 4.0% spot) yet had ZERO gap
    assert rows[1910]["spot"] == 4.5
    assert rows[1910]["spot"] > rows[1911]["spot"]
    assert rows[1910]["gap"] == 0.0


def test_verdict_is_unusual():
    is_unusual, y1911, _ = sta.verdict(sta.load())
    assert is_unusual is True
    assert y1911["explicit_split"] == "yes_gap"


def test_every_figure_carries_a_source_quote():
    for r in sta.load():
        assert r["source_quote"].strip()             # no figure without its Chronicle quote
        assert r["issue"].startswith("cfc_1")


@pytest.mark.skipif(not os.path.exists(sta.CRISES_CSV), reason="crises CSV absent")
def test_gap_is_agadir_specific_across_crises():
    rows = sta.load_crises()
    berlin = {r["crisis"]: r for r in rows if r["centre"] == "Berlin"}
    assert berlin["Agadir"]["gap"] == 0.5            # Berlin splits only in Agadir
    assert berlin["Bosnian annexation"]["gap"] == 0.0
    assert berlin["Balkan winter"]["gap"] == 0.0


@pytest.mark.skipif(not os.path.exists(sta.CRISES_CSV), reason="crises CSV absent")
def test_balkan_winter_is_tighter_yet_flat():
    rows = sta.load_crises()
    berlin = {r["crisis"]: r for r in rows if r["centre"] == "Berlin"}
    # Dec-1912 Berlin was TIGHTER in level than Agadir yet showed no gap -> not a level effect
    assert berlin["Balkan winter"]["spot"] > berlin["Agadir"]["spot"]
    assert berlin["Balkan winter"]["gap"] == 0.0


@pytest.mark.skipif(not os.path.exists(sta.CRISES_CSV), reason="crises CSV absent")
def test_london_forward_premium_widest_in_agadir():
    rows = sta.load_crises()
    london = {r["crisis"]: r for r in rows if r["centre"] == "London"}
    assert london["Agadir"]["gap"] > london["Balkan winter"]["gap"]
    assert london["Agadir"]["gap"] > london["Bosnian annexation"]["gap"]
