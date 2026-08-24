# Zone base vs. local override: what the architecture does to Finding B

**Date:** 2026-08-22 · Branch `claude/walmart-milk-pricing-sc-m7zc99`

> **Sourcing note, added after the client qualified their recollection.** The prompt for this
> analysis was the client's memory of designing Walmart's price zones — roughly 57 zones
> nationally, with store-level overrides and discretionary competitor adjustments. They have
> since said this is **12-year-old recollection (they left in 2014), does not cover how
> Walmart prices its private brand, and does not cover how Walmart prices today.** Since every
> price analysed here is a private-label gallon and the data is 2026, that recollection is
> **outside its own stated scope for this product and this period.** It is treated below as a
> hypothesis that motivated the tests, not as evidence. Every number in §2–§6 is computed from
> the price file alone; §7 marks which *interpretations* still depend on the hypothesis and
> which do not.

**Bottom line:** The price splits into a coarse geographic component and a fine store-level
one, roughly 59/41. The **coarse component shows no racial gradient anywhere** (t −0.75). The
**fine component is significantly negative nationally** (t −7.02) — store-level price
assignment runs *lower* in Blacker areas on average. Finding B lives entirely in the fine
component. **Louisiana is the one real survivor**, and reframed correctly it is a
*block-assignment* finding, which is the stronger theory anyway.

**What the data cannot tell us**, and what the retracted recollection would have: whether the
fine component is *local human discretion* or a *centrally-run algorithm assigning each store a
price point*. Those two have opposite consequences for class treatment (§5). Nothing in this
file distinguishes them.

---

## 1. Whatever the price is, it is not a contiguous zone map

This much is established from the file alone, with no reliance on anyone's recollection.

**Counties are cut apart.** Of 762 multi-store counties, **30% have an internal price spread
over $0.25, 21% over $0.50, and 9% over $1.00.** Maricopa County AZ runs 51 stores from $2.26
to $4.16. Craighead County AR: $3.06 to $5.24. Shelby County TN: $3.02 to $4.78. Stores sharing
the same **ZIP4** — effectively neighbours — differ by more than $0.50 in **17%** of cases, with
a maximum of $1.90. No contiguous zone map produces that.

**The price points are national, not regional.** The most common values recur across states
that share no border:

| Price | Stores | States |
|---|---|---|
| $3.12 | 196 | 17 (AL, AZ, FL, IA, MD, MI, NY, OH, TX, WV, …) |
| $3.82 | 190 | 17 (CA, CO, KS, MN, NH, NV, SC, VT, WA, …) |
| $3.26 | 102 | 14 (FL, IA, IN, MD, MN, NC, NE, RI, SC, …) |
| $3.32 | 83 | 18 (CT, DE, MN, NC, OR, SC, TN, TX, …) |
| **$3.64** | **124** | **3 (FL, TN, VA)** — Virginia's regulated price, the exception |

So the operative structure looks like a **national ladder of ~180 price points, with each store
assigned a rung.** Geography predicts the rung strongly but not deterministically. The regulated
states (VA, PA, ME, ND, MT, NV) are the ones that behave like true contiguous zones.

That is a different and better-supported model than "zone base plus override," and it does not
require the 57-zone recollection to hold. What follows uses "coarse" and "fine" rather than
"zone" and "override" for exactly that reason.

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

> **Corrected on the cleaned panel.** Those figures include eight states whose milk price is set
> by statute or dominated by freight (PA, NJ, ME, ND, VA, MT, AK, HI), several with a single
> price statewide, which inflates the between-state share. Excluding them the split is
> **43.7% coarse-geographic / 56.3% store-level** — the store-level layer is the *majority*, not
> the minority. That strengthens §5 below rather than weakening it: Finding B tests the
> store-level layer, and that layer is larger than stated here. See `reports/clean_panel.md`.

So on the cleaned panel **the majority of variation in what a Walmart shopper pays for a gallon
of milk is store-level, and a minority is explained by coarse geography.** Mean absolute store-level deviation: **$0.32**.
That is a large number — bigger than any racial gap claimed anywhere in this engagement.

## 3. The centrally-set component has no racial gradient

Regressing the **zone's** mean price on the **zone's** mean %Black:

