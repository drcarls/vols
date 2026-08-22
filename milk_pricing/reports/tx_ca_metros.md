# TX and CA metros, inside Aldi's real footprint — and what the same test does to Finding B

**Date:** 2026-08-22 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Question asked:** "did you find anything else in CA? or TX? aldi/lidl should have footprints there" → "sure use tx and ca metros"

**Bottom line:** No. Inside Aldi's verified footprint, neither TX nor CA metros show a
Walmart race or ethnicity effect. A large Hispanic effect appears in both states under
the memo's matched-pair design, but it is entirely a between-county effect and
disappears under county fixed effects. Applying that same within/between decomposition
to Finding B's states shows Finding B is also entirely between-county. That is a
question the memo has to answer, and it is now the most serious open exposure in the
retail theory.

---

## 1. Sample construction

The county-level validity filter from `RETRACTION_aldi_fallback.md` is applied first: a
county is usable only if it has ≥6 priced ZIPs and **zero** ZIPs at the $2.19 Instacart
no-serving-store fallback. Counties passing:

- **TX (147 ZIPs, 8 counties):** Brazoria, Collin, Dallas, Denton, Fort Bend, Harris, Tarrant, Travis
- **CA (116 ZIPs, 6 counties):** Fresno, Los Angeles, Riverside, San Bernardino, San Diego, Ventura

These are real Aldi markets — 27 distinct Aldi shelf prices across the CA sample, no
fallback clustering. This is the subsample where an Aldi-controlled comparison is
legitimate.

## 2. Result: null

County FE, SEs clustered on county, controls for median household income and population.
Coefficients are $/gal per percentage point.

| Sample | Outcome | %Hispanic | %Black |
|---|---|---|---|
| **TX metros** (n=147, 8 counties) | Walmart | −0.00052 (t −0.35) | −0.00035 (t −0.22) |
| | Aldi | +0.00225 (t +2.20) | −0.00108 (t −0.69) |
| | Walmart − Aldi spread | −0.00277 (t −1.31) | +0.00073 (t +0.36) |
| **CA metros** (n=116, 6 counties) | Walmart | −0.00014 (t −0.73) | +0.00021 (t +0.58) |
| | Aldi | +0.00209 (t +0.94) | **−0.01129 (t −2.98)** |
| | spread | −0.00223 (t −0.97) | **+0.01150 (t +2.81)** |
| **TX+CA pooled** (n=263, 14 counties) | Walmart | +0.00026 (t +0.50) | −0.00018 (t −0.17) |
| | spread | −0.00184 (t −1.07) | +0.00362 (t +1.21) |

**Walmart is flat on both race and ethnicity in every cell.** That is the outcome the
memo's theory is about, and it is null.

### The one significant CA cell does not survive

The CA %Black effect is on *Aldi*, not Walmart (the spread moves only because Aldi does).
It fails every robustness check:

- **Support.** CA metro %Black: median 4.2%, p75 7.8%, max 60.9%. Only **4 of 116** ZIPs
  are ≥20% Black; exactly **one** is ≥30%.
- **Drop the top-4 Black ZIPs** (same clustered county-FE model): Aldi slope −0.01639,
  **t −1.29**. Drop 5: t −1.10. Drop 10: t −0.70.
- **Leave-one-county-out:** dropping Los Angeles County alone takes it to **t −1.06**.
- **Within-county permutation on %Black, 5,000 draws:** **two-sided p = 0.177**
  (one-sided 0.091). With G=6 clusters the cluster-robust SE is badly downward-biased;
  the permutation p is the honest one.

Treat this cell as noise. It rests on four ZIPs.

## 3. The Hispanic result, and why it dies

Running the memo's own design — nearest-neighbour matching on income and log(population),
one-sided permutation inference, Walmart-only, full national file with no Aldi
restriction — on Hispanic tails produces the strongest retail result in this entire
engagement:

| State | Geo | Contrast | Pairs | Gap $/gal | t | perm p |
|---|---|---|---|---|---|---|
| TX | rural | Hisp ≥50% vs ≤20% | 45 | **+0.219** | 2.47 | **0.0270** |
| TX | urban | Hisp ≥50% vs ≤20% | 66 | +0.164 | 1.90 | 0.0913 |
| CA | rural | Hisp ≥50% vs ≤20% | 30 | +0.041 | 2.82 | 0.0540 |
| CA | urban | Hisp ≥50% vs ≤20% | 56 | **+0.113** | **8.24** | **<0.0001** |
| TX | rural | Black ≥30% vs ≤10% | 10 | −0.195 | −1.00 | 0.827 |
| TX | urban | Black ≥30% vs ≤10% | 17 | −0.533 | −3.71 | 0.999 |
| CA | rural/urban | Black ≥30% vs ≤10% | — | untestable: 0 and 1 high-Black ZIPs | | |

Four of four Hispanic cells positive, two significant, one at t=8.24. On its face this
looks like a finding.

