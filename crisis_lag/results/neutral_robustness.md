# Does the finance-as-constraint signal survive a *far* neutral? Mostly no

The cause-or-cover result was benchmarked against the **Dutch** yield. But the
Netherlands is not a far neutral — it borders Germany and would price invasion
risk in a European war. The genuine far neutrals are the **US, Sweden,
Switzerland**. If the per-country signal is real it should survive whichever
neutral we subtract. It does not (`neutral_robustness.py`).

## The signal scatters across neutrals

**Money market** (power open-market rate − neutral), percentile of the 180-day
crisis rise vs the non-crisis null:

| neutral | Morocco/Fr | Bosnia/Ru | Agadir/Ge | Balkans/Au |
|---|---|---|---|---|
| Amsterdam (near) | 0 | 81 | 51 | 84 |
| Switzerland | 0 | 49 | 26 | 75 |
| Sweden | 0 | 89 | 70 | 28 |
| US (call money) | 10 | 21 | 59 | 94 |

**Bonds** (power yield − neutral yield), percentile of the 270-day rise:

| neutral | Morocco/Fr | Bosnia/Ru | Agadir/Ge | Balkans/Au |
|---|---|---|---|---|
| Dutch | 9 | 78 | 90 | 89 |
| US bond | 50 | 32 | 35 | 94 |
| Italian | 46 | 100 | 7 | 100 |

Russia swings 21–89 (money) and 32–100 (bond); Germany 26–70 and 7–90; Austria
28–94 in the money market. **The per-country answer depends on which neutral you
pick** — so the "finance-as-constraint holds for Germany/Russia/Austria" reading
was **Dutch-specific and is withdrawn.**

## Why it scatters

Each small neutral market has its own idiosyncratic dynamics, and `power − neutral`
is only as clean as the neutral: US **call money** is violently volatile (no
central bank before 1913; the 1907 panic; crop-season spikes), so subtracting it
injects US noise; Switzerland and Sweden are thin markets; the Netherlands carries
war-proximity risk; Italy (a Triple-Alliance great power fighting the
Italo-Turkish war) is not a neutral at all. With four confounded crises and a
small country-specific signal, the neutral-benchmark event study is **underpowered
and benchmark-sensitive** — it cannot bear per-country causal weight.

## What *does* survive — and a fairer read of Russia

- **France was calm in the money market** — 0–10th percentile against Amsterdam,
  Switzerland, Sweden *and* the US. France's short-term financing was under no
  stress in 1905; its climb-down was not an affordability event. **Robust.**
- **Austria's long-term debt repriced in the Balkans** — 89–100th percentile
  against every bond neutral (Dutch, US, Italian). **Robust.**
- **Bosnia/Russia is better than "noise floor" — it is 2 of 3.** Weighting US call
  money equally was unfair: it is the worst benchmark of the set (the 1907 panic,
  no pre-1913 central bank), and it is the lone low read (21). Among the three
  *credible* neutrals, Russia is high in **2 of 3** — Amsterdam 81, Sweden 89, with
  Switzerland the middling 49. So the Russian Bosnia signal is **suggestive**, not
  absent; it just is not clean enough (1 of 3 middling, and Russia's own series is
  the administered bank rate) to assert on its own.
- Germany (Agadir) genuinely scatters (26–70) and cannot be claimed per country
  from the money market — though Germany *is* the one robust case in the Rigobon
  basis test (`../../war_premia/results/basis_robustness.md`).

## Consequence for the book

Do **not** make per-country finance-as-constraint claims from the neutral-benchmark
market data — they don't survive the neutral. The defensible, robust statements
are narrow: (i) France's short-term finances were calm in 1905 (so the 1905
constraint lay elsewhere — the ally, Russia); (ii) Austrian debt repriced through
the Balkan Wars; (iii) the aggregate Rigobon-Sack premia reproduce (they do not
rest on a single neutral); and (iv) July 1914's money-market seizure is an
absolute move needing no benchmark. Beyond those, the per-country brake is an
archival question, not a bond-price one.

## Reproduce

```bash
cd crisis_lag && python neutral_robustness.py
```
