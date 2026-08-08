# Modern run — the Gulf Wars (1990–91, 2003): the war priced through oil

The cases where **oil is the instrument** — the clearest modern answer to the framework's second
test (*which instrument carries the risk?*). And the academic anchor of the whole modern arc:
**Sack & Rigobon (2005), "The Effects of War Risk on U.S. Financial Markets"** built their war-risk
factor from exactly this episode, by the same heteroskedasticity-based identification this project
uses for the pre-1914 rates.

## Gulf War I, 1990–91 — priced through oil, then the inversion

| Date | Event | S&P 500 | WTI | What the market priced |
|------|-------|--------:|----:|------------------------|
| 1 Aug 1990 | pre-invasion | 355.52 | $21.59 | baseline |
| 2 Aug 1990 | **Iraq invades Kuwait** | 351.48 | $23.71 | the risk goes straight into **oil** |
| 11 Oct 1990 | oil peak / equity low | 295.46 | **$41.07** | WTI **~doubled (+90%)**, S&P **−17%** — a supply-catastrophe premium + recession fear |
| 15 Jan 1991 | eve of Desert Storm | 313.73 | $30.35 | still elevated on war-risk |
| **17 Jan 1991** | **Desert Storm begins** | **327.97** | **$21.48** | **the inversion: S&P +~4%, oil −~29–33% in a day** |
| 28 Feb 1991 | ceasefire | 367.07 | $19.28 | S&P above, oil below, pre-invasion — the whole premium unwound |

The famous counterintuitive result: **stocks soared and oil crashed the day the shooting started.**
Allied air supremacy from the first night removed the tail the market had been pricing — Saddam
torching the Gulf's fields, closing Hormuz — so the *war-supply-catastrophe premium* in oil
evaporated at once, and equities rallied on the resolved uncertainty. The chart
(`war_premia/results/gulf_war_1991.svg`) is the two lines crossing at 17 January.

**Contemporaneous attribution (the triangulation, done right).** This is not our gloss — it is the
**Bank of England's own Quarterly Bulletin, 1 March 1991**:

> *"In response to the outbreak of hostilities in the Gulf, the prices of both equities and bonds
> rose sharply on 17 January 1991 as news of early successes for the allies encouraged participants
> back into the market. Stock markets in the United States, Europe and Japan recorded rises of
> between 1% and 8%. **The largest-ever one day decline in oil prices helped the rallies.**"*

A central bank, in real time, naming what the market was pricing: allied success → resolved war
risk → the oil premium collapses → equities rally. Exactly the cause-vs-cover check the framework
demands, and it passes cleanly.

## Iraq War, 2003 — Rigobon & Sack's own case

The 1991 structure, replayed and formally measured:

- **War-risk build (Jan → mid-Mar 2003):** S&P fell ~12% (909 → 800) while WTI rose to ~$37 — war
  risk *up*, equities *down*, oil *up*.
- **The invasion (19 Mar 2003):** S&P **+9% off the low** into the invasion; WTI **−$7**. Same
  inversion — the premium resolved as the war began and went fast.

**Sack & Rigobon (2005)** computed a daily "war-risk factor" over the ten weeks to the invasion via
**heteroskedasticity-based identification**, and found rising war risk **lowered Treasury yields
and equities, widened low-grade corporate spreads, weakened the dollar, and raised oil** — with the
factor explaining a large share of those assets' variance in the run-up. This is the modern,
formal version of the book's claim, and it names **oil** as the carrier. That we reach the same
identification strategy independently for 1911 Berlin is the methodological through-line worth
stating.

## Where the Gulf Wars sit in the book

- **The instrument test, at its cleanest.** 1905 → the *fonds russes* (bonds). 1911/2022 → the
  exchange/energy. The Gulf Wars → **oil**, unambiguously. Which instrument carries the risk is a
  property of the crisis, and these are the case that makes oil the answer.
- **The oil lineage, paralleling the freeze lineage:** **Gulf 1990 → Iraq 2003 → 2022** — three
  wars the market priced through the barrel. In all three the equity market treated the conflict as
  an **energy shock**, not a systemic war (the 2022 discrimination finding is the same species).
- **The resolution-rally, generalized.** The relief rally is not only a *bond/equity* signature
  (Munich, Agadir); in an oil-instrument war it shows up as the **oil price collapsing on
  resolution**. Same mechanism — uncertainty priced, then unwound — different instrument.

## Reading it correctly

- **Effect, not influence** — a pricing result, as throughout; no claim that markets steered the
  war.
- **Oil ≠ the whole economy.** The 1990 equity decline blended the oil-war premium with a genuine
  **1990–91 recession** (NBER dates it from July 1990). The clean war signal is the **17 January
  inversion** (both assets reversing on the *military* news in one day), not the slow autumn drift —
  the same cause-vs-cover discipline the recession-confounded 1948 and 2022 cases required.

## Reproduce

```bash
# Oil (FRED WTI, daily back to 1986) + S&P (Yahoo ^GSPC):
curl -sS "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO&cosd=1990-06-01&coed=1991-04-30"
curl -sS -A "Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=644198400&period2=670464000&interval=1d"
# Gulf War I: Kuwait invaded 2 Aug 1990; Desert Storm 17 Jan 1991. Iraq War: invasion 19 Mar 2003.
```

**Sources:** Sack & Rigobon, "The Effects of War Risk on U.S. Financial Markets," *J. Banking &
Finance* 29(7) 1769–1789 (2005) / NBER w9609. Bank of England *Quarterly Bulletin*, Q1 1991.
Verify the tape values against a second source before publication.
