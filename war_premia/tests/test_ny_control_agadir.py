"""New York control for Agadir: descriptive seasonal-deviation check.

Pins the qualitative findings (no significance claims, matching the analysis):
New York shows no Agadir tightening and sits far below its own autumn seasonal
norm, while the continental deseasonalized signal is small (Paris the largest).
Skips if the short-rate workbook is absent.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ny_control_agadir as nc

pytestmark = pytest.mark.skipif(
    not os.path.exists(nc.SHORT), reason="short-rate workbook not present"
)


def _rows():
    from neal_weidenmier.load import load_short_rates, to_series_map
    return {r["label"]: r for r in nc.analyse(to_series_map(load_short_rates(nc.SHORT)))}


def test_new_york_does_not_tighten_and_falls_below_its_seasonal_norm():
    ny = _rows()["New York"]
    # never tightens meaningfully above its own norm...
    assert ny["peak_pos"]["dev"] < 0.6
    # ...and its largest move is a big NEGATIVE deviation (flat vs a seasonal spike)
    assert ny["peak_abs"]["dev"] < -2.0
    assert ny["dev_min"] < -2.0


def test_continental_tightening_is_small_relative_to_seasonal():
    rows = _rows()
    # Berlin's deseasonalized excess is modest and inside one baseline SD
    berlin = rows["Berlin"]
    assert berlin["peak_pos"]["dev"] < berlin["base_disp"]
    # Paris shows the largest genuine positive (Agadir) deviation of the four
    paris = rows["Paris"]
    assert paris["peak_pos"]["dev"] > berlin["peak_pos"]["dev"]
    assert paris["peak_pos"]["dev"] > rows["Amsterdam"]["peak_pos"]["dev"]


def test_neutral_reference_amsterdam_runs_below_norm():
    ams = _rows()["Amsterdam"]
    assert ams["dev_min"] < 0            # sits below its own seasonal baseline
    assert ams["peak_pos"]["dev"] < 0.3  # no meaningful tightening


def _contagion():
    from neal_weidenmier.load import load_short_rates, to_series_map
    return nc.contagion_1914(to_series_map(load_short_rates(nc.SHORT)))


@pytest.mark.skipif(not os.path.exists(nc.MONEY_CSV), reason="Chronicle money CSV absent")
def test_no_anticipation_june_1914_at_or_below_norm():
    june = _contagion()["june_dev"]
    # nobody was pricing the war on the eve of Sarajevo; Berlin actually easy
    assert june["Berlin"] < -0.5
    assert all(june[c] < 0.3 for c in ("New York", "Berlin", "Amsterdam"))


@pytest.mark.skipif(not os.path.exists(nc.MONEY_CSV), reason="Chronicle money CSV absent")
def test_ny_sign_flips_positive_in_july_1914():
    c = _contagion()
    ny_agadir = _rows()["New York"]["peak_abs"]["dev"]
    assert ny_agadir < -2.0              # Agadir: NY well BELOW its norm (insulated)
    assert c["ny_norm"] < 3.0            # quiet-summer seasonal norm
    assert c["ny_high"] >= 7.0           # outbreak spike (Chronicle 1914-08-01)
    assert c["flip_high"] > 4.0          # July 1914: strongly ABOVE norm -> sign flip
