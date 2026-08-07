# What the reanalysis changes — and what to put in the book

A synthesis of the war_premia / crisis_lag / neal_weidenmier work. Organised as:
what holds, what to revise, what's still open, and what to run next. The guiding
lesson from the reanalysis: **the defensible claims are the ones that survive the
choice of instrument (bonds vs commercial paper) and the choice of benchmark
(British consols vs a neutral); any single point estimate that silently assumed
British consols were risk-free is fragile.**

## 1. What holds (survives instrument + benchmark)

- **The Rigobon-Sack estimator reproduces**, but the premium is **pooled-only and
  neutral-shared** — the "war-risk" label is not clean (§2g). Berlin is the
  largest loading (0.35) but is **not significant in any individual crisis** (every
  per-crisis t < 1); it is significant only pooled (t 6.4). And the **neutrals
  carry equally significant pooled premia** (Copenhagen t 5.6, Stockholm t 4.3,
  Geneva t 2.8, Amsterdam t 2.2) — indeed in the Balkans neutral Stockholm is
  significant where Berlin is not. So the coefficient is best read as a **loading
  on a common London-centred money-market factor** (gold-standard integration that
  tightens under stress) that every connected market shares; Berlin's is merely the
  biggest. The per-conflict premia are not reliably identified at all (Agadir n=22:
  Belgium +5.75). See `../war_premia/results/basis_robustness.md` and
  `premia_by_conflict.md`.
- **Two country-specific market facts survive every neutral benchmark** (US,
  Sweden, Switzerland, Netherlands): **France's short-term finances were calm in
  1905** (so the 1905 constraint lay in the ally, Russia, not French solvency), and
  **Austrian debt repriced through the Balkan Wars.** The broader "finance bound
  Germany/Russia/Austria too" was **Dutch-benchmark-specific and does not survive a
  far neutral** — see §2e and `neutral_robustness.md`. The per-country brake beyond
  those two facts is at the noise floor of this data.
- **Kokovtsov's 1914 dismissal was priced as a palace reshuffle, not a credit
  event** — Russian bonds flat, the French rente firmed. A clean illustration that
  the market distinguished political noise from fiscal-regime change.
- **July 1914's brake was a money-market seizure** (Bank of England 3→4→8→10% in a
  week), and it came exactly as trading stopped.

## 2. What to revise in the book

**a. Drop the single "6–10 week" transmission figure; state it by instrument.**
The lag is not one number. On long *bonds* (a solvency proxy) onset→peak is
16–37 weeks; on *commercial paper* (the instrument the brake actually runs
through) the clearest case, Austria, is abnormal within ~13 weeks; and time-to-
*material* is 1–15 weeks. Say which lag and which instrument. This is more
defensible **and** stronger: it locates the brake in the money market and stops a
reviewer from falsifying a number you didn't need.

**b. Make the bonds-vs-commercial-paper distinction explicit — it is a genuine
contribution.** Bonds price *solvency*; commercial paper prices the *immediate
cost of financing mobilisation*. The brake is a mobilisation-finance mechanism, so
it bites first in the money market — which is why July 1914 shows a discount-rate
seizure while bonds merely slid. Run the war-risk premia and the lag on the money
market as primary, bonds as the solvency complement.

**c. Rewrite the July 1914 passage — neither "flat" nor "crash".** The pre-closure
reaction *is* observable (the European sovereign complex fell ~2.5–6% in the final
trading weeks), but two disciplines apply: (i) the cross-sectional *ordering* is
flight-to-liquidity, not a war-risk ranking — Consols fell hardest *because* they
were the most marketable, so don't rank war risk by the size of the drop; (ii) the
*identified* premium is unestimable because the market shut mid-repricing. The
honest sentence: the brake was seizing in the money market, and the exchange
closed before the bond repricing could complete.

