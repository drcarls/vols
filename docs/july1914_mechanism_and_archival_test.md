# July 1914: mechanism, not motive — and the one archival test

## The correction

Every *documented* motive for the July 1914 tempo is diplomatic: localize the war,
present Russia and France a fait accompli, exploit the post-Sarajevo sympathy
window. No participant minuted "move before the money market can react." **Any
claim of financial *intent* invents a source that does not exist**, and this repo
should not make it.

The defensible claim is the stronger one. The secrecy and speed were chosen for
diplomatic ends and *had* a financial **effect**: the market could not price what
it could not see (the money-market and bond evidence in `war_premia` shows it saw
nothing until the last week of July, then seized). A restraining financial
reaction, if one would have formed, was never given time to form. **Mechanism does
not require intent.** Where this repo uses the word "brake" (`crisis_lag`), read it
as a statement about the *market's* capacity to react in time, never as a claim
that anyone timed the crisis to defeat it.

What the market-side evidence here establishes: markets were surprised and
repriced too late to matter. What it says about the *state's* knowledge or intent:
**nothing.** That is a separate, archival question.

> **The parallel across the earlier crises — cause or cover?** The same
> intent-vs-mechanism split applies to Rouvier (1905), Kokovtsov (1908–09) and
> Biliński (1912–13): were their *fiscal* justifications the cause of each
> climb-down, or cover for a decision taken on other grounds? Market data cannot
> settle that either — but it gives one asymmetric, timing-based handle, run in
> [`../crisis_lag/results/cause_or_cover.md`](../crisis_lag/results/cause_or_cover.md).
> Properly controlled — benchmarked against a **neutral** creditor (the Dutch
> yield), measured as a **change**, against a **null distribution** — each power
> whose own solvency was in question shows an abnormal rise in its bonds during
> its crisis: **Germany** (Agadir, ~90th percentile), **Russia** (Bosnia, ~80th),
> **Austria** (Balkans, ~90th but only at the long horizon its two-winter war
> needed). **France (Morocco) shows none** — the creditor power, no own-market
> stress, consistent with the constraint lying in Russia's collapse, not French
> finances. So the timing evidence *is* consistent with finance-as-constraint for
> three of four (a crude level check first understated this, then I over-corrected
> to "artifact" — the neutral-benchmark control corrects both). Still consistency,
> never proof; intent still needs the archives named there, and France stays the
> case where the objection is most alive.

## The finite question

Did the Reichsbank or the Reich Treasury (Reichsschatzamt) take a **concrete
preparatory financial step during 5–23 July 1914** — after the "blank cheque"
(5–6 July), before the Austrian ultimatum (23 July) — *while the market was still
calm*?

- **If yes**, the state acted on knowledge the market lacked: an information
  asymmetry, the sharpest form of the mechanism. (Still not "intent to outrun the
  bourse" — it could be prudent contingency — but a state moving ahead of the
  market is the closest thing to a smoking gun.)
- **If no** — if the Treasury, like the market, was quiet until the ultimatum —
  the asymmetric-information version is *refuted*: the state was as surprised by
  the tempo as the market, and the mechanism reduces to "the market could not
  react in time," with no privileged state foresight.

It is a binary question with a findable answer.

## The two sources that settle it

- **Reinhold Zilch, *Die Reichsbank und die finanzielle Kriegsvorbereitung von
  1907 bis 1914*** (diss. 1976; Forschungen zur Wirtschaftsgeschichte, Berlin
  1987) — *the* archival monograph on Reichsbank financial war preparation, built
  on the Reichsbank and Treasury records. It is what would confirm or deny a
  quiet-weeks step.
- **The Reichsbank's own 1914 *Verwaltungsbericht*** — a day-by-day account of the
  bank's 1914 operations (discount policy, gold movements, note issue). The
  primary public record of *when* the Reichsbank actually moved.

### Where they're digitized (access map)

Searched Aug 2026. Both are *located*; neither could be pulled from this
repo's locked-down environment (curl-with-CA egress only — no browser that can
tunnel the agent proxy, Google Books API rate-limited, and every delivery
surface below is a JavaScript viewer or Cloudflare-gated). On an unrestricted
network the public-domain report opens in one click at the first two.

**Reichsbank 1914 *Verwaltungsbericht* (Berlin, 1915) — public domain, digitized:**
- **HathiTrust**, catalogue **Record 100598111** — the one confirmed digital
  run of the *Reichsbank* Verwaltungsbericht (full-view for the pre-1929
  volumes). Whether the 1914 business-year volume is among HathiTrust's held
  years could not be checked here (Cloudflare bot challenge blocks the catalogue
  and the API). This is the primary download route.
  <https://catalog.hathitrust.org/Record/100598111>
