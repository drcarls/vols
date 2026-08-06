# war_premia

Reproduce and extend **Carls (2005)**, *"Did Politicians Cry 'War' to Financial
Markets Once Too Often? An Examination of War Risk Premia Prior to World War I."*

Rigobon-Sack **identification-by-heteroskedasticity** of war-risk premia in the
weekly city money-market rates of the **Neal-Weidenmeier Gold Standard Database**
(mirrored in [`../neal_weidenmier`](../neal_weidenmier)). For each city rate `x`
and the London 3-month trade bill basis `y`, it regresses Δx on Δy with an
instrument built from the war/non-war regime sign, `w = ±Δy`, so the war-risk
factor is identified without being quantified.

```bash
cd war_premia && pip install -e .
war-premia reproduce     # Tables 3-7 on the mirrored NW short rates
war-premia july1914      # the extension + why the July-1914 premium isn't estimable
```

## Reproduction

`results/reproduction_tables.txt` is the committed output. The full sub-sample
(the paper's Table 7, the best-powered) matches closely:

| city (open-market) | paper | this repo |
|---|---|---|
| Paris | 0.11 (t 3.20) | **0.11 (t 3.46)** |
| Amsterdam | 0.09 | **0.09** |
| Copenhagen | 0.14 | **0.14** |
| Berlin | 0.38 (t 6.58) | 0.35 (t 6.40) |
| Vienna | 0.17 | 0.13 |
| Brussels | 0.21 | 0.18 |
| Geneva | 0.07 | 0.09 |
| New York | −0.23 | **−0.33** (safe haven) |

First Moroccan reproduces too (Geneva 0.30 = 0.30, Copenhagen 0.14 = 0.14, Paris
0.51 vs 0.46). The small-n crises (Second Moroccan n=22, Balkans) are noisy and
sensitive to the exact war-week→week mapping and window endpoints — the
imprecision the paper itself flags. Differences trace to (a) the First Moroccan
window is inferred (the paper gives n=62, not endpoints) and (b) event→Saturday
mapping conventions.

## The July-1914 extension — and why it can't be a Rigobon-Sack premium

The estimator needs a **war-week variance regime**. July 1914 denies it one on
*both* assets, because the markets closed exactly when war came:

- **Short-term rates end 1914-06-27**, the eve of Sarajevo (28 June). Every
  July-1914 war event is after the data — one boundary week, no crisis response.
- **Long-term bonds are quoted ~weekly through 1914-07-31** (the last LSE trading
  day), then a **5-day *closure* gap** to the 5 Aug nominal quote — the real gap is
  the closure, not a data gap. The heteroskedasticity-**identified** premium is
  still unestimable (the war-week variance regime is truncated by the closure, and
  post-closure quotes are nominal), but that is the *only* thing the closure denies.

This is the central empirical fact: the event that would have revealed whether
markets had finally stopped "crying wolf" is the one where the markets stopped
trading. But what they did *before* stopping is right there in the weekly data.

> **Correction (parse bug).** An earlier version read only the ~300 Excel-serial
> date cells and so mis-saw the bonds as "monthly, with a 63-day Jun-3→Aug-5 gap."
> The RAW date column is mostly **text** (`d/m/yyyy`); once parsed, the series is
> weekly through the closure, and the pre-closure war repricing is observable.

### The bond cross-section is uninterpretable (a withdrawn result)

An earlier version reported a June-3 → Aug-5 bond "cross-section" (Consols −0.3%,
French −1.8%, …) and read it as a trivially small, Ferguson-flat move. **That is
withdrawn.** Auditing the raw column (`war-premia july1914`, `bond_quote_audit`):

- The quotes are **prices** (points of par), not yields.
- The **June-3 baseline is ex-dividend** — Consols 76.75 (Jun 2) → 75.0 `xd`
  (Jun 3), a mechanical coupon drop, not a market move (same for the Russian 1822).
- The **post-closure quotes are not genuine trades**: Russian and Austrian bonds
  *rise* Aug→Sep 1914 (Austrian Gold 84→89, Russian 1822 120→125) — impossible for
  belligerent debt at war. They are nominal quotes carried through the closure.

Comparing a stale August quote to an ex-dividend June baseline manufactured the
spurious ~2%. The cross-section can't be interpreted at all.

**What *is* observable — the pre-closure war repricing** (`war-premia july1914`,
`war_week_bond_decline`, weekly text vintage, 15 Jun → 31 Jul, clean = to last
unflagged quote): the **whole European sovereign complex fell ~2.5–6%** in the
final trading weeks —

| sovereign | 15 Jun → 31 Jul (clean) | note |
|---|---|---|
| UK Consols 3% | **−5.8%** | 75.1 (24 Jul) → 70.5 on the last day |
| German Imperial 3% | −5.2% | |
| Prussian Consols 3.5% | −5.7% | |
| Austrian Gold 4% | −6.0% | |
| Russian New 4% | −4.5% (to 24 Jul) | 31 Jul 79.0 footnoted, further down |
| French 3% rente (Paris) | −2.5% | |
| Russian 1822 5% | −2.5% | thin, pegged at 121 then 118 |

With the money market seizing the same week (Bank of England 3 → 4 → 8 → 10%),
that is a market **routing as it shut**. So the reaction is *not* unobservable —
it is broad and sizable in the weekly data. What the closure denies is only the
*identified* premium (no post-closure variance regime); the post-closure quotes
themselves are nominal (see the audit above). Ex-dividend/footnote discipline is
applied: the clean decline stops at the last unflagged quote, so neither a coupon
(Jun-3 xd) nor the footnoted 31 Jul Russian print inflates it.

> **Read the level, not the ordering — flight to liquidity, not from British
> risk.** That **UK Consols fell as hard as the belligerents** (−5.8%, second only
> to Austria) is the tell: Consols were the *safest* sovereign credit and the
> *most liquid* asset on earth, so in a cash scramble they were sold first —
> because they had a bid. The cross-section ranks **marketability, not relative
> war risk**; "Consols fell more than the rente" does **not** mean Britain was the
> bigger war risk. Only the *aggregate* fall (everything down together) is a war
> signal; the ordering is a liquidity artifact. This is the July-1914 counterpart
> of the closure itself — the market's plumbing, not its risk assessment, drove
> the cross-section.

### The money market through July–August 1914 (descriptive)

The NW short rates end 1914-06-27; `data/july_aug_1914_money.csv` fills the war
weeks from the **Commercial and Financial Chronicle** (public domain, via FRASER /
Wayback), each figure carrying its OCR source quote. It is descriptive, not
identified. Two findings (see `results/july_aug_1914_money.md`):

- **No anticipation.** London 3-month bills drift ~1.9%→2.4% through July — an
  ordinary summer firming, no war being priced — then the market froze (LSE closed
  31 July). Ferguson again, in the short rates.
- **A convulsion, then the data goes dark.** When war came the Bank of England
  rate went **3 → 4 → 8 → 10%** in a week and NY call money to 7%. The bond market
  was routing too — the European sovereign complex fell ~2.5–6% in the final
  trading weeks (see the pre-closure decline above) — before trading stopped and
  the post-closure quotes went nominal. The *identified war premium* is what's
  unobservable (no post-closure variance regime); the reaction itself is not.

### NYC bonds, 1914: the closure and the reopening

`data/nyc_1914_bonds.csv` + `results/nyc_1914_bonds.md` (sourced to the *Chronicle*,
via FRASER/Wayback) cover the New York case, which ran on a **different mechanism**.
The US was a *debtor*: at the outbreak Europe dumped American securities for gold
($41.85M engaged in the first week), so the NYSE closed 31 July to stop the selling
and the gold drain — the US defending its gold, not a belligerent its debt. The
Aug–Nov closure quotes are minimum-price floors (excluded). The genuine, observable
reaction is the **28 Nov 1914 bond reopening**, and it was **firm**: trading resumed
"without a hitch," high grades near par — US Steel 5s 99¾–100¼ (the week's most
active), US Rubber 6s above par, short high grades ~99–100¼. NYC bonds did not
crash; the crash was pre-empted by closure, and US credit was, if anything, a war
beneficiary.

## St. Petersburg (Russia) — a series the original couldn't include

The paper reported the Russian market rate as unavailable. The NW short-rate file
carries a **St. Petersburg *bank* rate** (the Russian State Bank discount rate),
populated weekly across 1904–1914 — so Russia can enter the estimation for the
first time. `war-premia russia` reports it.

The finding is itself informative: the St. Petersburg bank-rate premium is ≈ 0,
against Berlin 0.21 and Paris 0.05 (full-sample, *bank* rates). Russia's rate was
**administered and sticky** — the State Bank held it through crises where the
Reichsbank moved — so it carries almost no war-risk signal. That is a real
limitation of the Russian series, not evidence that Russia bore no war risk; only
its market (open-market) rate would show it, and that is the series NW lacks after
1900.

### The Kokovtsov event test — a test the paper couldn't run (`war-premia kokovtsov`)

A sharp, datable probe of that limitation. **Vladimir Kokovtsov** — Russia's
finance minister and premier, who anchored Russian credit in Paris — was
dismissed in late Jan 1914 (O.S.); his cabinet ended **12 Feb 1914 (N.S.)**. If
any Russian asset should price political risk, it is this. The recovered data
runs it two ways (`results/kokovtsov_1914.md`):

- **Administered short rate — silent by construction.** The bank rate did not
  move: 5.5% for a **73-week plateau** (2 Nov 1912 → 28 Mar 1914) straddling the
  dismissal; the next change was a *cut* seven weeks later. The open-market rate
  that would carry a signal is the series NW loses after 1900 (ends 20 Oct 1900);
  no ruble exchange series either.
- **Market-priced debt — quoted weekly, and flat across the event.** The bond
  file *does* supply a market-priced Russian series: the **Russian New 4% and
  1822 5%, quoted weekly in London**. Both are flat across 12 Feb 1914 — bracket
  move **+0.0%**, the New 4% holding 89.0 for four straight weeks, against normal
  weekly variation of 0.6%. No repricing.
- **Transmission — France, Russia's banker, did not reprice either.** Paris had
  placed billions of francs of Russian loans with French savers, so a Russian
  credit scare should surface in the **French 3% rente**. It didn't: the rente
  *rose* ~+1.3% across the dismissal (85.95 → 87.10) and held. No contagion.

So it is not a pure data-blindness null: at **weekly** resolution the market
*did* have a chance to reprice Russian debt at Kokovtsov's fall and **did not** —
apt, since his successor Bark kept the same fiscal and Franco-Russian borrowing
policy. It turns the paper's general "Russia unavailable" caveat into a specific,
dated test on a genuine market-priced instrument. (A St Petersburg open-market
rate or ruble quote — *The Economist*'s weekly "Foreign Bourses", paywalled —
would add a Russia-specific read, but the London bonds already answer it.)

## Tests

```bash
python -m pytest -q      # estimator arithmetic + war-week coding, no network
```
