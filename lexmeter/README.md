# Lexmeter US — drip & junk fee collector

Scripted checkout flows that record, step by step, when and how mandatory fees appear
relative to the advertised price. The core measurement is **at which step does each
mandatory fee first appear, and what is the gap between headline and total**.

- `DRIP_FEE_COLLECTOR_PLAN.md` — design, verified legal map, open decisions, phased plan
- `METHOD_STATEMENT.md` — what a custodian certifies; **read §7 before relying on a capture**

## Layout

    config/
      jurisdictions.yaml      rules with effective dates, scope, remedies, verification status
      fact_patterns.yaml      filed-case fact patterns for the pattern-match screen
      collection_policy.yaml  pacing, prohibitions, block signals, egress and evidence settings
    src/lexmeter_fees/
      model.py        capture data contract (integer cents throughout)
      extract.py      money parsing, fee-line interpretation, first-appearance carry-forward
      taxonomy.py     fee label -> canonical category
      capture.py      flow runner; driver protocol
      drivers/        playwright (live) and fixture (offline) drivers
      flags.py        derived metrics and violation flags
      rules.py        resolves flags against jurisdiction rules by state and date
      evidence.py     canonical hashing, content addressing, Merkle anchoring, provenance
      politeness.py   enforces the declared collection posture
      store.py        storage adapters; append-only enforced by trigger
    fixtures/         local HTML reproducing a drip flow and a compliant flow

## Running

    pip install -e ".[dev]"
    pytest

The suite runs entirely offline against local fixtures — no network, no live sites.

## Two things to know before extending this

**Storage is behind an adapter.** The existing Lexmeter pipeline is not in this
repository, so `ArtifactStore` and `ObservationStore` are protocols with local
implementations. Pointing them at the real store is a config change.

**Flags are not findings.** `flags.py` records what a site did. `rules.py` decides which
rule that engages, where, and when — and refuses to assert a rule that was not yet
effective on the observation date, or whose own verification is incomplete. Keeping them
separate means a later correction to the legal map re-scores existing captures instead
of invalidating them.