- **Bundesarchiv R 2501** (Reichsbank records), harvested to DDB /
  Archivportal-D — but the DDB harvest of this series **skips the 1914
  business year** (it carries 1889–1908 and 1919–1941 scattered, no 1914 item),
  so BArch likely holds the 1914 volume un-harvested. Delivery is the invenio
  session viewer.
- German National Library serial record: `d-nb.info/01026602X`.
- **Correction:** an MDZ / Bayerische Staatsbibliothek digitization exists at
  **ZDB-ID 520775-7**, but the K10plus union catalogue attaches that link to
  the *Verwaltungsbericht der **Preussischen Bank*** — the Reichsbank's pre-1876
  predecessor — **not** the Reichsbank report, and it does not cover 1914. The
  three Reichsbank Verwaltungsbericht records in K10plus carry no digitization
  link at all. Do not cite MDZ for the 1914 Reichsbank report.

**Zilch (1987) — in copyright, no open-access full text.** The Akademie-Verlag
original (Forschungen zur Wirtschaftsgeschichte Bd. 20, from the 1976
dissertation) was reissued by De Gruyter in 2022 (ISBN 978-3-11-277326-0) and
sells commercially. An interlibrary-loan / purchase item, held at major
research libraries; not a free download. (DigiZeitschriften, one possible
route, was discontinued 31 Dec 2025.)

## Evidence state (audited against the scholarship that cites Zilch and BArch R 2)

**Established (documented):**
- The financial-mobilization **framework is old — 1891**: the Reichsbank as fiscal
  agent, loan-bank (Darlehnskassen) creation, and *draft war-finance laws to be
  enacted in case of war*, with "details added in later years." Refined by the
  Wermuth/Havenstein gold-accumulation program to 1914. **Readiness is a 23-year
  contingency plan, not a July 1914 initiative.**
- Operational steps are dated to the **crisis, not the quiet weeks**: specie
  payments suspended **31 July**; the imperial gold reserve (Kriegsschatz, 240 M
  ℳ) transferred to the Reichsbank **2 August** (BArch **R 2/41134**); the bank
  laws enacted **4 August**.
- The plan was built **for a short, victorious war** ("the departure from the gold
  standard was only temporary"). The state's *own* financial design shared the
  short-war assumption that mispriced the actual conflict — **readiness was not
  foresight.**

**Not established:**
- Any concrete Reichsbank/Treasury action dated **5–23 July 1914**. The
  authoritative *1914-1918-Online* synthesis — which *does* cite Zilch and even
  gives BArch R 2 signatures for the August steps — reports **no** discount-rate
  or gold-policy change before ~31 July, and nothing in the blank-cheque-to-
  ultimatum window. The public central bank was calm because it *was* calm.

**Unreliable (do not use):**
- The popular "Havenstein demanded all banks' gold on 18 June 1914" line (Mises
  op-ed) — conflates the multi-year campaign and supplies the *intent* framing to
  be avoided.

## Provisional verdict — and it leans *against* the smoking gun

On the currently documented evidence, the **asymmetric-information version is not
supported**: the Reichsbank did not act ahead of the market in the quiet weeks. It
held a long-standing plan and *activated it at the crisis* — 31 July onward,
roughly when the market itself woke up; in the last days it was even reacting to a
gold run, not front-running one. So the mechanism reduces to its honest core:
**the market could not react in time to a diplomatic tempo — not that the state
knew and moved first.** And the sharper irony is that the state's readiness was
calibrated to the *wrong* war (short, victorious), the same misjudgment the market
made about pricing one at all.

This is *provisional* because it rests on the English-language synthesis of Zilch,
not a line-by-line read of Zilch's German text or the 1914 *Verwaltungsbericht* —
either of which could surface a finer mid-July detail. But the burden has shifted:
the default reading is now **no privileged state action in the quiet weeks**, and
it would take a positive find in those two sources to overturn it.

**This note reports no archival finding of my own** — I have not read Zilch or the
1914 report directly. It names the two sources that decide the question, records
what the scholarship citing them already shows (a 1891 framework, no 5–23 July
step, a short-war premise), and states which way the evidence now points. Read the
two sources before asserting more.

## Sources

- *1914-1918-Online, International Encyclopedia of the First World War*: "War
  Finance (Germany)" and "War Finance and Monetary Consequences: The German Case
  Revisited."
- J. Popper (contemporary), "Germany's Financial Mobilization," *Quarterly Journal
  of Economics* 29:4 (1915).
- Flagged as unreliable for this purpose: Mises Institute, "The Reichsbank:
  Germany's Central Bank Lays Foundation of Monetary Disaster" (op-ed).
