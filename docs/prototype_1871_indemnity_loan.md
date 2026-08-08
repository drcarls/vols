# Prototype run — the Thiers indemnity loans (1871 & 1872): finance as recovery-lever

The 19th-century mirror of the 1906 Russian loan, but with **France as the debtor**. After
Sedan and the Commune, the Frankfurt treaty (10 May 1871) imposed a **5-billion-franc**
indemnity, with German troops to occupy French soil until it was paid. Adolphe Thiers'
government floated two great loans — a **5% rente** in June 1871 and the **3-billion "Emprunt
national"** in July 1872 — to raise it. The wager of the whole book's "inductive edge of
finance" is here in its purest form: a nation's **credit** — not its army — bought back its
territory.

Runs on the exact **Le Temps / Gallica** pipeline built for 1905–14, verbatim.

## The first loan — June 1871 (2 billion, ~2½× covered)

Massively oversubscribed in a single day:

- **30 June 1871:** *"les merveilleux résultats de l'emprunt… 4 milliards 500 millions… Paris…
  y figure pour plus des trois quarts, 3 milliards 500 millions."* — subscriptions past **4.5
  billion**, **Paris supplying more than three quarters** (≈3.5 billion).
- **1 July 1871:** *"nous atteignons près de 5 milliards en un seul jour."* — nearly **5
  billion in a day**.
- **2 July 1871 (the line to quote):** *"La veille, l'État avait demandé 2 milliards à la
  France; la France lui avait répondu par une offre de près de 5 milliards!"* — the state asked
  2 billion; the market answered with nearly 5. Roughly **2½× covered**.

## The second loan — July 1872 (3 billion, **more than 12× covered**)

The one that stunned Europe. Subscriptions were oversubscribed **before the Treasury windows
even opened**, and the final tally dwarfed the first loan:

- **28 July 1872:** *"EMPRUNT NATIONAL DE 3 MILLIARDS"*; *"l'emprunt était déjà couvert avant
  que le Trésor n'ouvrît ses guichets… les demandes s'élèvent sans autre limite que…"*
- **29 July 1872 (Versailles, morning):** *"Le total des souscriptions connues jusqu'à présent
  est d'environ quatre milliards"* — ~4 billion on the first day alone.
- **1 August 1872 (the headline):** *"Ce n'est pas seulement dix fois que l'emprunt a été
  couvert, c'est plus de douze fois; nous sautons de 30 milliards à **41 milliards 641
  millions** en capital."* — **> 12× covered**, total subscriptions **41.641 billion**. France's
  own share in rentes was **1,037 million** (Paris ≈791 million); the **foreign contingent
  1,427 million** — the loan drew capital from across Europe back into French paper.

Together the two loans let France pay the 5-billion indemnity **ahead of schedule**; the last
German troops left in **September 1873**, well before the treaty's outer limit.

Data: `war_premia/data/thiers_loan_1871.csv` (figures OCR-grade — verify against the page
image). All values are from Le Temps' **commentary**, not the garbled cote table, so they are
more reliable than a cote scrape — but still to be checked.

## Where it fits the framework

- **The instrument is the sovereign bond, not the money market** — same lesson as the *fonds
  russes* in 1905: the risk (here, the recovery) sits in the bond market, invisible to a
  discount-rate test.
- **The inductive edge of finance** (research agenda, "three faces," face #3). 1906 is France
  *lending* to buy an ally's alignment; 1871–72 is France *borrowing from its own public and
  from Europe* to buy back its soil. Both show finance as a **positive-edge tool** — the carrot,
  the recovery-lever — the mirror of the coercive squeeze (Ruhr 1923, the 1941 freeze).
- **A market vote of confidence.** A 12× cover with a large *foreign* contingent is Europe's
  capital markets pricing France as a good credit within a year of catastrophic defeat — the
  bond-market counterpart to a diplomatic verdict.
- **Causal discipline still applies.** The loans' success *documents* France's creditworthiness
  and *enabled and accelerated* the early evacuation; it does not by itself prove finance was the
  binding cause of the diplomatic timetable (the Frankfurt schedule and Bismarck's terms set
  that). Write "France's credit **funded and accelerated** the occupation's end," not "finance
  **ended** the occupation."

## Status

The two-loan **subscription** story is solid and quotable from commentary. Still open for a full
study: the **rente price trace** across 1871–73 (the cote table, verified against page images —
the OCR there is garbled and needs image-level reading), and the **German side** (was the
indemnity's arrival priced in Berlin?). This is the lowest-effort of the agenda's Tier-1
extensions, now substantially seeded.

## Reproduce

```bash
UA='Mozilla/5.0 (Windows NT 10.0) Chrome/120.0 Safari/537.36'
for D in 18710630 18710701 18710702 18720729 18720730 18720801; do
  ARK=$(curl -sS -A "$UA" -o /dev/null -w '%{redirect_url}' \
    "https://gallica.bnf.fr/ark:/12148/cb34431794k/date$D" | grep -oE 'bpt6k[0-9a-z]+' | head -1)
  for P in 1 2 3; do
    curl -sS -A "$UA" "https://gallica.bnf.fr/RequestDigitalElement?O=ark:/12148/$ARK&E=ALTO&Deb=$P" \
      | grep -oE 'CONTENT="[^"]*"' | sed 's/CONTENT=//;s/"//g' | tr '\n' ' '
  done
done | grep -oiE '.{0,40}(souscription|milliard|couvert|fois).{0,70}'
```
