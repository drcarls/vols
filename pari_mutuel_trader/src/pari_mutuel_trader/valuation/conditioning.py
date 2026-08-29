from __future__ import annotations

import pandas as pd

RANK = "rank"
VETO = "veto"
SIZE = "size"
MODES = (RANK, VETO, SIZE)

# Section 5's sizing ladder, cheapest bucket first.
DEFAULT_SIZE_MULTIPLIERS = {"cheap": 1.20, "neutral": 1.00, "expensive": 0.80, "extreme": 0.50}


def iv_signal(frame: pd.DataFrame, signal: str) -> pd.Series | None:
    """The IV reading to condition on. `combined` averages the 6% and 8% readings."""
    if signal == "combined":
        needed = ("discount_to_iv6", "discount_to_iv8")
        if any(c not in frame.columns for c in needed):
            return None
        values = 0.5 * (frame["discount_to_iv6"].rank(pct=True) + frame["discount_to_iv8"].rank(pct=True))
        return values if values.nunique() > 1 else None
    if signal not in frame.columns:
        return None
    values = frame[signal]
    return values if values.nunique() > 1 else None


def blend_rank(pooled: pd.Series, frame: pd.DataFrame, signal: str, iv_weight: float) -> pd.Series:
    """Section 3: mix the sleeve's own ranking with the IV ranking.

    Both sides are converted to percentile ranks first so the blend weight means what
    it says, rather than being swamped by whichever signal has the wider raw scale.
    """
    values = iv_signal(frame, signal)
    if values is None or iv_weight <= 0:
        return pooled
    aligned = values.reindex(pooled.index)
    if aligned.isna().all():
        return pooled
    strategy_rank = pooled.rank(pct=True)
    iv_rank = aligned.rank(pct=True).fillna(0.5)
    blended = (1.0 - iv_weight) * strategy_rank + iv_weight * iv_rank
    # Return something softmax-shaped and positive, ordered by the blend.
    return blended / blended.sum()


def veto_mask(frame: pd.DataFrame, signal: str, exclude_pct: float,
              require_both: bool = False) -> pd.Index:
    """Section 4: the names left after dropping the richest `exclude_pct` of the frame.

    With `require_both`, a name is only vetoed when the 6% and 8% readings both put
    it in the excluded tail - which, given the two are monotone transforms of each
    other, removes very few names that either would have kept.
    """
    if exclude_pct <= 0:
        return frame.index

    def tail(name: str) -> pd.Index:
        values = iv_signal(frame, name)
        if values is None:
            return pd.Index([])
        return values.index[values.rank(pct=True) <= exclude_pct]

    if require_both:
        vetoed = tail("discount_to_iv6").intersection(tail("discount_to_iv8"))
    else:
        vetoed = tail(signal)
    return frame.index.difference(vetoed)


def size_multipliers(frame: pd.DataFrame, signal: str,
                     multipliers: dict | None = None) -> pd.Series | None:
    """Section 5: a per-name multiplier from where the IV reading sits cross-sectionally."""
    values = iv_signal(frame, signal)
    if values is None:
        return None
    ladder = {**DEFAULT_SIZE_MULTIPLIERS, **(multipliers or {})}
    pct = values.rank(pct=True)
    out = pd.Series(ladder["neutral"], index=values.index, dtype=float)
    out[pct <= 0.10] = ladder["extreme"]
    out[(pct > 0.10) & (pct <= 0.30)] = ladder["expensive"]
    out[pct >= 0.70] = ladder["cheap"]
    return out


def apply_size(weights: pd.Series, multipliers: pd.Series | None) -> pd.Series:
    """Scale weights by the multiplier and renormalize so exposure is comparable."""
    if multipliers is None or weights.empty:
        return weights
    scaled = weights * multipliers.reindex(weights.index).fillna(1.0)
    total = float(scaled.sum())
    return scaled / total if total > 0 else weights


def from_config(cfg: dict | None) -> dict | None:
    """Parse the `iv_overlay` block; returns None when the overlay is off."""
    cfg = cfg or {}
    if not cfg.get("enabled"):
        return None
    mode = cfg.get("mode", RANK)
    if mode not in MODES:
        raise ValueError(f"Unknown iv_overlay mode {mode!r}; expected one of {MODES}")
    return {
        "mode": mode,
        "signal": cfg.get("signal", "discount_to_iv8"),
        "iv_weight": float(cfg.get("iv_weight", 0.25)),
        "exclude_pct": float(cfg.get("exclude_pct", 0.10)),
        "require_both": bool(cfg.get("require_both", False)),
        "multipliers": cfg.get("multipliers"),
    }
