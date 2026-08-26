"""End-user buyer discovery.

This is the module the whole thesis rests on. The hypothesis under test is that
*buyer depth* - how many real organisations could rationally want this exact
name, weighted by their ability to pay - predicts resale better than search
volume or CPC.

To test that hypothesis the buyer list has to be real. So:

  * Companies are never generated. They come from a source record: an uploaded
    company file, or (later) a live company/SERP API.
  * The *match* between a company and a domain is derived here, deterministically,
    with a named match type and a human-readable reason.
  * Every candidate keeps its ``evidence_url`` so a human can check it.
  * "We didn't look" and "we looked and found nobody" are different results and
    are represented differently (``BuyerSearchResult.searched``).

``ExampleFixtureBuyerProvider`` exists so the pipeline can be demonstrated with
no data sources at all. Its output is tagged ``FIXTURE`` and is refused unless
``ALLOW_FIXTURE_DATA=true``.
"""

from __future__ import annotations

import csv
import datetime as _dt
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from app.providers.base import (BuyerCandidateRecord, BuyerProvider,
                                BuyerSearchResult)
from app.provenance import Provenance, utcnow
from app.scoring.features import GENERIC_MODIFIERS
from app.scoring.lexicon import segment

NO_SOURCE_NOTE = (
    "No buyer data source configured. Set BUYER_PROVIDER=csv and "
    "BUYER_COMPANY_CSV_PATH to a company file, or implement a live provider."
)

_LEGAL_SUFFIXES = {"inc", "llc", "ltd", "limited", "corp", "corporation", "co",
                   "company", "gmbh", "bv", "nv", "ag", "sa", "srl", "plc",
                   "group", "holdings", "holding", "pty", "ab", "oy", "as"}

# Match types, in descending order of how strongly they imply the company would
# want this exact name. Base scores are hand-set V0 priors like everything else.
# Length of the prefix/suffix key used to bucket company names for the
# "longer variant" strategy. 4 is short enough to catch real extensions and
# long enough to keep each bucket small.
AFFIX_KEY_LENGTH = 4

MATCH_BASE_SCORES = {
    "exact_alt_tld": 95.0,
    "name_exact": 88.0,
    "modifier_stripped": 85.0,
    "separator_variant": 80.0,
    "name_extended": 62.0,
    "weak_domain_industry": 50.0,
    "industry_keyword": 38.0,
}

MATCH_REASONS = {
    "exact_alt_tld": "Operates on the same second-level name under a different extension",
    "name_exact": "Company name matches the domain exactly",
    "modifier_stripped": "Current domain is the same name plus a filler modifier",
    "separator_variant": "Current domain is a hyphen/digit variant of the same name",
    "name_extended": "Current domain is a longer variant built on the same root",
    "weak_domain_industry": "Operates in the matching industry on a weak current domain",
    "industry_keyword": "Operates in the industry the domain describes",
}


def _norm_name(text: str) -> str:
    """Company name -> comparable token string ('XYZ Fleet Systems, Inc.' -> 'xyzfleetsystems')."""
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    while tokens and tokens[-1] in _LEGAL_SUFFIXES:
        tokens.pop()
    return "".join(tokens)


def _strip_modifiers(sld: str) -> str:
    """Remove leading/trailing filler words: 'getflow' -> 'flow'."""
    words, _ = segment(re.sub(r"[^a-z]", "", sld.lower()))
    words = list(words)
    changed = True
    while changed and len(words) > 1:
        changed = False
        if words[0] in GENERIC_MODIFIERS:
            words.pop(0)
            changed = True
        if len(words) > 1 and words[-1] in GENERIC_MODIFIERS:
            words.pop()
            changed = True
    return "".join(words)


def _canonical(sld: str) -> str:
    """Strip hyphens and digits for variant comparison."""
    return re.sub(r"[^a-z]", "", sld.lower())


