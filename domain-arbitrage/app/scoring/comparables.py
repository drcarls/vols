"""Comparable-sales analysis.

Comparable sales are the only OBSERVED price evidence in the system. Everything
else is a prior. So this module is deliberately conservative:

  * It ships with an EMPTY comparable-sales table. Load real sales (a NameBio
    export, your own escrow records) with ``scripts/load_comparables.py``.
  * With no comps it reports ``available=False`` and confidence 0. It does not
    manufacture a comp set.
  * It uses a *weighted median*, not a mean, and reports the interquartile
    range, because a single exceptional sale should never set a valuation.
  * Confidence is penalised when the comp set is small, weakly similar, or
    widely dispersed.

Every comp actually used is written to ``comparable_matches`` with its
similarity breakdown, so a comp-driven valuation can be re-examined later.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

# Similarity weights. Hand-set V0 priors; they live here rather than in the YAML
# because they define what "comparable" *means* rather than tuning a score.
SIMILARITY_WEIGHTS = {
    "tld": 0.30,
    "category": 0.25,
    "token_overlap": 0.20,
    "word_count": 0.10,
    "length": 0.10,
    "keyword_profile": 0.05,
}

MIN_SIMILARITY = 0.45      # below this a sale is not a comparable
MAX_COMPS = 25
MIN_COMPS_FOR_CONFIDENCE = 5


@dataclass
class CompRecord:
    """Minimal view of a comparable sale, decoupled from the ORM for testing."""

    id: int
    domain: str
    sale_price: float
    tld: str = ""
    word_count: int = 0
    length: int = 0
    category: str | None = None
    words: list[str] = field(default_factory=list)
    cpc: float | None = None
    search_volume: float | None = None
    sale_date: Any = None
    venue: str | None = None


@dataclass
class ComparableStats:
    available: bool
    count: int
    median: float | None = None
    weighted_median: float | None = None
    p25: float | None = None
    p75: float | None = None
    maximum: float | None = None
    minimum: float | None = None
    confidence: float = 0.0
    mean_similarity: float = 0.0
    dispersion_ratio: float | None = None
    note: str | None = None
    used: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        return d


def _tld_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    # .com is its own asset class; cross-TLD comps are weak evidence.
    premium = {"com"}
    if a in premium or b in premium:
        return 0.15
    return 0.5


def _ratio_similarity(a: float, b: float) -> float:
    """1.0 when equal, decaying with the log ratio. Symmetric."""
    if a <= 0 or b <= 0:
        return 0.0
    return max(0.0, 1.0 - abs(math.log(a / b)) / math.log(4.0))


def _token_overlap(a: Sequence[str], b: Sequence[str]) -> float:
    sa, sb = {w for w in a if len(w) >= 3}, {w for w in b if len(w) >= 3}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def similarity(target_tld: str, target_words: list[str], target_length: int,
               target_word_count: int, target_category: str | None,
               target_cpc: float | None, comp: CompRecord) -> tuple[float, dict]:
    """Weighted similarity in 0..1 plus the per-dimension breakdown.

    ``keyword_profile`` only contributes when both sides have CPC data; its
    weight is otherwise redistributed so a missing field does not silently drag
    the similarity toward zero.
    """
    parts: dict[str, float] = {}
    weights: dict[str, float] = {}

    parts["tld"] = _tld_similarity(target_tld, comp.tld)
    weights["tld"] = SIMILARITY_WEIGHTS["tld"]

    if target_category and comp.category:
        parts["category"] = 1.0 if target_category == comp.category else 0.0
        weights["category"] = SIMILARITY_WEIGHTS["category"]

    parts["token_overlap"] = _token_overlap(target_words, comp.words)
    weights["token_overlap"] = SIMILARITY_WEIGHTS["token_overlap"]

    if comp.word_count:
        parts["word_count"] = _ratio_similarity(max(1, target_word_count),
                                                max(1, comp.word_count))
        weights["word_count"] = SIMILARITY_WEIGHTS["word_count"]

    if comp.length:
        parts["length"] = _ratio_similarity(max(1, target_length),
                                            max(1, comp.length))
        weights["length"] = SIMILARITY_WEIGHTS["length"]

    if target_cpc is not None and comp.cpc is not None:
        parts["keyword_profile"] = _ratio_similarity(max(0.01, target_cpc),
                                                     max(0.01, comp.cpc))
        weights["keyword_profile"] = SIMILARITY_WEIGHTS["keyword_profile"]

    total_w = sum(weights.values())
    if total_w <= 0:
        return 0.0, parts
    score = sum(parts[k] * weights[k] for k in weights) / total_w
    breakdown = {k: {"similarity": round(parts[k], 4),
                     "weight": round(weights[k] / total_w, 4)} for k in weights}
    return round(score, 4), breakdown


def weighted_median(values: list[float], weights: list[float]) -> float | None:
    """Median of a weighted sample. Robust to one huge outlier sale."""
    if not values:
        return None
    pairs = sorted(zip(values, weights))
    total = sum(w for _, w in pairs)
    if total <= 0:
        return statistics.median(values)
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= total / 2.0:
            return float(value)
    return float(pairs[-1][0])


def _confidence(count: int, mean_sim: float, dispersion: float | None) -> float:
    """0..1. Small, weak or scattered comp sets are not evidence.

    Three independent penalties, multiplied:
      * sample size, saturating at MIN_COMPS_FOR_CONFIDENCE
      * mean similarity of the set
      * dispersion (p75/p25); a 20x spread means the comps disagree
    """
    if count == 0:
        return 0.0
    size_factor = min(1.0, count / MIN_COMPS_FOR_CONFIDENCE)
    sim_factor = max(0.0, (mean_sim - MIN_SIMILARITY) / (1.0 - MIN_SIMILARITY))
    sim_factor = 0.25 + 0.75 * sim_factor       # never fully discount a real sale
    if dispersion is None or dispersion <= 0:
        disp_factor = 0.6
    else:
        # ratio 2 -> 1.0, ratio 10 -> ~0.4, ratio 50 -> ~0.15
        disp_factor = max(0.1, min(1.0, 2.0 / max(1.0, dispersion)))
        disp_factor = 0.4 + 0.6 * disp_factor
    return round(min(1.0, size_factor * sim_factor * disp_factor), 4)


def analyse(target_tld: str, target_words: list[str], target_length: int,
            target_word_count: int, target_category: str | None,
            target_cpc: float | None,
            comps: Iterable[CompRecord]) -> ComparableStats:
    """Select and summarise comparable sales for one domain."""
    scored: list[tuple[float, dict, CompRecord]] = []
    for comp in comps:
        sim, breakdown = similarity(target_tld, target_words, target_length,
                                    target_word_count, target_category,
                                    target_cpc, comp)
        if sim >= MIN_SIMILARITY:
            scored.append((sim, breakdown, comp))

    if not scored:
        return ComparableStats(
            available=False, count=0, confidence=0.0,
            note=("no comparable sales in the database met the similarity "
                  "threshold; comparable-based valuation unavailable"))

    scored.sort(key=lambda t: t[0], reverse=True)
    scored = scored[:MAX_COMPS]

    prices = [c.sale_price for _, _, c in scored]
    sims = [s for s, _, _ in scored]
    # Weight by similarity squared so near-identical names dominate.
    weights = [s * s for s in sims]

    ordered = sorted(prices)
    p25 = float(statistics.quantiles(ordered, n=4)[0]) if len(ordered) >= 4 else float(min(ordered))
    p75 = float(statistics.quantiles(ordered, n=4)[2]) if len(ordered) >= 4 else float(max(ordered))
    dispersion = (p75 / p25) if p25 > 0 else None

    stats = ComparableStats(
        available=True,
        count=len(scored),
        median=round(float(statistics.median(prices)), 2),
        weighted_median=round(float(weighted_median(prices, weights) or 0.0), 2),
        p25=round(p25, 2),
        p75=round(p75, 2),
        maximum=round(float(max(prices)), 2),
        minimum=round(float(min(prices)), 2),
        mean_similarity=round(sum(sims) / len(sims), 4),
        dispersion_ratio=round(dispersion, 3) if dispersion else None,
    )
    stats.confidence = _confidence(stats.count, stats.mean_similarity, dispersion)
    stats.used = [
        {"comparable_id": c.id, "domain": c.domain, "sale_price": c.sale_price,
         "similarity": s, "weight": round(w, 4), "breakdown": b,
         "venue": c.venue}
        for (s, b, c), w in zip(scored, weights)
    ]
    if stats.count < MIN_COMPS_FOR_CONFIDENCE:
        stats.note = (f"only {stats.count} comparable(s) found; treat the "
                      f"comparable-based figure as weak evidence")
    return stats


def index_by_tld_category(comps: Iterable[CompRecord]) -> dict[tuple[str, str | None], list[CompRecord]]:
    """Prefilter index so scoring 10k domains does not become O(n*m)."""
    index: dict[tuple[str, str | None], list[CompRecord]] = defaultdict(list)
    for comp in comps:
        index[(comp.tld, comp.category)].append(comp)
        index[(comp.tld, None)].append(comp)
    return index
