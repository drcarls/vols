# questa_scout — build write-up

A pre-sales prospecting engine for **Questa AI**, built by forking the
`presales_scout` engine (originally built for Cyber Defencely / NIS2) and
retargeting it to Questa's product and the US regulatory landscape. This
document records what was built, how it was validated live, the bugs that
live testing exposed, and what's left.

Everything lives under `questa_scout/` on branch
`claude/questa-presales-approach-kf8thm`. **38 tests passing.**

---

## 1. The premise

The Cyber Defencely deliverable was a signal-scored prospecting engine: take a
universe of companies, score each on a *regulatory trigger* (NIS2 scope) plus
*passive-OSINT pain signals* (weak email hygiene, no visible CISO), map each
signal to a service and a talking point, then rank. The ask here was to do the
same for **Questa AI** — a different company.

Questa sells a *"privacy firewall between sensitive data and any AI"*: it
redacts PII/PHI/financial data before anything reaches an LLM, sold as
**Blackbox** (self-hosted), **Developer** (API), and **Cloud** (managed). Its
timing hook mirrors NIS2 almost exactly: the **EU AI Act** is in enforcement
(penalties up to €35M / 7% of turnover) and the **shadow-AI problem** —
employees pasting regulated data into public LLMs — is universal.

So the same five-layer engine transferred; only the signals and the mapping
changed. Target market for this build: **US** (HIPAA / GLBA / state privacy).

## 2. The signal translation

| Layer | Cyber Defencely | **Questa (US)** |
|---|---|---|
| Qualifier (gate) | In NIS2 scope? (SNI + size) | **Regulated-data scope** — NAICS → PHI/HIPAA, financial/GLBA, legal/privilege, consumer-PII/state privacy, with a sensitivity tier |
| Trigger (act now) | NIS2 readiness | **Active AI adoption** — live LinkedIn GenAI/LLM job postings + homepage AI/chatbot |
| Opening | No visible CISO → CISO-as-a-Service | **No visible privacy/AI-governance owner** (DPO/CPO/Head of AI Governance) → the Questa opening |
| Context map | NIS2 Art. 21 / ISO → service | Finding → HIPAA/GLBA/state privacy → **Questa product** → talking point |
| Output | Ranked CSV + dashboard | Ranked CSV + per-finding CSV + HTML dashboard |

## 3. Architecture

```
src/questa_scout/
  models.py                 # Company, DataScopeVerdict, AiAdoptionSignal, GovernanceSignal, Finding, ProspectReport
  collectors/
    regulated.py            # NAICS -> regulated-data scope + data class + regime (the qualifier)
    ai_adoption.py          # SERP job postings + homepage signals -> adoption level + intensity
    web_signals.py          # passive homepage AI/chatbot grader (pure grader unit-tested)
    ai_governance.py        # SERP LinkedIn -> scored governance signal
    enrich.py               # company name -> domain (Clearbit autocomplete; conservative matcher)
    serp/                   # SerpBackend protocol; BrightData (live) + Fixture (offline) backends
  universe/edgar.py         # SEC EDGAR company listings by SIC -> candidate universe
  routing.py                # prospect -> Questa product (Blackbox / Developer / Cloud)
  context_map.py            # raw signal -> regulation + product + talking point (the sellable layer)
  scoring.py                # combine signals -> granular 0-100 fit + brief
  dashboard.py              # ranked reports -> self-contained HTML "Prospect Scout"
  pipeline.py               # CSV -> analyze -> rank -> CSV (ranked + per-finding)
  cli.py                    # questa universe / scan / discover
```

The pipeline is deliberately backend-swappable: the SERP layer is a
`SerpBackend` protocol with a live Bright Data implementation and an offline
fixture implementation, so the entire tool runs with **no token and no
network** for demos and tests, and switches to live automatically when a token
is present.

## 4. Commands

```bash
# Build a real candidate universe from SEC EDGAR (free, no key), with domains
export EDGAR_USER_AGENT="Your Name you@example.com"
questa universe --sectors health,finance,legal,software --limit 40 \
       --enrich-domains --out candidates.csv

# Score and rank (live signals when a Bright Data token + zone are set)
export BRIGHTDATA_API_TOKEN="…"; export BRIGHTDATA_ZONE="unblocker"
questa discover --input candidates.csv --out ranked.csv \
       --findings-out findings.csv --html prospects.html

# Fully offline (fixtures, no token/network) for a demo or CI
questa --offline --no-web discover --input fixtures/candidates.sample.csv --html demo.html
```

## 5. The scoring model

Fit is a granular 0–100 that ranks *within* the qualified tier rather than
saturating:

