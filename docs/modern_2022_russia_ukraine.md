# Modern run — Russia–Ukraine 2022: the discrimination test in real time, finance as weapon in full

The framework's modern apotheosis. The 2022 invasion lets us run the same four tests on live,
high-frequency data that we ran on Fraktur OCR — and both edges of the argument show up cleanly:
the **discrimination test** (what the great markets priced) *and* the **state-wielded weapon**
(what finance was used to do). It is the direct descendant of the Ruhr/1941-freeze/Suez lineage,
now at superpower-sanctions scale.

Charted series are pulled reproducibly from **FRED** (daily). Russian-side figures are from the
contemporary record, cited and flagged for verification — the same discipline as the OCR figures
elsewhere (here it is *feed-grade until checked against the primary release*).

## 1. The discrimination test — the great markets barely flinched

The largest European land war since 1945, and **Western equity shrugged**:

| Signal (FRED) | Invasion eve (23 Feb) | Crisis extreme | Reading |
|---------------|----------------------:|---------------:|---------|
| **S&P 500** | 4225 | 4385 (25 Feb, **up**) | **Closed UP on invasion day**; above the pre-war level by 29 Mar (4632). The June low (3667) was the **Fed/inflation**, not the war. |
| **VIX** | 31 | **36** (7 Mar) | Elevated but **far below panic** (COVID 82, GFC 80). The war scarcely registered as *systemic* risk. |
| **Brent crude** | $99 | **$133** (8 Mar, +34%) | The transmission channel: the market priced **energy**, narrowly — not a general war. |
| **10y UST** | 1.99% | 3.49% (rose) | **No sustained safe-haven bid**; the Fed dominated Treasuries. |
| **Broad dollar** | 114.7 | 121.7 | A modest, durable **flight-to-quality** to the dollar — the one clean safe-haven signal. |

Chart: `war_premia/results/modern_2022_discrimination.svg` — S&P vs Brent indexed to the invasion
eve. Equity roughly flat-to-recovering; oil spikes. **That divergence *is* the discrimination
finding**: the market did not price a general/systemic war for the West; it priced a *commodity
shock* through the energy channel.

This is the **Falklands pattern at scale** (a localized-in-impact war the great markets discount)
— and it maps onto the pre-1914 result exactly: the market prices *systemic/general* war risk,
not war-as-such. 2022 was catastrophic locally and narrow globally, and the price signals sorted
it correctly in days.

## 2. Which instrument carried the risk — the target's own market

As in 1905 (the *fonds russes*, not the money market), the violence sat where the exposure was —
**on Russia**, not on Western equity:

- The **ruble** fell from ~80 to ~**135/USD** (7 Mar 2022) before capital controls + a 20% policy
  rate + "gas-for-rubles" forced a rebound to **pre-war levels by ~June** *[VERIFY vs CBR/market
  data]*.
- The **Moscow Exchange (MOEX) closed for equities ~25 Feb–24 Mar 2022** — roughly a month — the
  modern echo of a bourse suspending trading in a panic *[VERIFY]*.
- Russia entered its **first foreign-currency sovereign default since 1918** in **June 2022**
  *[VERIFY vs rating-agency/press record]*.

The great markets discriminated; the belligerent's own market took the hit. Same lesson,
opposite century.

## 3. Exposure vs. constraint — finance as the weapon (state, coercive edge)

2022 is the cleanest modern case of the **coercive edge** in the "three faces" taxonomy — finance
wielded *by states, offensively*:

- The **G7/EU froze ~$300 billion of Russian central-bank reserves** — immobilizing roughly half
  the war chest Russia had built precisely to sanction-proof itself *[VERIFY vs official
  statements]*.
- **Major Russian banks were expelled from SWIFT**; a wave of corporate exit and secondary-sanction
  pressure followed.

This is the direct lineage of **Ruhr 1923 → the 1941 asset freeze → Suez 1956 → 2022** — the
negative/coercive edge of face #3 (state-wielded finance). Note the honesty rule still applies: the
*effect* (severe damage to the Russian economy) is documented; the *decisiveness* (did it change
the war's course?) is contested and should not be overclaimed — the reserve freeze squeezed without,
by itself, halting the invasion.

## 4. Press triangulation — the modern equivalent

The contemporary financial press named the drivers in real time (sanctions, energy, the reserve
freeze) exactly as *Le Temps* and Lansburgh did — the difference is only frequency and access, not
method. A full write-up would quote the FT/Bloomberg/*Economist* "what the market is pricing" copy
against the price series, the same cause-vs-cover check used throughout.

## Why it matters for the book

- It shows the framework **scales from Fraktur OCR to real-time FRED** without changing the four
  tests — the strongest possible evidence that the method is about *structure*, not a period.
- It supplies a **live discrimination result**: even a war this large was priced by the West as a
  *commodity shock*, not a systemic threat — the pre-1914 "general-war-only" finding, replayed.
- It anchors the **finance-as-weapon** extension (the face Kirshner's dove frame does not contain)
  in an unambiguous modern case, so the taxonomy is not a period curiosity.

## Reproduce

```bash
for ID in SP500 VIXCLS DCOILBRENTEU DGS10 DTWEXBGS; do
  curl -sS "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$ID&cosd=2022-01-03&coed=2022-06-30" -o fred_$ID.csv
done
# invasion: 24 Feb 2022. Index S&P and Brent to the 23 Feb eve to see the divergence.
```

*Caveats: charted series are FRED daily (reproducible). Russian-side figures (ruble low, MOEX
closure dates, reserve-freeze size, default date) are from the contemporary record and flagged
[VERIFY] against primary/official sources before publication. The June equity low was Fed-driven,
not the war — do not attribute it to Ukraine.*
