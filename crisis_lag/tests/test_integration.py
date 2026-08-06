"""End-to-end: synthetic multi-crisis dataset -> measure_all -> adjudicate.

Builds three comparators with peaks at 7/8/9 weeks plus a censored July 1914,
and checks the whole chain reports CORROBORATED — and that a single fast-peaking
crisis flips it to FALSIFIED.
"""

from datetime import date

from conftest import make_obs

from crisis_lag.events import CrisisEvent
from crisis_lag.lag import measure_all
from crisis_lag.report import CORROBORATED, FALSIFIED, adjudicate
from crisis_lag.series import rows_to_series


EVENTS = [
    CrisisEvent(name="Agadir_1911", onset="1911-07-01", series="germany",
                binding_power="Germany"),
    CrisisEvent(name="Bosnia_1908", onset="1908-10-06", series="russia",
                binding_power="Russia", search_days=210),
    CrisisEvent(name="Balkans_1912", onset="1912-10-08", series="austria_hungary",
                binding_power="Austria", search_days=300),
    CrisisEvent(name="July_1914", onset="1914-07-23", series="austria_hungary",
                binding_power="Austria", measurable=False, decision_window_days=5),
]


def _dataset(balkan_lag_days=56):
    return {
        "germany": make_obs(date(1911, 7, 1), lag_days=63),   # 9 wk
        "russia": make_obs(date(1908, 10, 6), lag_days=49),   # 7 wk
        "austria_hungary": make_obs(date(1912, 10, 8), lag_days=balkan_lag_days),
    }


def test_full_chain_corroborated():
    results = measure_all(_dataset(balkan_lag_days=56), EVENTS)  # 8 wk
    by_name = {r.name: r for r in results}
    assert by_name["Agadir_1911"].lag_to_peak_weeks == 9.0
    assert by_name["Bosnia_1908"].lag_to_peak_weeks == 7.0
    assert by_name["July_1914"].status == "censored"
    v = adjudicate(results)
    assert v.verdict == CORROBORATED
    assert v.n_comparators == 3


def test_full_chain_falsified_by_fast_crisis():
    # Austria-Hungary peaks in 1 week -> mechanism unsupported.
    results = measure_all(_dataset(balkan_lag_days=7), EVENTS)
    v = adjudicate(results)
    assert v.verdict == FALSIFIED


def test_missing_series_reported_not_crashed():
    data = {"germany": make_obs(date(1911, 7, 1), lag_days=63)}  # russia/austria absent
    results = measure_all(data, EVENTS)
    statuses = {r.name: r.status for r in results}
    assert statuses["Bosnia_1908"] == "no_data"
    assert statuses["Agadir_1911"] == "ok"


def test_rows_to_series_parsing():
    rows = [
        {"date": "1911-07-01", "series": "germany", "value": "210.0"},
        {"date": "1911-06-01", "series": "germany", "value": ""},      # blank dropped
        {"date": "bad", "series": "germany", "value": "5"},            # bad date dropped
        {"date": "1911-05-01", "series": "germany", "value": "x"},     # bad value dropped
    ]
    s = rows_to_series(rows)
    assert [d.isoformat() for d, _ in s["germany"]] == ["1911-07-01"]
