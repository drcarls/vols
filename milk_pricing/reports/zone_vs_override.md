# Zone base vs. local override: what the architecture does to Finding B

**Date:** 2026-08-22 · Branch `claude/walmart-milk-pricing-sc-m7zc99`

**Source for the architecture:** the client, who designed Walmart's pricing zones. As of
**2014**: roughly **57 zones nationally**, with **store-level overrides** and **discretionary
competitor adjustments** on top. Treated here as a design fact to test against, not as a
citable assertion — see §7.

**Bottom line:** The architecture splits Walmart's shelf price into a centrally-set component
and a locally-discretionary one, roughly 59/41. The **central component shows no racial
gradient anywhere** (t −0.75). The **local component is significantly negative nationally**
(t −7.02) — discretion lowers prices in Blacker areas on average. Finding B lives entirely in
the local component, which is the half that a Rule 23 commonality analysis treats least
favourably. **Louisiana is the one real survivor**, and reframed correctly it is a
*block-assignment* finding, which is the stronger theory anyway.

---

## 1. Why 57 zones is the number that matters

4,149 stores over ~57 zones is ~73 stores per zone. That is far coarser than anything visible
in the price file, which shows 184 distinct national prices and 52 distinct prices in Texas
alone. The reconciliation is the architecture: **observed price = zone base + store override +
competitor adjustment.** The fine price grid documented in
`walmart_pricing_geography.md` is not a zone map. It is a zone map plus two layers of local
discretion.

Every prior analysis in this engagement — the memo's matched-pair design, my ZIP3-region
re-test, the county fixed effects — was implicitly testing a single blended number without
knowing which layer it came from. That is the error this report corrects.

**Vintage caveat, stated up front.** The design fact is 2014; the price data is 2026, after
the digital-shelf-label rollout. The zone *count* may well have changed. What is being used
here is the *architecture* (central base + local override), which is the part that governs the
analysis, not the number 57.

## 2. Splitting the price

No zone map is available, so the coarsest exogenous partitions on hand are used as proxies:
**state** (51 groups) and **ZIP2 prefix** (98 groups). A true 57-zone map sits between them,
and both proxies give the same answer.

| Zone proxy | Groups | Zone (central) share of price variance | Override share | Override sd |
|---|---|---|---|---|
| State | 51 | **58.9%** | **41.1%** | $0.425 |
| ZIP2 | 98 | 61.2% | 38.8% | $0.413 |

So roughly **three-fifths of the variation in what a Walmart shopper pays for a gallon of milk
is centrally set, and two-fifths is local discretion.** Mean absolute override: **$0.32**.
That is a large number — bigger than any racial gap claimed anywhere in this engagement.

## 3. The centrally-set component has no racial gradient

Regressing the **zone's** mean price on the **zone's** mean %Black:

| Zone proxy | Raw | + median income |
|---|---|---|
| State (n=51) | −0.00679 (t −0.75) | −0.00670 (t −0.74) |
| ZIP2 (n=98) | −0.00398 (t −0.63) | −0.00421 (t −0.66) |

Null, and pointed the wrong way. **The half of the price Walmart sets centrally does not track
race.**

## 4. The discretionary component is nationally *negative*

Store-level deviation from the zone base, on store %Black, controlling income and log(pop):

| Zone proxy | Coefficient |
|---|---|
| State FE | **−0.00352 (t −7.02)** |
| ZIP2 FE | −0.00349 (t −6.72) |

Nationally, **local discretion pushes prices *down* in Blacker areas** — consistent with
competitor adjustments being used where hard discounters are present. That is the opposite of
the memo's theory, at t = −7.

Regionally it splits:

| Region | Geo | n | %Black on override |
|---|---|---|---|
| Deep South (SC, LA, MS, AL, GA, AR, NC, TN) | rural | 664 | −0.00066 (t −0.58) |
| Deep South | urban | 247 | +0.00170 (t +1.55) |
| Rest of country | rural | 1,811 | **−0.00428 (t −3.52)** |
| Rest of country | urban | 1,418 | **−0.00358 (t −5.10)** |

The Deep South is not *positive* — it is where the national discount **fails to appear**. That
is a real and defensible pattern, but it is a "differential absence of a benefit" claim, which
is materially weaker than "Black shoppers are charged more," and it should be described as
what it is.

## 5. The problem this creates for Finding B

Finding B is a within-state comparison of rural ZIPs. With ~57 national zones, most states are
one zone or a small number. **A within-state test is therefore a test of the override layer,
almost by construction.** Finding B is not a claim about Walmart's pricing policy. It is a
claim about **local discretionary departures from that policy**.

