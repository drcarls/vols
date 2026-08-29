from .base import Agent
from .momentum import MomentumAgent
from .low_vol import LowVolAgent
from .trend_quality import TrendQualityAgent
from .news_intensity import NewsIntensityAgent
from .macro_regime import MacroRegimeAgent
from .house import HouseAgent
from .valuation import ValuationAgent
from .dislocated_quality import DislocatedQualityAgent
from .quality import QualityAgent


AGENTS = {
    "momentum": MomentumAgent,
    "low_vol": LowVolAgent,
    "trend_quality": TrendQualityAgent,
    "news_intensity": NewsIntensityAgent,
    "macro_regime": MacroRegimeAgent,
    "valuation": ValuationAgent,
    "dislocated_quality": DislocatedQualityAgent,
    "quality": QualityAgent,
    "house": HouseAgent,
}

V1_AGENTS = ["momentum", "low_vol", "trend_quality", "news_intensity", "macro_regime", "valuation", "house"]


def build_agents(names: list[str] | None = None):
    """Build a sleeve's agent roster by name; defaults to the V1 set."""
    chosen = list(names) if names else V1_AGENTS
    unknown = [n for n in chosen if n not in AGENTS]
    if unknown:
        raise ValueError(f"Unknown agents: {unknown}. Available: {sorted(AGENTS)}")
    return [AGENTS[n]() for n in chosen]


def build_v1_agents():
    return build_agents(V1_AGENTS)
