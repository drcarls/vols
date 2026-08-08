# Prototype run — Munich 1938, the interwar Agadir

A proof-of-concept that the framework travels forward twenty-seven years, on the exact
**Le Temps / Gallica** pipeline we built for 1905–14. Munich is the interwar's canonical
"cried wolf" crisis — and it sits on Kirshner's home turf (appeasement), so pricing it is
the sharpest way to show what his argument looks like when you actually *measure* it.

## The full Sept–Oct arc (upgraded from the two-point sketch)

Rather than two snapshots, the run now brackets the whole crisis: twelve dated *Bulletin
financier* reports pulled from Gallica, of which four carry a datable market-tone verdict.
The arc has the textbook cried-wolf shape — **build → hope → relief rally → settle** — with
the finance column naming the war-or-peace news each time.

| Date | Phase | Driver | Market tone (Le Temps) |
|------|-------|--------|------------------------|
| **17 Sep 1938** | build | Chamberlain's abrupt return from Berchtesgaden; Henlein's proclamation | *"déception évidente"* — the talks had *"fait apparaître des difficultés sérieuses"* |
| **28 Sep 1938** | trough / turn | Hitler's Sportpalast speech (27 Sep), parsed overnight | *"plus calme, quoique très irrégulière"* — the speech *"ne contenait rien d'irréparable,"* leaving hope of *"une solution pacifique du problème des Sudètes"* |
| **30 Sep 1938** | **relief rally** | Munich Agreement, signed in the early hours of 30 Sep | *"a manifesté avec éclat un optimisme"* never *"complètement abandonné"*; the **franc rallied** on the accord |
| **8 Oct 1938** | settle | post-Munich calm; awaiting Daladier's financial measures | *"séance calme… la plupart des valeurs ont légèrement fléchi,"* the market *"se conformant aux recommandations de M. Daladier"* |

- **The one quantitative anchor** is the 30 September exchange move: the franc firmed on the
  relief — the pound easing from **178.90 → 178.51 fr** and the dollar from **38.90 → 37.55 fr**
  in the day's *Changes* table *[OCR — verify against the page image]*. Everything else in the
  arc is the qualitative report, not yet a price series.

Chart: `war_premia/results/munich_1938_arc.svg` (a schematic of the reported daily tone —
build, turn, relief, settle — explicitly *not* a price line). Data:
`war_premia/data/munich_1938_arc.csv`.

## Why the arc matters (beyond the two-point version)

The two snapshots showed a scare and a relief rally. The **arc** shows the market *working the
news day by day*: it fell on the Berchtesgaden breakdown (17 Sep), found its floor by reading
Hitler's speech as leaving a door open (28 Sep), broke sharply higher the moment the Agreement
was signed (30 Sep), and settled back into ordinary business within a week (8 Oct). That is the
same anatomy as **Agadir 1911** (the 4 Nov relief: *"la cote retrouve toute sa fermeté"*),
replayed with far cleaner, better-dated interwar data — the press naming the crisis at every
step. The framework — press-attributed price signal + the cried-wolf structure — travels cleanly
into the interwar.

**Why it matters against Kirshner.** Munich is his thesis-case (financial caution →
appeasement) but his empirics are France/Japan, not the British/French *markets*, and his
evidence is stated *preference*, not *priced* risk. This run supplies the **price counterpart he
asserts but never measures**: the 17 Sep slide and the 30 Sep relief rally *are* the financial
community's war-aversion, made quantitative and dated. A full study would add the London and
(post-Anschluss) German markets, a quantified rente/equity series rather than the text report,
and the *Economist*/FT alongside Le Temps — but the proof of concept holds.

*Caveats: OCR (verify against the page image); this is the qualitative market report plus a
single-day FX anchor, not yet a continuous price series; the 22/24/27 Sep and 2/15 Oct issues
did not surface a datable "La Bourse a…" report opening on the finance page and are omitted
rather than guessed at.*

## Reproduce

```bash
# Le Temps Bulletin financier across the Munich arc (finance section ~p5-7):
UA='Mozilla/5.0 (Windows NT 10.0) Chrome/120.0 Safari/537.36'
for D in 19380917 19380928 19380930 19381008; do
  ARK=$(curl -sS -A "$UA" -o /dev/null -w '%{redirect_url}' \
    "https://gallica.bnf.fr/ark:/12148/cb34431794k/date$D" | grep -oE 'bpt6k[0-9a-z]+')
  for P in 5 6 7; do
    curl -sS -A "$UA" "https://gallica.bnf.fr/RequestDigitalElement?O=ark:/12148/$ARK&E=ALTO&Deb=$P" \
      | grep -oE 'CONTENT="[^"]*"' | sed 's/CONTENT=//' | tr '\n' ' '
  done
done
```
