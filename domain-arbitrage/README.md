# Domain Arbitrage Intelligence Engine

A research and ranking engine for finding domain names priced materially below
their likely end-user resale value.

It answers one question: **which domains available today have the highest
expected return on capital, why, and who might buy them?** It is not a trading
platform. It buys nothing and bids on nothing. It produces a ranked table, a
defensible explanation for every number in it, and a paper portfolio that
records predictions so the model can be judged later against what actually
happened.

---

## Read this first

**Every valuation and probability this system produces comes from an
UNCALIBRATED V0 heuristic.** Not one coefficient has been fitted to observed
domain sales, because this repository ships with no outcome data. The numbers
are stated priors with an audit trail, not estimates with error bars.

That is deliberate. The alternative — inventing a sophisticated-looking model
with forty tuned weights and no data behind any of them — produces output that
*looks* far more trustworthy than it is. Everything here is designed so you can
see exactly how crude it is:

- every weight lives in one commented YAML file with a stated rationale
- every number decomposes into the inputs that produced it
- every missing field is recorded as MISSING and never silently defaulted
- the config version is stamped on every prediction, so old predictions stay
  reproducible when the model changes

The route from V0 to something worth capital runs through the paper portfolio,
not through more elaborate weights.

### The empirical question this is built to answer

> Does **buyer depth** — the number of genuinely plausible end buyers, weighted
> by their economic value — predict domain resale better than traditional
> metrics such as search volume and CPC?

Buyer depth is therefore a first-class object: computed separately, stored
separately, frozen onto every paper position at prediction time, and tested
directly at `GET /api/analysis/signal-power`. Today that endpoint reports
`UNDETERMINED` and will keep doing so until roughly twenty outcomes exist. That
is the correct answer, not a bug.

---

## Quick start

```bash
make install      # python3.12 venv + dependencies
make demo         # full pipeline on the bundled example data
make test         # 244 tests
make serve        # dashboard + API on http://localhost:8000
make sensitivity  # which conclusions survive being wrong about the priors?
make paper-buy    # draw a stratified paper cohort (dry run first)
```

`make demo` runs with `ALLOW_FIXTURE_DATA=true` and synthetic example companies,
so it demonstrates a populated pipeline without pretending to know anything real.
Every buyer it finds is tagged `FIXTURE`.

For real work:

```bash
cp .env.example .env
# point BUYER_COMPANY_CSV_PATH at a real company dataset
# point KEYWORD_CSV_PATH at a real keyword export
python scripts/load_comparables.py namebio_export.csv --source namebio
```

---

## 1. Repository structure

```
domain-arbitrage/
├── app/
│   ├── config.py                  settings from .env
│   ├── provenance.py              Sourced[T]: value + source + time + confidence
│   ├── main.py                    FastAPI app + dashboard
│   ├── api/routes.py              HTTP surface
│   ├── db/
│   │   ├── base.py                engine, session, UTC datetime type
│   │   └── init_db.py             schema creation
│   ├── models/
│   │   ├── core.py                Domain, Listing, DomainFeatures, Enrichment
│   │   ├── analysis.py            buyers, comps, valuation, probability, score
│   │   └── paper.py               PaperPosition, PaperObservation
│   ├── providers/                 the only place external data enters
│   │   ├── base.py                Provider protocols
│   │   ├── keyword.py             Null + CSV keyword providers
│   │   ├── buyer.py               buyer discovery and matching
│   │   └── llm.py                 LLM with content-addressed cache
│   ├── scoring/                   pure functions, no I/O
│   │   ├── config.py              versioned weights loader
│   │   ├── lexicon.py             dictionary, segmentation, syllables
│   │   ├── features.py            structural + linguistic features
│   │   ├── taxonomy.py            industry keywords, geography
│   │   ├── classify.py            deterministic classification, optional LLM
│   │   ├── buyer_depth.py         the signal under test
│   │   ├── comparables.py         comp selection and statistics
│   │   ├── valuation.py           wholesale / retail / strategic
│   │   ├── probability.py         log-odds sale model
│   │   └── opportunity.py         economics, ranking, recommendation
│   ├── services/
│   │   ├── normalize.py           domain normalisation and dedupe
│   │   ├── ingest.py              CSV import
│   │   ├── feed_mapping.py        third-party export column mapping
│   │   ├── pipeline.py            stage orchestration
│   │   ├── providers_registry.py  which sources are live for a run
│   │   ├── paper_portfolio.py     frozen predictions, observed outcomes
│   │   ├── paper_sampler.py       stratified cohort sampling
│   │   ├── reconcile.py           resolve positions against observed sales
│   │   ├── portfolio.py           budget allocation
│   │   └── report.py              daily opportunity report
│   ├── analysis/
│   │   ├── signal_power.py    does buyer depth actually predict?
│   │   ├── rescore.py         replay the config-dependent stages in memory
│   │   └── sensitivity.py     which conclusions survive being wrong?
│   └── templates/dashboard.html
├── config/scoring_v0.yaml         EVERY weight, with rationales
├── data/
│   ├── examples/                  SYNTHETIC example files
│   └── comparable_sales_TEMPLATE.csv
├── scripts/                       demo, comps loader, load test
└── tests/                         129 tests
```

The layering rule: `scoring/` is pure — no database, no network, no clock
dependence beyond timestamps. `providers/` touches the outside world.
`services/` orchestrates. That is what makes the scoring layer testable by
inspection.

---

## 2. Database schema

Fifteen tables. The shape follows the design principle that DATA, FEATURES,
VALUATION, PROBABILITY and DECISION stay separate, so any published number can
be walked backwards to the raw imported row.