def domain_weakness(company_domain: str | None) -> tuple[float, list[str]]:
    """0..100 score for how poor a company's current domain is, plus reasons.

    A company already on the perfect .com has no reason to buy. A company on
    ``get-fleet-analytics-hq.io`` has several.
    """
    if not company_domain:
        return 0.0, []
    parts = company_domain.lower().split(".")
    if len(parts) < 2:
        return 0.0, []
    sld, tld = parts[0], ".".join(parts[1:])
    reasons: list[str] = []
    score = 0.0
    if tld != "com":
        score += 30.0
        reasons.append(f"uses .{tld} rather than .com")
    if "-" in sld:
        score += 25.0
        reasons.append("hyphenated domain")
    if any(c.isdigit() for c in sld):
        score += 20.0
        reasons.append("digits in domain")
    if len(sld) > 18:
        score += 15.0
        reasons.append(f"long domain ({len(sld)} characters)")
    words, _ = segment(_canonical(sld))
    if any(w in GENERIC_MODIFIERS for w in words):
        mods = [w for w in words if w in GENERIC_MODIFIERS]
        score += 20.0
        reasons.append(f"uses filler modifier(s): {', '.join(mods)}")
    if len(words) >= 4:
        score += 10.0
        reasons.append("four or more words in domain")
    return min(100.0, score), reasons


@dataclass
class CompanyRecord:
    """One company as read from a source file. Nothing here is invented."""

    company_name: str
    company_domain: str | None
    industry: str | None = None
    keywords: list[str] | None = None
    employee_count: int | None = None
    revenue_usd: float | None = None
    funding_usd: float | None = None
    funding_currency: str | None = None
    last_funding_date: _dt.datetime | None = None
    evidence_url: str | None = None
    country: str | None = None

    @property
    def sld(self) -> str:
        if not self.company_domain:
            return ""
        return self.company_domain.lower().split(".")[0]

    @property
    def tld(self) -> str:
        if not self.company_domain or "." not in self.company_domain:
            return ""
        return self.company_domain.lower().split(".", 1)[1]


def size_bucket(employees: int | None, revenue: float | None) -> str | None:
    if employees is None and revenue is None:
        return None
    if employees is not None:
        if employees < 10:
            return "micro (<10)"
        if employees < 50:
            return "small (10-49)"
        if employees < 250:
            return "mid (50-249)"
        if employees < 1000:
            return "large (250-999)"
        return "enterprise (1000+)"
    assert revenue is not None
    if revenue < 1e6:
        return "micro (<$1M revenue)"
    if revenue < 1e7:
        return "small (<$10M revenue)"
    if revenue < 1e8:
        return "mid (<$100M revenue)"
    return "large ($100M+ revenue)"


def buyer_value_score(company: CompanyRecord) -> tuple[float, float, str]:
    """Economic weight of a buyer, 0..100, plus confidence and a basis note.

    Returns confidence 0.0 when *no* economic field is known. In that case the
    score is 0 and must be treated as UNKNOWN, not as "worthless buyer".
    """
    import math

    signals: list[tuple[float, float]] = []   # (score, weight)
    basis: list[str] = []

    if company.employee_count is not None and company.employee_count > 0:
        # log scale: 10 employees -> ~33, 100 -> ~50, 10k -> ~83
        s = min(100.0, math.log10(company.employee_count + 1) / 4.5 * 100.0)
        signals.append((s, 0.35))
        basis.append(f"{company.employee_count} employees")
    if company.revenue_usd is not None and company.revenue_usd > 0:
        s = min(100.0, math.log10(company.revenue_usd + 1) / 9.0 * 100.0)
        signals.append((s, 0.35))
        basis.append(f"${company.revenue_usd:,.0f} revenue")
    if company.funding_usd is not None and company.funding_usd > 0:
        s = min(100.0, math.log10(company.funding_usd + 1) / 9.0 * 100.0)
        weight = 0.30
        if company.last_funding_date is not None:
            age_days = (utcnow() - company.last_funding_date).days
            if age_days <= 540:
                # Recently funded companies rebrand and buy domains.
                s = min(100.0, s * 1.15)
                weight = 0.40
                basis.append("funded within 18 months")
        signals.append((s, weight))
        basis.append(f"${company.funding_usd:,.0f} raised")

    if not signals:
        return 0.0, 0.0, "no economic data available for this company"

    total_w = sum(w for _, w in signals)
    score = sum(s * w for s, w in signals) / total_w
    # Confidence rises with how many independent economic signals we have.
    confidence = min(0.9, 0.35 + 0.2 * len(signals))
    return round(score, 2), confidence, "; ".join(basis)


