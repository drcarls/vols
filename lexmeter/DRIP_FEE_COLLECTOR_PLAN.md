# Lexmeter US — Drip & Junk Fee Collector

Status: **design, pre-build.** No code written. Four decisions are open (see §3).

---

## 1. Scope finding: the pipeline is not in this repo

`drcarls/vols` contains, in full:

- `Infinite Dimension*.R`, `Infinite_Dimensions_Engine_Hardened_v2.R` — a demographic/geospatial
  clustering + ML engine (tidyverse, recipes, randomForest)
- `R Code UK locations.R` — UK demographic analysis off an Excel input
- `pari_mutuel_trader/` — a Python long-only weekly stock picker (numpy/pandas/FastAPI/Streamlit)

There is no browser automation, no scraping, no crawl scheduler, no object store, no database
layer, and no US or EU price-collection code anywhere in the tree. `grep` for
playwright/selenium/puppeteer/postgres/sqlalchemy/duckdb/boto3/s3/proxy returns nothing relevant.

`list_repos` reports exactly one repository reachable from this session: `drcarls/vols`.

**Consequence:** "extend the existing pipeline" cannot be honoured yet, because the existing
pipeline is not visible. Either name the repo (it can be attached mid-session) or confirm the
collector is greenfield. Everything below is written so it is correct under either answer, but the
storage and egress sections are the parts that would be rewritten to match an existing stack.

---

## 2. Legal map, as verified (2026-09-14)

Build this as configuration — one record per rule, with effective date, scope, exemptions, and
remedy — so the flag engine resolves a violation against a jurisdiction rather than hard-coding it.

| Jurisdiction | Instrument | Effective | Scope | Private right of action |
|---|---|---|---|---|
| Federal | Rule on Unfair or Deceptive Fees, 16 CFR pt. 464 | **2025-05-12** | Live-event tickets + short-term lodging only; includes platforms, resellers, travel agents | No — FTC enforcement only |
| CA | SB 478 (Honest Pricing), amends CLRA | **2024-07-01** | Cross-sector | Yes — CLRA: actual damages or min **$1,000/violation** in class actions, plus restitution, punitives, injunction, fees |
| CA | **SB 1524** — restaurant/bar/food-concession/grocery exception | 2024 | Narrow, and **conditional** | via CLRA |
| MN | junk-fee ban (2024 session) | **2025-01** | Cross-sector | confirm |
| VA | Va. Code § 59.1-607 et seq. | **2025-07-01** | Cross-sector | confirm |
| MA | 940 CMR 38.00 (AG regulation) | **2025-09-02** | Cross-sector; paired with subscription rules | confirm |
| CO | HB25-1090 | **2026-01-01** | Cross-sector | confirm |
| NJ | AG/Div. Consumer Affairs Junk Fees Enforcement Statement + Exec. Order No. 19 | **2026-06-15** | All industries, under the Consumer Fraud Act | CFA has one; AG posture is the new fact. Penalties $10k first / $20k subsequent per violation |
| Other | general UDAP | — | — | varies |

### Corrections and additions to the brief

1. **The CA restaurant carve-out is SB 1524, and it is conditional, not absolute.** The exemption
   applies only where the mandatory fee is "clearly and conspicuously displayed, with an
   explanation of its purpose," on the advertisement, menu, or other price display. That is a
   *testable predicate*, which makes restaurants a target rather than an exclusion: capture the
   menu display, test for presence-of-fee + presence-of-purpose-explanation, and a failure of
   either drops the business back under SB 478. (The brief cited "AB 1264"; that cite did not
   verify. AB 537, a California lodging-specific pricing rule, appeared in secondary sources and
   should be confirmed before it goes in the config.)
2. **Connecticut and Oregon** also have cross-sector price-transparency statutes and are absent
   from the vantage list. Adding them is cheap at design time and expensive later.
3. **CO 2026-01-01 was the last known effective-date boundary.** The "re-run every flow in the
   week a new law takes effect" rule therefore has no scheduled firing from this table and will
   silently never run. It needs a legislative-tracker input (2026–27 sessions) or it is dead code.

### Anchor cases for the pattern-match screen (verified)

- **StubHub / FTC**, announced 2026-04-09 — $10M in redress for ticket sales 2025-05-12 to
  05-14 where total price was absent from the initial display. Note this is an FTC action, not a
  private class action; useful as a fact pattern, not as a damages model.
