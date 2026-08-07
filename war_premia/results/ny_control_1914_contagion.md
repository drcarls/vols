# The New York control, extended: does its sign flip in July 1914?

The [Agadir check](ny_control_agadir.md) found New York *insulated* from a European
crisis: during Agadir (1911) NY call money never rose above its own seasonal norm and
ran to −2.7 points *below* it. The contagion prediction is the mirror image — when a
European crisis stops staying localized and actually becomes a world war, the control
should **break**: New York should flip from insulated to hit. July 1914 is the test.

**Data note (why this is a different instrument).** The Neal–Weidenmier weekly rates
end **1914-06-27**, the eve of Sarajevo — so the same money-market series *cannot*
reach the July outbreak. This extension therefore reads the outbreak weeks from the
**Commercial & Financial Chronicle** (weekly, public domain; FRASER via the Wayback
Machine), the same source already used for `july_aug_1914_money.csv`. Every figure
carries its OCR quote (see `data/july_aug_1914_gold.csv`). It is descriptive.

## 1. No anticipation — the last four weeks the money-market data covers

Deviation of each city from its own seasonal baseline over **1–27 June 1914** (the
final weeks before the series stops), same method as the Agadir check:

| city | mean deviation, 1–27 Jun 1914 |
|---|---|
| New York | −0.41 |
| **Berlin** | **−1.15** (actually *easy*) |
| Amsterdam | −0.56 |
| Paris | +0.15 |

On the eve of Sarajevo every market sat **at or below** its seasonal norm — Berlin
most of all. The war was **not** priced in advance. This is the paper's own thesis in
miniature: the pre-war crises cried "war" and were faded (Agadir priced risk that
never came, and New York stayed out of even that); July 1914 was priced at *nothing*
until it arrived, then repriced violently.

## 2. The flip — New York call money

| | value | reading |
|---|---|---|
| Agadir 1911, NY peak deviation | **−2.69 pts** | below norm → **insulated** |
| Late-Jul/early-Aug seasonal norm (1909/10/12/13) | 2.09% | a normal quiet summer |
| Outbreak week, NY call money (Chronicle, wk ending 1 Aug 1914) | **2–7%** | — |
| Outbreak **high** vs seasonal norm | **+4.9 pts** | above norm → **hit** |

New York's sign flips — from −2.7 (insulated during a localized crisis) to roughly
+4.9 (slammed in the outbreak week). The mechanism is exactly what distinguishes the
two episodes: Agadir never threatened the London-centred credit system New York was
plugged into, so gold flowed *toward* New York and its rate stayed quiet; July 1914
**froze** that system (Bank of England 3→4→8→10%, the London Stock Exchange shut 31
July, the NYSE shut the same day), and the freeze transmitted straight across the
Atlantic. The flip is the **financial-contagion / liquidity** channel made visible —
the same channel the neutral-premium decomposition kept pointing to.

*(The 7% is the high of a 2–7% within-week range as the NYSE closed, i.e. a liquidity
scramble, not a settled weekly discount rate. That is the right way to read it — the
point is the violence and direction of the move, not a clean level.)*

## 3. Gold corroborates — and ties the two crises together

From the *Chronicle* of 8 August 1914 (`cfc_19140808`; verbatim quotes in
`data/july_aug_1914_gold.csv`):

- **The German war-chest was built from Agadir onward.** *"the Bank of Germany has
  added upwards of $100,000,000 gold to its reserve since the Morocco incident. The
  great bulk of this addition has been accumulated since the recent Balkan war."* The
  Reichsbank treated **Agadir** (the "Morocco incident") as the starting gun for gold
  accumulation — a direct primary-source line connecting the crisis New York shrugged
  off to the one that broke.
- **In the outbreak week gold poured *out* of New York toward London.** The
  *Kronprinzessin Cecilie* turned back mid-Atlantic with **$10,000,000** in gold
  aboard; a **$100,000,000** shipment to London was contemplated "to relieve the
  situation"; the weekly bank statement shows Sub-Treasury operations and gold exports
  draining **$16.8M** from New York banks. Gold flowing *out* under stress is the
  opposite of the safe-haven *inflow* New York enjoyed while insulated — **contagion,
  not refuge.**

## What it establishes

The New York control is not a one-sided artifact ("New York never moves"). It moves
**when, and only when, the crisis reaches the system New York belongs to**: silent
through Agadir, violently repriced in the July-1914 outbreak. That two-sided behavior
is exactly what makes it a usable control — and the gold record both confirms the
July-1914 direction (out of New York, toward London) and, in the Reichsbank's own
accumulation "since the Morocco incident," ties the faded crisis to the real one.

## Reproduce

```bash
cd war_premia && python ny_control_agadir.py   # prints both the Agadir table and the 1914 flip
```

Sources: Neal–Weidenmier Gold Standard Database (weekly short rates, → 1914-06-27);
Commercial & Financial Chronicle, 1 Aug & 8 Aug 1914 issues (FRASER, St. Louis Fed).