```
fit = scope + sensitivity + adoption×intensity + governance   (clamped 0-100)

scope:        in_scope 30 · likely 20 · unknown 6 · out_of_scope -100
sensitivity:  PHI 15 · financial/legal 10 · consumer_pii 5
adoption:     (intensity / 5) × 30      intensity = strong-hiring(2)+homepage-AI(1)+chatbot(2)
              unknown adoption -> small floor (5)
governance:   none_found 25 · uncertain 12 · governed 0
```

Components sum to ~100 only when a prospect is maxed (PHI + full adoption + no
owner), so sensitivity and adoption intensity order the hot tier. Each fired
signal is also mapped by `context_map.py` to a regulation, a Questa product,
and a one-line talking point (e.g. `AI_SHADOW_RISK` → HIPAA §164.308 →
Blackbox → *"You're putting regulated data into AI with no governance owner —
that's the breach and the fine in one gap."*).

## 6. Live validation

The full pipeline was run live end-to-end on 12 real US companies across
health, fintech, insurance, legal, and SaaS — **live** SEC EDGAR, Clearbit
domain enrichment, Bright Data SERP (LinkedIn jobs + governance), and homepage
fetches. Representative result:

| # | Fit | Data | Adoption | Product | Company |
|--|--|--|--|--|--|
| 1 | 100 | PHI | active (jobs+site+chatbot) | Blackbox | HCA Healthcare |
| 2 | 95 | legal | active + chatbot | Blackbox | LegalZoom |
| 3 | 94 | PHI | active | Blackbox | Teladoc Health |
| 4 | 83 | financial | active | Blackbox | Oscar Health |
| 5 | 82 | PHI | active | Blackbox | Molina Healthcare |
| 6–7 | 78 | consumer PII | active | Developer | UiPath, Snowflake |
| 8–9 | 77 | financial | emerging/active | Blackbox | Robinhood, Lemonade |
| 10 | 71 | financial | emerging | Blackbox | Affirm |
| 11 | 70 | financial | unknown | Blackbox | SoFi |
| 12 | 66 | consumer PII | emerging | Developer | Twilio |

Fit spread 66–100 with 10 distinct values. Adoption signals were genuinely
live (real GenAI/LLM job postings + AI features/chatbots on the companies'
actual homepages); SaaS firms routed to Developer, regulated enterprises to
Blackbox.

**Verified reachable through the environment proxy:** SEC EDGAR, Clearbit
autocomplete, `api.brightdata.com`. The account's Bright Data zone is a **Web
Unlocker** zone (`unblocker`), which returns SERP JSON via `brd_json`.

## 7. Bugs live testing exposed (all fixed)

1. **Batch abort on one bad request.** The Web Unlocker zone is slow (it solves
   Google's anti-bot per call); a single 30s timeout or an HTML block-page
   response crashed the whole run. Fixed: the backend retries, then degrades
   that one query to no-signal, so a batch never dies on one request.
2. **Governance signal manufactured `uncertain` from noise.** A
   `site:linkedin.com/in … "Company"` query returns generic "Chief Privacy
   Officer" profiles at *other* employers (Microsoft, Apple, IQVIA) for any
   company. The detector counted that as "people found" → every company read
   `uncertain`. Fixed: it now ignores profiles that don't mention the company,
   so an unmatched set correctly reads `none_found` ("verify by hand").
3. **Fit saturated at 100.** The original additive score pinned nearly every
   qualified prospect at the cap. Fixed by the granular model in §5.

## 8. Known limitations & next steps

- **Governance under-detects (the big one).** Google won't reliably surface a
  company's *own* privacy owner for this query, so most companies read
  `none_found`. This is honest (the tool flags "verify by hand") but it doesn't
  distinguish a company that *has* a visible owner from one that doesn't. The
  fix is a **LinkedIn people/org-API backend** (e.g. Bright Data's LinkedIn
  dataset) — the natural next backend to add behind the `SerpBackend` seam.
- **Domain enrichment recall.** Clearbit resolves well-known firms (HCA,
  Molina, Prudential, Aegon…) but returns nothing for obscure SEC micro-caps;
  the matcher is deliberately conservative (no domain rather than a wrong one).
- **Size data.** EDGAR gives name/sector/state but not headcount/revenue, which
  drive product routing between Blackbox and Cloud — enrich from your own data.

## 9. Ethics & data handling

Passive OSINT only — public search results, public job postings, public
homepages, public SEC filings. No probing, no scraping behind logins. Signals
are screening heuristics, not determinations; a governance gap is flagged for
human verification before outreach. Governance detection touches named
individuals, so for real use keep the data minimal, document a
legitimate-interest basis, and set a retention limit.

## 10. Provenance

The Cyber Defencely `presales_scout` package is untouched on its own branch;
`questa_scout` is a separate, self-contained package. The two share a design
lineage but no code.
