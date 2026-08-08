# Continental press on the war-scare money markets: Paris (Agadir) and Vienna (Balkans)

Primary-source money-market commentary from the French and Austrian press, to sit
beside the German (Lansburgh / *Die Bank*) evidence. Both are open-access and
machine-readable, pulled here directly:

- **France — *Le Temps*** (daily), via **Gallica** ALTO OCR
  (`RequestDigitalElement?O=ark:/12148/<ark>&E=ALTO&Deb=<page>`; the *Bulletin
  financier* sits on p.5). Same pipeline as this repo's `gallica_le_temps`.
- **Austria — *Neue Freie Presse*** (daily), via **ANNO**
  (`annoshow?text=nfp|<YYYYMMDD>|<page>`; the finance section is ~p.13–17).

**Access caveat on *Der Österreichische Volkswirt*.** It is catalogued on ANNO
(`aid=ovw`) but **no page images or OCR could be retrieved for 1911–1912** (image-only
or sparse holdings there). *Der Österreichische Volkswirt*'s analytical text exists on
**HathiTrust** (catalog 102712766) but that host is access-restricted from here. So the
working Austrian daily source is the *Neue Freie Presse*; ÖVW would need a HathiTrust
session. **Figures below are Fraktur/French OCR — verify against page images.**

## France — the Paris market through the Agadir crisis (*Le Temps*, 1911)

The daily *Bulletin financier* prices the crisis in its own words, and names the cause.

- **Onset — 3 July 1911** (the *Panther* reached Agadir on 1 July):
  > *"Comme il fallait s'y attendre, la nouvelle de l'envoi par l'Allemagne d'une
  > canonnière au Maroc … a déterminé sur notre marché des offres très importantes, à
  > l'ouverture, dans tous les compartiments de la cote."*
  Heavy selling across the whole list on the gunboat news, from day one.

- **Quarter-end climax — 29 Sept 1911** (the eve of the end-September liquidation):
  > *"On ne peut aujourd'hui formuler aucune prévision sur le loyer de l'argent à la
  > liquidation de demain. On croit assez généralement qu'il sera de 5 % environ, mais …
  > ce taux peut varier suivant les nouvelles qui seront reçues demain relativement aux
  > différentes questions politiques en suspens."* — and *"Nos rentes sont lourdes."*
  The cost of money at the settlement ~**5%** [verify], explicitly hostage to the
  political news; French rentes heavy. (Late September also opened the Italo-Turkish
  war over Tripolitania — the "questions politiques en suspens" were Morocco *and*
  Tripoli.)

- **6 Oct 1911:**
  > *"Le marché témoigne d'une très grande indécision. L'incertitude qui règne au sujet
  > de … la marche des négociations relatives au Maroc provoque quelque nervosité."*
  The nervousness is named on the **Morocco negotiations** — the market attributing its
  own unease to the diplomacy, not the reverse.

- **Resolution — 4 Nov 1911** (the Franco-German convention was signed that day):
  > *"Le temps d'arrêt qui s'était manifesté hier dans le mouvement de hausse n'a pas eu
  > de suite aujourd'hui et la cote retrouve toute sa fermeté précédente."*
  The relief rally — the premium unwinding as the crisis settles.

**Reading.** The Agadir war-risk premium is visible in Paris in the **report /
liquidation market** (the *loyer de l'argent*, ~5% at the quarter-end turn) and in heavy
rentes — **not** in the Banque de France official rate, which France, flush with gold,
held at **3%** throughout. That matches our Neal-Weidenmier result (Paris carried the
largest positive deseasonalized bump at the Sept–Oct climax) and answers cause-vs-cover
from the French side: *Le Temps* repeatedly names the political crisis as the driver.

### France as Germany's creditor — closing the loop

Lansburgh's German-side claim was that **French creditors withdrew their balances from
Berlin**, stripping the German banks (see `lansburgh_die_bank_autumn1911.md`). The
French-side footprint:

- **The great Berlin banks in distress, from Paris's Berlin correspondent — 30 Sept 1911
  ("Déclarations rassurantes à Berlin"):**
  > *"Berlin, 29 septembre. Les directeurs des grandes banques de Berlin ont reçu ce
  > matin du ministère des affaires étrangères des assurances optimistes au sujet de la
  > marche des négociations franco-allemandes."*
  The directors of the great Berlin banks sought and got Foreign-Office reassurance on
  29 September — **exactly the episode Lansburgh describes from the German side** (Deutsche
  Bank pressing the *Auswärtiges Amt* for a calming declaration at end-September, driven
  by the deposit/withdrawal drain). Two independent sources, the same event.
- The Paris market's own tightening (the ~5% *loyer de l'argent*, the 3 July selloff)
  is the near-side of the same flow: French money pulling home from Berlin as the crisis
  peaked.

**The quantitative capstone — the mark falls to the gold point, then recovers.** The
direct market footprint of the repatriation is the Paris quotation of the mark (Le Temps
*Changes* table, francs per 100 marks; par ≈ 123.46, lower gold point ≈ 122.8). It traces
the crisis exactly (`war_premia/data/mark_franc_agadir_1911.csv`, raw OCR kept for
verification):

