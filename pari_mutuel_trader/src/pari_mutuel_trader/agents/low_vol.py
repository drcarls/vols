from __future__ import annotations

import pandas as pd
from .base import Agent


class LowVolAgent(Agent):
    name = "low_vol"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        return -features_df["vol_20d"]
