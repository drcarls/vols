# Prototype run — the 1871 Thiers indemnity loan: finance as recovery-lever

The 19th-century mirror of the 1906 Russian loan, but with **France as the debtor**. After
Sedan and the Commune, the Frankfurt treaty (10 May 1871) imposed a **5-billion-franc**
indemnity, with German troops to occupy French soil until it was paid. Adolphe Thiers'
government floated a **5% rente** to raise it. The wager of the whole book's "inductive edge
of finance" is here in its purest form: a nation's **credit** — not its army — bought back
its territory.

Runs on the exact **Le Temps / Gallica** pipeline built for 1905–14, verbatim.

## What the market did (Le Temps, late June – early July 1871)

The first loan (2 billion fr nominal, opened 27 June 1871) was **massively oversubscribed in
a single day**:

- **30 June 1871:** *"les merveilleux résultats de l'emprunt. Le montant des souscriptions
  réalisées est encore plus considérable que nous ne l'avions annoncé… 4 milliards 500
  millions… Paris… y figure pour plus des trois quarts, 3 milliards 500 millions."*
  — subscriptions past **4.5 billion**, of which **Paris alone supplied more than three
  quarters** (≈3.5 billion).
- **1 July 1871:** *"nous atteignons près de 5 milliards en un seul jour."* — nearly **5
  billion in a single day**.
- **2 July 1871 (the line to quote):** *"La veille, l'État avait demandé 2 milliards à la
  France; la France lui avait répondu par une offre de près de 5 milliards! Messieurs, un pays
  qui, au lendemain de tant de désastres, sait [se relever ainsi]…"*
  — **the state asked France for 2 billion; France answered with an offer of nearly 5** — a
  country that, the day after so many disasters, could still raise this.

So the 2-billion tranche came in roughly **2½× covered**. A second, larger loan followed in
July 1872; together they let France pay the indemnity **ahead of schedule** and end the German
occupation early.

Data: `war_premia/data/thiers_loan_1871.csv` (figures OCR-grade — verify against the page
image). All values are from Le Temps' **commentary**, not the garbled cote table, so they are
more reliable than a cote scrape — but still to be checked.

## Where it fits the framework

- **The instrument is the sovereign bond, not the money market** — same lesson as the *fonds
  russes* in 1905: the risk (here, the recovery) sits in the bond market, invisible to a
  discount-rate test.
- **The inductive edge of finance** (research agenda, "three faces," face #3). 1906 is France
  *lending* to buy an ally's alignment; 1871 is France *borrowing from its own public* to buy
  back its soil. Both show finance as a **positive-edge tool** — the carrot, the recovery-lever
  — the mirror of the coercive squeeze (Ruhr 1923, the 1941 freeze).
- **Causal discipline still applies.** The loan's success *documents* France's creditworthiness
  and *enabled* the early evacuation; it does not by itself prove finance was the binding cause
  of the diplomatic timetable (the Frankfurt schedule and Bismarck's terms set that). Write
  "France's credit **funded and accelerated** the occupation's end," not "finance **ended** the
  occupation."

## Status

Reconnaissance stub, not a full study. Confirmed: the pipeline works for 1871, and the
oversubscription story is real and quotable from commentary. A full run would add the **rente
price trace** across 1871–73 (the cote table, verified against page images), the **second
(1872) loan**, and the German side (was the indemnity's arrival priced in Berlin?). Lowest-effort
of the agenda's Tier-1 extensions, now seeded.

## Reproduce

```bash
UA='Mozilla/5.0 (Windows NT 10.0) Chrome/120.0 Safari/537.36'
for D in 18710630 18710701 18710702; do
  ARK=$(curl -sS -A "$UA" -o /dev/null -w '%{redirect_url}' \
    "https://gallica.bnf.fr/ark:/12148/cb34431794k/date$D" | grep -oE 'bpt6k[0-9a-z]+' | head -1)
  for P in 1 2 3; do
    curl -sS -A "$UA" "https://gallica.bnf.fr/RequestDigitalElement?O=ark:/12148/$ARK&E=ALTO&Deb=$P" \
      | grep -oE 'CONTENT="[^"]*"' | sed 's/CONTENT=//;s/"//g' | tr '\n' ' '
  done
done | grep -oiE '.{0,40}(souscription|milliard).{0,70}'
```
