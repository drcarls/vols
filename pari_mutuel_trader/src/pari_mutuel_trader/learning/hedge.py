from __future__ import annotations

import math


def normalize(weights: dict[str, float], min_w: float, max_w: float) -> dict[str, float]:
    clipped = {k: min(max_w, max(min_w, v)) for k, v in weights.items()}
    total = sum(clipped.values())
    return {k: v / total for k, v in clipped.items()}


def hedge_update(weights: dict[str, float], performance: dict[str, float], eta: float, min_w: float, max_w: float) -> dict[str, float]:
    updated = {k: v * math.exp(eta * performance.get(k, 0.0)) for k, v in weights.items()}
    return normalize(updated, min_w=min_w, max_w=max_w)