That distinction is the whole ballgame for class treatment, and counsel should look at it
early: in *Wal-Mart Stores, Inc. v. Dukes*, 564 U.S. 338 (2011), the Court held that a policy
of **allowing discretion** to local supervisors is "just the opposite of a uniform employment
practice" and cannot by itself supply Rule 23(a)(2) commonality. Dukes is a Title VII case and
a retail-pricing theory would run under different substantive law, but the commonality
reasoning is not limited to employment, and it is Walmart's own precedent. **A pricing theory
built on the override layer walks into it; a theory built on the zone layer does not.**

Effect sizes make the same point from the other direction. Against a national override sd of
$0.425:

- **LA:** Finding B implies $0.084 across a 20-point %Black gap = **0.41 sd** of that state's
  rural override.
- **SC:** implies $0.033 = **0.06 sd**.

## 6. Louisiana, restated correctly

Per-state override regressions (within-state price on %Black, controls) put Louisiana alone:

| State | Stores | Override sd | All stores | Rural only |
|---|---|---|---|---|
| **LA** | 100 | $0.195 | **+0.00372 (t +3.30)** | **+0.00418 (t +2.72)** |
| SC | 92 | $0.539 | +0.00543 (t +1.37) | +0.00164 (t +0.33) |
| AR | 88 | $0.491 | +0.00666 (t +2.65) | +0.00550 (t +1.93) |
| MS | 67 | $0.436 | −0.00099 (t −0.39) | +0.00001 (t +0.01) |
| NC | 167 | $0.591 | −0.00627 (t −2.44) | −0.00608 (t −1.89) |
| AL | 117 | $0.579 | −0.00746 (t −2.96) | −0.00469 (t −1.66) |
| TX | 420 | $0.538 | **−0.01422 (t −7.03)** | −0.00787 (t −2.75) |
| OK | 101 | $0.582 | −0.03643 (t −5.59) | −0.02333 (t −3.44) |

*(Virginia's rural cell reads +0.00000 at t +4.59 — degenerate. VA has an override sd of
$0.028 and essentially two prices statewide. Ignore it; it is not a finding.)*

Louisiana is the one cell that survives stress-testing:

- Unrestricted permutation on %Black: **p = 0.0004** (all stores), **p = 0.0008** (rural).
- Leave-one-parish-out: t stays between **+2.30 and +3.56** across every parish dropped.
- Drop the 2/4/6/8 highest-%Black stores: t stays between **+2.54 and +3.37**.

And Louisiana has the **second-tightest override of any large state** ($0.195). That is the
interesting part: LA behaves almost like a pure zone state, and its small residual variation is
systematically racial.

**What is actually going on in Louisiana is block assignment, not store discretion.** LA has
two price blocks:

| Block | Stores | Mean price | %Black | Median income | Urban |
|---|---|---|---|---|---|
| **LOW** ($4.19–4.32) | 36 | $4.316 | **25.7%** | $52,548 | 14% |
| **HIGH** ($4.64–4.78) | 64 | $4.714 | **34.2%** | $58,654 | 38% |

Gap: **$0.398**. Modelling assignment directly — P(store sits in the HIGH block) on %Black,
controlling income, log(population) and urban:

> **+0.00744 per point (t +2.61)** — a 20-point %Black gap makes a store **14.9 percentage
> points more likely** to be assigned to the high-price block.

Note the income control is doing real work here and cuts the right way: the high-price block is
*richer* ($58.7k vs $52.5k) and *Blacker*, so the racial gradient is not an income proxy.

**The honest limit:** the blocks are nearly geographically disjoint — 19 parishes in the low
block, 26 in the high, only **2** containing both. So this remains a between-region contrast,
with the same vulnerability documented in `tx_ca_metros.md`. The difference is that now we know
the between-region contrast is the *right* unit of analysis, because that is where the policy
operates. The question is no longer "is this confounded by geography" but "**was this boundary
drawn in a way that has racial impact**" — which is a merits question about zone design, not a
statistical artifact.

## 7. What to do

1. **Re-plead the retail theory on zone/block assignment.** Not "Walmart charges more in Black
   areas" (an override claim, nationally false, and squarely in Dukes territory) but "Walmart's
   centrally-administered price-zone assignment places Black communities in higher-price blocks"
   — a single, uniform, centrally-made decision. Louisiana is the exhibit.
2. **Discovery is now precise.** The zone assignment table for every store; zone boundary
   definitions and revision history; the criteria and any model used to assign stores; and
   separately, the **store-override and competitor-adjustment logs**, which are what will show
   whether the Deep South's missing discount is a pattern or an accident.
3. **Do not put the client's own design knowledge into the memo.** It is the reason we know
   where to look, and it should stay that. Everything in this report is derived from the public
   price file and stands on its own; the architecture only told us how to cut it. The
   confidentiality and side-switching questions flagged earlier apply and should go to counsel
   before any of this is characterised as inside knowledge.
4. **Finding A is untouched** and is now clearly the stronger of the two theories: a published
   federal schedule, centrally set, with no discretionary layer to argue about.

## Reproduction

`analysis/zone_override.py`. Input: `data/national_walmart_official.csv` (gitignored).
