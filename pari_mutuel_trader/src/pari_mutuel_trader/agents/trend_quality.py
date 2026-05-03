from __future__ import annotations

import pandas as pd
from .base import Agent


class TrendQualityAgent(Agent):
    name = "trend_quality"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        return features_df["breakout_20d"] + 0.5 * features_df["trend_persistence"] - 0.25 * features_df["vol_20d"]
