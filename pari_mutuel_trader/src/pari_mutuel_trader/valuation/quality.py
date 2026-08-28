from __future__ import annotations

from dataclasses import dataclass


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(min(max(x, lo), hi))


@dataclass
class QualityProfile:
    """Competitive position and enduring return on invested capital.

    These two inputs are what stretch or shrink the window over which a business
    can compound above its cost of capital, so they drive the fade schedule used
    by the intrinsic value engine rather than being scored on the side.
    """

    moat: float = 0.5
    roic: float = 0.12
    roic_stability: float = 0.5
    wacc: float = 0.08

    @property
    def spread(self) -> float:
        return self.roic - self.wacc

    def durability(self) -> float:
        """0..1 score for how enduring the economics look."""
        spread_score = _clamp(self.spread / 0.15)
        return _clamp(0.45 * _clamp(self.moat) + 0.35 * _clamp(self.roic_stability) + 0.20 * spread_score)

    def competitive_advantage_period(self, base_years: int = 5, max_years: int = 15) -> int:
        """Years of above-cost-of-capital growth before the business fades to a commodity."""
        return int(round(base_years + self.durability() * (max_years - base_years)))

    def terminal_growth(self, floor: float = 0.0, cap: float = 0.03) -> float:
        return float(floor + self.durability() * (cap - floor))

    def terminal_roic(self) -> float:
        """ROIC decays toward WACC; only durable franchises keep part of the spread."""
        return float(self.wacc + self.durability() * max(self.roic - self.wacc, 0.0))