**It is not.** The gap is entirely between counties:

| State | n | Counties | No FE, %Hisp | County FE + cluster SE, %Hisp | Within-county permutation |
|---|---|---|---|---|---|
| TX | 418 | 128 | **+0.00285 (t +2.42)** | −0.00112 (t −0.74) | p = 0.166 |
| CA | 252 | 41 | **+0.00103 (t +3.48)** | +0.00011 (t +0.44) | p = 0.574 |

The reason is visible in the sample: the two tails almost never share a county.
In TX, only **5 of 86** counties contain both a ≥50%-Hispanic and a ≤20%-Hispanic ZIP —
the high tail is Hidalgo, El Paso, Bexar; the low tail is Collin, Denton, Tarrant. In CA,
**7 of 31**. The matched-pair design is comparing Rio Grande Valley Walmarts to Collin
County Walmarts. That is a geography contrast wearing an ethnicity label.

## 4. The same test, applied to Finding B

Honesty requires running this symmetrically. Rural Walmart-only, %Black continuous,
income and log(pop) controls:

| State | Rural n | Counties | No FE %Black | Within-county %Black (multi-ZIP counties only) | Counties with both tails |
|---|---|---|---|---|---|
| SC | 59 | 32 | +0.00164 (t +0.33) | −0.00034 (t −0.04) | 3 of 25 |
| LA | 71 | 40 | **+0.00418 (t +2.72)** | −0.00140 (t −1.71) | 3 of 25 |
| MS | 61 | 41 | +0.00001 (t +0.01) | −0.00188 (t −0.64) | 1 of 32 |
| AR | 76 | 46 | +0.00550 (t +1.93) | **−0.01620 (t −2.33)** | 1 of 39 |
| NC | 122 | 68 | −0.00608 (t −1.89) | −0.00359 (t −0.54) | 2 of 55 |
| AL | 91 | 40 | −0.00469 (t −1.66) | −0.00172 (t −0.41) | 4 of 33 |

**Not one Finding-B state shows a positive within-county %Black effect.** LA goes to
−1.71; AR flips to significantly negative. The positive matched-pair results in
`memo_finding_b_revalidated.md` (LA p=0.0050, MS p=0.0143, SC p=0.0167, AR p=0.0367)
are between-county contrasts, structurally identical to the TX/CA Hispanic result that
just evaporated.

### This is genuinely two-sided — do not over-read it either way

**Against Finding B:** if the right counterfactual for a high-Black rural ZIP is a
comparable ZIP in the *same* local market, the effect is not there. The between-county
version is confounded with everything that varies across rural counties in the Deep
South and is not in the income/population controls: distance to a distribution centre,
store format and vintage, local competitive structure, freight, and Class I zone.

**For Finding B:** county fixed effects may be a *bad control* here. If Walmart sets
milk prices by market zone rather than by store, then the between-market comparison **is**
the policy comparison, and absorbing county absorbs the mechanism the case is about.
The within-county estimates are also weakly identified — only 36–49 ZIPs sit in
multi-ZIP counties, and only 1–4 counties per state contain both tails, so the
within-county coefficient is fit off a handful of atypical counties and its
confidence intervals include the between-county point estimates.

**What resolves it, and it is not more statistics:** whether Walmart's milk price is set
at store level or zone level, and at what geographic granularity. That is a
discovery question. Until it is answered, Finding B should be characterised as a
*between-market* disparity, not a within-market one, and the memo should say so
explicitly rather than let a reader assume the stronger claim.

## 5. Where this leaves the two theories

- **Finding A (USDA Class I differential):** untouched and still the stronger of the two.
  %Black on the differential +0.0354 (t 29.07) raw, +0.0330 (t 25.14) under controls,
  93/7 between/within-state. The differential is a published federal schedule; there is
  no store-level/zone-level ambiguity to litigate.
- **Finding B (Walmart retail):** survives its own design in four states but is now known
  to be a between-county contrast, with a documented same-shape false positive
  (TX/CA Hispanic) produced by that design.
- **All Aldi-based DiD findings:** remain retracted per `RETRACTION_aldi_fallback.md`.
  The TX/CA metro test above is the properly filtered rebuild, and it is null.

## Reproduction

Scripts are committed under `analysis/`; run them from the `milk_pricing/` root.

- `analysis/metros.py` — TX/CA metro regressions (Table in §2)
- `analysis/ca_sens.py` — CA leave-out, leave-one-county-out, within-county permutation (§2)
- `analysis/txca_memo.py` — the memo's matched-pair design on TX/CA race and ethnicity tails (§3)
- `analysis/hisp_fe.py` — within/between-county decomposition of the Hispanic gap (§3)
- `analysis/fb_within.py` — same decomposition applied to the Finding B states (§4)

Inputs: `data/national_walmart.json`, `data/sc_walmart_official.json`, `data/aldi_pooled.json`
(all gitignored; regenerate with the collectors in `src/milk_pricing/sources/`).