| Table | Holds | Provenance |
|---|---|---|
| `import_batches` | one CSV upload, with rejection counts | OBSERVED |
| `domains` | one row per unique normalised name, ever | OBSERVED |
| `listings` | an observed offer: price, venue, auction end, raw row | OBSERVED |
| `domain_features` | ~30 deterministic structural + linguistic features | DERIVED |
| `enrichments` | generic field store: value, provenance, source, retrieved_at, confidence, evidence_url | any |
| `buyer_candidates` | a company that could want this name, with match type, reason, evidence | OBSERVED / FIXTURE |
| `comparable_sales` | recorded domain sales — **ships empty** | OBSERVED |
| `comparable_matches` | which comps were used for which domain, and why | DERIVED |
| `valuations` | wholesale / retail / strategic ranges + full multiplier walk | ESTIMATED |
| `sale_probabilities` | 12/24/36-month probabilities + every log-odds term | ESTIMATED |
| `opportunity_scores` | score, components, economics, recommendation, explanation | ESTIMATED |
| `pipeline_runs` | config stamp, live providers, data gaps, warnings | — |
| `paper_positions` | a frozen prediction + its signal snapshot | ESTIMATED |
| `paper_observations` | what actually happened | OBSERVED |
| `llm_cache` | content-addressed LLM responses | — |

**Why a generic `enrichments` table.** The requirement is that *every* enriched
field carries value + source + retrieved_at + confidence. A wide table cannot do
that without quadrupling its column count, and it could not represent "we asked
and there was no answer". A field we failed to source is still written, marked
MISSING, which is what makes the coverage report honest.

**PostgreSQL.** SQLite is the default. Nothing in the model layer uses
SQLite-specific types or behaviour: JSON columns use SQLAlchemy's portable type,
timestamps are timezone-aware through a custom `UtcDateTime`, and no
`AUTOINCREMENT` or `PRAGMA` semantics are relied on. Changing `DATABASE_URL` is
the migration. Add Alembic when the schema starts moving.

---

## 3. Scoring methodology

Five stages, strictly one-directional. Nothing reads backwards.

```
raw listing
   ↓  deterministic parsing
features  (length, words, syllables, brandability, …)
   ↓  taxonomy lookup, optional LLM
classification  (industry, intent, geography)
   ↓  company-file matching
buyer depth  (count, strong count, depth value, max buyer value)
   ↓  similarity search over recorded sales
comparables  (weighted median, IQR, confidence)
   ↓  multiplicative heuristic + log-space comp blend
valuation  (wholesale / retail / strategic ranges + confidence)
   ↓  log-odds model
sale probability  (12 / 24 / 36 months)
   ↓  arithmetic
expected value  (profit, ROI, maximum bid)
   ↓  weighted sum + hard gates
ranking and recommendation
```

### 3.1 Features — DERIVED

Pure functions of the domain string plus a frozen lexicon. Word segmentation
uses a unigram language model over corpus frequencies (`wordfreq`), maximising
the sum of token log-probabilities. Because every token contributes a *negative*
score, a split only happens when it genuinely explains the string better:
`datacentercooling` → `data|center|cooling`, and `xkqzp` stays one token with
segmentation confidence 0.

The six linguistic scores (pronounceability, memorability, spelling ambiguity,
semantic coherence, brandability, business-name plausibility) are bounded 0–100
composites of deterministic parts, each storing its own component breakdown.
Brandability has a hard gate: below 55 pronounceability the score is scaled down
proportionally, so an unsayable string cannot score well merely for being short.
Invented-but-sayable names (`zillow`, `kajabi`) pass that gate, which is exactly
the distinction wanted.

### 3.2 Buyer depth — the signal under test

A candidate buyer is produced by matching a company from a source file against
the domain. Seven match types, in descending strength:

| Match type | Base score | Meaning |
|---|---|---|
| `exact_alt_tld` | 95 | same second-level name on a different extension |
| `name_exact` | 88 | company name *is* the domain |
| `modifier_stripped` | 85 | their domain is ours plus filler (`getflow` → `flow`) |
| `separator_variant` | 80 | hyphen/digit variant of the same name |
| `name_extended` | 62 | longer name on the same root |
| `weak_domain_industry` | 50 | right industry, poor current domain |
| `industry_keyword` | 38 | right industry |

A weak current domain (non-`.com`, hyphens, digits, filler words, excessive
length) adds up to 15 points, because a company already on the perfect `.com`
has no reason to buy. `buyer_value_score` is a log-scaled blend of employees,
revenue and funding, with a bump for funding raised in the last 18 months — and
is **zero confidence when no economic field is known**, so "we don't know how big
they are" never reads as "they are worthless".

Depth is then five separate quantities — `count`, `strong_count`, `depth_value`,
`max_buyer_value`, `economic_coverage` — rather than one blend, because the point
is to discover *which* of them carries information.

The single most important distinction in the system lives here:
`BuyerDepth.missing` separates **"we did not look"** from **"we looked and found
nobody"**. The first is ignorance; the second is a finding. They must never be
scored alike, and a test enforces it.

### 3.3 Valuation — ESTIMATED

```
retail_mid = base(tld) × ∏(multipliers)      then blended with comps in log space
```

Multiplicative and flat: no interaction terms, no ensemble, because there is
nothing to learn from yet and a model whose structure you cannot read is a model
you cannot audit. A real walk from the demo:

```
   2,500.00   base for .com
 ×    1.025   length (13-character second-level name)
 ×    1.000   word_count (2 words)
 ×    1.300   dictionary (every token is a dictionary word)
 ×    1.476   brandability (75/100)
 ×    1.828   commercial_intent (65/100, from CPC $6.40 and competition 0.62)
 ×    1.200   buyer_depth (4 credible buyers identified)
= 10,780.96   heuristic retail mid
```