class NullBuyerProvider(BuyerProvider):
    """Looks for nobody, and says so."""

    name = "buyer.null"

    @property
    def available(self) -> bool:
        return False

    def find_buyers(self, domain, sld, tld, words, category=None, limit=50):
        return BuyerSearchResult(candidates=[], provenance=Provenance.MISSING,
                                 source=self.name, searched=False,
                                 note=NO_SOURCE_NOTE)


class CompanyFileBuyerProvider(BuyerProvider):
    """Deterministic buyer matching against a company file you supply.

    Expected CSV columns (case-insensitive; ``company_name`` required, and at
    least one of ``company_domain`` / ``industry``)::

        company_name,company_domain,industry,keywords,employee_count,
        revenue_usd,funding_usd,funding_currency,last_funding_date,
        evidence_url,country

    Where to get one: your CRM, a Crunchbase/PitchBook export, an OpenCorporates
    extract, a Common Crawl host list joined to an industry classifier, or a
    scraped list of advertisers bidding on the relevant keyword.
    """

    name = "buyer.company_file"
    default_provenance = Provenance.OBSERVED

    def __init__(self, path: Path | None, *, provenance: Provenance | None = None,
                 source_label: str | None = None) -> None:
        self.path = Path(path) if path else None
        self.provenance = provenance or self.default_provenance
        self.source_label = source_label or self.name
        self._companies: list[CompanyRecord] = []
        self._by_sld: dict[str, list[CompanyRecord]] = defaultdict(list)
        self._by_canonical: dict[str, list[CompanyRecord]] = defaultdict(list)
        self._by_stripped: dict[str, list[CompanyRecord]] = defaultdict(list)
        self._by_name: dict[str, list[CompanyRecord]] = defaultdict(list)
        self._by_token: dict[str, list[CompanyRecord]] = defaultdict(list)
        # Prefix/suffix buckets for the "longer name built on the same root"
        # strategy. Without them that strategy is a full scan of the company
        # file per domain, which is O(domains x companies) - fine for a 40-row
        # example file, fatal for 10,000 domains against 100,000 companies.
        self._by_prefix: dict[str, list[CompanyRecord]] = defaultdict(list)
        self._by_suffix: dict[str, list[CompanyRecord]] = defaultdict(list)
        self._loaded = False

    # -- loading ------------------------------------------------------------
    @property
    def available(self) -> bool:
        return bool(self.path and self.path.exists())

    @staticmethod
    def _int(v: str | None) -> int | None:
        if not v:
            return None
        try:
            return int(float(str(v).replace(",", "").strip()))
        except ValueError:
            return None

    @staticmethod
    def _float(v: str | None) -> float | None:
        if not v:
            return None
        try:
            return float(str(v).replace("$", "").replace(",", "").strip())
        except ValueError:
            return None

    @staticmethod
    def _date(v: str | None) -> _dt.datetime | None:
        if not v:
            return None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m"):
            try:
                return _dt.datetime.strptime(v.strip(), fmt).replace(
                    tzinfo=_dt.timezone.utc)
            except ValueError:
                continue
        return None

    def load(self) -> int:
        if self._loaded:
            return len(self._companies)
        self._loaded = True
        if not self.available:
            return 0
        assert self.path is not None
        with self.path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                low = {(k or "").strip().lower(): (v or "").strip()
                       for k, v in row.items()}
                name = low.get("company_name") or ""
                if not name:
                    continue
                kw = [k.strip().lower() for k in
                      re.split(r"[;|,]", low.get("keywords", "")) if k.strip()]
                rec = CompanyRecord(
                    company_name=name,
                    company_domain=(low.get("company_domain") or None),
                    industry=(low.get("industry") or None),
                    keywords=kw or None,
                    employee_count=self._int(low.get("employee_count")),
                    revenue_usd=self._float(low.get("revenue_usd")),
                    funding_usd=self._float(low.get("funding_usd")),
                    funding_currency=(low.get("funding_currency") or None),
                    last_funding_date=self._date(low.get("last_funding_date")),
                    evidence_url=(low.get("evidence_url") or None),
                    country=(low.get("country") or None),
                )
                self._index(rec)
        return len(self._companies)

    def _index(self, rec: CompanyRecord) -> None:
        self._companies.append(rec)
        if rec.sld:
            self._by_sld[rec.sld].append(rec)
            self._by_canonical[_canonical(rec.sld)].append(rec)
            stripped = _strip_modifiers(rec.sld)
            if stripped and stripped != _canonical(rec.sld):
                self._by_stripped[stripped].append(rec)
        norm = _norm_name(rec.company_name)
        if norm:
            self._by_name[norm].append(rec)
        tokens = set()
        for field_value in (rec.industry or "", " ".join(rec.keywords or [])):
            tokens.update(re.findall(r"[a-z]{3,}", field_value.lower()))
        if rec.sld:
            tokens.update(w for w in segment(_canonical(rec.sld))[0] if len(w) >= 3)
        for tok in tokens:
            self._by_token[tok].append(rec)
        canon = _canonical(rec.sld)
        if len(canon) >= AFFIX_KEY_LENGTH:
            self._by_prefix[canon[:AFFIX_KEY_LENGTH]].append(rec)
            self._by_suffix[canon[-AFFIX_KEY_LENGTH:]].append(rec)

    # -- matching -----------------------------------------------------------
    def _make(self, rec: CompanyRecord, match_type: str, target: str,
              extra_reason: str = "") -> BuyerCandidateRecord:
        weakness, weak_reasons = domain_weakness(rec.company_domain)
        base = MATCH_BASE_SCORES[match_type]
        # A weak current domain raises the chance they actually move. Capped so
        # it adjusts rather than dominates the match type.
        match_score = min(100.0, base + 0.15 * weakness)
        value, value_conf, value_basis = buyer_value_score(rec)

        reason = MATCH_REASONS[match_type]
        if extra_reason:
            reason = f"{reason}; {extra_reason}"
        if weak_reasons:
            reason = f"{reason}. Current-domain weaknesses: {', '.join(weak_reasons)}"
        if value_basis:
            reason = f"{reason}. Economic basis: {value_basis}"

        return BuyerCandidateRecord(
            company_name=rec.company_name,
            company_domain=rec.company_domain,
            reason_for_match=reason,
            match_type=match_type,
            match_score=round(match_score, 2),
            buyer_value_score=value,
            provenance=self.provenance,
            source=self.source_label,
            evidence_url=rec.evidence_url,
            company_size_estimate=size_bucket(rec.employee_count, rec.revenue_usd),
            employee_count=rec.employee_count,
            funding_if_known=rec.funding_usd,
            funding_currency=rec.funding_currency,
            last_funding_date=rec.last_funding_date,
            industry=rec.industry,
            # Confidence blends how sure we are of the match with how much we
            # know about the company's economics.
            confidence=round(min(0.95, 0.4 + 0.5 * (match_score / 100.0)) *
                             (0.6 + 0.4 * value_conf), 3),
        )

    def find_buyers(self, domain: str, sld: str, tld: str, words: list[str],
                    category: str | None = None,
                    limit: int = 50) -> BuyerSearchResult:
        if not self.available:
            return BuyerSearchResult([], Provenance.MISSING, self.source_label,
                                     searched=False,
                                     note=f"company file not found at {self.path}")
        self.load()
        target_canon = _canonical(sld)
        seen: dict[tuple[str, str], BuyerCandidateRecord] = {}

        def add(rec: CompanyRecord, mtype: str, extra: str = "") -> None:
            if rec.company_domain and rec.company_domain.lower() == domain.lower():
                return  # they already own it
            key = (rec.company_domain or rec.company_name, mtype)
            if key in seen:
                return
            seen[key] = self._make(rec, mtype, sld, extra)

        # 1. same name, different extension - the single strongest signal.
        for rec in self._by_sld.get(sld, []):
            if rec.tld != tld:
                add(rec, "exact_alt_tld", f"currently on .{rec.tld}")

        # 2. company name is literally the domain.
        for rec in self._by_name.get(target_canon, []):
            add(rec, "name_exact")

        # 3. their domain is ours plus a filler modifier (getflow -> flow).
        for rec in self._by_stripped.get(target_canon, []):
            add(rec, "modifier_stripped", f"currently on {rec.company_domain}")

        # 4. hyphen/digit variant of the same name.
        for rec in self._by_canonical.get(target_canon, []):
            if rec.sld != sld:
                add(rec, "separator_variant", f"currently on {rec.company_domain}")

        # 5. longer name built on the same root (fleetanalytics ->
        # fleetanalyticssystems). Candidates come from the affix buckets rather
        # than a full scan; the exact test is still applied below.
        if len(target_canon) >= AFFIX_KEY_LENGTH:
            affix_pool = (self._by_prefix.get(target_canon[:AFFIX_KEY_LENGTH], [])
                          + self._by_suffix.get(target_canon[-AFFIX_KEY_LENGTH:], []))
            for rec in affix_pool:
                c = _canonical(rec.sld)
                if not c or c == target_canon or len(c) <= len(target_canon):
                    continue
                if c.startswith(target_canon) or c.endswith(target_canon):
                    add(rec, "name_extended", f"currently on {rec.company_domain}")

        # 6/7. industry and keyword overlap. Requires a shared meaningful token,
        # and is only credited when we have at least two words of context or an
        # explicit industry match, to keep this from matching everything.
        content_words = [w for w in words if len(w) >= 4]
        if content_words:
            counts: dict[int, int] = defaultdict(int)
            pool: dict[int, CompanyRecord] = {}
            for tok in content_words:
                for rec in self._by_token.get(tok, []):
                    counts[id(rec)] += 1
                    pool[id(rec)] = rec
            for rid, overlap in counts.items():
                rec = pool[rid]
                if overlap < 1:
                    continue
                weakness, _ = domain_weakness(rec.company_domain)
                matched = [w for w in content_words
                           if rec in self._by_token.get(w, [])]
                extra = f"shares term(s): {', '.join(matched)}"
                if weakness >= 30:
                    add(rec, "weak_domain_industry", extra)
                elif overlap >= 2 or (category and rec.industry and
                                      category.lower() in rec.industry.lower()):
                    add(rec, "industry_keyword", extra)

        # Keep the best match type per company rather than double-counting.
        best_per_company: dict[str, BuyerCandidateRecord] = {}
        for cand in seen.values():
            ident = (cand.company_domain or cand.company_name).lower()
            prev = best_per_company.get(ident)
            if prev is None or cand.match_score > prev.match_score:
                best_per_company[ident] = cand

        results = sorted(best_per_company.values(),
                         key=lambda c: (c.match_score, c.buyer_value_score),
                         reverse=True)[:limit]
        return BuyerSearchResult(
            candidates=results, provenance=self.provenance,
            source=self.source_label, searched=True,
            note=(None if results else
                  "searched the company file and found no credible buyer"))


class ExampleFixtureBuyerProvider(CompanyFileBuyerProvider):
    """Same matching engine, pointed at the synthetic example company file.

    Everything it returns is tagged FIXTURE. It exists so ``make demo`` shows a
    populated pipeline; it is not evidence and the API refuses to serve it
    unless ``ALLOW_FIXTURE_DATA=true``.
    """

    name = "buyer.example_fixture"
    default_provenance = Provenance.FIXTURE

    def __init__(self, path: Path) -> None:
        super().__init__(path, provenance=Provenance.FIXTURE,
                         source_label=self.name)


def build_buyer_provider(kind: str, csv_path: Path | None, *,
                         allow_fixture: bool = False,
                         fixture_path: Path | None = None) -> BuyerProvider:
    if kind == "csv" and csv_path:
        return CompanyFileBuyerProvider(csv_path)
    if kind == "fixture" or (allow_fixture and fixture_path and not csv_path):
        if fixture_path:
            return ExampleFixtureBuyerProvider(fixture_path)
    return NullBuyerProvider()
