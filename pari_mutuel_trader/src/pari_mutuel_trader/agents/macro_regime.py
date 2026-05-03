from __future__ import annotations

import pandas as pd
from .base import Agent


class MacroRegimeAgent(Agent):
    name = "macro_regime"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        if "macro_regime" not in features_df.columns:
            return pd.Series(0.0, index=features_df.index)
        regime = features_df["macro_regime"].fillna(0.0).clip(-1, 1)
        return regime * (features_df["ret_20d"] - features_df["vol_20d"])