That is the actual stored walk for `berlinroofing.com` in the demo run, read
back from `valuations.components`. A test asserts the product reconstructs the
stored value.

Comparable sales, when available, take up to 60% of the weight — never 100%,
because comp sets are small and survivorship-biased. The blend is in log space,
since an arithmetic average of $500 and $50,000 is meaningless.

Confidence is a **separate axis from value**. It starts at 0.55 (this model is
uncalibrated; nothing should report high confidence), is reduced for missing
keyword and buyer data, and raised by comp evidence. Ranges widen as confidence
falls — at low confidence the reported band is 0.30×–3.2× the midpoint, which is
an honest statement of what a heuristic with no data behind it knows.

**Missing data never moves a multiplier.** When keyword or buyer data is absent,
the multiplier is forced to 1.0 and a confidence penalty is applied instead. A
gap must not be able to flatter a domain.

### 3.4 Sale probability — ESTIMATED

```
logit(p_annual) = logit(base_rate) + Σ (coefficient_i × z_i)
```

Each `z_i` is a bounded driver in [−1, +1], so a coefficient reads directly as
"how much this axis moves the log-odds between a bad and a good domain". Every
term is stored with its z, coefficient and contribution, so a probability
decomposes into "buyer depth added +0.9, the four-word length took away −0.3".

The base annual sell-through rate is **1.5%**. This is the single most
consequential number in the system — it sets the scale of every expected value —
and it is a prior taken from the commonly cited 1–2% range for retail-priced
aftermarket portfolios, not a measurement. Multi-year rollup assumes independent
annual hazards with 0.85 decay, because the best names sell first and the
residual pool gets worse.

MISSING drivers contribute exactly zero and are listed in `data_gaps`. They are
not imputed.

This shape was chosen because it is the shape a logistic regression will take
once the paper portfolio has enough outcomes to fit one. At that point the
`coefficients` block in the YAML gets replaced by fitted values and nothing else
in the codebase changes.

### 3.5 Expected value — arithmetic only

```
expected_sale_value   = P(sale ≤ 24m) × retail_mid
residual_if_unsold    = (1 − P) × wholesale_mid × 0.5
expected_terminal     = expected_sale_value + residual_if_unsold
expected_profit_24m   = expected_terminal − price − renewals − P × retail_mid × commission
expected_roi          = expected_profit / (price + renewals)
recommended_max_bid   = (expected_terminal − costs) × margin_of_safety
```

Two choices worth defending. **Transaction costs are probability-weighted**: you
only pay a commission on a sale. **The unsold branch is not worthless**: a name
that fails to reach an end user can usually be liquidated into the investor
market, and valuing that branch at zero understates every opportunity by roughly
the same amount, distorting the ranking as well as the level. The recovery ratio
(0.5 of modelled wholesale) is configurable and set to a round guess; set it to
0 to model a pure write-off.

**Maximum bid is derived from expected value, not from retail value.** Bidding
against retail means bidding against a price you have only a probability of ever
achieving. The margin of safety is 0.5 — bid at most half the modelled EV —
because a large discount is the only defence against an uncalibrated model.

### 3.6 Ranking and recommendation

Nine components, each normalised 0–100 and stored with its raw value, weight and
contribution:

| Component | Weight |
|---|---|
| valuation_gap | 0.20 |
| capital_efficiency | 0.15 |
| sale_probability | 0.15 |
| **buyer_depth** | **0.15** |
| buyer_quality | 0.08 |
| commercial_intent | 0.08 |
| comparable_confidence | 0.07 |
| brandability | 0.07 |
| liquidity | 0.05 |

Buyer depth gets a deliberately *moderate* weight. Giving the hypothesis under
test a dominant weight would make the ranking circularly confirm it.

"Why did A rank above B" is answered by subtracting the two component vectors —
`GET /api/domains/{name}/explain` prints exactly that.

The raw score is then multiplied down by confidence
(`raw × (0.55 + 0.45 × confidence)`). Without this, a domain with no keyword data
and no buyer search posts a flattering score because nothing contradicted it.
**Ignorance must not be rewarded.**

Recommendation is the score plus hard gates. Negative expected profit forces
AVOID regardless of score. Unknown buyer depth, or expected ROI below 25%, caps
the result at WATCH. Every gate that fired appears in the explanation.

---

## 4. Working features

Verified end to end:

- **CSV import** — normalisation (scheme, `www.`, ports, paths, trailing dots,
  case, IDN → punycode, multi-label public suffixes), deduplication, and
  rejection *with a reason per row*. Re-importing supersedes prior listings and
  keeps price history.
- **Feature extraction** — ~30 structural and linguistic features per domain.
- **Semantic classification** — 31-category taxonomy with 561 keywords, plus
  geographic scope detection; optional LLM refinement when the deterministic
  pass is unsure.
- **Buyer discovery** — seven deterministic match strategies with reasons,
  evidence URLs and economic weighting.
- **Comparable analysis** — weighted median, IQR, dispersion, confidence, with
  every comp used recorded alongside its similarity breakdown.
- **Valuation** — wholesale / retail / strategic ranges with full walk.
- **Sale probability** — 12/24/36 months, every term stored.
- **Expected value, ROI, maximum bid** — reproducible by hand from stored inputs.
- **Ranking** — nine stored components with an explanation layer.
- **Portfolio construction** — three scenarios, budget and exposure caps, with
  the binding constraint reported for every excluded domain.
- **Paper portfolio** — frozen predictions with a signal snapshot, observation
  recording, and a performance report that *withholds statistics* below ten
  resolved outcomes.
- **Stratified sampling and reconciliation** — draw a falsifiable cohort across
  score and buyer-depth bands, resolve it against a sales export, and check
  whether the cohort can answer the question it was drawn for. See §10.
