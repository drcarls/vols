from __future__ import annotations

import pandas as pd
from .base import Agent


class NewsIntensityAgent(Agent):
    name = "news_intensity"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        if "news_intensity" not in features_df.columns:
            return pd.Series(0.0, index=features_df.index)
        return features_df["news_intensity"].fillna(0.0)
