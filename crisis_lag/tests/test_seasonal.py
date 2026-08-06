"""Seasonal (control-year) baseline: the fix for autumn-tightening false signals."""

from datetime import date

from crisis_lag.events import CrisisEvent
from crisis_lag.lag import measure_all, measure_lag
from crisis_lag.seasonal import (
    crisis_years,
    deseasonalize,
    seasonal_index,
    unit_key,
)


def test_unit_key_month_and_week():
    assert unit_key(date(1911, 7, 1), "month") == 7
    assert unit_key(date(1911, 1, 3), "week") == date(1911, 1, 3).isocalendar()[1]


def test_crisis_years_from_onsets():
    assert crisis_years(["1911-07-01", "1914-07-23", "bad"]) == {1911, 1914}


def test_seasonal_index_excludes_crisis_years():
    obs = [
        (date(1910, 3, 1), 2.0), (date(1910, 10, 1), 4.0),   # control year
        (date(1911, 3, 1), 9.0), (date(1911, 10, 1), 9.0),   # crisis year, excluded
        (date(1912, 3, 1), 2.0), (date(1912, 10, 1), 4.0),   # control year
    ]
    idx = seasonal_index(obs, exclude_years=frozenset({1911}), unit="month")
    assert idx[3] == 2.0   # mean of control-year Marches
    assert idx[10] == 4.0  # mean of control-year Octobers (1911 excluded)


def test_deseasonalize_subtracts_norm_and_drops_unknown_units():
    obs = [(date(1911, 3, 1), 5.0), (date(1911, 8, 1), 7.0)]
    idx = {3: 2.0}  # no August norm
    out = deseasonalize(obs, idx, unit="month")
    assert out == [(date(1911, 3, 1), 3.0)]  # August dropped (undefined norm)


def _seasonal_series(years, spring, autumn):
    """A series with only a seasonal pattern: `spring` in Mar, `autumn` in Oct."""
    obs = []
    for y in years:
        obs.append((date(y, 3, 15), spring))
        obs.append((date(y, 10, 15), autumn))
    return obs


def test_pure_seasonality_yields_no_stress_after_adjustment():
    # Every year: calm 2.0 in spring, tighten to 6.0 in autumn — NO real crisis.
    obs = _seasonal_series(range(1905, 1915), 2.0, 6.0)
    smap = {"germany": sorted(obs)}
    ev = CrisisEvent(name="Agadir", onset="1911-07-01", series="germany",
                     binding_power="Germany", search_days=180)

    # Raw: the autumn value looks like a big peak above the spring baseline.
    raw = measure_lag(smap["germany"], ev)
    assert raw.status == "ok" and raw.peak_value is not None
    assert raw.peak_value > 3.0  # a spurious "spike" from seasonality

    # Seasonal: deseasonalised, the autumn value equals its norm -> no abnormal stress.
    seas = measure_all(smap, [ev], seasonal=True)[0]
    # peak abnormal stress is ~0 (value minus its own seasonal norm minus baseline)
    assert abs(seas.peak_value or 0.0) < 1e-9


def test_seasonal_is_noop_when_flat():
    # A flat series has a flat seasonal index; results match the plain method.
    obs = [(date(y, m, 15), 3.0) for y in range(1905, 1915) for m in range(1, 13)]
    smap = {"germany": sorted(obs)}
    ev = CrisisEvent(name="X", onset="1911-07-01", series="germany",
                     binding_power="Germany")
    plain = measure_all(smap, [ev])[0]
    seas = measure_all(smap, [ev], seasonal=True)[0]
    assert plain.status == seas.status == "ok"
    # A flat series carries no abnormal stress either way: same peak lag, and
    # neither crosses the material threshold.
    assert plain.lag_to_peak_days == seas.lag_to_peak_days
    assert plain.lag_to_material_days is None and seas.lag_to_material_days is None