- **Signal-power analysis** — Spearman correlation and AUC per signal against
  observed outcomes, with a plain-language verdict on the buyer-depth hypothesis.
- **Sensitivity and ablation analysis** — sweeps every prior across a grid and
  ablates each ranking component, reporting rank stability and level movement
  separately. See §9.
- **API + dashboard** — 25 endpoints, `/docs`, and a single-page dashboard whose
  every row links into the audit trail.

### Performance

Measured with `make load-test` on 10,000 synthetic domains:

| Stage | Time |
|---|---|
| ingest | 9.0 s |
| pipeline (score all stages) | 12.0 s |
| report (top 50) | 0.1 s |
| portfolio allocation | 3.0 s |
| peak memory | 533 MB |

The success criterion — 10,000 domains in, ranked table with a defensible
explanation for every number out — is met in about 25 seconds. Timings vary by
a factor of two with machine load; re-measure with `make load-test` rather than
trusting this table.

---

## 5. Missing data sources

This is the honest limitations section. **None of these gaps is filled with an
invention.** Each one is reported as MISSING, penalises confidence, and appears
in `data_gaps` on the run and on every affected domain.

| Gap | Impact today | How to close it |
|---|---|---|
| **Comparable sales** — table ships empty | Valuation rests entirely on the heuristic prior; `comparable_confidence` scores 0 for every domain | `scripts/load_comparables.py` with a NameBio / DNJournal / Sedo export |
| **Keyword data** — no live provider | Commercial-intent multiplier forced to 1.0, confidence −0.25 | `KEYWORD_PROVIDER=csv` with a Google Ads / Semrush / Ahrefs / DataForSEO export; or implement `KeywordProvider` |
| **Company dataset** — the primary signal | Without it buyer depth is UNKNOWN for every domain and no BUY is possible | `BUYER_COMPANY_CSV_PATH` pointing at a CRM export, Crunchbase/PitchBook extract, OpenCorporates data, or a Common Crawl host list joined to an industry classifier |
| **Live web/SERP search for buyers** | Buyer discovery is limited to companies already in your file; it cannot find a company you have never heard of | Implement a `BuyerProvider` over a SERP API; the interface is already in place |
| **WHOIS / DNS / traffic** | No signal on whether a matched company's domain is actually live or parked | Add an enrichment provider; `Enrichment` already stores arbitrary fields with provenance |
| **Registrar auction feeds** | Prices come from an uploaded CSV, so they go stale between imports | Poll GoDaddy / Dynadot / Namecheap feeds into `listings` |
| **Full Public Suffix List** | 40 common multi-label suffixes are hard-coded; an exotic one mis-splits | `pip install publicsuffix2` and swap the lookup in `app/services/normalize.py` |
| **Outcome feed** | Paper-position outcomes must be entered by hand | Scrape sale confirmations, or reconcile against a NameBio export on a schedule |
| **Non-English names** | The lexicon and taxonomy are English-only; a German or Spanish name segments poorly and classifies as MISSING | `wordfreq` supports many languages; segmentation would need a language guess first |

**Also missing: calibration.** The largest gap in this system is not a data
source. It is that no coefficient has been checked against reality.

---

## 6. Tests

244 tests, ~14 seconds.

```bash
make test
```

| File | Covers |
|---|---|
| `test_normalize.py` | normalisation, public suffixes, IDN, rejection reasons |
| `test_features.py` | segmentation, syllables, plurals, score bounds, brandability gate |
| `test_integrity.py` | **the data-integrity rules** |
| `test_scoring.py` | valuation decomposition, probability terms, economics arithmetic, gates |
| `test_comparables.py` | similarity, weighted median, confidence, comp blending |
| `test_buyers.py` | match strategies, domain weakness, buyer value, dedupe |
| `test_pipeline.py` | ingest, stage separation, ranking, determinism |
| `test_paper_portfolio.py` | frozen predictions, outcomes, withheld statistics, portfolio caps |
| `test_api.py` | every endpoint, audit-trail completeness, dashboard |
| `test_sensitivity.py` | re-score fidelity, rank statistics, sweep and ablation harness |
| `test_paper_sampler.py` | stratification, cohort health, reconciliation, censoring |
| `test_feed_mapping.py` | column aliasing, refused lookalikes, ambiguity, sales-export detection |

The tests that matter most are in `test_integrity.py` and assert things a
reviewer would otherwise have to police by hand:

- a null provider returns MISSING, never zero
- "did not search" and "searched and found nothing" produce different results
- fixture data is labelled FIXTURE and is off by default
- missing keyword data is *recorded* as missing, not omitted

And three in `test_scoring.py` that keep the arithmetic honest:

- the multiplier walk reconstructs the valuation
- probability terms sum to the log-odds
- component contributions sum to the raw score

---

## 7. Example output

`GET /api/report/text` (demo data — buyers are SYNTHETIC):

