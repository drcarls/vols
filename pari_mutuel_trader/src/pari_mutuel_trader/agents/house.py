from __future__ import annotations

import pandas as pd
from .base import Agent


class HouseAgent(Agent):
    name = "house"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        return pd.Series(0.0, index=features_df.index)
