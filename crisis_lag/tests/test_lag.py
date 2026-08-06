from datetime import date

from conftest import make_obs

from crisis_lag.events import CrisisEvent
from crisis_lag.lag import measure_lag
from crisis_lag.stress import baseline_for


ONSET = date(1911, 7, 1)
EVENT = CrisisEvent(name="test", onset="1911-07-01", series="germany",
                    binding_power="Germany", search_days=180)


def test_recovers_injected_peak_lag():
    obs = make_obs(ONSET, lag_days=63)  # 9-week peak
    r = measure_lag(obs, EVENT)
    assert r.status == "ok"
    assert r.lag_to_peak_days == 63
    assert abs(r.lag_to_peak_weeks - 9.0) < 1e-9
    assert abs(r.peak_value - 350.0) < 1e-6  # base 200 + peak_add 150


def test_material_stress_is_earlier_than_peak():
    obs = make_obs(ONSET, lag_days=63)
    r = measure_lag(obs, EVENT, z_threshold=2.0)
    # First post-onset point already clears z=2 given the small baseline sd.
    assert r.lag_to_material_days is not None
    assert r.lag_to_material_days <= r.lag_to_peak_days


def test_baseline_drawn_before_onset():
    obs = make_obs(ONSET, lag_days=63)
    b = baseline_for(obs, EVENT)
    assert b is not None
    assert b.end < ONSET  # strictly pre-onset
    assert abs(b.mean - 200.0) < 2.0
    assert b.sd > 0


def test_censored_event_not_measured():
    ev = CrisisEvent(name="July_1914", onset="1914-07-23", series="austria_hungary",
                     binding_power="Austria", measurable=False, decision_window_days=5)
    r = measure_lag([], ev)
    assert r.status == "censored"
    assert r.measurable is False
    assert r.decision_window_days == 5
    assert abs(r.decision_window_weeks - 5 / 7) < 1e-9


def test_no_baseline_when_window_empty():
    # All observations sit after onset -> empty baseline window.
    obs = make_obs(ONSET, lag_days=63, before_days=0)
    r = measure_lag(obs, EVENT)
    assert r.status == "no_baseline"


def test_peak_is_maximum_not_last():
    obs = make_obs(ONSET, lag_days=42)  # peak at 6 weeks, then declines
    r = measure_lag(obs, EVENT)
    assert r.lag_to_peak_days == 42
    # The series continues past the peak, so peak != final observation.
    assert r.peak_date == "1911-08-12"