- **FTC + 7 states v. Live Nation / Ticketmaster**, filed 2025-09 — includes historic drip pricing.
- **Chowning v. Tyler Technologies (ReserveCalifornia)**, filed 2025-05-08, N.D. Cal. — single
  mandatory last-step reservation fee, often >20% of reservation cost, retained by the vendor
  while presented as going to Cal Parks. $37M projected FY25/26, **$398M over contract life**.
  Pleaded under CLRA, Honest Pricing, FAL, UCL. This is the cleanest template for the screen:
  one mandatory fee, one late step, one vendor, many public-sector contracts.

---

## 3. Open decisions (blocking or near-blocking)

**D1 — Where does the existing pipeline live?** §1. Blocking for storage/egress design.

**D2 — Geolocated egress provider.** Residential proxy networks carry a consent-provenance
problem: if opposing counsel asks how the vantage IPs were obtained and the answer is a
residential pool of undocumented consent, the collection method becomes the story. Recommended:
a named commercial ISP/datacenter proxy vendor that will supply a written provenance
attestation, accepting a higher block rate. Cloud regions only cover VA (us-east-1) and CA
(us-west-1) — not MN, MA, CO, NJ.

**D3 — First buyer: plaintiff firm or defendant-side audit?** This reorders the build, not just the
reports. Plaintiff-first means the pattern-match screen is the v1 surface and evidence grade is
the binding constraint. Defendant-first means per-company depth, remediation-oriented diffs, and
a client authorization that dissolves D4 entirely.

**D4 — robots.txt posture.** This is the one the brief does not address and it is
build-determinative. Most target sites disallow `/checkout`, `/cart`, and equivalents in
robots.txt. "Respect robots.txt" and "script checkout flows" are in direct conflict; strict
compliance removes most of the target set. Three coherent positions:
  - (a) robots.txt governs crawlers, not a single scripted user-paced session — defensible, widely
    practised, but a position rather than settled law;
  - (b) strict compliance, log the rest as blocked — smallest legal surface, smallest dataset;
  - (c) strict for discovery/inventory, position (a) for the scripted flow, documented in the
    method statement so a declarant can testify to it.
  This interacts with D3: a defendant-side client authorizes the collection and the question
  evaporates; a plaintiff-side buyer inherits whatever exposure the method creates, and a
  defendant will use it.

---

## 4. Design notes that change the spec

### 4.1 The federal rule has already moved the top of the market

