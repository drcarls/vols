from __future__ import annotations

import pandas as pd
from .base import Agent


class GeopoliticalAgent(Agent):
    """Geopolitical mispricing sleeve.

    Reads a precomputed ``geo_signal`` column (a per-symbol tilt from the decision-odds-vs-premium
    gap; see ``data/geopolitical.py``). Neutral (all-zero) when the column is absent, exactly like
    the news/macro agents — so the sleeve degrades gracefully on universes without geo exposure.
    """

    name = "geopolitical"

    # Conviction ramp: share multiplier = 1 + GAIN * min(max|geo_signal|, CAP). Quiet book
    # (geo_signal ~ 0) -> ~1.0 (no boost, baseline untouched); a live event with a large edge*exposure
    # -> up to 1 + GAIN*CAP. Lets the sleeve concentrate when it actually has something to say.
    CONVICTION_GAIN = 4.0
    CONVICTION_CAP = 0.5

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        if "geo_signal" not in features_df.columns:
            return pd.Series(0.0, index=features_df.index)
        return features_df["geo_signal"].fillna(0.0)

    def conviction(self, features_df: pd.DataFrame) -> float:
        if "geo_signal" not in features_df.columns:
            return 1.0
        mag = float(features_df["geo_signal"].abs().max())
        if mag != mag:  # NaN guard
            return 1.0
        return 1.0 + self.CONVICTION_GAIN * min(mag, self.CONVICTION_CAP)