**d. Fix the benchmark — the basis asset is itself belligerent-grade.** Britain's
assets move with its own involvement (Agadir), fiscal politics (the 1909 naval
scare + People's Budget), and liquidity flight (July 1914). Worse than "contaminated":
measured against neutral bases, **London's own money-market war premium is 0.22–0.42
— as large as Berlin's** (§2g, `../war_premia/results/basis_robustness.md`). So the
Rigobon-Sack *basis* is one of the two most war-sensitive markets, not a neutral
reference; every city premium is differenced against a war-moving asset, which
compresses the premia and distorts the ranking. Re-benchmarking to a neutral also
swings real numbers (Morocco's bond lag 16 wk → 3 wk). **Re-estimate the core
premia against a neutral basis, and state plainly that the London basis biases the
original results.**

**e. Cause-vs-cover: claim only what survives a far neutral — which is very
little.** Benchmarked against the Dutch yield the market data seemed to show
finance binding Germany/Russia/Austria and not France; but re-run against genuine
far neutrals (US, Sweden, Switzerland) the per-country percentiles **scatter**
(`neutral_robustness.md`), so that reading was benchmark-specific and does not
survive. Only two country facts hold against *every* neutral: **France's short-term
finances were calm in 1905** (so the 1905 constraint lay in the ally, Russia, not
French solvency — an alliance-transmission mechanism) and **Austrian debt repriced
through the Balkan Wars.** Beyond those, the per-country brake is at the noise floor
of this data. So do **not** make per-country financial-causation claims from bond/
bill prices; whether each minister's fiscal argument *caused* or *dressed* the
climb-down is an archival question. The lesson to state in the book: a
country-specific war-risk-constraint signal is not robustly recoverable from these
spreads once you stop assuming any one market is a clean neutral.

**f. Frame the data gaps as scope conditions, not weaknesses.** Russia has no
open-market rate after 1900 (only the administered, sticky bank rate); July 1914's
short rates end 27 June, before the seizure; several crisis→power series are
confounded (Morocco→Russia by the Russo-Japanese war and 1905 revolution). Stating
these plainly is more persuasive than a false uniformity.

**g. Add a neutral placebo, and report premia against the neutral floor — not
zero.** Re-estimating the premia against neutral bases (Amsterdam, Switzerland,
Sweden, US) and placebo-testing the neutrals themselves
(`../war_premia/results/basis_robustness.md`) shows: **Berlin (0.34–0.35) is
robust to a Swiss basis and clearly exceeds the ~0.10 premium that genuine neutrals
(Amsterdam 0.09, Geneva 0.09, Stockholm 0.12) carry against London; Paris and
Vienna sit at that neutral floor.** So the Rigobon premium against a war-sensitive
money-market basis partly measures war-week money-market *integration*, which every
European market shares, not pure country war risk. Three things for the book: (i)
the German result is *not* an artifact of the contaminated London basis — a Swiss
basis reproduces it, a genuine robustness win; (ii) present the other premia as a
cluster around the neutral floor that the method cannot cleanly rank by war risk,
with the neutral placebo shown as the yardstick; (iii) **be candid about
significance** — Berlin is significant *only* pooled (t 6.4), not in any single
crisis (per-crisis t < 1), and the neutrals' pooled premia are just as significant
(Copenhagen t 5.6, Stockholm t 4.3). So the defensible claim is not "country X had a
war premium of β" but "European money markets loaded on a common London-centred
stress factor, most heavily Berlin, detectable only in the pooled sample." That
thesis is still interesting; the per-country/per-crisis premium table is not.

## 3. What is still open (needs archives or new data)

- **Intent / cause-vs-cover** for Rouvier, Kokovtsov, Biliński, and Germany — the
  cabinet and finance-ministry records. See
  [`july1914_mechanism_and_archival_test.md`](july1914_mechanism_and_archival_test.md)
  and the sources named in
  [`../crisis_lag/results/cause_or_cover.md`](../crisis_lag/results/cause_or_cover.md).
- **The German 5–23 July 1914 "quiet weeks"** — did the Reichsbank/Treasury act
  before the ultimatum? (Zilch; the Reichsbank 1914 *Verwaltungsbericht*.)
- **The acute July-1914 money-market brake** is censored in NW — document it from
  the *Chronicle* / *Economist* weekly rates (partly done, descriptively).

## 4. What to run next (ranked)

1. **Re-estimate the core Rigobon-Sack premia against a neutral basis (Amsterdam)**
   instead of the London trade bill. This is the highest-value check — the
   UK-benchmark finding puts a question mark over the current basis, and if the
   premia survive a neutral basis it is a major credibility win.
2. **Obtain the archival sources** (Zilch, Reichsbank 1914 report, French/Austrian
   cabinet records) — the only route to intent and the German quiet-weeks question.
3. **Extend the July–August 1914 money-market series** from the *Chronicle* /
   *Economist* so the acute brake is documented even though it is not
   Rigobon-Sack-estimable.
4. **Find a St Petersburg open-market rate** (the *Economist* "Foreign Bourses"
   column) to close the Russia data gap and let Russia enter on a market rate.
5. **Widen the comparator set** (Fashoda 1898, Liman von Sanders 1913, the two
   Balkan wars separately) to give the lag band statistical power — four
   confounded crises is a range check, not a test.

## One-line version

Keep the core thesis — finance was a real brake and July 1914 gave it no time —
but state the lag by instrument (money market, not one number), fix the benchmark
(neutral, not Britain), and concede that *which* powers were bound by their own
finances (Germany/Russia/Austria) differs from *how* France was bound (via
Russia), with intent left to the archives.
