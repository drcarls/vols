from __future__ import annotations


def crowding_penalty(volume_spike: float, media_attention: float, obviousness: float) -> float:
    return max(1.0, 1.0 + 0.4 * volume_spike + 0.3 * media_attention + 0.3 * obviousness)


def pari_score(expected_edge: float, penalty: float) -> float:
    return expected_edge / max(1e-6, penalty)