| Date | Mark (FF/100) | |
|---|---|---|
| 5 Aug 1911 | 123.69 | at par |
| 2 Sep | 123.50 | at par |
| 16 Sep | 122.75 | **at the lower gold point** |
| 14 Oct | 122.88 | weak |
| 21 Oct | 122.69 | **weakest — at/below the gold point** |
| 11 Nov | 123.13 | recovering (the convention was 4 Nov) |
| 25 Nov | 123.38 | back near par |

The mark slid from par to the **gold-export point** in Paris as Agadir peaked
(Sept–Oct) and recovered to par after the **4 November** Franco-German convention — the
signature of French balances being pulled home from Berlin and the pressure releasing on
resolution. It sat *at* the gold point but was held there: Germany defended (the
Reichsbank rate rise and the rediscount squeeze Lansburgh documents), which fits his boast
that the French balances were repaid *"ohne… Exporte von Gold nach Frankreich."* So three
independent French-side traces — the 3 July selloff, the ~5% *loyer de l'argent*, and the
mark at the gold point — all corroborate the German-side withdrawal story. Chart:
`war_premia/results/mark_franc_agadir_1911.svg`.

*(OCR caveat: the columnar Changes table defeated clean extraction on several dates; the
seven values above parsed cleanly and are kept with their raw OCR, but verify against the
page images.)*

**What could not be closed here (stated plainly):**
- **Raffalovich's *Le Marché financier* is on Gallica only for 1896–1901 and 1910** — the
  **1911–12 volume that would carry the Agadir retrospective is not digitized there**, so
  his analytical account of the French withdrawal could not be pulled.
- *Le Temps*'s **daily** bulletin carries no explicit "nous avons rapatrié nos fonds de
  Berlin" sentence; the withdrawal is documented from the German side and corroborated by
  the Berlin-distress dispatch above. The direct quantitative French footprint — the
  **mark weakening in the Paris exchange** as balances were repatriated — is the natural
  next pull (Le Temps's *Changes* table), and an analytical French statement would sit in
  *L'Économiste français* (Leroy-Beaulieu) rather than the daily.

## Austria — the Vienna market through the Balkan Wars (*Neue Freie Presse*, 1912)

The Vienna question the London-based *Chronicle* couldn't answer (it quoted only a bare
"Vienna 6%"): did Vienna's own market show the war scare? **Yes — sharply.**

- **The Austro-Hungarian Bank tightened step by step as the Balkan war escalated:**
  bank rate **5%** (12 Oct 1912) → **5½%** (26 Oct: *"die Erhöhung des Bankzinsfußes auf
  5½ Prozent"*) → **6%** (30 Nov) [verify]. The private discount rose from ~**4%** to
  **5½%**.
- **Vienna carried a real term structure**, which the *Chronicle*'s single figure
  flattened: 30 Nov 1912 — *"Bankzinsfuß 6 Prozent, Privatdiskont 5½ Prozent, längere
  Sichten 6 bis 6¼ Prozent"* (private discount below the 6% bank rate; longer bills
  dearer). So the earlier "Vienna never splits" was a limit of the *Chronicle*'s
  reporting, not of the Vienna market.
- **The market priced the scare and its easing** — the bourse firmed on news
  *"daß es wegen der schwebenden politischen Fragen nicht zu einem ernsten Zerwürfnis
  unter den Großstaaten kommen werde"* (that the pending political questions would not
  bring a serious rupture among the great powers).
- **Bonus — a third-party check on Berlin.** NFP's Berlin telegram the same day quotes
  *"über Ultimo 6 bis 7"* and *"Privatdiskont lang 5¾, kurz 6"* — the month-end
  short-over-long inversion, corroborating our Berlin spot/to-arrive finding from a
  Vienna source.
- **July 1914:** at the outbreak the Austro-Hungarian Bank rate went to **8%** (1 Aug
  1914: *"die Erhöhung des Bankzinsfußes auf 8 Prozent"*) — Vienna's share of the
  worldwide August spike.

## Bearing

Across all three capitals the pattern is the same and is stated in each market's own
press: the war scares priced through **deposit/report stringency and central-bank
tightening**, explicitly tied to the political news, and unwound on resolution. Paris
(Agadir) and Vienna (Balkans) each show it at home — the Paris *loyer de l'argent* ~5%
and the Austro-Hungarian Bank's 5→6% march — which the London-centred rate series
either muffle (Vienna as one number) or, for Paris, register only as a modest bump.

## Reproduce

```bash
# France — Le Temps issue for a date -> ark -> ALTO OCR of the Bulletin financier (p5)
UA='Mozilla/5.0 (Windows NT 10.0) Chrome/120.0 Safari/537.36'
curl -sS -A "$UA" -o /dev/null -w '%{redirect_url}\n' \
  "https://gallica.bnf.fr/ark:/12148/cb34431794k/date19110930"   # -> bpt6k240625s
curl -sS -A "$UA" "https://gallica.bnf.fr/RequestDigitalElement?O=ark:/12148/bpt6k240625s&E=ALTO&Deb=5"

# Austria — Neue Freie Presse finance page OCR
curl -sS "https://anno.onb.ac.at/cgi-content/annoshow?text=nfp|19121130|17"
```

Sources: *Le Temps* (Gallica/BnF, public domain); *Neue Freie Presse* (ANNO/ÖNB,
public domain). Verify all transcribed figures against the original page images.
