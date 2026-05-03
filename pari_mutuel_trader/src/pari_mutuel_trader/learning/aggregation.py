from __future__ import annotations

import numpy as np
import pandas as pd


def softmax(signal: pd.Series, temperature: float = 1.0) -> pd.Series:
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    z = signal.astype(float) / temperature
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def pari_mutuel_aggregate(agent_probs: dict[str, pd.Series], agent_weights: dict[str, float]) -> pd.Series:
    out = None
    for name, probs in agent_probs.items():
        out = probs * agent_weights[name] if out is None else out.add(probs * agent_weights[name], fill_value=0.0)
    if out is None:
        raise ValueError("No probabilities provided")
    return out / out.sum()
