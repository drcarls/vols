from __future__ import annotations

import pandas as pd
from .base import Agent


class MacroRegimeAgent(Agent):
    name = "macro_regime"

    CONVICTION_GAIN = 2.0  # |regime| in [0,1] -> up to 1 + GAIN; quiet (regime~0) -> ~1.0

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        if "macro_regime" not in features_df.columns:
            return pd.Series(0.0, index=features_df.index)
        regime = features_df["macro_regime"].fillna(0.0).clip(-1, 1)
        return regime * (features_df["ret_20d"] - features_df["vol_20d"])

    def conviction(self, features_df: pd.DataFrame) -> float:
        if "macro_regime" not in features_df.columns:
            return 1.0
        mag = float(features_df["macro_regime"].fillna(0.0).abs().max())
        if mag != mag:
            return 1.0
        return 1.0 + self.CONVICTION_GAIN * min(mag, 1.0)
