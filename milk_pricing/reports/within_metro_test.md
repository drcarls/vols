# The within-metro test: Atlanta and eight other metros

**Date:** 2026-08-22 · Branch `claude/walmart-milk-pricing-sc-m7zc99`
**Prompt:** "You got some data already for Atlanta and other metros."

**Bottom line:** Correct, and it is the test that has been missing. Every positive result in
this engagement has been a **between-region** contrast, and every attempt to control for region
either killed the effect or was open to the charge of over-controlling. A large metro solves
that structurally: Fulton and Clayton counties are ~67–68% Black, Cherokee and Forsyth are under
7%, and all of them sit in one metropolitan market, one labour market, one competitive
environment, and (in Atlanta's case) two adjacent Class I differentials. **Run inside Atlanta,
the memo's own design returns −$0.029/gal, t = −0.59, permutation p = 0.65.** Pooled over
eight metros, 84 within-metro matched pairs give −$0.060, t = −1.28.

This is a **well-powered** null, not an underpowered one — see §4.

---

## 1. The metro sample

| Metro | Stores | Median %Black | ZIPs ≥30% | ZIPs ≤10% | Price sd |
|---|---|---|---|---|---|
| **Atlanta** (20 cos.) | **71** | **26.4** | **30** | **13** | $0.290 |
| Dallas–Fort Worth | 99 | 11.1 | 11 | 46 | $0.295 |
| Houston | 66 | 11.5 | 5 | 29 | $0.298 |
| Chicago | 62 | 5.0 | 8 | 42 | $0.250 |
| Birmingham | 28 | 13.2 | 7 | 7 | $0.492 |
| Detroit | 25 | 4.8 | 0 | 20 | $0.233 |
| Cleveland | 24 | 5.8 | 1 | 18 | $0.186 |
| Baltimore | 24 | 17.7 | 6 | 7 | $0.391 |
| Charlotte | 23 | 16.7 | 6 | 7 | $0.294 |
| Jacksonville | 21 | 12.3 | 4 | 9 | $0.307 |
| New Orleans | 21 | 30.4 | 11 | 5 | **$0.007** |
| Columbia SC | 15 | 26.1 | 5 | 1 | $0.373 |

Atlanta is the best-powered cell available anywhere in this project: **30 high-Black stores**,
more than SC's entire rural high-Black sample (25) and comparable to Louisiana's (33), and
unlike those it has a matched low-Black comparison group **in the same market**.

Note New Orleans: sd **$0.007** across 21 stores. There is essentially no intra-metro price
variation in New Orleans at all, which means Louisiana's surviving result is entirely a rural
phenomenon and cannot be tested in that state's largest city.

## 2. Continuous specification

Walmart price on %Black, controlling median income and log(population), within each metro:

| Metro | n | %Black coefficient |
|---|---|---|
| **Atlanta** | 71 | **+0.00046 (t +0.28)** |
| Chicago | 62 | +0.00186 (t +1.25) |
| Houston | 66 | +0.00128 (t +0.34) |
| Cleveland | 24 | +0.00206 (t +0.54) |
| New Orleans | 21 | +0.00012 (t +1.48) |
| Birmingham | 28 | −0.00167 (t −0.43) |
| Charlotte | 23 | −0.00234 (t −0.52) |
| Dallas–FW | 99 | −0.00259 (t −1.11) |
| Jacksonville | 21 | −0.00444 (t −0.65) |
| Detroit | 25 | −0.00585 (t −0.60) |
| Baltimore | 24 | −0.00778 (t −1.90) |
| Columbia SC | 15 | −0.00936 (t −1.33) |

**Not one metro is significantly positive.** Pooled over the nine metros with at least four
stores in each racial tail, with metro fixed effects: **−0.00071 (t −0.88)**, n = 415.

## 3. The memo's own design, inside a single metro

Nearest-neighbour matching on income and log(population), ≥30% vs ≤10% Black, one-sided
permutation inference — the identical procedure that produced Finding B:

| Metro | Pairs | Gap $/gal | t |
|---|---|---|---|
| **Atlanta** | **30** | **−$0.029** | **−0.59** (perm p = **0.65**) |
| Chicago | 8 | +$0.211 | +1.83 |
| Houston | 5 | +$0.344 | +1.55 |
| Birmingham | 7 | +$0.026 | +0.10 |
| New Orleans | 11 | +$0.003 | +0.90 |
| Dallas–FW | 11 | −$0.075 | −0.67 |
| Baltimore | 6 | −$0.317 | −2.57 |
| Charlotte | 6 | −$0.840 | −4.09 |
| **All pooled** | **84** | **−$0.060** | **−1.28** |

Atlanta's raw high-vs-low gap is +$0.049, and it goes to −$0.029 under matching — because
Atlanta's high-Black stores sit in ZIPs averaging **$66,554** median income against **$94,688**
for the low-Black stores. Income matching is doing real work, exactly as it should.

The dose-response ladder is flat and non-monotonic:

| Atlanta stores by %Black sextile | 4.9 | 12.7 | 21.0 | 35.0 | 56.4 | 81.0 |
|---|---|---|---|---|---|---|
| mean price | $3.196 | $3.057 | $3.203 | $3.227 | $3.299 | $3.240 |

A $0.04 rise from the whitest sextile to the Blackest, with the second sextile the cheapest of
all. And by county, DeKalb (44.2% Black, $3.089), Gwinnett (27.2%, $3.083) and Forsyth (6.8%,
$3.090) are within a penny of each other. Atlanta's expensive stores are the **outer ring** —
Carroll $4.000, Fayette $3.670, Henry $3.665, Hall $3.360 — the same distance-from-core pattern
documented for SC in `why_sc_varies.md`, not a racial one.

## 4. The null is informative

30 pairs, sd of pair differences $0.272, SE $0.0497.

- **95% CI on the Atlanta gap: −$0.127 to +$0.068.**
- **Minimum detectable effect (80% power, one-sided 5%): $0.124/gal.**

Against the effects claimed elsewhere in this project:

| Claimed effect | Size | Atlanta's power to detect it |
|---|---|---|
| SC rural high-vs-low-Black raw gap | $0.278 | **>99%** |
| Louisiana two-block gap | $0.398 | **>99%** |
| SC unmatched DiD | $0.162 | **95%** |
| LA Finding B over a 20-pt %Black gap | $0.084 | 52% |

So Atlanta rules out anything the size of the memo's headline claims. It does not rule out an
effect as small as Louisiana's continuous slope — that one needs more metros, not more Atlanta.

## 5. What this settles

The recurring objection to every prior test was symmetrical and unresolvable: county fixed
effects might be over-controlling (absorbing the mechanism), while no controls at all leaves a
between-region confound. **A metro breaks the symmetry.** Within Atlanta there is no plausible
story in which Fulton and Cherokee face different distribution costs, different freight,
different Class I zones, or different chain-level pricing regions — and the racial contrast is
as large as anywhere in the country.

Consequences:

1. **The urban retail theory is dead.** It is null in Atlanta on the memo's own design, null on
   the continuous specification in twelve of twelve metros, and null pooled. This should be
   stated affirmatively in the memo rather than left for the other side to find.
2. **Finding B, if it survives at all, is a rural phenomenon** — and specifically a phenomenon
   about which *market* a rural store is assigned to, since New Orleans shows that Louisiana's
   own largest metro has a $0.007 price spread.
3. **It reinforces the SC result in `why_sc_varies.md`**: the operative gradient in the data is
   distance from a metro core, not race. Where Black and white communities share a metro they
   pay the same; the disparity arises because Black communities are disproportionately outside
   metros. That is a real disparate-impact structure and a defensible one to plead, but it is a
   different claim than the memo currently makes.
4. **Priority for the comparison basket** (`why_sc_varies.md` §7): Atlanta is where to run it.
   71 stores, both racial tails, one market — a within-store placebo across products, inside a
   design that already controls geography.

## Reproduction

`analysis/within_metro.py`. Input: `data/national_walmart_official.csv` (gitignored).
Metro definitions are county lists in the script; they are conventional MSA approximations, not
official CBSA delineations, and are listed there for inspection.
