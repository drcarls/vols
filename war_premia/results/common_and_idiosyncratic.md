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

## Testing the trade-exposure channel — done, and it holds (modestly)

**Design.** The blockade channel predicts a neutral more dependent on
**Central-Powers trade** (the trade the British blockade severed) carries a higher
war premium.

I first called this untestable (n≈3, no data). **That was premature.** Expanding the
cross-section to **Italy, Spain and Portugal** (open-market rates NW also carries)
gives eight European neutrals, and the **Correlates of War Bilateral Trade v4.0**
dataset supplies real 1913 trade shares. Run
([`trade_exposure.md`](trade_exposure.md), `war-premia`/`trade_exposure.py`):

- **Within the eight neutrals, the premium rises with Central-Powers trade share:
  r = +0.64 (t≈2.0), %Germany r = +0.53** — the right sign, moderate-to-strong.
  Denmark (33% Central, β 0.14) and Sweden anchor the top, Portugal (16%, β 0.01)
  the bottom. Central-Powers share beats all-belligerent share, as "the trade the
  blockade cut" should.
- **Suggestive, not conclusive:** n = 8, three of them the Scandinavian
  monetary-union bloc, so t≈2 is borderline; adding belligerents (idiosyncratic
  premia) washes it out.
- **The US is the informative break:** high belligerent trade (44.9%) but a
  *negative* premium — a war **supplier/beneficiary**, not a disrupted neutral. So
  exposure is **disruptive dependence**, not trade volume — which refines the
  hypothesis rather than denying it.

So the trade-exposure channel is *visible* in the neutrals' premia (r ≈ 0.64, the
predicted sign) — but a robustness check shows it is **not confirmed**: it holds on
the London-basis premium and the common-factor loading (r ≈ 0.41) yet **vanishes on
the Swiss basis** (partly mechanical — Geneva is itself the top-Central-trade
neutral). Suggestive, sourced, but measure-dependent and underpowered (n = 8). A real
confirmation needs the direct instrument (**marine war-risk insurance / freight
rates**) and a larger cross-section — see [`trade_exposure.md`](trade_exposure.md).

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
