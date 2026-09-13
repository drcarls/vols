# California WIC exposure — the memo's §3, audited

**It verifies. Every figure in the August memorandum's §3 reproduces to the third decimal
on the underlying CDPH data, which this project did not previously hold.**

Reproduce: `python3 analysis/ca_wic.py` (defaults to 2024; pass a year for another)

---

## Source

CDPH, **WIC Participants by County**, CHHS Open Data Portal dataset
`890afa4a-fc77-4d1a-a09f-52a7f0e3a490`, **Report 2 — participants by county of residence and
by race/ethnicity, 2019–2024**. Public, unauthenticated, monthly and annual.

This matters for what the numbers mean: these are **actual participant counts by race**, not
county racial composition used as a proxy. The exposure figures are participant-weighted in
the strict sense, which is a stronger design than the ZIP-level ecological work elsewhere in
this project. 56 of 58 counties matched to the USDA differential table; **1,000,430 issued
participants** in 2024.

## 1. Participant-weighted Class I differential, by race/ethnicity (2024)

| Group | Participants | Share | Before | After | Rise | Gap vs White, before → after | Ratio |
|---|---|---|---|---|---|---|---|
| Black | 55,273 | 5.5% | $1.929 | $2.600 | +$0.670 | **+0.6¢ → +1.2¢/gal** | 1.058 |
| Hispanic | 769,380 | 76.9% | $1.910 | $2.584 | +$0.674 | +0.4¢ → +1.1¢/gal | 1.052 |
| Asian | 45,937 | 4.6% | $1.868 | $2.502 | +$0.634 | +0.1¢ → +0.4¢/gal | 1.019 |
| Other | 56,609 | 5.7% | $1.855 | $2.463 | +$0.609 | −0.1¢ → +0.1¢/gal | 1.003 |
| White NH | 73,231 | 7.3% | $1.861 | $2.456 | +$0.595 | — | — |

**Against the August memorandum, which reported Black $1.93 → $2.60, Hispanic $1.91 → $2.58,
Asian $1.87 → $2.50, White $1.86 → $2.45 — every value reproduces.** So does the Hispanic
share of CA WIC (memo "≈77%", actual 76.9%) and the differential rise (memo "+$0.67/cwt vs
white +$0.59", actual +$0.670 vs +$0.595).

## 2. The 2025 change widened it, for every group

| Group | Exposure ratio to White NH, before → after | |
|---|---|---|
| Black | 1.0366 → **1.0585** | widened |
| Hispanic | 1.0260 → **1.0519** | widened |
| Asian | 1.0033 → 1.0185 | widened |
| Other | 0.9964 → 1.0029 | widened |

The memo reported the overall ratio rising 1.038 → 1.061; the Black-specific figure is
1.0366 → 1.0585. Same movement.

## 3. Where the Black exposure sits

| County | Black participants | % of CA Black WIC | Before | After | Rise |
|---|---|---|---|---|---|
| Los Angeles | 20,582 | **37.2%** | $2.10 | $2.80 | +$0.70 |
| San Bernardino | 5,281 | 9.6% | $1.80 | $2.60 | +$0.80 |
| Sacramento | 4,570 | 8.3% | $1.70 | $2.20 | +$0.50 |
| San Diego | 4,169 | 7.5% | $2.10 | $2.80 | +$0.70 |
| Riverside | 3,810 | 6.9% | $2.00 | $2.80 | +$0.80 |
| Alameda | 3,186 | 5.8% | $1.80 | $2.40 | +$0.60 |
| Contra Costa | 2,407 | 4.4% | $1.80 | $2.40 | +$0.60 |
| Fresno | 2,132 | 3.9% | $1.60 | $2.20 | +$0.60 |

The memo said "Los Angeles County alone contains ≈40% of Black exposure (San Bernardino 10%,
San Diego 8%, Riverside 7%, Sacramento 7%)." Actual: LA **37.2%**, San Bernardino 9.6%,
Sacramento 8.3%, San Diego 7.5%, Riverside 6.9%. Correct to within a point, with Sacramento
and San Diego in the opposite order.

## 4. Annual dollars — the one place to be careful

The differential is $/cwt. Converting to a household figure requires an assumed annual
gallonage **and** full retail pass-through. Neither is measured here.

Per-gallon rise: Black **5.76¢**, White **5.12¢**, difference **0.65¢**.

| Assumed gallons/yr | Black $/yr | White $/yr | Difference |
|---|---|---|---|
| 16 — conservative | $0.92 | $0.82 | $0.10 |
| 32 — ≈ the August memo's implied figure | $1.84 | $1.64 | $0.21 |
| 43 — WIC child package, 16 qt/mo at 90% redemption | $2.48 | $2.20 | $0.28 |

The memo reported $1.87–$2.49/yr for Black participants against $1.64–$2.19 for white. That
corresponds to roughly 32 gallons a year, which sits inside the plausible range for the WIC
food package. **The figures are defensible; they are an assumption rather than an
observation, and should be labelled as such.**

## 5. What this supports

**Supports:** a real, participant-weighted exposure gap in a federal nutrition program, and
its widening by the 2025 amendment. Because it uses actual participant counts by race rather
than area composition, it is not vulnerable to the ecological objection that applies to the
ZIP-level work.

**Does not support:** any dollar claim about a household. California is a low-differential
state; the per-person amounts are cents to low single dollars a year; retail pass-through is
unmeasured. **The value of this section is the nexus, not the magnitude** — a federal
nutrition program whose participants are disproportionately minority, buying a good whose
federal price floor USDA raised while certifying no civil-rights impact.

## 6. One caveat the memo does not state

Hispanic participants are **76.9%** of CA WIC and their exposure ratio (1.052) is close to the
Black ratio (1.058). The gap is therefore not specific to Black participants within the WIC
population — it is a gap between *both* large minority groups and white participants, driven
by Southern California county differentials. That is a different shape from the national
Finding A, where Hispanic incidence is approximately neutral. Worth stating before an
opposing expert points it out.