```
==============================================================================
TODAY'S TOP DOMAIN OPPORTUNITIES
generated 2026-08-26T19:04:10  |  run 1  |  scoring config v0.1.0+579b729d29da
==============================================================================

DATA AND MODEL WARNINGS
  ! USING SYNTHETIC FIXTURE COMPANIES: every buyer candidate is tagged FIXTURE
    and is NOT evidence of a real company.
  ! Scoring config v0.1.0 is UNCALIBRATED: no coefficient was fitted to
    observed sales.
  ! No comparable sales loaded. Valuations rest entirely on the heuristic prior.

Scored 30 domain(s); 5 have positive expected profit; 28 have at least one
identified buyer.
Recommendations: {'AVOID': 25, 'PASS': 3, 'WATCH': 2}

------------------------------------------------------------------------------
1. berlinroofing.com   [WATCH]  score 57/100 (confidence 74%)
    Asking / current: $425   auction ends 2026-08-27
    Maximum recommended bid: $863
    Retail value: $5,310 - $25,605 (mid $10,781, valuation confidence 55/100)
    Sale probability: 12m 6.3%  24m 11.2%  36m 15.3%  (expected hold 34 months)
    Expected 24m profit: $1,301   expected ROI: 291%
    Credible buyers: 4
      - Berlin Roofing GmbH [FIXTURE] (berlinroofing.de) fit 100/100 - exact_alt_tld
      - Berlin Dach und Roofing [FIXTURE] (berlin-roofing.com) fit 84/100 - separator_variant
      - Hauptstadt Roofing [FIXTURE] (hauptstadtroofing.de) fit 57/100 - weak_domain_industry
    Why it ranks here:
      + modelled retail is 25.4x the asking price (10x scores 100) (+20.0 points)
      + expected 24-month ROI 291% (200% scores 100) (+15.0 points)
      + 4 credible buyer(s) identified, 2 at identity level (+6.1 points)
      + brandability 75/100 (pronounceability 100, 2 words) (+5.3 points)
      + commercial intent 65/100 from CPC and competition (+5.2 points)
    Risks:
      - No comparable sales were available; the valuation rests entirely on
        the heuristic prior.
      - Expected holding period is 34 months, which ties up capital.
    MISSING DATA: comparable_frequency, comparable_sales
```

The ranked table from `GET /api/domains` (10,000-domain load test):

| Rank | Domain | Price | Retail | P(24m) | Buyers | Max bid | Score | Rec |
|---|---|---|---|---|---|---|---|---|
| 1 | datalogistics.com | $239 | $7,177 | 18.5% | 8 | $773 | 53.5 | WATCH |
| 2 | datasystems.com | $63 | $7,211 | 18.9% | 5 | $788 | 52.9 | WATCH |
| 3 | peaklogistics.com | $160 | $6,982 | 17.3% | 7 | $720 | 52.8 | WATCH |

**A finding worth stating.** With a 1.5% base sell-through rate, the V0 model
rates most aftermarket asking prices as *not* arbitrage: 78% AVOID, 17% PASS,
4% WATCH, 0% BUY in the load test. That is either a correct read of a market
where most listings are overpriced, or evidence that the base rate is too
pessimistic. **Which one it is cannot be settled from inside the model** — only
by recording outcomes. It is the first thing calibration should resolve.

The sensitivity analysis in §9 sharpens this: the *levels* move with the base
rate (the median recommended bid swings 1.6× across a 12× change in the prior)
but the *ranking* largely does not. So the AVOID-heavy verdict is a statement
about the levels, which are unverified — while the ordering underneath it is
comparatively stable and can be acted on now.

---

## 9. Sensitivity: which conclusions survive being wrong?

Every weight here is a hand-set prior, so the useful question is not whether the
model is right — it plainly is not yet — but which of its conclusions hold up if
the priors are wrong.

```bash
make sensitivity                        # or: python scripts/sensitivity.py
curl localhost:8000/api/analysis/sensitivity/text
```

The harness re-scores the whole cohort once per grid point. It does **not**
re-run the pipeline: features, classification, buyer matching and comparable
search do not depend on the scoring config, so `app/analysis/rescore.py`
reloads the stored stage inputs and replays only valuation → probability →
decision. A test asserts that a baseline re-score reproduces every stored score
exactly — without that, every sweep number would be reconstruction noise rather
than config sensitivity.

Rank stability and level movement are reported **separately** and never blended
into one reassuring number.

### Findings on the 10,000-domain corpus

**The ranking is robust to the base sell-through rate.** Across a 12× swing
(0.5% → 6%), the baseline top 50 keeps at least 80% of its membership and
Kendall tau stays at 0.73 or above. Over the same grid the median recommended
maximum bid moves 1.6×.

That is the answer to the question the harness was built for: **the relative
ordering carries information that the dollar figures do not.** It is reasonable
to paper-buy off the ranking now, treating every currency amount as unverified.

**But the buyer-depth weight matters more than the base rate does.** Sweeping it
from 0.0 to 0.35 changes up to 30% of the top 50 — more than a 12× swing in the
sell-through prior. Which names surface depends more on one hand-set judgement
about the hypothesis than on the most consequential probability in the model.

**Component ablation — zero each weight, rescale the rest:**

| Component | Configured | Effective | Gap | Coverage | Diagnosis |
|---|---|---|---|---|---|
| buyer_depth | 15% | 35% | +20% | 100% | load-bearing |
| capital_efficiency | 15% | 18% | +2% | 100% | load-bearing |
| liquidity | 5% | 18% | +12% | 100% | load-bearing |
| sale_probability | 15% | 15% | +0% | 100% | load-bearing |
| brandability | 7% | 10% | +3% | 100% | minor contributor |
| valuation_gap | 20% | 2% | −18% | 100% | **redundant** |
| buyer_quality | 8% | 2% | −6% | 100% | **redundant** |
| commercial_intent | 8% | 0% | −8% | **0%** | **no data** |
| comparable_confidence | 7% | 0% | −7% | **0%** | **no data** |

"Effective" is the component's share of total measured influence; "coverage" is
the fraction of domains where it had data at all.

Three things fall out of that table, and the distinction between them matters:

1. **`valuation_gap` carries the largest configured weight (20%) and produces 2%
   of the discrimination.** It is not starved of data — it varies by 39 points
   across the corpus. It is *redundant*: `capital_efficiency` already encodes
   price-versus-value, so removing either leaves the other doing the same job.
   The config is describing a model that is not the model being run.

