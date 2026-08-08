# Modern run — the nuclear limit: Berlin 1961 & Cuba 1962

The discrimination test's outer boundary, and one of the book's strongest closing arguments.
Run the framework on the two moments the world came closest to nuclear war — the **Checkpoint
Charlie tank standoff (27–28 October 1961)** and the **Cuban Missile Crisis (16–28 October
1962)** — and the result is not a null to apologize for. It is a *finding*:

> **You cannot price a catastrophe you will not survive to collect on.**

If the tail event is the end of the world (and of the exchange, the currency, and the
counterparty), there is no state of the world in which selling pays off. A stock is a claim on a
future that, in the catastrophic branch, does not exist. So the market can only price the
**survivable** branch — the crisis resolving — and rationally holds or even buys into the danger.
The muted tape is the discrimination test hitting its ceiling: **markets price survivable,
collectable risks, not existential ones.**

## The evidence (S&P 500 daily, Yahoo Finance ^GSPC)

| Crisis | Standoff | Worst close | Drawdown | +25 trading days |
|--------|---------:|------------:|---------:|-----------------:|
| **Berlin / Checkpoint Charlie** | 27 Oct 1961 (68.34) | 67.98 (24 Oct) | **−0.5%**, and the dip *preceded* the standoff | **+5%** (71.93) |
| **Cuban Missile Crisis** | 22 Oct 1962 (Kennedy's quarantine speech, 54.96) | 53.49 (23 Oct) | **−3.8%** from the 19 Oct pre-speech level | **+13%** (62.12); ~+18% into December |

Two facts do the work:

1. **Berlin 1961 is invisible in the tape.** US and Soviet tanks faced off at Checkpoint Charlie;
   the S&P moved −0.2% on the day and **rose steadily throughout**, up ~5% within five weeks. The
   market simply did not react.
2. **Cuba 1962's low came *before* the most dangerous days.** The trough (53.49) was **23
   October** — the day after Kennedy's speech. The most dangerous days were **24–28 October** (the
   blockade enforced, an American U-2 shot down over Cuba on the 27th) — and the market **rose on
   24 October** and kept rising, rallying ~18% into December. The tape got *calmer* as the danger
   *peaked*.

Chart: `war_premia/results/modern_nuclear_limits.svg` — both crises in event time, indexed to the
standoff day. Two nearly flat lines through the danger, then a drift up.

## Reading it correctly (the honesty the finding requires)

- **Context matters and is disclosed.** 1962 was already a bad year — the spring "Kennedy Slide"
  had bottomed in June — so October's move sits inside a recovery. That *strengthens* the point:
  even against a jittery tape, the closest brush with annihilation produced only a ~4% wobble that
  reversed before the crisis ended.
- **This is not "markets are efficient/wise."** It is a structural limit: the pay-off matrix of an
  extinction-scale risk has no branch in which bearishness is rewarded, so the signal is
  *unavailable*, not *absent*. The framework's whole logic (price = probability-weighted,
  collectable loss) simply runs out of domain.
- **It closes the discrimination ladder.** Localized wars → ignored (Second Balkan 1913, Falklands
  1982). General/systemic war → priced, modestly (Agadir, 1912, and — through the energy channel —
  2022). Existential/nuclear → **un-priceable** (Berlin '61, Cuba '62). The same rule generates all
  three rungs: the market prices the risks it could survive to collect on, and only those.

## Against Kirshner

This is squarely on his turf (US Cold War) but it is not a *preference* claim — no one argues
bankers lobbied Kennedy. It is a **pricing-limits** claim, a face his frame doesn't reach: the
market's silence in October 1962 is not war-aversion expressed or suppressed; it is the risk
calculus meeting a payoff it cannot represent.

## Reproduce

```bash
# S&P 500 daily via Yahoo v8 chart API (reaches back to 1928; negative epochs OK):
curl -sS -A "Mozilla/5.0" \
  "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=-230000000&period2=-223000000&interval=1d"  # Cuba 1962
curl -sS -A "Mozilla/5.0" \
  "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=-261500000&period2=-254500000&interval=1d"  # Berlin 1961
# parse timestamp + indicators.quote[0].close from the JSON.
```

*Caveat: closes are the ^GSPC daily series (index level, adjusted); verify the crisis-window
values against a second source (e.g. official S&P records) before publication.*
