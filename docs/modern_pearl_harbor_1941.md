# Modern run — Pearl Harbor & the 1941 asset freeze: the weapon that provoked, and the surprise that couldn't be priced

Two events, one year, two distinct lessons — and the anchor of the **freeze lineage** (1941 → Suez
1956 → 2022). The **July 1941 asset freeze** is finance-as-weapon in its most consequential form;
**Pearl Harbor** is the framework's limiting case on the *anticipation* side — a genuine surprise,
where there was no war scare to price in advance.

## Part 1 — the freeze (the weapon), 26 July 1941

FDR froze Japanese assets in the US and imposed a de facto oil embargo — the financial strangulation
that historians credit with **cornering Japan toward war**. The US market's reaction:

- **Flat.** 10.34 → 10.36 across the fortnight. The single most consequential act of American
  financial coercion of the century was **invisible in the tape**.

Why it matters: the market **did not price the consequence of its own government's weapon.** The
freeze's damage fell on Japan, not on US assets, and no one connected the embargo to the war it
would provoke five months later. This is the **coercive edge, state-wielded** — but with the
outcome that separates it from Suez: the 1941 freeze *worked* (it strangled Japan) and thereby
**backfired into war**, where the 1956 freeze *worked* and forced a **retreat**. Same weapon,
opposite results — see the lineage below.

## Part 2 — Pearl Harbor (the surprise), 7–8 December 1941

| Moment | Move | Reading |
|--------|-----:|---------|
| **Pre-war drift** (Jul → Dec 1941) | **−10%** | War risk was **already being priced in aggregate** — the market slid from 10.34 to 9.32 through autumn on the European war and the Japan crisis. |
| **Pearl Harbor** (first trading day, 8 Dec) | **−3.8%**; −6.9% by day two | A genuine **surprise attack** — no scare to price in advance — yet the day-one drop was **modest for US entry into a world war**. |
| **Wartime low** (28 Apr 1942) | **−20%** from pre-Pearl | Ground lower through the dark months (Bataan, Singapore, U-boats off the coast), bottoming at the point of maximum Axis advance — and turning *before* Midway. |

Two framework points:

1. **A surprise has no anticipation to measure.** The book's press-triangulation and cried-wolf
   machinery needs a *build-up* — the market pricing a rising probability. Pearl Harbor had none:
   the attack was a discontinuity. So the −3.8% is not a "war premium" building; it is the market
   **repricing instantly** to a fact it could not have discounted. The limiting case that defines
   what the anticipation tests *can* and *cannot* see.
2. **Modest — because half-priced and survivable.** −3.8% for entry into WWII is strikingly
   contained next to Korea's −5.4% for a far smaller war. Two reasons the framework supplies:
   (a) **war risk was already in the price** (the −10% autumn drift), so only the *residual*
   surprise repriced on 8 December; (b) US entry, however catastrophic, was **survivable and
   collectable** — the homeland was not at risk and war production promised an eventual boom, so
   this was priceable, not the Cuba-'62 un-priceable ceiling. The deeper −20% low tracked the
   *military* tide, not the day of the attack.

Chart: `war_premia/results/pearl_harbor_1941.svg`.

## The freeze lineage — 1941 → 1956 → 2022 (the "also 2022" thread)

The three cleanest cases of the **state-wielded coercive freeze**, and they sort by *outcome* —
the taxonomy the book should draw:

| Case | The weapon | Market footprint | Outcome of the squeeze |
|------|-----------|------------------|------------------------|
| **1941** — US freeze of Japanese assets + oil embargo | Strangle an adversary's dollar/oil access | **Invisible** in the US tape (fell on Japan) | **Provoked war** — the corner left Japan choosing between climb-down and attack |
| **1956** — US denies IMF access; sterling run | Withhold reserves/credit from an *ally* | Reserves, not a price series (pegged FX) | **Forced a retreat** — Britain aborted Suez |
| **2022** — G7 freezes ~$300bn of reserves; SWIFT | Immobilize an adversary's war chest | The *target's* market took it (ruble, MOEX, default); the West priced only the **energy channel** | **Punished, did not halt** — the invasion continued |

Three deployments of the same instrument, three outcomes: **provoked (1941), coerced a retreat
(1956), punished without stopping (2022).** The freeze is not one thing — its effect depends on
whether the target has a survivable alternative (Japan didn't; Britain did; Russia chose to absorb
it). That is the disciplined version of "finance is a weapon": *a weapon with contingent effects,
not a lever that always pulls the same way.* Effect documented in all three; **decisiveness varies
and must be argued case by case**, never assumed.

## Where these sit in the book

- **Pearl Harbor** = the *anticipation* boundary: what the cried-wolf/press-triangulation method
  cannot see (a true surprise), and why a modest reaction can coexist with a catastrophic event
  (pre-pricing + survivability).
- **The freeze lineage** = the spine of the finance-as-weapon chapter — 1941/1956/2022 as the
  coercive edge with three different endings, disciplined by the effect-vs-decisiveness rule.

## Reproduce

```bash
curl -sS -A "Mozilla/5.0" \
  "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=-900500000&period2=-872000000&interval=1d"
# freeze 26 Jul 1941; Pearl Harbor 7 Dec 1941 (first trading day 8 Dec).
```

*Caveat: ^GSPC daily index levels; verify crisis-window values and event datings against a second
source before publication. The 1941-freeze → Japan-war causal link is standard historiography
(the oil embargo cornered Japan) but should be cited (e.g. Sagan; Utley) rather than asserted.*
