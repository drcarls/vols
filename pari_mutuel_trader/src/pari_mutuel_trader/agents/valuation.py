from __future__ import annotations

import pandas as pd
from .base import Agent


class ValuationAgent(Agent):
    """Scores names on their discount to IV15 and their penalty past IV8.

    Degrades to neutral when the feature frame carries no intrinsic value columns,
    the same way the news and macro agents do.
    """

    name = "valuation"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        if "discount_to_iv15" not in features_df.columns:
            return pd.Series(0.0, index=features_df.index)
        discount = features_df["discount_to_iv15"].fillna(0.0)
        premium = features_df.get("premium_to_iv8")
        if premium is None:
            return discount
        return discount - premium.fillna(0.0).clip(lower=0.0)
