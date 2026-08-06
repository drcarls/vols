from crisis_lag.lag import LagResult
from crisis_lag.report import (
    CORROBORATED,
    FALSIFIED,
    INCONCLUSIVE,
    adjudicate,
    format_table,
    format_verdict,
)


def _comparator(name, lag_weeks):
    return LagResult(
        name=name, series="x", onset="1911-07-01", measurable=True, status="ok",
        lag_to_peak_days=int(round(lag_weeks * 7)),
        lag_to_material_days=int(round(lag_weeks * 7)),
    )


def _july_1914(window_days=5):
    return LagResult(
        name="July_1914", series="austria_hungary", onset="1914-07-23",
        measurable=False, status="censored", decision_window_days=window_days,
    )


def test_corroborated_when_lags_in_band_and_1914_short():
    results = [_comparator("a", 7), _comparator("b", 8), _comparator("c", 9), _july_1914()]
    v = adjudicate(results)
    assert v.verdict == CORROBORATED
    assert v.n_in_band == 3
    assert v.decision_window_weeks < 1


def test_falsified_when_a_comparator_peaks_in_days():
    # One crisis peaked in 1 week -> the brake could have bitten in 5 days.
    results = [_comparator("a", 8), _comparator("b", 1), _july_1914()]
    v = adjudicate(results)
    assert v.verdict == FALSIFIED
    assert v.min_lag_weeks == 1.0


def test_inconclusive_when_out_of_band_but_above_floor():
    results = [_comparator("a", 3), _comparator("b", 4), _comparator("c", 5), _july_1914()]
    v = adjudicate(results)
    assert v.verdict == INCONCLUSIVE


def test_inconclusive_when_no_comparators():
    v = adjudicate([_july_1914()])
    assert v.verdict == INCONCLUSIVE
    assert v.n_comparators == 0


def test_band_is_configurable():
    results = [_comparator("a", 3), _comparator("b", 4), _july_1914()]
    v = adjudicate(results, band_lo_weeks=2, band_hi_weeks=5)
    assert v.verdict == CORROBORATED


def test_format_helpers_return_strings():
    results = [_comparator("a", 8), _july_1914()]
    v = adjudicate(results)
    tbl = format_table(results)
    assert "crisis" in tbl and "July_1914" in tbl
    txt = format_verdict(v)
    assert "VERDICT:" in txt
