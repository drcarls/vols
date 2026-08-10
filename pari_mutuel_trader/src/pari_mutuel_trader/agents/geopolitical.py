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

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        if "geo_signal" not in features_df.columns:
            return pd.Series(0.0, index=features_df.index)
        return features_df["geo_signal"].fillna(0.0)
