"""Estimator arithmetic — exact recoveries and IV mechanics."""

import math

from war_premia.estimator import estimate, first_diff, iv_single, iv_two


def test_single_iv_recovers_exact_beta():
    # If dx = beta*dy exactly, the just-identified IV returns beta with 0 residual.
    dy = [1.0, -2.0, 0.5, -0.3, 2.0, -1.0]
    beta = 0.46
    dx = [beta * y for y in dy]
    war = [True, True, False, False, True, False]
    r = iv_single(dx, dy, [1 if w else -1 for w in war])
    assert abs(r.beta - beta) < 1e-9
    assert r.n == 6 and r.n_war == 3


def test_two_iv_recovers_exact_beta():
    dy = [1.0, -2.0, 0.5, -0.3, 2.0, -1.0, 0.8]
    beta = -0.3
    dx = [beta * y for y in dy]
    sign = [1, 1, -1, -1, 1, -1, -1]
    r = iv_two(dx, dy, sign)
    assert abs(r.beta - beta) < 1e-9


def test_heteroskedasticity_identifies_over_confounded_ols():
    # Common factor f loads on both; f has big variance on war weeks, tiny off.
    # The idiosyncratic shock in x is CONSTANT within each +/- factor pair, so it
    # is orthogonal to the instrument w = sign*dy (sum w_i*idio_i = 0) and cancels
    # in the IV even though it perturbs the fit (residual != 0).
    f = [3.0, -3.0, 2.5, -2.5, 0.2, -0.2, 0.1, -0.1]
    war = [True, True, True, True, False, False, False, False]
    beta = 0.7
    idio = [0.5, 0.5, 0.4, 0.4, 0.3, 0.3, 0.2, 0.2]  # constant within each pair
    dy = list(f)
    dx = [beta * fi + ii for fi, ii in zip(f, idio)]
    r = estimate(dx, dy, war, two_instrument=False)
    assert abs(r.beta - beta) < 1e-9   # recovered despite the noise OLS would absorb


def test_estimate_dispatch_and_signs():
    # War weeks carry the larger variance (as the method requires), so w'dy != 0.
    dy = [2.0, -2.0, 0.5, -0.5]
    dx = [0.5 * y for y in dy]
    war = [True, True, False, False]
    assert abs(estimate(dx, dy, war).beta - 0.5) < 1e-9


def test_first_diff():
    dates, deltas = first_diff([("a", 1.0), ("b", 1.5), ("c", 1.2)])
    assert dates == ["b", "c"]
    assert deltas == [0.5, -0.30000000000000004] or all(
        abs(d - e) < 1e-9 for d, e in zip(deltas, [0.5, -0.3])
    )
