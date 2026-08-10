from .base import Agent
from .momentum import MomentumAgent
from .low_vol import LowVolAgent
from .trend_quality import TrendQualityAgent
from .news_intensity import NewsIntensityAgent
from .macro_regime import MacroRegimeAgent
from .house import HouseAgent
from .geopolitical import GeopoliticalAgent


def build_v1_agents():
    return [
        MomentumAgent(),
        LowVolAgent(),
        TrendQualityAgent(),
        NewsIntensityAgent(),
        MacroRegimeAgent(),
        GeopoliticalAgent(),
        HouseAgent(),
    ]
