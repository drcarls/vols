from __future__ import annotations


def estimate_edge(leader_return: float, lagger_beta: float = 1.0) -> float:
    return leader_return * lagger_beta
