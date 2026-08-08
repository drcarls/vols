# Modern run — the Berlin Airlift, 1948–49: discrimination without the nuclear confound

The first great Cold War confrontation, and a valuable rung on the discrimination ladder because
of *where* it sits: a prolonged US–USSR standoff (Soviet blockade of West Berlin, **24 June
1948**; airlift June 1948 – May 1949; blockade **lifted 12 May 1949**) that carried real
great-power-war risk — but **before nuclear parity**. The US still held the atomic monopoly (the
USSR did not test until August 1949), so a 1948 war, however terrible, was *not* existential-for-
America the way Cuba 1962 was. The market therefore *could* price it. That removes the
un-priceability confound and turns Berlin 1948 into a **clean discrimination test**: did the
market price this as a probable general war, or discount it?

It discounted it — and did so with unusual clarity.

## The evidence (S&P 500 daily, Yahoo ^GSPC)

| Phase | Move | What it shows |
|-------|-----:|---------------|
| **War-scare buildup** (Czech coup 25 Feb → June) | **+21%** (14.07 → 17.06) | The market **rallied through** the Czech coup, the March-1948 "war scare," and the Marshall Plan tensions. Recovery optimism dominated; war was priced as low-probability. |
| **Blockade onset** (24 June 1948) | **−1.0%** | A shrug. The blockade began with the S&P within 1% of its high. |
| **Airlift period** (June 1948 → May 1949) | −13% | A real decline — but it tracked the **November-1948 NBER recession** and the **surprise Truman re-election** (business feared his program), **not** Berlin war fear. |
| **Blockade lifted** (12 May 1949) | **no relief rally** | The market was near its lows and **did not rally** on the lift — it fell *further* (to 13.55 by mid-June) before the great 1949 bull market began. |

Chart: `war_premia/results/berlin_airlift_1948.svg`.

## The elegant part — the missing relief rally

This case supplies the framework's cleanest internal-consistency check. In the crises the market
**did** price — **Agadir 1911** (*"la cote retrouve toute sa fermeté"*) and **Munich 1938** (the
*"optimisme… avec éclat"* on the accord) — the *resolution* produced a **relief rally**. Berlin
1948 produced **none**: the blockade's end passed unremarked because the war it might have caused
was never in the price to begin with.

So the **presence or absence of a relief rally is itself a diagnostic** of whether a war scare was
being priced. Munich rallied because the market had been pricing the danger; Berlin didn't because
it hadn't. Same test, opposite outcome — and the contrast is the evidence.

## Reading it correctly

- **The −13% is not Berlin.** Attributing the airlift-period slide to the blockade would be the
  classic cause-vs-cover error. The 1948–49 recession and the Truman upset are the drivers; the
  blockade's own onset and *lifting* both left the tape unmoved. Disclose this — it is exactly the
  discipline the 1905 and 2022 cases demanded.
- **Why it matters that it's pre-parity.** Unlike Berlin '61 and Cuba '62 (where the muted tape is
  the *un-priceability* ceiling — you can't price extinction), Berlin '48 was a *survivable,
  collectable* risk the market **chose** to discount. So its calm is a genuine **discrimination**
  result (judged unlikely to go general), not the nuclear limit. The two mechanisms look similar in
  the tape but are different in kind, and 1948 vs 1962 is the pair that separates them.

## Where it sits in the book

- A **discrimination data point**: a real great-power confrontation the market judged unlikely to
  go general — beside the pre-1914 scares that stayed diplomatic (Bosnia 1908–09).
- The **relief-rally diagnostic**: paired with Munich/Agadir, it shows the relief rally is a
  *signature of prior pricing*, not a reflex to any good news.
- With **Berlin '61 / Cuba '62**, it forms the Cold-War triptych that **separates discrimination
  from un-priceability** — the same calm tape, two different reasons, dated by the arrival of the
  Soviet bomb.

## Reproduce

```bash
curl -sS -A "Mozilla/5.0" \
  "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=-695000000&period2=-646000000&interval=1d"
# parse timestamp + indicators.quote[0].close; blockade 24 Jun 1948, lifted 12 May 1949.
```

*Caveat: ^GSPC daily index levels; verify crisis-window values against a second source before
publication. The recession/Truman attributions are standard (NBER dates the recession from Nov
1948) but should be cited explicitly in the manuscript.*
