# Integration & the Real Moat

*The scraper is not the moat. The integration is.*

Anyone can check a DMARC record. What can't be copied is **this signal wired into
the systems that turn it into revenue** — Clay's enrichment waterfall, UpliftIQ's
scoring, and Cyber Defencely's own delivery data feeding back as ground truth. This
note is how that fits together, and why each connection compounds.

```
                         ┌─────────────────────────────┐
   registry feed ───────▶│   presales_scout engine     │  proprietary signal:
  (allabolag/Roaring)    │  NIS2 scope · email hygiene │  regulatory-risk fit,
                         │  CISO gap · hiring trigger  │  not firmographics
                         │  attack surface · suppliers │
                         └──────────────┬──────────────┘
                                        │ JSON per domain
                        ┌───────────────▼───────────────┐
                        │            CLAY               │  waterfall enrichment:
                        │  our column + Apollo/Clearbit │  contacts, emails,
                        │  /Hunter/LinkedIn + AI cols   │  firmographics, phones
                        └───────────────┬───────────────┘
                                        │ enriched row
                        ┌───────────────▼───────────────┐
                        │          UPLIFTIQ             │  predicts revenue /
                        │  blends our fit + vuln signal │  ranks leads+vulns
                        │  with their internal model    │  (their edge)
                        └───────────────┬───────────────┘
                                        │ scored, prioritised
                        ┌───────────────▼───────────────┐
                        │   CYBER DEFENCELY systems     │  CRM + assessment
                        │  CRM · sequencer · real       │  findings = GROUND
                        │  assessment outcomes          │  TRUTH, fed back ▲
                        └───────────────────────────────┘
                                        │
                     won/lost + "what was actually wrong" ──── retrains fit
```

---

## Where Clay fits

[Clay](https://clay.com) is the orchestration layer most modern GTM teams already
run. It's a spreadsheet where each column can call a data provider, and it does
**waterfall enrichment** — try provider A for an email, fall back to B, then C —
plus AI columns and push-to-CRM/sequencer. Clay gives you *breadth*: contacts,
verified emails, firmographics, phone numbers, intent data.

What Clay **doesn't** have is our column. There is no off-the-shelf Clay provider
that returns *"this company is in NIS2 scope, has an unenforced DMARC record, no
visible CISO, and is hiring one right now."* That's the integration:

- **`presales_scout` as a Clay HTTP-enrichment source.** Clay sends a domain to our
  endpoint; we return the signal bundle as JSON → it lands as columns Clay can
  filter, score, and sequence on. One thin HTTP wrapper around the existing
  collectors (the `Company`/`Finding` shapes already serialise to rows).
- **Waterfalled, not standalone.** Clay resolves the *who* (the security-buyer
  contact, their email) while we supply the *why now* (the regulatory-risk trigger).
  Neither is a campaign alone; together they're a personalised, timed outbound.
- **Trigger-driven.** The "hiring a CISO" signal is a Clay-native use case — watch
  for it, and when it fires, auto-enrich + draft the opener referencing the exact
  gap. Half the demo list was actively recruiting; that's a live-req alert, not a
  static list.

The same wrapper serves anything Clay-shaped — n8n, Make, HubSpot workflows,
Apollo plays. Build the endpoint once.

## Where UpliftIQ fits

UpliftIQ is the scoring/prediction layer — it predicts revenue and ranks leads and
vulnerabilities against its own internal model. That's deliberately *their* edge, and
we don't rebuild it. Our job is to hand it **two clean, join-ready feeds** it can't
get anywhere else:

- **Leads feed** — one row per company, the fit signal + evidence.
- **Vulnerabilities feed** — one row per finding, already context-mapped to NIS2
  measure + ISO control + severity + remediating service (§8 of the methodology).

UpliftIQ blends those with its dataset to produce the tiered A/B/C · Hot/Warm output.
The value we add is *feature quality*: a regulatory-risk signal no generic enrichment
vendor produces, pre-mapped to the frameworks that make it a sales-ready reason.

## Where Cyber Defencely's own systems fit — the flywheel

This is the part competitors structurally cannot copy, because it's built from
Cyber Defencely's **private** data:

1. The engine predicts *"weak here, no CISO, in scope."*
2. Outreach lands; Cyber Defencely runs a real assessment.
3. The assessment produces **ground truth** — what was *actually* wrong, what closed,
   what the deal was worth.
4. That outcome flows back: which signals actually predicted a real gap, which
   predicted a won deal. The fit model retrains on Cyber Defencely's own conversion
   and delivery history.

Every engagement makes the next prediction sharper — a data asset that grows with the
business and lives on no competitor's servers. **That** is the moat: not the OSINT,
but the OSINT closing the loop against proprietary outcome data.

## Why the split of responsibilities holds up

| Layer | Owner | Why it's defensible |
|---|---|---|
| Regulatory-risk signal | `presales_scout` | Curated NIS2/ISO crosswalk + passive collectors; deterministic, auditable, no generic vendor sells it |
| Breadth enrichment | Clay + providers | Best-in-class contacts/emails; no reason to rebuild |
| Prediction / ranking | UpliftIQ | Their internal model is their edge; we feed it better features |
| Ground truth + retraining | Cyber Defencely | Private assessment + CRM outcomes; the compounding, uncopyable asset |

Each layer does the one thing it's best at, and the seams are clean JSON/CSV. The
moat isn't any single box — it's that the loop **closes** on data only Cyber
Defencely holds.

## The Clay endpoint, concretely

The HTTP wrapper is built — `src/presales_scout/integrations/clay.py`. Clay's
HTTP-enrichment column POSTs a domain; the endpoint runs the full stack and
returns one flat JSON object that maps straight onto Clay columns:

```
REQUEST   POST /enrich   { "domain": "goteborgenergi.se",
                           "name": "Göteborg Energi AB",
                           "sni_code": "35110", "employees": 1150 }

RESPONSE  200            { "nis2_in_scope": true, "nis2_sector": "Energy",
                           "email_weakness": "weak", "dmarc_policy": "none",
                           "ciso_status": "none_found", "ciso_confidence": 0.7,
                           "top_finding": "DMARC not enforced (p=none)",
                           "top_finding_nis2": "Art. 21(2)(g) basic cyber hygiene",
                           "top_finding_service": "Rapid Cybersecurity Assessment …",
                           "finding_count": 10, "max_severity": "high",
                           "talking_point": "…grounded one-line opener…",
                           "findings": [ … full context-mapped rows … ] }
```

Every field is scalar/flat so it becomes a filterable Clay column; `findings` is
the full context-mapped detail for the sequence body. Run it standalone with
`python -m presales_scout.integrations.clay 8787` (POST `/enrich`, GET `/health`),
or drop `enrich_domain()` into FastAPI/Flask behind your gateway. The pure
function is unit-tested offline; a live call against a real domain returns the
same signal the demo brief is built from.

## Build order (cheapest → highest-leverage)

1. **CSV feeds to UpliftIQ** — already produced; wire the join. *(done)*
2. **HTTP endpoint** wrapping the collectors → Clay enrichment column + webhook.
   *(built — `integrations/clay.py`; add auth + deploy)*
3. **Registry feed** (allabolag / Bolagsverket / Roaring) so candidate generation
   scales past the hand-verified 10 — the one real dependency (methodology §8).
4. **Feedback capture** — a field in Cyber Defencely's CRM for assessment outcome,
   piped back to retrain fit weighting. This is what turns a tool into a moat.
