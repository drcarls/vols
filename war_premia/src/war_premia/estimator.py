"""Rigobon-Sack identification-by-heteroskedasticity, IV form (pure Python).

Reproduces the estimator in Carls (2005). War risk is an unobserved common factor
whose variance is elevated on "war weeks"; it biases OLS of one asset's change on
another's. Identification splits the sample into war / non-war regimes.

For a basis asset return Δy (the London 3-month trade bill) and a target asset
return Δx, regress Δx on Δy using an instrument built from the regime sign:

    w_t = s_t · Δy_t ,   s_t = +1 on war weeks, -1 on non-war weeks

The just-identified IV coefficient is β = Σ(w·Δx) / Σ(w·Δy), which equals the
heteroskedasticity estimator (Cov_war − Cov_nonwar)/(Var_war − Var_nonwar). Carls
also reports a two-instrument (2SLS) variant adding z_t = s_t · Δx_t.

No matrix library: the single-instrument case is scalar sums; the 2SLS case needs
only a 2×2 inverse, done by hand.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class IVResult:
    beta: float
    t_stat: float
    n: int
    n_war: int


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def iv_single(dx: Sequence[float], dy: Sequence[float], sign: Sequence[int]) -> IVResult:
    """Just-identified IV with the London-basis instrument w = sign·Δy."""
    n = len(dx)
    w = [s * y for s, y in zip(sign, dy)]
    wdy = _dot(w, dy)
    if wdy == 0:
        return IVResult(float("nan"), float("nan"), n, sum(1 for s in sign if s > 0))
    beta = _dot(w, dx) / wdy
    resid = [x - beta * y for x, y in zip(dx, dy)]
    dof = max(n - 1, 1)
    sigma2 = _dot(resid, resid) / dof
    var_beta = sigma2 * _dot(w, w) / (wdy * wdy)
    t = beta / math.sqrt(var_beta) if var_beta > 0 else float("nan")
    return IVResult(beta, t, n, sum(1 for s in sign if s > 0))


def _inv2(m: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    a, b, c, d = m
    det = a * d - b * c
    if det == 0:
        raise ZeroDivisionError("singular 2x2")
    return (d / det, -b / det, -c / det, a / det)


def iv_two(dx: Sequence[float], dy: Sequence[float], sign: Sequence[int]) -> IVResult:
    """2SLS with two instruments: w = sign·Δy and z = sign·Δx."""
    n = len(dx)
    w = [s * y for s, y in zip(sign, dy)]
    z = [s * x for s, x in zip(sign, dx)]
    # Z'Z (2x2), Z'X where X = dy (2x1)
    ZtZ = (_dot(w, w), _dot(w, z), _dot(z, w), _dot(z, z))
    ZtX = (_dot(w, dy), _dot(z, dy))
    try:
        inv = _inv2(ZtZ)
    except ZeroDivisionError:
        return IVResult(float("nan"), float("nan"), n, sum(1 for s in sign if s > 0))
    # a = (Z'Z)^-1 Z'X ; Xhat = Z a ; project dy onto instruments
    a0 = inv[0] * ZtX[0] + inv[1] * ZtX[1]
    a1 = inv[2] * ZtX[0] + inv[3] * ZtX[1]
    xhat = [a0 * wi + a1 * zi for wi, zi in zip(w, z)]
    denom = _dot(xhat, dy)  # = xhat·xhat (P_Z idempotent)
    if denom == 0:
        return IVResult(float("nan"), float("nan"), n, sum(1 for s in sign if s > 0))
    beta = _dot(xhat, dx) / denom
    resid = [xv - beta * yv for xv, yv in zip(dx, dy)]
    dof = max(n - 1, 1)
    sigma2 = _dot(resid, resid) / dof
    var_beta = sigma2 / denom
    t = beta / math.sqrt(var_beta) if var_beta > 0 else float("nan")
    return IVResult(beta, t, n, sum(1 for s in sign if s > 0))


def estimate(
    dx: Sequence[float], dy: Sequence[float], war: Sequence[bool], *, two_instrument: bool = False
) -> IVResult:
    """War-risk premium of asset x over basis y. ``war`` marks war weeks."""
    sign = [1 if w else -1 for w in war]
    return iv_two(dx, dy, sign) if two_instrument else iv_single(dx, dy, sign)


def first_diff(pairs: Sequence[Tuple[object, float]]) -> "tuple[list, list]":
    """Week-over-week first differences of a sorted (date, value) series.

    Returns ``(end_dates, deltas)`` where ``end_dates[i]`` is the later date of the
    consecutive pair — only used for *consecutive* observations (no imputation
    across gaps is done by the caller aligning on common dates first)."""
    dates, deltas = [], []
    for i in range(1, len(pairs)):
        dates.append(pairs[i][0])
        deltas.append(pairs[i][1] - pairs[i - 1][1])
    return dates, deltas
