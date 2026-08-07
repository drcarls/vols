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
