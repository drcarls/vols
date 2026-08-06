"""war_premia — reproduce and extend Carls (2005), *"Did Politicians Cry 'War' to
Financial Markets Once Too Often?"*

Rigobon-Sack identification-by-heteroskedasticity of war-risk premia in the
weekly city money-market rates of the Neal-Weidenmeier Gold Standard Database
(mirrored in ``../neal_weidenmier``). :mod:`estimator` is the pure IV/2SLS;
:mod:`warweeks` transcribes the paper's Appendix Table 1 (+ a July-1914 coding);
:mod:`run` reproduces Tables 3-7; :mod:`july1914` handles the extension and why
the July-1914 premium is not estimable (markets closed).
"""

from __future__ import annotations

from .estimator import IVResult, estimate, iv_single, iv_two
from .run import CityResult, format_table, run_crisis
from .warweeks import CRISES, Crisis, get_crisis, war_mask

__all__ = [
    "IVResult", "estimate", "iv_single", "iv_two",
    "CityResult", "run_crisis", "format_table",
    "CRISES", "Crisis", "get_crisis", "war_mask",
]

__version__ = "0.1.0"