2. **`commercial_intent` and `comparable_confidence` show zero influence because
   they are MISSING for every domain**, not because they are worthless. 15% of
   the configured weight is sitting on components that are constant, and
   therefore discriminate nothing. That is a missing data source, and the fix is
   a provider, not a weight change. The harness reports these two cases
   differently on purpose — collapsing them would quietly argue for deleting
   exactly the signals not yet sourced.

3. **`liquidity` gets 5% of the weight and 18% of the influence.**

### What has deliberately *not* been done about this

The weights have not been changed. Re-tuning them to match measured influence
would be fitting the config to one corpus of *synthetic* load-test names with no
outcome data behind it — the precise failure mode this design exists to avoid.
The redundancy is now documented; whether to merge `valuation_gap` into
`capital_efficiency` is a modelling decision to make deliberately, ideally after
running the harness against real inventory.

**Influence is a property of the corpus, not of the model.** A corpus of
near-identical names makes almost everything look redundant. The figures above
come from combinatorially generated test domains; run the harness against the
inventory you actually screen before acting on any of them. The report emits
this warning on every run.

---

## 10. Collecting outcome data

Everything above is uncalibrated. This is the machinery for changing that.

```bash
python scripts/paper_buy.py --size 200 --cohort 2026Q3 --dry-run   # read the warnings
python scripts/paper_buy.py --size 200 --cohort 2026Q3             # commit the cohort
python scripts/reconcile_outcomes.py sales_export.csv --source namebio
python scripts/paper_buy.py --health --cohort 2026Q3
```

### Why the cohort is stratified, and not just the top N

**Paper-buying the model's own top picks measures precision but never recall.**
It answers "of the names we liked, how many sold?" but not "did the names we
passed on sell just as often?" — and the second question is the one that decides
whether the score means anything. A model tested only on its own selections
cannot be falsified. So the sampler deliberately draws PASS and AVOID names as a
control group, and records what the model *would* have done rather than only
what we would have bought.

**Stratifying on score alone would confound buyer depth with score.** Buyer depth
contributes 15% of the opportunity score, so a score-ranked sample
over-represents high-depth names at the top. Any measured association between
depth and resale could equally be an association between *score* and resale. To
tell them apart the cohort needs high-depth/low-score and low-depth/high-score
names in it on purpose.

So sampling runs over a two-dimensional grid — score band × buyer-depth band —
allocating as evenly as supply allows.

**Bands are quantiles of the corpus, not fixed thresholds.** The first version
used absolute bands (0–30, 30–45, …, 65+) and two of them were unfillable. That
looked like an inventory shortage and was not: with `commercial_intent` and
`comparable_confidence` MISSING for every domain, 15 of the 100 raw score points
are unreachable, and the confidence adjustment scales what remains — so the real
ceiling on that corpus is about 48, not 100. **No inventory would ever have
filled a band defined at 65+.**

Absolute bands are a trap wherever data coverage is incomplete, which is
always. Quantile bands are defined by the corpus's own distribution, so every
band is populated by construction and means "the top fifth of what is actually
available". The band edges are carried in the stratum label itself
(`score_q5_ge32.85`) so two cohorts drawn from different corpora can never share
a label while meaning different things. `--banding absolute` remains available
for fixed-scale comparisons, with the caveat above.

On the 10,000-domain corpus:

```
banding: quantile  score edges [11.8, 17.6, 24.2, 32.9]  depth edges [1, 3]
score ceiling: 48/100 (15 raw points unreachable: commercial_intent,
                       comparable_confidence)

stratum                             avail  want   got
  score_q1_lt11.85|buyers_0          1625    11    11
  score_q1_lt11.85|buyers_le1         352    10    10
  score_q1_lt11.85|buyers_le3          22    10    10
  score_q2_lt17.57|buyers_0           725    11    11
  score_q2_lt17.57|buyers_le1         607    11    11
  score_q2_lt17.57|buyers_le3         538    11    11
  score_q2_lt17.57|buyers_gt3         130    10    10
  ... 19 cells, all populated ...
  score_q5_ge32.85|buyers_0            74    11    11
  score_q5_ge32.85|buyers_le1         610    11    11
  score_q5_ge32.85|buyers_le3         950    11    11
  score_q5_ge32.85|buyers_gt3         367    10    10

200 position(s)   by recommendation: {'AVOID': 149, 'PASS': 38, 'WATCH': 13}
```

Nineteen cells, every one populated, buyer depth varying within every score
band. The only warning left is the honest one: the score ceiling is 48 because
two data sources are unconfigured.

`--health` runs the structural check, independent of any outcomes. Worth running
the day a cohort is drawn: a confounded or one-sided sample will not become
informative by waiting, and finding out immediately is far cheaper than finding
out in eighteen months. It reports whether buyer depth varies *within* score
bands (if it never does, the two are collinear and no volume of outcomes will
separate them) and whether a control group exists at all.

Sampling is deterministic given `--seed`, so a cohort is reproducible.

### Absence from a sales feed is not evidence of no sale

This is the integrity hazard of the whole exercise. Public sale feeds cover a
fraction of the market — private deals, brokered transfers, and marketplaces that
publish nothing are all invisible. Marking a position UNSOLD because it did not
appear in one export biases the measured sale rate **downward**, in precisely the
direction that would make an over-pessimistic base rate look correct.

So the two operations are separate and behave differently:

| Operation | Does | Never does |
|---|---|---|
| `reconcile` | records SOLD for positions that appear in the export | resolves anything as unsold |
| `close_observation_window` | resolves positions past their horizon | marks UNSOLD unless you assert the window was complete |

