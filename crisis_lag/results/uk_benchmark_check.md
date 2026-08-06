# Does the UK move? Yes — so it is a contaminated benchmark

Everything spread against Britain — the original bond spreads (`country − British
consol`), and the paper's Rigobon-Sack basis (the London 3-mo trade bill) — assumes
the UK is a stable reference. It is not. Britain was a great power with its own
war risk and its own fiscal politics, and its assets move.

## The UK moves when Britain is involved or has its own crisis — not otherwise

UK consol yield benchmarked against the neutral **Dutch** yield, percentile of the
crisis-window rise vs the non-crisis null (same test as the powers):

| crisis | UK bond 90/180/270 | what is actually moving it |
|---|---|---|
| **Bosnia 1908–09** | **96 / 96 / 95** | *not Bosnia* — the 1909 naval scare ("we want eight", Mar 1909) and the People's Budget hit consols |
| **Agadir 1911** | **79 / 93 / 88** | plausibly real — Britain *was* in it (Lloyd George's Mansion House speech, 21 Jul 1911) |
| **Morocco 1905** | 34 / 24 / 49 | modest |
| **Balkans 1912–13** | 0 / 0 / 0 | Britain detached — consols still |

And in **July 1914** the UK moves hardest of all: consols **75.1 (24 Jul) → 70.5
(31 Jul)**, −6% on the last trading day — the flight-to-liquidity, plus the Bank
rate 3→4→8→10% the week after (just past where NW ends). British assets were not a
safe-haven constant; in the acute crisis they led the fall.

## It changes the answer — re-benchmark the lag and Morocco moves 16 → 3 weeks

Rebuilding the bond lag spreads against the **Dutch** neutral instead of British
consols:

| crisis | lag vs **British** consol | lag vs **Dutch** neutral |
|---|---|---|
| Morocco 1905 | 16.0 wk | **3.0 wk** |
| Bosnia 1908 | 16.4 wk | 16.4 wk |
| Agadir 1911 | 16.9 wk | 15.9 wk |
| Balkans 1912–13 | 37.4 wk | 40.4 wk |

Most crises are unchanged, but **Morocco collapses from 16 weeks to 3** once the
British benchmark is removed — the British consol's own 1905 move had been shifting
the `russia − UK` spread's peak. (The 3-week Morocco figure is itself confounded:
the Russian spread in spring 1905 was moving on Tsushima and the revolution, not
Morocco. But that is a *series* problem, separate from the *benchmark* problem this
exposes.)

## Consequence

- **Use the Dutch neutral, not British consols** — Britain carries its own moving
  war-risk-and-fiscal premium (Agadir involvement, the 1909 naval/budget crisis,
  the July-1914 liquidity flight), so `country − UK` spreads import it. This is
  what the cause-or-cover control already switched to; the finding here is that the
  original bond *lag* spreads (`nw_spreads_long.csv`, `country − British consol`)
  are contaminated for at least Morocco, and should be read against the
  Dutch-benchmarked version.
- **The paper's basis inherits the problem.** The London trade bill as the
  Rigobon-Sack basis assumes London is orthogonal to war risk; in the crises where
  Britain is a party (Agadir, and a fortiori July 1914) it is not, which weakens
  the identification exactly when it matters most. A neutral basis (Amsterdam)
  would be cleaner.

**Bottom line:** the UK moves — sometimes more than the crisis power (Bosnia
window), sometimes because it *is* the crisis (July 1914) — so it cannot serve as
the stable reference. Benchmark against a genuine neutral; where the two disagree
(Morocco), trust the neutral.

## Reproduce

The UK percentiles and the Dutch-vs-British lag comparison are computed inline
(see the session), reusing `cause_or_cover.neutral_benchmark_check` with a `uk`
series and `build_nw_spreads._dutch_neutral`. `tests/test_uk_benchmark.py` pins
the two headline facts: the UK is distinctive in Agadir but not the Balkans, and
the Morocco lag shortens sharply under the Dutch benchmark.
