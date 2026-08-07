# Lansburgh on the Berlin private discount — the term spread, at the quarter-end

Two 1912 *Die Bank* articles by Alfred Lansburgh on the Berlin private-discount market.
They bear directly on the spot-versus-to-arrive work: Lansburgh describes, from inside
the Berlin bill market, the *same* thing we measured off the *Chronicle* — a term
spread in short bills that the market's single quotation normally hides and that
fractures at the **quarter-end settlements**, intensifying "for the past year" (i.e.
from ~1911). He also opens with an explicit warning against **averaging** that is, in
effect, the methodological lesson of our single-snapshot-vs-weekly reversal.

Provenance: Zenodo 5115892 (CC-BY-4.0); Lansburgh d. 1937 → PD 2008. Plain-text, not
page images: **verify every figure against the original before publication.**

*(Bibliographic bonus: article B refers to article A as appearing "im **Aprilheft** der
Bank" — the April **issue** — independently confirming* Die Bank *was a **monthly**.)*

## A. "Der Berliner Privatdiskont" (April 1912 issue, Bd 1, 322–328)

The single Berlin private-discount quotation broke down for the first time in the
Bourse's history — at a quarter-end.

- **The mechanism.** The Berlin *Privatdiskont* is fixed not officially by the
  *Börsenvorstand* but by a private broker firm with the largest discount houses, as a
  **single** notation (*Einheitssatz*) covering all bills from 56 to 90 days. It had
  become "ever harder to bring the discounters under one hat," because they wanted a
  different rate for **short bills (*Schnittwechsel*, 56–70 days)** than for **long
  bills (>70–90 days)**.
- **25 March 1912 — the break.** *"…am 25. März trat zum ersten Male der Fall ein dass
  eine Einigung überhaupt nicht zu erzielen war. Für Schnittwechsel war keine Nachfrage
  unter 5% da, während lange Wechsel zu 4¾% unterzubringen waren."* — for the first
  time no single quotation could be agreed: **short bills found no demand under 5%,
  while long bills placed at 4¾%.** They let the big discounters privately announce that
  one class traded at 5%, the other at 4¾%. [figures: VERIFY]
- **It is a quarter-end phenomenon, and recent.** *"…es ist ebenso wenig ein Zufall dass
  der Unterschied sich gerade jetzt und zwar wenige Tage vor einem **Quartalstermin**
  zum ersten Male in seiner ganzen Schärfe offenbart hat… [Veränderungen] die **seit
  einem Jahre speziell an den Terminen** zu ganz eigenartigen Verhältnissen geführt
  haben."* — no accident that the divergence showed in full sharpness a few days before
  a **quarter-end settlement**, the product of changes that "**for the past year,
  especially at the settlement dates,**" had produced peculiar conditions. ("For the
  past year" = since ~spring 1911 — the Agadir-era strain.)
- **Consequence.** The Bourse would likely amend §44 of its usances to **note two
  discount rates** instead of the single one — the market itself conceding that the
  single quote had been masking a real spread.

## B. "Privatdiskont und Bankdiskont" (Bd 2, 733–740, later 1912)

On the spread between the market's private discount and the Reichsbank's official
("bank") discount — and, first, on method.

- **The anti-averaging warning (quotable).** *"…gut tut sich jeglicher Berechnung von
  Durchschnitten zu enthalten. Die Durchschnittsrechnung ist hier… nicht am Platze weil
  sie die charakteristischen Höhen und Tiefen hinter einer nichtssagenden mittleren
  Linie verschwinden lässt."* — one does well to abstain from any averaging; it makes
  the characteristic highs and lows vanish behind a meaningless mean line. He is explicit
  that this is *regime* contamination: at month-, quarter-, and semester-end the spread
  "shrinks or vanishes entirely," not because the causes changed but because part of
  them is switched off — so *"wer die Ursachen ermitteln will der darf naturgemäss nur
  solche Perioden in Rücksicht ziehen wo sie existent sind"* (study only the periods
  where the causes are present). This is the *Termin*/non-*Termin* regime split — a
  contemporary statement of exactly why our single Oct-1 snapshot misled and why the
  weekly, un-averaged panel was the right instrument.
- **Germany's spread was structurally the widest.** *"…am Berliner Geldmarkt [muss] der
  Privatdiskont normalerweise tief unter dem Bankdiskont notieren, tiefer als an
  irgendeinem anderen der grossen europäischen Geldmärkte."* For most of the year the
  private rate runs **>1% below** the bank rate. Citing the literature (Schaer-Reccius,
  1901–1910 averages): Germany **≈1%** vs **England 0.60%**, **France 0.43%** [VERIFY] —
  German money-market spreads over the official rate were more than double the other
  centres', even with the spread-compressing *Termine* included.
- **Why: the bill material is bank acceptances.** Unlike England/France, the German
  discount market's eligible paper "**fast ausschliesslich aus Bank-Akzepten**" —
  *"Privatdiskonten und Bank-Akzepte sind hier geradezu Synonyma."* (Ties back to the
  autumn-1911 point that German banks depended on placing acceptances abroad, above all
  in the French market.)

## Bearing on Chapter III and the spot-vs-to-arrive finding

1. **It confirms the spread is real, structural, and quarter-end-locked — from inside
   Berlin.** Lansburgh independently documents that the Berlin bill market carried a term
   spread its single quotation hid, that the spread "reveals itself at the quarter-end
   *Termine*," and that this sharpened "for the past year" (~1911). That is our weekly
   result in his own words: the forward/term gap is a **quarter-end** feature, not an
   Agadir fingerprint — but it *intensified* in the Agadir era.
2. **A caveat on axes (do not conflate).** Lansburgh's spread is **short vs long
   maturity** (*Schnittwechsel* 56–70 d vs long 70–90 d), and on 25 March 1912 it ran
   **short *above* long** (5% vs 4¾%). The *Chronicle*'s "spot vs to-arrive" is a
   **delivery-timing** spread (bills now vs bills to arrive), which ran to-arrive above
   spot. These are related but distinct manifestations of the same thing — the bill
   market's single price fracturing along term/liquidity lines under quarter-end stress
   — and the manuscript should present them as parallel, not identical.
3. **It hands the chapter a contemporary methodological ally.** Lansburgh's refusal to
   average across the *Termine* is precisely why the single Oct-1 snapshot was
   misleading and the weekly panel was right. If the chapter keeps any rate argument, it
   can cite Lansburgh both for the substance (the quarter-end term fracture, German
   dependence on bank acceptances placed in France) and for the method (don't average
   across settlement regimes).

## Reproduce

```bash
curl -L "https://zenodo.org/api/records/5115892/files/Lansburgh.zip/content" -o Lansburgh.zip
unzip Lansburgh.zip
less "Lansburgh/Artikel/Lansburgh Alfred 1912 Der Berliner Privatdiskont 1 322-328.txt"
less "Lansburgh/Artikel/Lansburgh Alfred 1912 Privatdiskont und Bankdiskont 2 733-740.txt"
```

Deposit: Zenodo 5115892 (CC-BY-4.0). Verify all figures against the original *Die Bank*
page images before publication.
