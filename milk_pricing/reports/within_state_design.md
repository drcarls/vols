# The rural gradient is between states, not within them

**Prompted by the client's observation that Mississippi has low-Black rural ZIP codes.
Following it up found that the stratification used throughout this project selects on
state, and that correcting it reverses the sign of the Walmart finding.**

Reproduce: `python3 analysis/within_state_design.py`

---

## 1. The flaw

`analysis/segmented_rural.py` stratifies on **national** income quartiles and **absolute**
racial thresholds (≥30% Black against ≤10%). Both choices select on state.

**The income cut.** A national bottom quartile keeps a very different share of each
state's rural ZIPs:

| state | rural ZIPs | in national Q1 | high-Black | low-Black |
|---|---|---|---|---|
| Mississippi | 61 | 36 (**59%**) | 26 | **3** |
| Louisiana | 71 | 38 (54%) | 23 | **0** |
| Arkansas | 76 | 45 (59%) | 13 | 20 |
| Tennessee | 89 | 40 (45%) | 4 | 27 |
| **Texas** | 209 | 55 (**26%**) | 5 | 33 |

Poor states are retained wholesale and richer ones filtered out. Poor states are also
disproportionately Black, so an income control intended to make areas comparable instead
sorts the sample by state.

**The racial threshold.** ≤10% Black is near-unsatisfiable in Mississippi — **4 rural
ZIPs in the entire panel** — and easy in Tennessee. The client's observation was correct
and the cause is the threshold, not the data.

Together, the two comparison groups are drawn from different states by construction:

| | states supplying the group |
|---|---|
| high-Black (154 ZIPs) | MS 25, GA 24, LA 23, SC 18, AL 16 |
| low-Black (289 ZIPs) | MO 32, KY 28, TX 27, TN 23, OK 22 |

**The confound is in the design, before any price is examined.**

## 2. The corrected design

Rank ZIPs **within their own state**: keep the poorer half of each state's rural ZIPs,
then compare the top and bottom thirds of *that state's* Black share. Every contrast is
then between rural ZIPs sharing a state, an income position, and a milk market.

| state | n hi | n lo | % Black hi | % Black lo | Walmart gap |
|---|---|---|---|---|---|
| North Carolina | 20 | 20 | 41.5 | 3.7 | **−$0.472** |
| Georgia | 16 | 16 | 55.8 | 12.0 | −$0.268 |
| Alabama | 15 | 15 | 51.0 | 5.1 | −$0.217 |
| Maryland | 4 | 4 | 31.8 | 5.4 | −$0.213 |
| Illinois | 15 | 15 | 20.1 | 1.1 | −$0.199 |
| South Carolina | 10 | 10 | 58.8 | 26.0 | −$0.150 |
| Texas | 35 | 35 | 22.2 | 1.0 | −$0.100 |
| Kentucky | 12 | 13 | 11.7 | 0.7 | −$0.032 |
| Florida | 14 | 15 | 32.3 | 3.7 | +$0.033 |
| Arkansas | 13 | 13 | 48.1 | 1.2 | +$0.078 |
| **Mississippi** | 10 | 10 | **68.9** | **25.4** | **+$0.083** |
| Louisiana | 12 | 12 | 54.0 | 21.1 | +$0.203 |

**Weighted mean −$0.121/gallon, positive in only 4 of 12 states.**

Note that the racial contrasts are real and often larger than under the old design —
Mississippi now compares 68.9% Black against 25.4%, on 10 ZIPs a side, instead of 26
against 3.

## 3. It is not an artifact of the cut points

Every combination of income restriction and racial quantile gives a negative weighted
mean:

| income kept | race cut | states | weighted mean | positive |
|---|---|---|---|---|
| poorest third | 0.25 / 0.33 / 0.40 | 18 / 11 / 10 | −0.129 / −0.210 / −0.103 | 7,4,5 |
| poorer half | 0.25 / 0.33 / 0.40 | 19 / 12 / 10 | −0.130 / −0.121 / −0.055 | 6,4,4 |
| poorest three quarters | 0.25 / 0.33 / 0.40 | 22 / 13 / 11 | −0.095 / −0.047 / −0.034 | 6,6,4 |
| no income restriction | 0.25 / 0.33 / 0.40 | 20 / 13 / 12 | −0.066 / −0.024 / −0.010 | 8,6,6 |

**Negative in all twelve variants.** The regression form agrees: on rural ZIPs, price on
%Black with income and log population gives **+0.00388 (t +1.08)**; adding state fixed
effects gives **−0.00069 (t −0.50)**.

## 4. What this means

| | Walmart rural racial gap |
|---|---|
| Pooled, national income quartile, absolute thresholds | **+$0.216** |
| Within state, within-state income and racial cuts | **−$0.121** |

**The rural gradient is a between-state composition effect.** Black rural Americans do
face higher Walmart milk prices on average — that incidence is real — but it is because
they live disproportionately in Mississippi, Louisiana, Georgia, South Carolina and
Alabama rather than in Tennessee, Texas and Missouri. Compare rural ZIP codes *inside* a
state and the gradient is zero to slightly negative.

This is the same shape as the federal-differential finding in `reports/clean_panel.md`:
burden concentrated by region, not by neighbourhood. It is a coherent result, and it is
not the result the retail theory needs.

## 5. Corrections this forces

- **`reports/segmented_rural.md` is superseded.** Its +19¢ headline is the pooled
  national-quartile figure and its +8.5¢ within-state figure used the same absolute
  thresholds, which in Mississippi meant 26 high-Black ZIPs against 3 low-Black. The
  corrected within-state estimate is −12¢.
- **The client's original design does not survive**, and my earlier acceptance of it was
  too quick. It reproduced only because the stratification selected on state; I checked
  that it reproduced without checking what it was comparing.
- **`reports/aldi_comparison.md` and `reports/aldi_2026_09.md` are unaffected in their
  conclusions** — both already withdrawn — but the reason is now sharper: the Aldi
  comparison was never going to work, because the Walmart quantity it was differencing
  was itself a between-state artifact.

## 6. What still stands

The milk carve-out (`reports/walmart_basket_national.md`, `reports/aldi_2026_09.md` §2),
the identification of each chain's pricing unit, and the federal Class I differential
findings, none of which depend on this design.
