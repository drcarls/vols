from __future__ import annotations

import pandas as pd
from .base import Agent


class QualityAgent(Agent):
    """Ranks on franchise durability - moat plus enduring return on capital.

    NOTE ON INDEPENDENCE: durability is an input to the intrinsic value model, where
    it sets the competitive advantage period and the terminal ROIC. So a quality
    sleeve defined this way is not independent of IV, and asking whether IV adds
    information inside it is partly circular. `trend_quality`, which is built from
    price behaviour alone, is the non-circular control.
    """

    name = "quality"

    def abstains(self, features_df: pd.DataFrame) -> bool:
        if "durability" not in features_df.columns:
            return True
        return bool(features_df["durability"].fillna(0.0).eq(0.0).all())

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        if "durability" not in features_df.columns:
            return pd.Series(0.0, index=features_df.index)
        return features_df["durability"].fillna(0.0)
