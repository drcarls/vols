"""Buyer-depth aggregation - the central signal under test.

The thesis this repository exists to evaluate:

    the number of genuinely plausible end buyers, weighted by their economic
    value, predicts domain resale better than traditional metrics such as
    search volume or CPC.

So buyer depth is computed as several *separate* quantities rather than one
blended number, because the point is to find out which of them carries the
information:

    count               how many credible buyers exist
    strong_count        how many match on identity, not just industry
    depth_value         count weighted by match strength and buyer economics
    max_buyer_value     the single strongest buyer (drives strategic value)
    economic_coverage   what fraction of buyers we actually have economics for

``missing`` is the most important field. A domain with no buyer search run is
not the same as a domain searched and found to have none, and the models must
not conflate them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.providers.base import BuyerCandidateRecord, BuyerSearchResult

# A match below this score is recorded but does not count toward "credible
# buyers". Industry-only matches sit near 38-50; identity matches sit near 80+.
CREDIBLE_MATCH_THRESHOLD = 50.0
STRONG_MATCH_THRESHOLD = 78.0


@dataclass
class BuyerDepth:
    missing: bool
    searched: bool
    count: int = 0
    strong_count: int = 0
    total_found: int = 0
    depth_value: float = 0.0
    max_buyer_value: float = 0.0
    mean_match_score: float = 0.0
    economic_coverage: float = 0.0
    by_match_type: dict[str, int] = field(default_factory=dict)
    source: str = "unknown"
    provenance: str = "MISSING"
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def summarise(result: BuyerSearchResult) -> BuyerDepth:
    """Aggregate a buyer search into the depth signals."""
    if result.is_missing:
        return BuyerDepth(missing=True, searched=result.searched,
                          source=result.source, provenance="MISSING",
                          note=result.note or "buyer search not performed")

    candidates: list[BuyerCandidateRecord] = list(result.candidates)
    credible = [c for c in candidates if c.match_score >= CREDIBLE_MATCH_THRESHOLD]
    strong = [c for c in credible if c.match_score >= STRONG_MATCH_THRESHOLD]

    by_type: dict[str, int] = {}
    for c in candidates:
        by_type[c.match_type] = by_type.get(c.match_type, 0) + 1

    with_economics = [c for c in credible if c.buyer_value_score > 0]
    coverage = (len(with_economics) / len(credible)) if credible else 0.0

    # depth_value: each credible buyer contributes match strength x economic
    # weight. Buyers with unknown economics contribute at a reduced, explicit
    # rate rather than either zero (which would erase them) or an invented
    # average (which would fabricate). 0.25 is the "we know they exist but not
    # how big they are" discount.
    UNKNOWN_ECONOMICS_WEIGHT = 0.25
    depth_value = 0.0
    for c in credible:
        match_w = c.match_score / 100.0
        econ_w = (c.buyer_value_score / 100.0) if c.buyer_value_score > 0 \
            else UNKNOWN_ECONOMICS_WEIGHT
        depth_value += match_w * econ_w

    return BuyerDepth(
        missing=False,
        searched=True,
        count=len(credible),
        strong_count=len(strong),
        total_found=len(candidates),
        depth_value=round(depth_value, 4),
        max_buyer_value=round(max((c.buyer_value_score for c in credible),
                                  default=0.0), 2),
        mean_match_score=round(
            sum(c.match_score for c in credible) / len(credible), 2) if credible else 0.0,
        economic_coverage=round(coverage, 3),
        by_match_type=by_type,
        source=result.source,
        provenance=(candidates[0].provenance.value if candidates else "OBSERVED"),
        note=result.note,
    )
