# questa_scout

A pre-sales prospecting engine for **Questa AI** — the "privacy firewall
between your sensitive data and any AI." Point it at a set of US companies and
it ranks them by how good a prospect they are, built around the pitch that
lands right now: the **EU AI Act** is in enforcement (penalties up to €35M /
7% of turnover) and the **shadow-AI problem** is everywhere — employees are
putting regulated data into public LLMs while nobody owns AI governance.

It answers, per company:

1. **Do they handle regulated data?** — from NAICS industry code: healthcare
   (PHI / HIPAA), finance & insurance (financial / GLBA), legal (privileged /
   state privacy), BPO / consulting / SaaS (consumer PII / CCPA-CPRA). This
   sets a **data-sensitivity tier** (PHI highest).
2. **Are they actively adopting AI?** — open AI/ML job postings (via the
   **Bright Data SERP API**) plus a passive homepage check for advertised AI
   features and a customer-facing chatbot. Active adoption = live data
   exposure *now* = the buy-now trigger.
3. **Is there a visible privacy / AI-governance owner?** — via SERP: a
   LinkedIn search for a DPO / Chief Privacy Officer / Head of AI Governance.
   **No visible owner while AI adoption accelerates is the direct Questa
   opening.**

…then scores and ranks them, routes each to the right Questa product, and
emits a per-company brief plus two CSVs (a ranked prospect list and a
per-finding list mapped to regulations, products, and talking points).

This is a fork of the `presales_scout` engine (built for Cyber Defencely /
NIS2), retargeted to Questa's product and the US regulatory landscape. The
pipeline, SERP backend, scoring skeleton, and CLI carry over unchanged; the
qualifier, collectors, and context catalog are Questa-specific.

## Install

```bash
cd questa_scout
python3 -m pip install -e .        # or: pip install -r requirements.txt
```

## Run (offline, no token needed)

The tool ships with fixtures so the whole pipeline runs with no Bright Data
account and no network:

```bash
questa --offline --no-web discover --input fixtures/candidates.sample.csv \
       --out ranked.csv --findings-out findings.csv --top 10
questa --offline --no-web scan --name "Cascade Health Partners" --naics 621111 --employees 900
```

(`--offline` forces the fixture SERP backend; `--no-web` skips the live
homepage fetch. Drop both when a token and network are available.)

## Run (live, via Bright Data SERP)

Set your token in the environment — **never commit it**:

```bash
export BRIGHTDATA_API_TOKEN="…"     # from your Bright Data account
questa discover --input my_candidates.csv --out ranked.csv --findings-out findings.csv
```

With a token present (and without `--offline`) the SERP backend switches to
the live Bright Data SERP API automatically. It runs two Google queries per
company — one for open AI/ML jobs, one for a governance owner:

```
site:linkedin.com/jobs ("GenAI" OR "LLM" OR "ML Engineer" OR …) "<Company>"
site:linkedin.com/in  ("Data Protection Officer" OR "Chief Privacy Officer"
   OR "Head of AI Governance" OR …) "<Company>"
```

Cost is ~$1.50 / 1000 requests (two requests per company; 5k/month free
tier), and failed requests aren't billed. Without `--no-web` it also fetches
each company's homepage over HTTPS to grade advertised AI + chatbot signals.

## Input format (Stage 1)

Candidates come from a CSV — see `fixtures/candidates.sample.csv`:

| column | meaning |
|---|---|
| `name` | company legal name (required) |
| `domain` | for the homepage AI/chatbot check |
| `naics_code` | NAICS industry code — drives the regulated-data match |
| `employees`, `revenue_usd` | drive product routing (Cloud vs Blackbox) |
| `state` | US state (state-privacy nexus) |

In v1 you supply this CSV. A live **SEC EDGAR / data.gov / state-registry**
backend that builds the candidate universe by NAICS + size is the planned
next step; it populates the same `Company` shape, so nothing downstream
changes.

## How the score works

| Signal | Meaning | Weight |
|---|---|---|
| **Data scope** (qualifier) | in regulated-data sector? | `in_scope` +45 · `likely` +30 · `unknown` +10 · `out_of_scope` −100 |
| **AI adoption** (trigger) | actively building with AI? | `active` +40 · `emerging` +22 |
| **Governance gap** (opening) | no visible privacy/AI owner? | `none_found` +30 · `uncertain` +15 |
| **Sensitivity** (tie-break) | PHI > financial/legal > PII | +10 / +7 / +3 |

Score is clamped to 0–100. An out-of-scope company is pushed to the bottom
regardless of the other signals — the same qualifier logic the NIS2 version
used.

## Product routing

Each qualified prospect is routed to the lead Questa product:

- **Questa Blackbox (self-hosted)** — regulated enterprises with strict data
  residency (hospitals, banks, insurers at scale, legal).
- **Questa Developer (API)** — SaaS / software / hosting firms embedding AI
  into their own product (NAICS 5112 / 5182 / 5415).
- **Questa Cloud** — small teams and startups.

## How it's organized

```
src/questa_scout/
  models.py                 # Company, DataScopeVerdict, AiAdoptionSignal, GovernanceSignal, Finding, ProspectReport
  collectors/
    regulated.py            # NAICS -> regulated-data scope + data class + regime
    ai_adoption.py          # SERP job postings + homepage signals -> adoption level
    web_signals.py          # passive homepage AI/chatbot grader (pure grader unit-tested)
    ai_governance.py        # SERP LinkedIn -> scored governance signal
    serp/
      base.py               # SerpBackend protocol + normalized SerpResult
      query.py              # job & governance query building, title/job classification
      brightdata_serp.py    # live Bright Data SERP backend + parse_serp_json()
      fixture.py            # offline backend (routes jobs vs profiles by query)
  routing.py                # prospect -> Questa product
  context_map.py            # raw signal -> regulation + product + talking point (the sellable layer)
  scoring.py                # combine signals -> fit score + brief
  pipeline.py               # CSV -> analyze each -> rank -> CSV (ranked + per-finding)
  cli.py                    # `questa scan` / `questa discover`
```

Swap or add a SERP backend by implementing `SerpBackend.search()`.

## Important caveats

- **A missing governance owner is a confidence signal, not proof.** No search
  hit can mean a private profile, an outsourced DPO, or a small firm.
  `none_found` results always carry `verify_recommended` — eyeball before
  outreach.
- **Stay passive.** Everything here reads public search results, public job
  postings, and a public homepage. No probing, scraping behind logins, or
  scanning — that needs the prospect's authorization.
- **Privacy law cuts both ways.** Governance detection pulls *named
  individuals*. For B2B prospecting a legitimate-interest basis is defensible,
  but keep the data minimal, document the basis, and set a retention limit.
  Don't hoard profiles.
- The regulated-data and adoption checks are **screening heuristics**, not
  legal or compliance determinations.

## Tests

```bash
python3 -m pytest -q
```
