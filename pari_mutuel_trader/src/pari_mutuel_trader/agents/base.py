from __future__ import annotations

import pandas as pd


class Agent:
    name: str = "agent"

    def compute_signal(self, features_df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    def abstains(self, features_df: pd.DataFrame) -> bool:
        """True when the agent has no data to vote on.

        An abstaining agent is dropped from the pool rather than voting a flat
        signal: a uniform vote is not neutral, it dilutes the agents that do have
        a view.
        """
        return False
