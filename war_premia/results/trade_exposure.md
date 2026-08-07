# Testing the blockade / trade-exposure channel — and it holds (modestly)

Does the neutral war-risk premium scale with **trade dependence on the Central
Powers** — the trade the British blockade actually severed? Earlier I said this
couldn't be tested (n≈3, no data). That was premature: expanding the cross-section
to **Italy, Spain and Portugal** (open-market rates NW also carries) gives eight
European neutrals, and the **Correlates of War Bilateral Trade v4.0** dataset
supplies real 1913 trade shares. Run it (`trade_exposure.py`):

## Data

- **y** = full-sample Rigobon-Sack money-market premium (vs the London basis), from
  the Neal-Weidenmier short rates.
- **x** = 1913 trade with Germany / with the Central Powers (Germany+Austria) / with
  all belligerents (DE, AT, UK, FR, RU), as a share of each country's total trade —
  extracted from the COW dyadic file (`data/cow_trade_shares_1913.csv`).

| country | premium β | %Germany | %Central | %Bellig |
|---|---|---|---|---|
| Denmark | 0.14 | 32.1 | 33.1 | 75.8 |
| Sweden | 0.12 | 29.2 | 29.2 | 67.1 |
| Italy | 0.12 | 16.1 | 23.9 | 49.4 |
| Netherlands | 0.09 | 19.1 | 19.1 | 32.7 |
| Switzerland | 0.09 | 27.6 | 33.4 | 63.2 |
| Spain | 0.09 | 18.6 | 19.4 | 65.6 |
| Norway | 0.08 | 26.2 | 26.2 | 61.8 |
| Portugal | 0.01 | 14.9 | 16.4 | 48.8 |
| *USA* | *−0.33* | *13.8* | *14.8* | *44.9* |

## Result — the right sign, moderate, marginally significant

**Within the eight European neutrals:**

| x | Pearson r | Spearman | t (df 6) |
|---|---|---|---|
| **% trade with Central Powers** | **+0.64** | +0.48 | **2.02** |
| % trade with Germany | +0.53 | +0.52 | 1.55 |
| % trade with all belligerents | +0.38 | +0.43 | 1.00 |

Neutrals more dependent on **Central-Powers** trade carried **higher** war premia —
the direction the blockade channel predicts, at a moderate-to-strong r ≈ 0.6.
Denmark (32% Central, β 0.14) and Sweden (29%, 0.12) anchor the high end; Portugal
(16%, β 0.01) the low. Central-Powers share beats all-belligerent share, exactly as
"the trade the blockade cut" should.

**But it is suggestive, not conclusive.** n = 8, and three of the eight are the
Scandinavian monetary-union bloc (so effective n is smaller); t = 2.0 on the best
variable is borderline. Adding the belligerents washes it out (their premia are
idiosyncratic, driven by *being* belligerents — r falls to 0.26), as it should.

## The US is the informative break

The US has **high belligerent trade (44.9%)** yet a **negative** premium. High trade
*volume* with the belligerents did not raise its premium, because the US was a war
**supplier and creditor — a beneficiary, not a disrupted neutral** (gold flowed in;
it is the R²≈0 outlier on the common factor). So the channel is not trade volume per
se but **disruptive dependence**: being cut off from, or fought over, versus selling
into the war. Central-Powers dependence captures the first; the US embodies the
second. That refines your hypothesis rather than contradicting it.

## Verdict

The blockade/trade-exposure channel is **supported in sign and magnitude** among the
European neutrals (premium rises with Central-Powers trade share, r ≈ 0.64) — a real,
sourced result, not a hand-wave — but it is **underpowered** (n = 8, Scandinavian
bloc) and only marginally significant. To harden it you would want the direct
instrument (marine war-risk insurance / freight rates) and a larger cross-section;
but on the data obtainable, the neutrals' premia do track their exposure to the
trade a European war would sever, and the US proves the exposure is about
disruption, not volume.

## Sources

- Trade: **Correlates of War Bilateral Trade v4.0** — Barbieri, Katherine, Omar M. G.
  Keshk, and Brian Pollins (2009), "Trading Data," *Conflict Management and Peace
  Science* 26(5): 471–491. Dyadic file, 1913; shares in `data/cow_trade_shares_1913.csv`.
- Premia: Neal-Weidenmier short rates via `war_premia`.

## Reproduce

```bash
cd war_premia && python trade_exposure.py
```
