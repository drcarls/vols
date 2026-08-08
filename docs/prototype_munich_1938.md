# Prototype run — Munich 1938, the interwar Agadir

A proof-of-concept that the framework travels forward twenty-seven years, on the exact
**Le Temps / Gallica** pipeline we built for 1905–14. Munich is the interwar's canonical
"cried wolf" crisis — and it sits on Kirshner's home turf (appeasement), so pricing it is
the sharpest way to show what his argument looks like when you actually *measure* it.

## What the Paris market priced (Le Temps *Bulletin financier*)

- **Crisis peak — 28 September 1938** (after Hitler's Sportpalast speech, war looking
  imminent):
  > *"La Bourse a été aujourd'hui plus calme, quoique très irrégulière encore. Le discours
  > du Führer allemand a … fait l'objet de tous les commentaires… le marché … a estimé que
  > le seul fait que ce discours ne contenait rien d'irréparable autorisait l'espoir qu'une
  > solution pacifique du problème des Sudètes pourrait encore intervenir."*
  The market is pricing the Sudeten crisis directly — hanging on Hitler's speech, buying
  the *hope* of "une solution pacifique." Textbook press-triangulation: the finance column
  names the war-or-peace news as the driver.

- **The relief rally — 30 Sep – 1 Oct 1938** (the Munich Agreement, signed 30 Sept;
  Chamberlain's "peace for our time"):
  > *"…après **deux jours de hausse importante**… des ordres d'achat … font dépasser les
  > cours … et la clôture s'effectue au plus haut."* (Le Temps, 1 Oct 1938)
  Two days of strong gains on the accord, closing at the high.

## The result

Same structure as **Agadir 1911** (the 4 Nov relief: *"la cote retrouve toute sa
fermeté"*), replayed in 1938: a war scare **priced** as it built, then a **relief rally**
on resolution, with the press naming the crisis both times. The framework — press-attributed
price signal + the cried-wolf structure — travels cleanly into the interwar.

**Why it matters against Kirshner.** Munich is his thesis-case (financial caution →
appeasement) but his empirics are France/Japan, not the British/French *markets*. This run
supplies the **price counterpart he asserts but never measures**: the relief rally *is* the
financial community's war-aversion, made quantitative and dated. A full study would add the
London and (post-Anschluss) German markets, a quantified rente/equity series rather than the
text report, and the *Economist*/FT alongside Le Temps — but the proof of concept holds.

*Caveats: OCR (verify against the page image); this is the qualitative market report, not
yet a price series; a fuller run should bracket the whole Sept–Oct 1938 arc and de-trend.*

## Reproduce

```bash
# Le Temps Bulletin financier around Munich (finance section ~p5):
UA='Mozilla/5.0 (Windows NT 10.0) Chrome/120.0 Safari/537.36'
curl -sS -A "$UA" -o /dev/null -w '%{redirect_url}\n' \
  "https://gallica.bnf.fr/ark:/12148/cb34431794k/date19380928"   # crisis peak
curl -sS -A "$UA" "https://gallica.bnf.fr/RequestDigitalElement?O=ark:/12148/<ARK>&E=ALTO&Deb=5"
```
