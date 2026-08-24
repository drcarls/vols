# State pricing laws and which comparator states are contaminated

**Date:** 2026-08-24 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Question:** do other states have milk pricing rules, or other pricing rules?

**Bottom line:** Yes to both, and they behave completely differently. **Milk-specific
minimum-retail-price laws compress prices to near-uniformity and raise them by about $1.28/gal.
General below-cost / minimum-markup laws do essentially nothing** — the four *least* compressed
states in the country all have one. South Carolina has a below-cost law and it plainly does not
bind, so SC remains a clean jurisdiction for this analysis.

---

## 1. Three distinct regimes, often conflated

| Regime | What it does | States |
|---|---|---|
| **Minimum *retail* milk price** | fixes what a store may charge | **PA, NJ** |
| **Classified / producer-side pricing** | regulates what processors pay farmers | ME, MT, NV, NY, ND, PA, VA (USDA AMS list) |
| **General below-cost / minimum-markup** | bans selling under cost + a markup, all goods | ~24 states incl. AR, CA, CO, HI, ID, KY, LA, ME, MD, MA, MN, MT, NE, NC, ND, OK, RI, **SC**, TN, UT, WA, WV, WI, WY |

The USDA list is the one most often cited and it is **not** the list that matters here — it
covers producer pricing. New Jersey is absent from it yet has the tightest retail regulation in
the country: the **New Jersey Milk Control Act** sets a *presumptive retail price*, and the
Department of Agriculture publishes it. That is why NJ shows one price across 59 stores.

*The ~24-state below-cost list comes from a secondary compilation and has not been verified
statute by statute. Treat state membership as indicative; the empirical grouping below does not
depend on any single state's classification.*

## 2. Only the retail-price fix does anything

Walmart whole milk, state-level coefficient of variation:

| Group | States | Mean CV | Median CV | **Mean price** |
|---|---|---|---|---|
| **Milk retail-price fix** (PA, NJ) | 2 | 3.4% | 3.4% | **$4.75** |
| USDA classified only, no retail fix | 6 | 3.9% | **1.7%** | $3.87 |
| General below-cost law only | 20 | 9.9% | 9.7% | $3.69 |
| Neither | 18 | 12.1% | 11.2% | **$3.47** |

- ME 0%, ND 0%, VA 1%, MT 3% — the classified-pricing states that also fix retail behaviour
- NY 9%, NV 11% — classified pricing that does **not** reach retail, and they disperse normally
- **The general below-cost group is statistically indistinguishable from no law at all**

The reason is mechanical. A below-cost statute sets a floor at *cost plus a few percent*. Milk
is rarely sold below cost even as a loss leader, so the floor almost never binds. A minimum
retail price sets the *price*, so it binds always.

The four least-compressed states in the country — **SC (17.4%), MA (17.5%), NC (18.3%), TN
(20.1%)** — all have below-cost laws.

## 3. The largest price effect in this entire project

Milk-regulated states average **$4.75/gal** against **$3.47** where neither regime applies:
**+$1.28**, or **+37%**.

For scale, against everything else measured here:

| Effect | Size |
|---|---|
| **State milk-price regulation** | **+$1.28/gal** |
| SC metro discount (urban vs rural) | −$0.45 |
| Louisiana two-block gap | +$0.40 |
| SC raw high-vs-low-Black gap (composition) | +$0.28 |
| Finding B, LA, over a 20-pt %Black gap | +$0.08 |

**The single largest determinant of what an American pays for a gallon of milk in this dataset
is which state's regulatory regime they live under — by a factor of three over anything racial,
and sixteen times the surviving retail finding.**

## 4. What this means for the case

1. **Exclude PA, NJ, ME, ND, VA and MT as comparator states.** Their price distributions are set
   by statute, not by Walmart. Any pooled national regression that includes them is partly
   measuring state dairy law. (Every analysis of record here uses state or finer fixed effects,
   so this is a caution for future work rather than a defect in existing results.)
2. **South Carolina is clean.** SC has a below-cost statute, but at 17.4% CV and 21 distinct
   prices it is among the most dispersed states in the country — the law demonstrably does not
   bind. Nothing in SC's price structure is regulatory.
3. **Louisiana is clean too** (4.3% CV but no milk-price statute on either list — its compression
   is something else, consistent with `zone_vs_override.md` finding LA behaves like a near-pure
   zone state).
4. **It sharpens the PA point already made.** `pa_minimum_pricing.md` showed PA is the strongest
   counterexample to the memo's intuition — highest prices, whitest exposed population, cause is
   regulation. NJ now makes the same point independently: the second-most-regulated state, one
   price statewide, and the regulation is race-neutral on its face and in operation.
5. **Two compressed states remain unexplained** — NM (2.3%) and MO (2.8%) have no law on either
   list. HI (0%, $6.28, the highest in the country) is almost certainly isolation and freight
   rather than statute. None of these matter for the case, but they are loose ends if anyone
   builds a national model.

## Sources

- USDA AMS, "States with Classified Pricing Programs" —
  https://www.ams.usda.gov/rules-regulations/moa/dairy/classified-milk-pricing
- Pennsylvania Milk Marketing Board, minimum producer and resale prices —
  https://www.pa.gov/agencies/pmb/minimum-prices
- New Jersey Department of Agriculture, presumptive wholesale/retail milk price schedules —
  https://www.nj.gov/agriculture/divisions/md/ (monthly PDFs); N.J.S.A. 4:12A-29
- Wisconsin DATCP, Unfair Sales Act (minimum markup) —
  https://datcp.wi.gov/Pages/Programs_Services/UnfairSalesAct.aspx
- R Street Institute, "The Case Against Minimum Pricing Laws" (state survey) —
  https://www.rstreet.org/wp-content/uploads/2019/01/Final-Short-No.-661.pdf

## Reproduction

`analysis/state_pricing_laws.py`. Input: `data/national_walmart_official.csv` (gitignored).
