"""Stratified paper-buy sampling.

The paper portfolio only produces usable evidence if the sample is drawn
properly, and the obvious way to draw it is the wrong way.

**Why not just paper-buy the top N.** A cohort made of the model's own top picks
can measure precision - of the names we liked, how many sold - but never recall.
It cannot answer "did the names we passed on sell just as often?", which is the
question that decides whether the score means anything. A model tested only on
its own selections is unfalsifiable.

**Why stratify on buyer depth as well as score.** Buyer depth contributes 15% of
the opportunity score, so a sample drawn on score alone over-represents
high-buyer-depth names at the top. The two would be confounded, and any measured
association between buyer depth and resale could equally be an association
between *score* and resale. To attribute the effect we need domains with high
depth and low score, and low depth and high score, in the cohort deliberately.

So the sampler works over a two-dimensional grid: score band x buyer-depth band,
allocating as evenly as it can across cells and reporting exactly which cells it
could not fill. Sparse cells are a finding about the inventory, not something to
paper over.

Sampling is deterministic given a seed, so a cohort can be reproduced.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import OpportunityScore, PipelineRun
from app.models.core import Domain
from app.models.paper import PaperPosition
from app.services.paper_portfolio import PaperPortfolioError, open_position

# Absolute score bands, used only when banding="absolute" is requested. They
# span the whole nominal 0-100 range, which is exactly their weakness: the top
# of that range may be structurally unreachable. See `reachable_score_ceiling`.
ABSOLUTE_SCORE_BANDS: tuple[tuple[str, float, float], ...] = (
    ("score_00_30", 0.0, 30.0),
    ("score_30_45", 30.0, 45.0),
    ("score_45_55", 45.0, 55.0),
    ("score_55_65", 55.0, 65.0),
    ("score_65_plus", 65.0, 1e9),
)

# Absolute buyer-depth bands. Zero is always its own band because "no
# identifiable buyer" is a qualitatively different state, not just a low count.
ABSOLUTE_DEPTH_BANDS: tuple[tuple[str, int, int], ...] = (
    ("buyers_0", 0, 0),
    ("buyers_1_2", 1, 2),
    ("buyers_3_9", 3, 9),
    ("buyers_10_plus", 10, 10 ** 9),
)

DEFAULT_SCORE_BINS = 5
DEFAULT_DEPTH_BINS = 4

# Status assigned from the model's own recommendation. The sampler records what
# the model WOULD have done, so precision and recall are both measurable later.
STATUS_BY_RECOMMENDATION = {
    "STRONG_BUY": "PAPER_BUY",
    "BUY": "PAPER_BUY",
    "WATCH": "PAPER_WATCH",
    "PASS": "PAPER_PASS",
    "AVOID": "PAPER_PASS",
}

# Below this many positions per cell, a cell contributes almost nothing to the
# comparison it exists to support.
MIN_PER_CELL_FOR_POWER = 5


def reachable_score_ceiling(components: dict[str, dict],
                            confidence: float) -> dict[str, Any]:
    """The highest opportunity score attainable given current data coverage.

    A component that is MISSING scores zero for every domain, so its weight is
    not merely unused - it is deducted from the maximum any domain can reach.
    The confidence adjustment then scales what remains.

    This is why absolute score bands are a trap: with two providers unconfigured
    the nominal 0-100 scale is really 0-68, and a band defined at 65+ looks like
    an inventory shortage when it is actually a missing data source.
    """
    missing = sorted(name for name, c in components.items()
                     if c.get("status") == "MISSING")
    lost = sum(100.0 * float(components[name].get("weight", 0.0))
               for name in missing)
    raw_ceiling = 100.0 - lost
    return {
        "missing_components": missing,
        "raw_points_unavailable": round(lost, 2),
        "raw_score_ceiling": round(raw_ceiling, 2),
        "observed_confidence": round(confidence, 4),
        "final_score_ceiling": round(raw_ceiling * confidence, 2)
        if confidence else None,
    }


@dataclass
class Banding:
    """The band edges a cohort was drawn under.

    Edges are carried in the stratum label itself rather than only in the plan,
    because two cohorts drawn from different corpora would otherwise share a
    label like ``score_q5`` while meaning different things - and that would
    quietly corrupt any comparison across cohorts.
    """

    kind: str                       # quantile | absolute
    score_edges: list[float] = field(default_factory=list)
    depth_edges: list[int] = field(default_factory=list)

    def score_band(self, score: float) -> str:
        if self.kind == "absolute":
            for name, low, high in ABSOLUTE_SCORE_BANDS:
                if low <= score < high:
                    return name
            return ABSOLUTE_SCORE_BANDS[-1][0]
        for index, edge in enumerate(self.score_edges):
            if score < edge:
                return f"score_q{index + 1}_lt{edge:g}"
        return f"score_q{len(self.score_edges) + 1}_ge" \
               f"{self.score_edges[-1]:g}" if self.score_edges else "score_q1"

    def depth_band(self, count: int) -> str:
        if self.kind == "absolute":
            for name, low, high in ABSOLUTE_DEPTH_BANDS:
                if low <= count <= high:
                    return name
            return ABSOLUTE_DEPTH_BANDS[-1][0]
        if count == 0:
            return "buyers_0"
        for edge in self.depth_edges:
            if count <= edge:
                return f"buyers_le{edge}"
        return (f"buyers_gt{self.depth_edges[-1]}" if self.depth_edges
                else "buyers_1_plus")

    def stratum(self, score: float, count: int) -> str:
        return f"{self.score_band(score)}|{self.depth_band(count)}"

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "score_edges": self.score_edges,
                "depth_edges": self.depth_edges}


def _quantile_edges(values: list[float], bins: int) -> list[float]:
    """Interior cut points splitting ``values`` into ``bins`` equal parts.

    Duplicate edges are collapsed, so a lumpy distribution simply yields fewer
    bands rather than empty ones. That is the whole point: bands defined by the
    data cannot be unfillable.
    """
    if bins < 2 or len(values) < bins:
        return []
    ordered = sorted(values)
    edges: list[float] = []
    for i in range(1, bins):
        edge = ordered[int(round(i * len(ordered) / bins)) - 1]
        if not edges or edge > edges[-1]:
            edges.append(float(edge))
    return edges


def build_banding(scores: list[float], depths: list[int], *,
                  kind: str = "quantile", score_bins: int = DEFAULT_SCORE_BINS,
                  depth_bins: int = DEFAULT_DEPTH_BINS) -> Banding:
    """Choose band edges.

    Quantile banding (the default) defines bands from the corpus's own
    distribution, so every band is populated by construction and a band means
    "the top fifth of what is actually available" rather than an absolute
    threshold that current data coverage may put out of reach.

    Absolute banding stays available for comparing cohorts on a fixed scale,
    with the caveat above.
    """
    if kind == "absolute":
        return Banding(kind="absolute")

    positives = [d for d in depths if d > 0]
    return Banding(
        kind="quantile",
        score_edges=_quantile_edges(scores, score_bins),
        # Zero already occupies a band, so the positive counts are split into
        # one fewer bin.
        depth_edges=[int(e) for e in
                     _quantile_edges([float(d) for d in positives],
                                     max(2, depth_bins - 1))],
    )


@dataclass
class CellPlan:
    """One cell of the sampling grid, and how well it could be filled."""

    stratum: str
    score_band: str
    depth_band: str
    available: int
    requested: int
    sampled: int
    shortfall: int

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SamplePlan:
    """What a sampling run would do, or did."""

    cohort: str
    run_id: int
    target_size: int
    eligible: int
    planned: int
    cells: list[CellPlan] = field(default_factory=list)
    banding: Banding | None = None
    reachability: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["cells"] = [c.to_dict() for c in self.cells]
        d["banding"] = self.banding.to_dict() if self.banding else None
        return d


@dataclass
class SampleResult:
    plan: SamplePlan
    opened: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"plan": self.plan.to_dict(), "opened": self.opened,
                "skipped": self.skipped, "dry_run": self.dry_run,
                "opened_count": len(self.opened),
                "skipped_count": len(self.skipped)}


def _allocate(cells: dict[str, list], target: int) -> dict[str, int]:
    """Spread ``target`` picks across cells as evenly as their supply allows.

    Repeatedly gives one pick to every cell that still has inventory, so a cell
    with three candidates contributes all three and the remaining demand flows
    to cells that can meet it. Balanced-as-possible rather than proportional:
    proportional allocation would reproduce the inventory's own skew, and the
    inventory is skewed toward exactly the low-score names that dominate any
    aftermarket feed.
    """
    allocation = {key: 0 for key in cells}
    remaining = target
    while remaining > 0:
        hungry = [key for key, items in cells.items()
                  if allocation[key] < len(items)]
        if not hungry:
            break
        for key in hungry:
            if remaining == 0:
                break
            allocation[key] += 1
            remaining -= 1
    return allocation


def plan_sample(session: Session, *, size: int, cohort: str,
                run_id: int | None = None, seed: int = 0,
                max_price: float | None = None,
                banding: str = "quantile",
                exclude_open: bool = True) -> tuple[SamplePlan, dict[str, list]]:
    """Build the sampling plan without opening anything."""
    if size <= 0:
        raise PaperPortfolioError("sample size must be positive")
    if banding not in {"quantile", "absolute"}:
        raise PaperPortfolioError("banding must be 'quantile' or 'absolute'")

    if run_id is None:
        run_id = session.execute(
            select(PipelineRun.id).where(PipelineRun.status == "complete")
            .order_by(PipelineRun.id.desc()).limit(1)).scalar()
    if run_id is None:
        raise PaperPortfolioError("no completed pipeline run to sample from")

    rows = session.execute(
        select(OpportunityScore, Domain).join(Domain)
        .where(OpportunityScore.run_id == run_id)).all()

    plan = SamplePlan(cohort=cohort, run_id=run_id, target_size=size,
                      eligible=0, planned=0)

    already_open: set[int] = set()
    if exclude_open:
        already_open = {p.domain_id for p in session.execute(
            select(PaperPosition).where(PaperPosition.outcome.is_(None))).scalars()}

    eligible: list[tuple[Any, Any]] = []
    for score, domain in rows:
        if domain.id in already_open:
            continue
        if max_price is not None and (score.acquisition_price is None
                                      or score.acquisition_price > max_price):
            continue
        # A domain with no price cannot be paper-bought: there is nothing to
        # record as the entry cost, so its ROI could never be evaluated.
        if score.acquisition_price is None or score.acquisition_price <= 0:
            continue
        eligible.append((score, domain))

    plan.eligible = len(eligible)
    if not eligible:
        plan.warnings.append(
            "No eligible domains. Every candidate was already in an open "
            "position, priced out, or had no asking price.")
        return plan, {}

    # Explain the score ceiling before banding, because an unreachable ceiling
    # is the usual reason an absolute top band looks like an inventory shortage.
    best = max(eligible, key=lambda pair: pair[0].score)[0]
    plan.reachability = reachable_score_ceiling(best.components or {},
                                                best.confidence)
    if plan.reachability["missing_components"]:
        plan.warnings.append(
            f"{plan.reachability['raw_points_unavailable']:.0f} of 100 raw "
            f"score points are unreachable because "
            f"{', '.join(plan.reachability['missing_components'])} have no data "
            f"for any domain. The effective score ceiling is about "
            f"{plan.reachability['final_score_ceiling']:.0f}, not 100. This is a "
            f"missing data source, not a shortage of good domains.")

    plan.banding = build_banding([s.score for s, _ in eligible],
                                 [s.buyer_count for s, _ in eligible],
                                 kind=banding)

    cells: dict[str, list] = defaultdict(list)
    for score, domain in eligible:
        cells[plan.banding.stratum(score.score, score.buyer_count)].append(
            (score, domain))

    # Deterministic shuffle so a cohort is reproducible from its seed.
    rng = random.Random(seed)
    for key in cells:
        cells[key].sort(key=lambda pair: pair[1].name)   # stable base order
        rng.shuffle(cells[key])

    allocation = _allocate(cells, size)

    for key in sorted(cells):
        score_name, depth_name = key.split("|")
        plan.cells.append(CellPlan(
            stratum=key, score_band=score_name, depth_band=depth_name,
            available=len(cells[key]), requested=allocation.get(key, 0),
            sampled=allocation.get(key, 0), shortfall=0))
    plan.planned = sum(c.requested for c in plan.cells)

    if plan.planned < size:
        plan.warnings.append(
            f"Requested {size} positions but only {plan.planned} could be "
            f"allocated; the inventory does not contain enough distinct "
            f"eligible domains.")

    _add_balance_warnings(plan)
    return plan, cells


def _add_balance_warnings(plan: SamplePlan) -> None:
    """Warn when the cohort cannot support the comparison it exists for."""
    filled = [c for c in plan.cells if c.requested > 0]
    if not filled:
        return

    thin = [c.stratum for c in filled if c.requested < MIN_PER_CELL_FOR_POWER]
    if thin:
        plan.warnings.append(
            f"{len(thin)} cell(s) have fewer than {MIN_PER_CELL_FOR_POWER} "
            f"positions and will contribute little: {', '.join(sorted(thin)[:6])}"
            + (" ..." if len(thin) > 6 else ""))

    depth_bands = {c.depth_band for c in filled}
    if len(depth_bands) < 2:
        plan.warnings.append(
            f"Only one buyer-depth band is populated ({', '.join(depth_bands)}). "
            f"Buyer depth does not vary in this cohort, so its effect cannot be "
            f"measured at all. Widen the company file before drawing.")

    # The decisive check: is there buyer-depth variation WITHIN score bands? If
    # every score band contains only one depth band, the two are collinear in
    # this cohort and no amount of outcome data will separate them.
    by_score: dict[str, set[str]] = defaultdict(set)
    for cell in filled:
        by_score[cell.score_band].add(cell.depth_band)
    varying = [band for band, depths in by_score.items() if len(depths) >= 2]
    if not varying:
        plan.warnings.append(
            "CONFOUNDED: no score band contains more than one buyer-depth band. "
            "Buyer depth and opportunity score move together throughout this "
            "cohort, so their effects cannot be told apart no matter how many "
            "outcomes arrive. Widen the inventory before relying on this sample.")
    elif len(varying) < 2:
        plan.warnings.append(
            f"Only one score band ({varying[0]}) contains buyer-depth "
            f"variation. Attribution between depth and score will be weak.")


def draw_sample(session: Session, *, size: int, cohort: str,
                run_id: int | None = None, seed: int = 0,
                max_price: float | None = None, banding: str = "quantile",
                dry_run: bool = False, notes: str | None = None) -> SampleResult:
    """Open a stratified cohort of paper positions.

    Each position freezes the prediction as it stands now, tagged with its
    cohort and stratum. Status follows the model's own recommendation, so the
    cohort records what the model would have done rather than what we wish it
    had.
    """
    plan, cells = plan_sample(session, size=size, cohort=cohort, run_id=run_id,
                              seed=seed, max_price=max_price, banding=banding)
    result = SampleResult(plan=plan, dry_run=dry_run)
    if not cells:
        return result

    allocation = {c.stratum: c.requested for c in plan.cells}
    for stratum, wanted in allocation.items():
        taken = 0
        for score, domain in cells[stratum]:
            if taken >= wanted:
                break
            status = STATUS_BY_RECOMMENDATION.get(score.recommendation, "PAPER_WATCH")
            entry = {"domain": domain.name, "stratum": stratum,
                     "status": status, "recommendation": score.recommendation,
                     "opportunity_score": score.score,
                     "buyer_count": score.buyer_count,
                     "asking_price": score.acquisition_price}
            if dry_run:
                result.opened.append(entry)
                taken += 1
                continue
            try:
                position = open_position(
                    session, domain.name, status=status, run_id=plan.run_id,
                    notes=notes or f"stratified sample '{cohort}'",
                    sample_cohort=cohort, sample_stratum=stratum)
            except PaperPortfolioError as exc:
                result.skipped.append({"domain": domain.name, "reason": str(exc)})
                continue
            entry["position_id"] = position.id
            result.opened.append(entry)
            taken += 1

        for cell in plan.cells:
            if cell.stratum == stratum:
                cell.sampled = taken
                cell.shortfall = max(0, wanted - taken)

    short = sum(c.shortfall for c in plan.cells)
    if short:
        plan.warnings.append(
            f"{short} planned position(s) could not be opened; see 'skipped'.")
    return result


# --------------------------------------------------------------------------
# cohort diagnostics
# --------------------------------------------------------------------------

@dataclass
class CohortHealth:
    """Can this cohort answer the question it was drawn for?"""

    cohort: str | None
    positions: int
    resolved: int
    by_score_band: dict[str, int] = field(default_factory=dict)
    by_depth_band: dict[str, int] = field(default_factory=dict)
    by_stratum: dict[str, int] = field(default_factory=dict)
    by_recommendation: dict[str, int] = field(default_factory=dict)
    score_bands_with_depth_variation: list[str] = field(default_factory=list)
    confounded: bool = False
    can_measure_recall: bool = False
    verdict: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def cohort_health(session: Session, cohort: str | None = None) -> CohortHealth:
    """Structural check on a cohort, independent of any outcomes.

    Worth running the day a cohort is drawn: a confounded or one-sided sample
    will not become informative by waiting, and finding that out immediately is
    far cheaper than finding it out in eighteen months.
    """
    query = select(PaperPosition)
    if cohort is not None:
        query = query.where(PaperPosition.sample_cohort == cohort)
    positions = session.execute(query).scalars().all()

    health = CohortHealth(cohort=cohort, positions=len(positions),
                          resolved=sum(1 for p in positions if p.outcome))
    if not positions:
        health.verdict = "No positions in this cohort."
        return health

    by_score: dict[str, set[str]] = defaultdict(set)
    for position in positions:
        # Prefer the stratum the position was drawn under. Recomputing it from
        # today's corpus would silently re-band an old cohort against a
        # distribution it was never part of.
        if position.sample_stratum and "|" in position.sample_stratum:
            s_band, d_band = position.sample_stratum.split("|", 1)
        else:
            snapshot = position.signal_snapshot or {}
            score = position.opportunity_score
            depth = snapshot.get("buyer_depth_count")
            fallback = Banding(kind="absolute")
            s_band = fallback.score_band(score) if score is not None else "unknown"
            d_band = (fallback.depth_band(int(depth)) if depth is not None
                      else "unknown")

        health.by_score_band[s_band] = health.by_score_band.get(s_band, 0) + 1
        health.by_depth_band[d_band] = health.by_depth_band.get(d_band, 0) + 1
        key = position.sample_stratum or f"{s_band}|{d_band}"
        health.by_stratum[key] = health.by_stratum.get(key, 0) + 1
        rec = position.recommendation or "UNKNOWN"
        health.by_recommendation[rec] = health.by_recommendation.get(rec, 0) + 1
        by_score[s_band].add(d_band)

    health.score_bands_with_depth_variation = sorted(
        band for band, depths in by_score.items() if len(depths) >= 2)
    health.confounded = not health.score_bands_with_depth_variation

    negatives = sum(count for rec, count in health.by_recommendation.items()
                    if rec in {"PASS", "AVOID"})
    positives = sum(count for rec, count in health.by_recommendation.items()
                    if rec in {"BUY", "STRONG_BUY"})
    health.can_measure_recall = negatives >= MIN_PER_CELL_FOR_POWER

    if health.confounded:
        health.warnings.append(
            "CONFOUNDED: buyer depth does not vary within any score band, so "
            "their effects cannot be separated in this cohort.")
    if not health.can_measure_recall:
        health.warnings.append(
            f"Only {negatives} position(s) on names the model rated PASS or "
            f"AVOID. Without a control group the cohort can measure precision "
            f"but not recall, and cannot falsify the score.")
    if positives == 0:
        health.warnings.append(
            "No positions on names the model rated BUY or STRONG_BUY. "
            "Precision on the model's actual picks will be unmeasurable.")

    parts = [f"{len(positions)} position(s) across "
             f"{len(health.by_stratum)} stratum/strata, "
             f"{health.resolved} resolved."]
    if health.confounded:
        parts.append("Buyer depth is confounded with score - this cohort "
                     "cannot attribute an effect to either.")
    elif health.can_measure_recall:
        parts.append(
            f"Buyer depth varies within "
            f"{len(health.score_bands_with_depth_variation)} score band(s) and "
            f"{negatives} control position(s) are present, so both precision "
            f"and recall are measurable once outcomes arrive.")
    else:
        parts.append("Depth variation is present but the control group is thin.")
    health.verdict = " ".join(parts)
    return health