Since 2025-05-12 the major ticketing platforms and hotel/OTA brands largely display all-in totals
by default — StubHub paid $10M for a **two-day** window. Expect the core flag ("mandatory fee
first shown at final step") to fire *rarely* at the top of industries 1 and 2. That is not the
collector failing. The residual yield in ticketing/lodging is:
  - all-in display present but **opt-in rather than default**;
  - fees added *after* the all-in event price (order processing, delivery, facility);
  - the long tail — regional venues, minor-league teams, festivals, university and independent
    box offices, and **vacation rentals / property managers**, which are materially less compliant
    than hotel chains.

Industries 3–5 are not covered by the federal rule at all, and the strongest verified anchor case
(*Chowning*) sits in industry 4. **Recommendation: keep ticketing first — the flows are easy and
the anchors are public, which is what you need to build the machine — but move reservation
platforms ahead of food delivery, and expect industry 4 and 5 to carry the violation density.**

### 4.2 Vantage state is the wrong control variable for fee amount

Ticketing and lodging fees are set by event and property, not buyer IP; running eight vantages
weekly across all flows buys very little variance and multiplies cost and block rate by eight.
Where vantage genuinely matters is different and more valuable: **jurisdictional display
switching** — a company that renders all-in pricing to a CA or MN visitor and drip pricing to an
NY visitor has demonstrated it *can* comply and elected not to. That is a strong UDAP fact and it
is cheap to detect.

Design accordingly:
  - weekly full sweep runs from **one control vantage**;
  - a **differential probe** runs the same flow across all vantages on a sampled subset, tuned to
    detect display switching rather than price variance;
  - for food delivery, the control variable is the **delivery address entered**, not the egress
    IP — most platforms geolocate on address, not network.

This cuts the weekly matrix by close to an order of magnitude with no loss of signal.

### 4.3 "No account" excludes most of food delivery

DoorDash, Uber Eats, Grubhub, and Instacart gate the fee breakdown behind login. Under the
no-account constraint, industry 3 reduces to restaurant-direct ordering (Toast, ChowNow,
Olo-powered sites), which usually expose fees anonymously — and which is exactly where the
conditional SB 1524 test in §2 applies. Worth stating plainly so the industry-3 numbers are not
read as coverage of the delivery platforms.

### 4.4 Evidence grade: hashes alone will not get this admitted

A SHA-256 computed and stored by us proves integrity only relative to our own custody. For
litigation support:
  - **RFC 3161 trusted timestamps** over each artifact hash, or a daily **Merkle root** of all new
    hashes anchored to an external timestamp authority. Cheap, and it converts "we hashed it" into
    "nothing was added or altered after date X."
  - **FRE 902(13)/(14)** self-authentication requires a certification from a qualified person.
    That means a named human custodian, a written method statement, and per-capture provenance
    records a declarant can attest to — designed in now, because retrofitting means re-collecting.
  - **Capture the network layer**: a HAR with response bodies. A DOM snapshot at the review step
    does not prove what was rendered at step 1.
  - **Record video of each flow.** Playwright gives it nearly free, and a 20-second clip of a price
    climbing is what actually persuades a reader that drip occurred — the step table is the proof,
    the video is the exhibit.
  - Full-page screenshots of dynamic checkouts are unreliable (lazy-load, sticky headers,
    virtualized lists). Prefer per-step viewport captures at recorded scroll positions, plus the
    video, plus the DOM.

### 4.5 Comparability across weeks

"Capture the same flows weekly; the variation is itself evidence" only holds if the SKU is stable.
Events sell out, inventory rotates, dates pass. Anchor definition:
  - lodging: same property, **rolling +30-day check-in**, fixed 2-night stay, plus a small set of
    **fixed holiday dates** for the peak-vs-off-peak comparison;
  - ticketing: same venue + event while it exists, with a documented substitution rule when it
    does not;
  - every anchor carries a stability flag so a week-over-week delta is never computed across a
    silent SKU substitution.

### 4.6 Storage

Content-addressed artifacts (path = hash) in an object store with versioning and **object lock in
compliance mode**; relational layer in Postgres, separate schema from reference-price data, append
-only with `UPDATE`/`DELETE` revoked at the role level rather than by convention. Daily Merkle
root per §4.4.

---

## 5. Phased plan

**Phase 0 — days 1–3.** Resolve D1–D4. Stand up the schema, the artifact store, the hash/timestamp
chain, and the rule config with §2 loaded. Write the method statement that the eventual declarant
will certify. No collection yet.

**Phase 1 — days 4–14: ticketing live.** 10–15 companies, 1–2 flows each, one control vantage,
weekly cadence. Deliberately include long-tail venues, not only the majors — that is where the
flags will fire. **Budget for Ticketmaster to fail**: Queue-It and enterprise bot management will
consume the sprint if allowed to. Per the spec's own rule, log it blocked and move on; that rule
is what protects this date. Exit criterion: step-indexed fee tables, gap metrics, and a linked
evidence page for every capture, reproducible on re-run.

**Phase 2 — weeks 3–4: lodging + the differential probe.** Hotel chains, OTAs, and vacation-rental
platforms, weighted toward vacation rentals per §4.1. Turn on the multi-vantage differential probe
and measure whether jurisdictional display switching actually occurs — if it does, it becomes a
headline product feature; if it does not, the finding retires eight-vantage weekly capture and
saves the budget.

**Phase 3 — weeks 5–6: reservation platforms.** Promoted ahead of food delivery. Seed directly
from the *Chowning* fact pattern: vendor-operated public-sector reservation systems charging a
single mandatory fee presented as though it accrues to the agency. Tyler Technologies and its
peers hold many such contracts; one matched pattern across several states is the first real output
of the screen.

**Phase 4 — weeks 7–8: the pattern-match screen.** Fact patterns as first-class records (last-step
service charge; mandatory reservation fee; resort fee excluded from headline), each linked to its
filed case, each matched against every captured company with litigation status attached. This is
the product; the per-company report and the league table fall out of the same tables.

**Phase 5 — rolling.** Car rental and parking; food delivery under the §4.3 caveat; telecom and
utilities parked until 1–4 are stable. Legislative tracker wired to the effective-date re-run
trigger per §2.

Airlines excluded throughout — ADA preemption, DOT regime.