`close_observation_window` marks positions **CENSORED** by default — the
observation stopped, which is a fact about us, not about the domain. Censored
positions are excluded from every statistic. That loses statistical power, and
losing power is the right trade against silently counting invisible sales as
failures. Passing `--observation-complete` is you asserting that a sale of any of
these domains *would* have reached you; only then are they marked UNSOLD, and the
report says so loudly.

### End-to-end mechanism check

The loop was verified by generating a synthetic sales file in which buyer depth
genuinely drives the sale probability, then running sample → reconcile → analyse:

```
sampled 200 across 8 strata
matched 49 sales; 151 marked unsold
observed rate 0.245  |  mean predicted p24 0.043  |  calibration gap +0.202

signal                  n  cover     AUC     rho    lift
buyer_depth_count     200   100%   0.641   0.223    1.63
buyer_depth_value     200   100%   0.631   0.204    1.60
buyer_quality_max     200   100%   0.581   0.126    1.24
search_volume           0     0%       -       -       -
cpc                     0     0%       -       -       -

VERDICT: Strongest signal: buyer_depth_count (AUC 0.641, n=200). No keyword
signals had coverage, so buyer depth cannot yet be compared against the
traditional metrics.
```

**Those numbers are not evidence about domains.** The sales file was fabricated
with a buyer-depth-dependent probability, so recovering that effect only shows
the machinery detects an effect that is there. What it does confirm: the analysis
correctly declined to declare the hypothesis supported, because the metrics it
would need to compare against had zero coverage.

### Schema changes

Adding the sampling columns broke every database created before them —
`create_all` makes missing tables but never alters existing ones. `init_db` now
detects that and says so in one sentence instead of failing with a driver error
far from the cause:

```
This database was created by an older version of the models and is missing
columns that the code now selects:
  paper_positions: missing column(s) sample_cohort, sample_stratum
Recreate the database with `make reset` (destructive), or add the columns by
hand if it holds paper positions you need to keep.
```

This is where Alembic starts earning its place. Until then the honest answer to
a schema change is "recreate the database".

---

## 11. Where to get real data

Sourced August 2026. **Verify before committing money** — terms, pricing and API
availability in this market change without notice, and several of these are
explicitly licensed for particular uses.

### Live inventory (domains currently for sale)

| Source | What it gives | Access |
|---|---|---|
| **GoDaddy Auctions inventory files** | Every live expiry listing — closeouts, expiry auctions and other listing types — as downloadable files intended for import into databases and scripts | `inventory.auctions.godaddy.com`; GoDaddy also has Expiry APIs supporting bulk exact-match search, closeout instant purchase and bulk bidding |
| **Dynadot API** | `get_open_auctions`, `get_auction_details`, `get_auction_bids`, `get_closed_auctions`, `get_expired_closeout_domains` | Documented API commands; account required |
| **ExpiredDomains.net** | Daily lists across 676 TLDs, aggregating many registrars | Web UI and manual CSV export only — **no API**, public or paid. Budget for manual exports or a scraping layer |
| **Karma.Domains** | Aggregates GoDaddy, NameJet, DropCatch, Dynadot and Namecheap hourly, with history and link checks | Third-party aggregator; saves running five integrations |
| **Namecheap / NameSilo / Sav / Sedo / Park.io** | Each auctions its own expiring inventory; Park.io specialises in ccTLDs | Per-platform APIs and exports |

Start with **one** source. The importer handles vendor column layouts (§ below),
so adding a second is cheap once the first is working end to end.

### Comparable sales (the empty table in §5)

| Source | What it gives | Access |
|---|---|---|
| **NameBio** | 7M+ transactions, $3B+ in recorded sales; ~939 sales added on a single day in Aug 2026 | Free to search as a guest. Exports, sub-$100 sales history and **API access require paid Business membership**. API: `Comps` (25 credits, up to 25 comps for a domain), `CheckDomain`, `DailySales`, `TopSales`, `KeywordStats`. Free unauthenticated endpoints exist for `RetailStats`, `TLDStats` and Verisign drop order. Max 30 req/min, no multithreading, and **written permission is required to use API data in a commercial product** |
| **DNJournal** | Weekly reported sales | Free, partial coverage |
| **Sedo / Afternic / GoDaddy published sale lists** | Venue-specific reported sales | Free, partial |

NameBio's `Comps` endpoint is close to a drop-in for this system's comparable
module — it returns the same shape `scripts/load_comparables.py` expects.

### Zone files (free, and the basis for your own drop detection)

**ICANN CZDS** (`czds.icann.org`) gives approved users bulk DNS zone files across
participating gTLDs — around 1,151 zones, roughly 1,079 approved at time of
writing. Access is free for legitimate research, brand protection or market
analysis; you apply per zone, approval lasts at least three months, and you may
download each zone once per 24 hours.

Day-over-day zone diffs give you registrations and drops without paying anyone.
That is the cheapest route to a proprietary inventory signal — but read the CZDS
terms: the access policy constrains use, and bulk registrant contact is
explicitly out of scope.

### Company data (the buyer-depth signal)

The buyer provider needs a company file with domains and, ideally, economics.
Options, roughly by cost:

- **Free**: SEC EDGAR (US public companies), Companies House (UK), OpenCorporates
  (registry data, API), Common Crawl host lists joined to an industry
  classifier, Tranco / Majestic Million top-site lists.
- **Paid**: Crunchbase (funding, the `funding_usd` and `last_funding_date`
  fields), People Data Labs, Clearbit, BuiltWith.

Coverage matters more than depth here. The sampler showed buyer depth is the most
load-bearing component in the ranking (§9), so a company file covering more of
the market is worth more than richer fields on a smaller one.

### Keyword data

Google Ads Keyword Planner (free with an active Ads account, coarse volume
buckets), or Semrush / Ahrefs / DataForSEO exports. Any of them closes the
`commercial_intent` gap that costs 8 of the 100 score points today.

