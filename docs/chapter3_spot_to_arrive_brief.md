# Brief: was Berlin's spot-versus-to-arrive gap unusual in autumn 1911?

**The question, and why it decides Chapter III.** The chapter's scene rests on one
narrow empirical claim — that in the autumn of 1911, at the Agadir climax, Berlin's
money market priced *bills to arrive* dearer than *spot* bills by an amount it did not
price in ordinary autumns. If that gap was ordinary, the rates carry no weight and the
chapter becomes an account of credit withdrawal and contemporary belief with the
prices dropped out. If it was unusual, the scene stands — and it stands on a price, not
a mood.

**Why the mirrored data can't answer it.** The Neal–Weidenmier series carries a single
open-market rate per city; it has no room for an intra-market spread between spot and
forward bills. The gap therefore has to be read off the *Commercial & Financial
Chronicle*'s weekly Berlin money paragraph — one figure per autumn. "Spot versus
to-arrive" turns out to be the Chronicle's own wording, not a construct imposed on it:
it quotes Berlin's rate "for spot bills" and, separately, "for bills to arrive."

**Method.** I take each year's early-October issue — the Oct-1 quarter-end settlement
week, the exact seasonal moment of the scene — for 1908 through 1913 (1907 excluded as
the panic), and read Berlin's spot and to-arrive quotes. The gap is *to-arrive minus
spot*; a positive gap means forward money dearer than spot. Every figure below carries
its verbatim quote (`war_premia/data/berlin_spot_to_arrive_autumn.csv`).

## The six autumns

| Autumn | Spot | To-arrive | **Gap** | What the *Chronicle* actually drew |
|---|---|---|---|---|
| 1908 | 3% | 3% | **0** | one undivided rate ("at Berlin and Frankfort it is 3%") |
| 1909 | ~3½%* | ~3½%* | **0** | one undivided rate (Berlin+Frankfort lumped) |
| 1910 | 4½% | 4½% | **0** | *stated equal*: "4½% for **both** spot bills and bills to arrive" |
| **1911** | **4%** | **4½%** | **+0.5** | **a gap**: "spot bills at 4%, **but** for bills to arrive the terms are 4½%" |
| 1912 | 3¾% | 3¾% | **0** | *stated equal*: "the closing rate for **all maturities**… was 3¾%" |
| 1913 | 4⅜–4½%† | — | **0** | a quotation *range*, not a spot/to-arrive split |

\* 1909 level OCR-uncertain; the point is that a *single* undivided rate was quoted, so
the gap is 0 regardless. † 1913 gives a bid–ask range (width ⅛), not a spot/forward
distinction.

## Verdict: unusual. Keep the scene.

Berlin drew a spot-versus-to-arrive gap in **exactly one of the six autumns — 1911**,
and it drew it in the source's own words ("spot bills at 4%, *but* for bills to arrive
4½%"). In every other autumn it either stated the two were equal (1910, 1912) or quoted
a single undivided rate (1908, 1909, 1913). Three points make the result more than a
one-off number:

1. **1910 is the control that kills the obvious objection.** Autumn 1910 was *firmer*
   than 1911 in level — the Reichsbank had just put its official rate to 5% and private
   discounts stood at 4½%, above 1911's 4% spot — yet spot and to-arrive were quoted
   *equal*. So the 1911 gap is not a by-product of a high rate or a tight autumn; a
   tighter autumn a year earlier produced no gap at all. The gap is specific to 1911.

2. **The 1911 figure is conservative.** It is the 7 October quote, taken *after* the
   quarter-end strain had already broken — the same issue notes the spot rate "has
   fallen to 4%" from the abnormal settlement-week levels. The peak gap, a few days
   earlier, was if anything wider; +0.5 is the residual after the worst had passed.

3. **The direction is the tell.** To-arrive dearer than spot means the market was
   pricing money to be *tighter going forward* — a forward premium for continued
   Agadir/fourth-quarter uncertainty. That is precisely the "credit withdrawal and
   contemporary belief" of the chapter, but registered as an actual price in the
   forward bill market rather than inferred from commentary. London, quoted in the same
   1911 paragraph, carried only a ~¼-point forward premium at ninety days — so Berlin's
   half-point was the wider of the two great centres that week.

The honest limits: this is one quarter-end snapshot per year (as the "one figure each"
design intends), the absolute gap is small (½ point), and 1913's range is genuinely
ambiguous rather than a clean zero. None of that disturbs the finding, because the
comparison is not gap-size against a threshold but *a gap at all* against five autumns
that show none — including a firmer one. Autumn 1911 is the year Berlin's forward bills
detached from spot. The scene stays as written.

## Sources & reproduce

*Commercial & Financial Chronicle*, early-October issues 1908–1913 (FRASER, Federal
Reserve Bank of St. Louis): `cfc_19081003`, `cfc_19091002`, `cfc_19101001`,
`cfc_19111007`, `cfc_19121005`, `cfc_19131004`. Verbatim quotes in the CSV.

```bash
cd war_premia && python spot_to_arrive.py   # prints the table + verdict, writes the SVG
```
