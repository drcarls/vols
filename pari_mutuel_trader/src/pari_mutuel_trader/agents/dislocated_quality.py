from __future__ import annotations

import pandas as pd
from .base import Agent

REQUIRED = ("durability", "discount_to_iv15", "dislocation")


class DislocatedQualityAgent(Agent):
    """Durable businesses whose price has fallen further than their value.

    Two of the three inputs are the point. Quality on its own buys expensive
    compounders; cheapness on its own buys businesses that deserve to be cheap.
    The agent wants the intersection, and it scores dislocation rather than raw
    weakness so that a price which fell alongside its own intrinsic value - a
    deterioration, not an opportunity - earns nothing.

    It votes against the momentum agent by construction, which is the point of
    having it in the pool.
    """

    name = "dislocated_quality"

    def __init__(self, value_weight: float = 0.5, dislocation_weight: float = 0.3, quality_weight: float = 0.2):
        self.value_weight = value_weight
        self.dislocation_weight = dislocation_weight
        self.quality_weight = quality_weight

    def abstains(self, features_df: pd.DataFrame) -> bool:
        if any(c not in features_df.columns for c in REQUIRED):
            return True
        return bool(features_df["discount_to_iv15"].fillna(0.0).eq(0.0).all())

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        if any(c not in features_df.columns for c in REQUIRED):
            return pd.Series(0.0, index=features_df.index)
        discount = features_df["discount_to_iv15"].fillna(0.0)
        dislocation = features_df["dislocation"].fillna(0.0)
        durability = features_df["durability"].fillna(0.0)
        return (
            self.value_weight * discount
            + self.dislocation_weight * dislocation
            + self.quality_weight * durability
        )
