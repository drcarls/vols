from __future__ import annotations

import pandas as pd


class Agent:
    name: str = "agent"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    def conviction(self, features_df: pd.DataFrame) -> float:
        """Transient per-rebalance multiplier on this agent's share of the pari-mutuel pool.

        Default 1.0 = no change (the slow hedge weight decides everything). An event-driven agent
        overrides this to raise its share *only while it has a live, high-magnitude signal* and fall
        back to 1.0 when quiet — so a live event can push it above its 1/N hedge weight without
        permanently altering the hedge-learned weights. Engine applies it only if
        ``learning.use_conviction`` is set, so default behaviour is unchanged.
        """
        return 1.0
