# The client was right: the retail finding is not uniformly null

**It is confined to low-income rural areas, where it reproduces — and where the
metro tests that carried the null could not reach it. It is also not robust. Both
halves of that belong in any memo.**

Reproduce: `python3 analysis/segmented_rural.py`

---

## What prompted this

A summary written on 2026-09-14 described the Walmart retail finding as null across
"six independent tests." The client pushed back: *"I had run regressions and segmented
black/white in urbanicity and income and it held."*

They were right, and the summary was wrong in a specific and avoidable way. **The
within-metro tests that carried `within_metro_test.md` — Atlanta, then twelve metros —
are urban by construction.** The client's design is a stratified comparison inside
income × urbanicity cells, and the cell their result lives in is *rural*. Those tests
could not have found it.

## 1. Why the pooled specification looks null

| specification | coef $/gal per point | t naive | t clustered |
|---|---|---|---|
| %Black + income + urbanicity | −0.00024 | −0.39 | −0.07 |
| + log population | +0.00032 | +0.53 | +0.10 |

Flat. But splitting by cell shows why:

| cell | n high-Black | n low-Black | high-Black | low-Black | gap |
|---|---|---|---|---|---|
| **Q1 income, rural** | 165 | 383 | $3.988 | $3.799 | **+0.189** |
| Q1 income, urban | 84 | 94 | $3.298 | $3.348 | −0.050 |
| **Q2 income, rural** | 41 | 503 | $3.680 | $3.608 | **+0.071** |
| Q2 income, urban | 51 | 121 | $3.287 | $3.337 | −0.050 |
| **Q3 income, rural** | 24 | 407 | $3.616 | $3.521 | **+0.095** |
| Q3 income, urban | 33 | 242 | $3.093 | $3.351 | −0.258 |
| Q4 income, rural | 5 | 298 | $3.036 | $3.417 | −0.381 |
| Q4 income, urban | 23 | 429 | $2.941 | $3.338 | −0.397 |

**The three lower-income rural cells are positive; every urban cell is negative.**
Pooled, they cancel. Reporting only the pooled coefficient concealed a real pattern —
that is a presentation failure, not a data one.

## 2. Inside the cell where it lives

Bottom-income-quartile rural, n = 691, 37 states, 440 counties:

| geographic control | coef $/gal per point | t naive | t clustered on state |
|---|---|---|---|
| none | **+0.00334** | **+2.77** | +1.00 |
| state fixed effects | −0.00159 | −1.34 | −0.78 |
| ZIP3 fixed effects | −0.00525 | −2.80 | **−2.16** |
| county fixed effects | **+0.00450** | **+2.01** | +1.42 |

**The client's specification reproduces at t = +2.77.** It also reverses under ZIP3
controls and returns under county controls. **The sign depends on how "same area" is
defined**, and that instability is as much the finding as the point estimate.

## 3. Why the controls disagree

| | states | counties |
|---|---|---|
| high-Black (≥30%) stores | 15 | 128 |
| low-Black (≤10%) stores | 35 | 267 |
| **containing both** | 13 | **29 of 440** |

High-Black rural stores are in MS (26), GA (25), LA (23), SC (20), AL (18), NC (17),
AR (13) — the Deep South. Low-Black rural stores are in MO (39), TX (33), KY (30),
TN (27), OK (25), WV (21) — the Ozarks, Appalachia and the plains. **Only 29 counties
in the whole cell contain both groups.** Any county-level control is therefore
estimated off a very thin slice, and a ZIP3 control is finer still.

## 4. The same-state comparison

| state | n hi | n lo | high-Black | low-Black | gap |
|---|---|---|---|---|---|
| Mississippi | 26 | 3 | $4.474 | $3.967 | **+0.507** |
| Florida | 5 | 12 | $3.984 | $3.606 | +0.378 |
| Tennessee | 4 | 27 | $4.312 | $3.994 | +0.318 |
| Arkansas | 13 | 20 | $4.398 | $4.192 | +0.206 |
| Texas | 5 | 33 | $3.934 | $3.802 | +0.132 |
| Georgia | 25 | 3 | $3.792 | $3.727 | +0.066 |
| Illinois | 3 | 19 | $3.373 | $3.354 | +0.019 |
| Alabama | 18 | 12 | $3.974 | $4.226 | −0.251 |
| North Carolina | 17 | 16 | $3.305 | $3.768 | **−0.463** |

**Weighted within-state gap +$0.085/gal, positive in 7 of 9 states** — against +$0.189
pooled across states. So roughly **half** the raw gap is between-state composition and
half survives inside states. Several of the state cells rest on 3–5 stores on one side.

## 5. The defensible statement

> In low-income rural areas — and only there — Walmart milk prices average
> **19¢/gallon higher** in ZIP codes that are at least 30% Black than in ZIP codes
> under 10% Black, matched on income and urbanicity. About half of that survives
> comparing only within the same state (**+8.5¢**), and it is positive in 7 of the 9
> states where both groups appear. It does **not** survive clustering
> (t = +1.00), it **reverses** under a finer ZIP3 geographic control, and the two
> groups share only 29 of 440 counties, so a like-for-like comparison is thin.
> In urban areas the gradient runs the other way.

**That is neither "robust" nor "dead."** It is a real pattern in a specific segment
that the available data cannot cleanly separate from the geography of the rural South.

## 6. What this corrects

- The 2026-09-14 summary's "six independent tests, no positive result" was **wrong as
  stated.** Several of those tests are urban by construction and could not have
  detected this.
- `reports/within_metro_test.md` stands as to *metros*. Its conclusion should not be
  generalised to rural areas, and this report is the counterweight.
- The withdrawal of cover-memo §9 **still stands on its own terms** — that section
  claimed the premium was "robust in South Carolina and Louisiana after a same-region
  control," and SC (−$0.0087, t −1.56) and LA (+$0.0003, t +0.37) do not support it.
  The correct statement is *rural low-income segment, not those two states, and not
  robust*.
