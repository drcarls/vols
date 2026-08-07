# Common risk + idiosyncratic risk — and why even neutrals are exposed

The premia decompose exactly as the pattern suggested: a **common European factor**
that every European market loads on, plus **idiosyncratic** country risk on top,
with the **US as the non-European outlier** (`war-premia factor`).

## The decomposition

Common factor F = the mean of the European money markets' weekly rate changes.
Loading (β) and R² (share of each market that is *common*):

| market | β on F | R² |
|---|---|---|
| **Berlin** | +1.98 | **0.35** |
| Stockholm~ | +0.85 | 0.27 |
| Copenhagen~ | +0.74 | 0.26 |
| Paris | +0.86 | 0.22 |
| Vienna | +0.99 | 0.21 |
| Geneva~ | +0.86 | 0.21 |
| Christiania~ | +0.52 | 0.15 |
| Amsterdam~ | +0.89 | 0.14 |
| **New York~US** | −0.71 | **0.00** |

Every European market — belligerent *and* neutral — loads positively; **Berlin
loads the heaviest and is the most common-driven** (R² 0.35). **The US alone has
R² ≈ 0**: it does not co-move with the European factor. And its war premium is
*negative* — a safe haven, gold flowing *in*. So the US is the clean control that
proves the common factor is specifically **European**.

## So: common European war exposure, or just financial integration?

**Three** channels produce a common European component, and the money-market data
cannot fully separate them:

0. **Contagion of war (fast, expectational) — the deepest one.** The common factor
   is, at root, the market pricing the **probability that a *localized* crisis
   cascades through the alliance system into a *general* war** — Entente vs Triple
   Alliance, the mechanism that turned Sarajevo into a world war. This is why a
   crisis nominally between two powers prices risk *everywhere*, neutrals included:
   localization might fail. It is the natural name for the war-week Rigobon
   component, it explains the **US outlier** better than economics alone (the US
   was outside the *alliance* system, not just the economy), and it *is* the
   paper's own thesis — the pre-war crises priced a general-war probability that
   kept **not** materialising ("crying wolf"); July 1914 it did.
   **But the direct test is weak at weekly resolution:** average European
   cross-market correlation is **0.07 in the 29 war-event weeks vs 0.14 in peace**
   — it does *not* spike (one cross-bloc pair, Paris–Vienna, 0.18 vs 0.11, does; the
   average doesn't). The contagion signal, if present, is small against the
   financial-integration/seasonal noise and buried by weekly resolution. So
   contagion is the right *interpretation* of the war-week premium, not a
   demonstrated correlation result — pinning it needs daily data and event-studies
   around specific escalation/de-escalation news (`war-premia factor`).

1. **Financial integration (mechanical).** European money markets co-moved via
   London and the gold standard (bill-on-London, gold points, shared discount
   cycles) in *all* periods. This is most of the common factor here — note F's
   variance is **not** war-amplified (0.6× in war weeks; the 1907 panic and autumn
   seasonals dominate it). So the *big* common factor is integration, not war.
2. **Common war exposure (fundamental) — your point.** A European war genuinely
   damages European *neutrals* too, so a neutral war-risk premium is economically
   rational, not an artifact:
   - **Blockade & contraband control** — the British blockade throttled neutral
     trade with the Central Powers; neutral cargoes were stopped, seized,
     rationed (the Netherlands' NOT, the Scandinavian agreements).
   - **Shipping & marine war-risk insurance** — freight and hull war-risk premia
     spiked; the North Sea and Baltic became mined war zones. Neutral **Norway
     lost ~half its merchant fleet** in the war — an existential shipping-nation
     risk, and note Christiania (Oslo) is in the exposed bloc.
   - **Financial contagion** — a London freeze (July 1914) hit every connected
     market at once, neutral or not.
   - **Adjacency / drawn-in risk** — the Netherlands and Belgium bordered the
     likely front; Belgium *was* invaded.

   These are the war-week-specific effects the Rigobon β isolates (identified off
   war-week heteroskedasticity) — the smaller premium riding on the big
   integration factor. It is consistent with genuine neutral exposure, but
   **integration-intensifying-under-stress produces the same signature**, so this
   channel cannot be cleanly proven from money-market rates alone.

## Testing the trade-exposure channel — design, and why it can't be done here

**Design.** The blockade channel predicts: a neutral more dependent on
**Central-Powers trade** (the trade the British blockade actually severed) carries a
**higher** war premium. Test = regress each neutral's premium on its ~1913 share of
trade with Germany/Austria, with the US as the low-exposure anchor.

**Why it is not a real test with these premia (three reasons, the first fatal):**
- **n ≈ 3.** There are five European money-market neutrals, but the three
  Scandinavians are one monetary-union bloc (the SMU shows up in their 0.33–0.61
  cross-betas), so ~3 independent points. A 3-point regression is a scatter, not a
  test — no power, whatever the data.
- **Wrong `y`.** The neutral premia are mostly the *common integration factor* (not
  clean country war risk), noisy, and benchmark-dependent. Correlating them with
  trade shares stacks noise on noise.
- **Data.** Clean, comparable, sourced 1913 bilateral trade shares for the five
  neutrals need Mitchell's *International Historical Statistics* / national year-
  books; the open web (searched) gives only qualitative descriptions. Inventing
  approximate shares to run a 3-point regression would violate this repo's sourcing
  discipline **and** produce a meaningless coefficient — so it is not done here.

**What survives (the coarse cut):** the **US** — low dependence on any single
belligerent — has **R² ≈ 0** on the European factor and a *negative* (safe-haven)
premium, while the European neutrals — all highly belligerent-trade-dependent —
carry positive premia. So the trade-exposure prediction holds at the **US-vs-Europe**
level (the outlier result), just not resolvably *within* the five European neutrals.

**The real test needs a different instrument** — one that prices the channel
directly instead of through five bloc-correlated money-market rates:
- **Marine war-risk insurance and freight war-risk rates** (Lloyd's; the shipping
  press) — the direct weekly price of the blockade/shipping channel, independent of
  the noisy money-market premia. Neutral Norway losing ~half its fleet is *this*
  series, quoted contemporaneously.
- Or a **large sovereign-bond cross-section** (n ≈ 20) where trade exposure varies
  independently of belligerent status — giving the power a 3-point neutral scatter
  never can.

## What this settles, and what it doesn't

- **Settles:** risk = common European factor (mostly integration) + idiosyncratic
  country risk (Berlin's excess loading and its Rigobon premium). The **US is
  outside the European system** (R² 0, safe haven) — the decisive non-EU control.
  So "war-risk premium" is largely a *shared European* phenomenon, with Germany
  carrying the distinct extra — exactly the common/idiosyncratic split.
- **Doesn't settle:** whether the neutrals' war-week premium is fundamental war
  exposure (blockade, shipping) or financial contagion. To price the blockade/
  shipping channel *directly* you need the instruments that quote it: **marine
  war-risk insurance and freight war-risk rates** (Lloyd's; the shipping press),
  neutral **exchange rates**, and premia scaled by each neutral's **trade exposure**
  to the belligerents. Those are the natural next data, and they would test your
  hypothesis on its own terms rather than through the money market's common factor.

## Reproduce

```bash
cd war_premia && war-premia factor
```
