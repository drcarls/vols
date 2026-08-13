# flywheel — the UpliftIQ decision → outcome capture layer

The instrumentation that makes the moat real *from customer one*: a
warehouse-agnostic dbt project + JSON event contracts that capture every
decision, what the customer did with it, and what actually happened — then
attribute the **causal lift** back to the mapping that produced the decision.

That last arrow is the whole point. The mapping (signal → decision) is the
*product*; the accumulating record of **which mappings drove results, for which
customer type** is the *moat*. This layer is what turns the second into data —
and it only works if it's capturing from the very first decision, so it's built
to drop in on day one with whatever counterfactual a customer can give you.

## The loop it instruments

```
   surfaced          customer            outcome            uplift            map
   decision   ──▶     acts       ──▶     measured   ──▶    attribution ──▶   sharpened
  (the map)        (in their sys)    (what happened)   (was it real?)   (for this segment)
      ▲                                                                        │
      └───────────────  every pass sharpens the map  ◀────────────────────────┘
```

Each stage is an event you emit (`schemas/events.*.schema.json`); dbt turns the
raw events into the flywheel tables and the two marts that matter.

## The grain (what each table is one row of)

| Table | One row per | Role |
|---|---|---|
| `stg_decisions` | surfaced decision | the recommendation + its mapping + segment |
| `stg_actions` | response to a decision | accepted / modified / rejected + holdout arm |
| `stg_outcomes` | (decision, metric, window) | measured result + counterfactual basis |
| `fct_decision_spine` | decision | decision ⋈ action ⋈ mapping lineage |
| `fct_attribution` | (decision, metric) | **isolated lift** + validity tier |
| `mart_mapping_performance` | (tenant, mapping_version, segment, metric) | **the moat** — which map works, for whom |
| `mart_benchmark` | (mapping_family, segment, metric) | **the network effect** — anonymized, k-gated |

## Capture from customer one

Emit three event types (validated against the JSON schemas); land them in the
`flywheel_raw` source tables:

1. **`DecisionEvent`** — the moment a recommendation is shown. Carries the
   `mapping_version_id` (the moat link) and the `segment` (the "for which
   customer type" axis). Domain-generic: the actual recommendation is an opaque
   payload, so pricing, promo, and allocation all use one schema.
2. **`ActionEvent`** — what the customer did. `modified` and `rejected` are
   signal, not rows to drop. Carries the holdout arm when there was one.
3. **`OutcomeEvent`** — the measured result and its counterfactual. One `method`
   field (`holdout` / `pre_post` / `observational`) says which counterfactual is
   authoritative; the schema requires the fields that method needs.

## Attribution — three methods, one field

You rarely get a clean experiment on day one, so the schema supports all three
counterfactuals and grades them by trust (`attribution/methods.md`):

| method | counterfactual | tier | weight |
|---|---|---|---|
| `holdout` | randomized control | experimental | 1.00 |
| `pre_post` | pre-period / diff-in-diff | quasi | 0.60 |
| `observational` | modeled match / synthetic control | observational | 0.30 |

`mart_mapping_performance` pools lift **weighted by validity**, so one clean
holdout outweighs a stack of guesses instead of being averaged flat with them —
the rule that stops the flywheel from confidently learning the wrong lesson.

## Cross-customer benchmark — the network effect, safely

`mart_benchmark` rolls mapping performance up across tenants by segment, and
emits a cell **only when at least `benchmark_k` (default 5) distinct tenants
contribute** — k-anonymity by construction, no tenant id or tenant-level value
ever exposed. That's the asset no single customer and no platform can
reproduce, and it's exactly what you give back as "the benchmark" in return for
the data rights that let you build it. More customers → richer benchmark → a
sharper map → more customers.

## Warehouse-agnostic by design

Runs on any dbt-supported warehouse (Snowflake / BigQuery / Databricks /
Postgres / Redshift). Standard SQL throughout; the one primitive that genuinely
diverges — percentile — is isolated behind a dispatched macro
(`macros/flywheel_percentile.sql`). Types use dbt's cross-database `type_*`
macros. Matching / synthetic-control math is *not* forced into SQL; it runs in
your modeling layer and lands as `counterfactual_value`.

## Run it

```bash
# point profiles.yml at your warehouse (profile: flywheel), then:
dbt deps           # if you enable the dbt_utils test used in _marts__models.yml
dbt seed           # loads the example mapping-version lineage
dbt build          # runs staging -> marts and all data tests
```

Configure per deployment in `dbt_project.yml`: `flywheel_raw_schema` (where
events land) and `benchmark_k` (the anonymity threshold).

## See it turn — no warehouse needed

`examples/run_demo.py` runs the **actual model SQL** against seeded data in
DuckDB (an in-process engine) — it only shims the dbt Jinja so the same files
execute locally. Eleven decisions across all three attribution methods, three
tenants, two mapping versions:

```bash
pip install duckdb
python3 examples/run_demo.py
```

It prints the three stages turning: every outcome attributed to isolated lift
with its validity tier, the per-tenant **mapping-performance** moat table
(pricing_elasticity v3 beats v2 in mid-market; promo_timing v2 posts negative
lift → retire it), and the k-anonymized **benchmark** that only emits where
tenants agree. What `dbt build` runs on a real warehouse is the identical SQL.

## How it maps to the moat narrative

- **`fct_attribution`** is the honest-attribution arrow — "was the lift real?"
- **`mart_mapping_performance`** is the map getting sharper — the roadmap writes
  itself from which mappings won, by segment.
- **`mart_benchmark`** is why in-house can't catch up and why a platform is your
  substrate, not your killer: it holds the cross-customer, segment-conditioned
  record of what works, which only exists because the loop was captured from
  customer one.

## Scope note

This lives under `flywheel/` in this repo for now, on the current working
branch. It's a separate concern from the Questa prospecting tool (`questa_scout/`)
and can be split to its own branch or repo whenever you want.
