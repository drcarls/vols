# Finding A — what it is, and a partial replication

## What it claims

Finding A is about a **federal regulation**, not a company. The USDA sets the **Class I differential** (7 CFR 1000.52): a location-specific minimum price processors must pay for the raw milk that becomes drinking milk. One dollar figure per county, roughly 3,100 rows, from a $1.60/cwt floor in the Eau Claire, Wisconsin base zone up to $7.40 in South Florida. It is a price **floor**, so it is embedded in what a gallon costs.

The values come from a spatial cost model whose inputs are entirely supply-side — hauling costs, supply and demand locations, plant capacity, road weight limits — anchored to Wisconsin. **No input is demographic or distributional.**

The memo's claim: because the geography of milk supply intersects the historical geography of Black settlement (the Delta, the Black Belt), this race-neutral cost rule falls measurably harder on Black communities — and the January 2025 amendment widened the gap rather than preserving it, from +3.8¢ to +5.6¢/gallon person-weighted.

The legal hook is not the pricing rule itself, which sits inside USDA's producer-focused AMAA mandate. It is that USDA's separate and mandatory Civil Rights Impact Analysis certified "no major civil rights impact is likely" without performing an incidence analysis, while the CRIA directive expressly covers program beneficiaries by race and by receipt of public assistance — i.e. WIC and SNAP recipients by name.

## My partial replication

The national Walmart file carries `class_I_diff_cwt`, so I could test this independently on **4,123 store-ZIPs across 49 states**. This is a different sample from the memo's county universe — only ZIPs with a Walmart — so it is corroboration, not a reproduction.

| Model | % Black coef ($/cwt per point) | t |
|---|---:|---:|
| Raw | **+0.0354** | **29.07** |
| + income, urbanicity, Hispanic share | **+0.0330** | **25.14** |
| + state fixed effects, SE clustered on state | +0.0024 | 1.86 |

And the blunt version:

| | Mean Class I differential |
|---|---:|
| ZIPs ≥50% Black (n=178) | **$5.289/cwt** |
| ZIPs ≤10% Black (n=2,729) | **$3.704/cwt** |
| Difference | **+$1.584/cwt = +13.6¢/gallon** |

## What that shows

**The effect is real and large, and it barely moves under controls.** Adding income, urbanicity and Hispanic share takes the coefficient from 0.0354 to 0.0330 — a 7% reduction. Compare Finding B, where the equivalent controls took the coefficient to zero. This is what a robust association looks like next to a fragile one.

**It is overwhelmingly a between-state effect.** With state fixed effects the coefficient falls to 6.8% of its raw value. The memo says ~92% between-state and ~8% within; I get 93/7 on a different sample. That is close agreement, and it is the memo's own characterisation, not a contradiction of it.

My within-state t is 1.86 against the memo's 16 because I clustered standard errors on state. For a claim about a state-level price surface that is the defensible choice, and counsel should expect an opposing expert to insist on it. **The within-state gradient is the weak part of Finding A; the between-state level is the strong part.**

## Why Finding A is the stronger of the two

| | Finding A (federal) | Finding B (retail) |
|---|---|---|
| Raw effect | t = 29 | t ≈ 2–3 |
| Survives income/urbanicity | **yes, ~unchanged** | no, → 0 |
| Survives pooled regression | yes (between-state) | **no** |
| Depends on a matching design | no | **yes** |
| Source | published federal regulation | scraped retail prices |

Finding A rests on a public rule anyone can read off 7 CFR 1000.52 and join to the Census. There is no scraping methodology to attack, no comparator pool, no threshold. That matters a great deal for an attorney-ready document.

## The honest tension in Finding A

Being ~93% between-state is simultaneously its robustness and its legal problem. It means the rule does not treat a Black neighbourhood differently from a white one **within** any market — the memo shows this directly, with Prince George's County (59% Black) and Fairfax (10%) both at $4.6. The disparity is about where Black Americans live relative to a national cost surface.

That is a genuine disparate-impact structure. It is also the shape of claim a defendant will argue is pure geography. The memo's §6 answer — that ~20% of the gap is removable at the same aggregate cost by letting the increase track USDA's own cost surface — is the part that does the real work, and it is worth more attention than the incidence statistics.

## What I have not done

I have not audited the rulemaking record, the CRIA, the 2025 amendment figures, the WIC analysis, or the §6 counterfactual. This is a check on the core incidence claim only, on a Walmart-ZIP sample.