| Zone proxy | Raw | + median income |
|---|---|---|
| State (n=51) | −0.00679 (t −0.75) | −0.00670 (t −0.74) |
| ZIP2 (n=98) | −0.00398 (t −0.63) | −0.00421 (t −0.66) |

Null, and pointed the wrong way. **The half of the price Walmart sets centrally does not track
race.**

## 4. The store-level component is nationally *negative*

Store-level deviation from the zone base, on store %Black, controlling income and log(pop):

| Zone proxy | Coefficient |
|---|---|
| State FE | **−0.00352 (t −7.02)** |
| ZIP2 FE | −0.00349 (t −6.72) |

Nationally, **store-level price assignment runs *lower* in Blacker areas** — consistent with
price-matching where hard discounters are present, though this data cannot confirm the
mechanism. That is the opposite of the memo's theory, at t = −7.

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

Finding B is a within-state comparison of rural ZIPs, and the coarse component is roughly
state-sized. **A within-state test is therefore a test of the fine, store-level component,
almost by construction.** Finding B is not a claim about Walmart's coarse geographic pricing.
It is a claim about **store-by-store price assignment**.

Whether that helps or hurts depends entirely on a fact we do not have:

- **If store-level assignment is local human discretion** — a manager or market director
  choosing to match a competitor — then counsel should look hard at *Wal-Mart Stores, Inc. v.
  Dukes*, 564 U.S. 338 (2011), where the Court held that a policy of **allowing discretion** to
  local supervisors is "just the opposite of a uniform employment practice" and cannot by itself
  supply Rule 23(a)(2) commonality. Dukes is a Title VII case and a retail-pricing claim runs
  under different substantive law, but the commonality reasoning is not employment-specific,
  and it is Walmart's own precedent.
- **If store-level assignment is a centralised algorithm** choosing each store's rung from the
  national ladder — which is what modern retail price optimisation looks like, and what the
  national recurrence of price points in §1 is consistent with — then there is **no Dukes
  problem at all.** A single model applied uniformly to every store is close to an ideal
  common question: one practice, one set of inputs, one output rule.

**This data cannot distinguish the two**, and the client's recollection, now qualified as
predating the relevant period and not covering private brand, cannot either. Establishing
which one governs Great Value milk today is therefore the **single highest-value item in
discovery** — it determines whether the retail theory is certifiable, not merely whether it is
true. An earlier draft of this report asserted the discretion reading; that was resting on the
recollection and is withdrawn.

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

**Holds regardless of the recollection** (computed from the price file):

1. **The 59/41 coarse-vs-fine split**, the null on the coarse component (t −0.75), and the
   nationally *negative* fine component (t −7.02).
2. **"Walmart charges more in Black areas" is false nationally** and should not be pleaded.
3. **Louisiana**, and its restatement as block assignment: the two-block structure, the $0.398
   gap, the +14.9pp assignment effect, and every stress test.
4. **The price structure is not a contiguous zone map** (§1).
5. **Finding A is untouched** and is now clearly the stronger of the two theories: a published
   federal schedule with no store-level layer to argue about.

**Depends on facts we do not have:**

6. **Whether the fine component is discretion or an algorithm** (§5) — and therefore whether
   the retail theory is certifiable. Get this first.
7. **Re-plead the retail theory on price-point assignment**, not on "Walmart charges Black
   shoppers more." Louisiana is the exhibit either way; the *characterisation* of the practice
   (a centrally-administered assignment rule vs. delegated local discretion) waits on item 6.
8. **Discovery, in priority order:** how the shelf price for Great Value milk is determined
   today, and by whom or what; the price-point assignment for every store with its inputs; any
   pricing model or optimisation system and its feature set; the price-change and
   competitor-match logs; and the history of all of it back through the class period.

**On the client's own knowledge.** It prompted these tests and should stay in that role. The
qualification helps here rather than hurting: 12-year-old general knowledge that does not cover
the product at issue or the current period sits much closer to the "general skill and knowledge"
side of the expert side-switching line than to specific confidential information. That is
counsel's call, but the concern is smaller than it looked. Nothing in this report cites it, and
nothing in it depends on it.

## Reproduction

`analysis/zone_override.py`. Input: `data/national_walmart_official.csv` (gitignored).