### Importing a vendor export

Every marketplace uses different headers, so the importer maps them onto the
canonical schema by matching alias sets — and **shows you the mapping before
importing**:

```bash
python scripts/import_feed.py auctions.csv --source-label godaddy        # dry run
python scripts/import_feed.py auctions.csv --source-label godaddy --yes  # commit
```

```
proposed column mapping:
  Auction End Time             -> auction_end_date
  Bids                         -> bid_count
  Current Bid                  -> current_bid
  Domain                       -> domain
  Traffic                      -> traffic
  Estimated Value              -> REFUSED (an appraisal, not a price anyone is asking)
  Renewal Price                -> REFUSED (the cost to renew, not to acquire)
```

Three refusals are deliberate, because each would corrupt every downstream number
while looking entirely plausible:

1. **Appraisal columns** (`Estimated Value`, `GoDaddy Value`, `appraisal`) are
   never mapped to a price. They are someone else's model output. Feeding one in
   as `asking_price` would make the system compare its valuation against another
   valuation and call the agreement a finding.
2. **Renewal, transfer, restore and reserve prices** are never mapped to
   `asking_price` or `current_bid`. They are real prices for a different thing.
3. **Completed-sales exports are refused entirely.** A NameBio-style file has
   `sale_price` and `sale_date`; imported as listings, historical clearing prices
   would read as today's asking prices, every domain would look fairly priced,
   and the ranking would become noise. The importer detects the shape and points
   you at `scripts/load_comparables.py` instead.

Ambiguity also blocks an automatic import rather than warning: if two columns
could both be the asking price, neither is mapped and the import stops, because
silently proceeding without a price produces listings that look imported but can
never yield an ROI, a maximum bid or a paper position. Resolve it explicitly:

```bash
python scripts/import_feed.py feed.csv --map "Buy It Now=asking_price" --yes
```

Unmapped columns are never discarded — they are retained on the listing's
`raw_row`, so nothing from the source file is lost.

---

## 8. Recommended Phase 2

In priority order. The first item is worth more than the rest combined.

**1. Get outcome data — nothing else matters until this exists.** The machinery
is now built (§10); what remains is running it against real inventory. Draw
200–400 positions with `scripts/paper_buy.py`, check `--health` the same day,
and reconcile monthly against a sales feed. Around 100 resolved outcomes,
`/api/analysis/signal-power` starts producing a real verdict on the buyer-depth
hypothesis; around 300, the probability coefficients can be fitted.

Note what diagnosing the sampler's empty bands turned up: they were not an
inventory shortage at all. With two providers unconfigured, 15 of 100 score
points are unreachable and the effective ceiling is ~48, so absolute bands above
that could never fill. Banding is now quantile-based and every band populates
(§10) — but the ceiling is real, and closing it means configuring the keyword and
comparable-sales providers (§11).

**2. Load real comparable sales.** The largest single lift available to
valuation accuracy, and the loader already exists. It converts the only
OBSERVED price evidence in the system from absent to present, and closes 7 of
the 15 score points currently unreachable. NameBio's paid API is the obvious
route (§11).

**3. Build the real buyer provider.** The company file is the primary signal's
bottleneck. A SERP-backed provider that finds companies you have never heard of
— rather than matching against a list you already have — is what makes buyer
depth a discovery mechanism instead of a lookup. Add WHOIS/DNS liveness so a
matched company's domain is verified as actually in use.

**4. Replace V0 valuation with a fitted model.** Once comps are loaded, fit
`log(sale_price) ~ features` on the comp set itself. That is a supervised
problem with data available *today*, independent of the paper portfolio, and it
replaces the multiplier ladder with something measured. Keep the multiplicative
form for interpretability; keep the walk.

**5. Fit the probability model.** Logistic regression on resolved paper
positions, replacing the `coefficients` block in the YAML. Report a calibration
curve, not just an AUC. Set `meta.calibrated: true` only when this is done.

**6. Resolve the `valuation_gap` / `capital_efficiency` redundancy.** §9 shows
the largest configured weight producing almost none of the discrimination.
Decide whether they are one component or two, on the inventory you actually
screen rather than on the synthetic load-test corpus. Cheap, and it makes the
config an honest description of the running model.

**7. Live listing feeds.** Poll registrar auction APIs into `listings` on a
schedule, so prices and auction end times stop going stale between imports.

**8. Operational hardening.** Alembic migrations, PostgreSQL, background jobs
for the pipeline, and authentication before this is exposed beyond localhost.

*(Sensitivity and ablation tooling was Phase 2 item 6 in the original plan and
is now built — see §9. Its findings are what reordered the list above.)*

### Deliberately *not* in Phase 2

- Bidding, buying, or any capital deployment. Not until step 5 reports a
  calibration curve worth looking at.
- A richer scoring model. More weights on no data is exactly the failure mode
  this design is built to avoid.
- UI polish. The dashboard's job is to make the audit trail reachable, and it
  does that.

---

## Design principles, restated

1. **Never convert missing information into invented information.** A field we
   could not source is written, marked MISSING, with a note saying why.
2. **Separate data, features, valuation, probability and decision.** No opaque
   composite score.
3. **The LLM does semantics, never arithmetic.** Classification, brandability
   judgement, buyer/domain reasoning, prose explanations. Never parsing, never
   scoring rules, never comp selection, never a number. Structured JSON only,
   cached, capped per run, and entirely optional.
4. **Every weight is configurable, versioned and stamped onto its predictions.**
5. **Confidence is separate from value**, and low confidence discounts the
   ranking rather than the estimate.
6. **Understandable beats clever.** Multiplicative valuation and additive
   log-odds are both weaker than what could be built, and both can be checked
   by hand.
