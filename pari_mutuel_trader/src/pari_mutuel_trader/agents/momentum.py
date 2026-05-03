from __future__ import annotations

import pandas as pd
from .base import Agent


class MomentumAgent(Agent):
    name = "momentum"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        return 0.6 * features_df["ret_20d"] + 0.4 * features_df["ret_60d"]
