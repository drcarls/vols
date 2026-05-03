from __future__ import annotations

import pandas as pd


class Agent:
    name: str = "agent"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError
