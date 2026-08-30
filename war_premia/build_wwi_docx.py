"""Assemble the WWI/pre-1914 book + the later risk episodes into one Word document.

Part I  = the assembled pre-1914 book (not_this_year.md).
Part II = the later risk episodes (modern_* cases, chronological) + the synthesis.

Uses the dependency-free md_to_docx generator (no pandoc/LibreOffice needed). Real Heading styles ->
Word Navigation pane + one-click Insert-TOC.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from md_to_docx import inline, blocks_to_xml, build_docx, _para  # noqa: E402

DOCS = Path("/home/user/vols/docs")
OUT = DOCS / "What-Really-Matters.docx"

MODERN = [
    ("modern_arc_companion.md",               "The Modern Arc — Companion"),
    ("prototype_munich_1938.md",              "Munich, 1938"),
    ("modern_wwii_outbreak_1939_1940.md",     "The Outbreak of WWII, 1939–1940"),
    ("modern_pearl_harbor_1941.md",           "Pearl Harbor & the 1941 Freeze"),
    ("modern_berlin_airlift_1948.md",         "The Berlin Airlift, 1948"),
    ("modern_korea_1950.md",                  "Korea, 1950"),
    ("modern_suez_1956.md",                   "Suez, 1956"),
    ("modern_nuclear_limits.md",              "Cuba & Berlin — the Nuclear Limits, 1961–62"),
    ("modern_gulf_wars.md",                   "The Gulf Wars, 1991 & 2003"),
    ("modern_2022_russia_ukraine.md",         "Russia–Ukraine, 2022"),
    ("modern_iran_2026_prediction_markets.md", "Iran, 2025–26 — the Prediction-Market Era"),
    ("modern_contemporaneous_sources.md",     "Note on Contemporaneous Sources"),
    ("synthesis_and_lessons.md",              "Synthesis & Lessons"),
]

BOOK_CHAPTERS = [
    "Russia, 1905 — the alliance as an asset",
    "Bosnia, 1908–09 — the empty treasury",
    "Agadir, 1911 — the squeeze",
    "The Balkans, 1912–13 — where the money actually bit",
    "July 1914 — the question nobody asked",
]


def demote(md: str, levels: int = 1) -> str:
    for _ in range(levels):
        md = re.sub(r"(?m)^(#{1,5})(\s)", r"\1#\2", md)
    return md


def strip_first_h1(md: str) -> str:
    return re.sub(r"(?m)\A\s*#\s+.*\n", "", md, count=1)


def read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def build_agadir_chapter() -> str:
    """The real Chapter III: the full 'Squeeze' essay + the Berlin money-market technical brief,
    replacing the status-stub that stood in not_this_year.md. Written at the book's native heading
    levels so the single global demote() nests it correctly under Part I."""
    essay = read("agadir-essay-magazine.md")
    essay = re.sub(r"(?m)\A#\s+.*\n", "", essay, count=1)        # drop "# THE SQUEEZE"
    essay = re.sub(r"(?m)\A\s*###\s+.*\n", "", essay, count=1)   # drop "### Berlin, autumn 1911"
    essay = demote(essay.strip(), 1)                             # ## sections -> ###
    digest = read("chapter3_digest_for_handoff.md")
    cut = digest.find("\n# rates")                               # drop the raw rates/corpus tail
    if cut != -1:
        digest = digest[:cut]
    digest = re.sub(r"(?m)\A#\s+.*\n", "", digest, count=1)      # drop "# Chapter III ..."
    digest = demote(digest.strip(), 2)                           # ## Part -> ####
    return (
        "## III. Agadir, 1911 — The Squeeze\n\n"
        "*The full chapter — Berlin, autumn 1911.*\n\n"
        + essay + "\n\n"
        "### Chapter III — the money-market evidence (technical brief)\n\n"
        + digest + "\n"
    )


INTRODUCTION = """Everything a great war needs was in place by 1905 — the alliances signed, the \
conscript armies raised, the naval race running, the mobilisation timetables printed and revised each \
year — and it sat there, unused, for nine years. Then, in the summer of 1914, it was used. This volume \
is about the interval: not the catastrophe, which has been explained many times over, but the nine \
years of peace that preceded it, and the machinery of money that had to work before any of those \
armies could march.

The wager of the book is easy to state and hard to prove. A war has to be paid for, and paying for it \
is a step at which things can fail — not because the money does not exist, but because in a given \
crisis the arrangements cannot be made in the time available, or cannot be made without a political \
price the government will not pay, and someone has to say so. Between 1905 and 1913, crisis after \
crisis, someone did. In July 1914 no one did. What changed was not the wealth of nations but the \
condition of their money markets at the moment the question was put.

Holding that claim honestly requires a discipline the book keeps throughout, and states here at the \
outset. A creditor position documents exposure, not automatic power; a price movement is a symptom of \
a counterparty's condition, not proof that finance drove a decision. **Finance was the substrate and \
the lever — never the cause, unless a specific choice can be shown to have bent to it.** That is a \
narrower thesis than the one the project began with, and it is the one the evidence supports.

The evidence itself is a price almost no one has read for this purpose. Every week from 1904 to 1914, \
in thirteen cities from Paris and Berlin to Stockholm, Bombay and New York, men set a rate for short \
money, and those quotations survive. Read together they say something unexpected: Europe's markets did \
not price war country by country. They moved as one. Neutral Stockholm carried premiums as heavy as \
Paris; in the Balkan scares it was Stockholm that flinched and Berlin that did not. *The market was \
not pricing which nation would fight. It was pricing whether the system would hold* — whether a local \
quarrel would run along the alliances and the bill networks until it went general and choosing a side \
stopped mattering. Only New York sat outside the structure, its rate falling when Europe frightened \
itself, because a country beyond the alliance system was where the contagion did not reach.

From that single observation the book takes its method, and the method is why there is a Part II. Two \
ideas do the work.

The first is the **instrument problem**. The famous finding about 1914 — that markets never saw it \
coming — rests on sovereign bond spreads, which barely stir until the last days of July. The bonds \
were right: a bond prices the risk of not being repaid over decades, and that risk did not rise; \
consols had survived Napoleon. What rose was the price of cash next month, and that lived in a \
different instrument, held by different people, read by different eyes — the discount market, where \
states borrowed short and a finance minister learned within days that the next bill would come dearer \
or come up short. The signal was never absent. It was in the instrument no one thought to read. Find \
the exposed instrument and you find the signal; read the index and you find nothing.

The second is the distinction between **anticipation and resolution**. Markets are poor prophets and \
good accountants. They rarely forecast the decision to fight; they price its consequences briskly once \
the decision is visible. The corollary runs through every case in this book and the next — *trade the \
resolution, not the forecast* — together with its harder companion: know which risks can be priced at \
all. A localised or survivable shock is priced and discriminated; an existential, system-ending war \
cannot be, and the silence of the instrument is then not comfort but its own kind of information.

**Part I** works these ideas through the nine years before 1914, crisis by crisis — Russia in 1905, \
Bosnia in 1908, Agadir in 1911, the Balkans in 1912–13, and the July that ended the sequence — asking \
of each power the same four questions: could it turn wealth into usable public finance (*capability*), \
hold the political consent a war demands (*consent*), produce spendable money inside the crisis itself \
(*liquidity*), and would the crisis stay open long enough for a weakness to bind (*time*). The answers \
are not a league table of guilt. They are a study of where, when, and in which instrument money made \
itself felt — and, as often, where a real weakness was simply irrelevant because no one was going to \
fight that year.

**Part II** takes the same instruments and the same questions out of the period, into the later risk \
episodes — Munich 1938, the outbreak of 1939, Pearl Harbor, the Berlin Airlift, Korea, Suez, the \
nuclear brinkmanship of Cuba and Berlin, the Gulf Wars, Russia's invasion of Ukraine, and the \
prediction-market era of 2025–26. These are not proofs; they are out-of-sample tests of a method built \
on a single decade. Each asks the questions the pre-war chapters raise: did the market anticipate the \
war or only price its resolution? Which instrument carried the signal, and which merely looked like it \
did? Was the risk priceable at all, or the kind the market cannot see because seeing it changes \
nothing? The century between Agadir and Hormuz rhymes more than it repeats — and where it breaks the \
pattern is as instructive as where it keeps it.

A word on what to expect and what not to. Where market figures appear they are sourced or \
reproducible. Documented effects are kept separate from inferred intent; contemporary perception from \
causal verdict. The book does not claim that finance stopped a war. It claims something smaller and \
more durable: that money was the medium in which the possibility of war was continuously, imperfectly, \
and legibly priced — and that if you read the right instrument, in the right city, in the right week, \
you can still watch them doing it."""


def main():
    parts = []

    # --- Title page ---
    parts.append(_para(inline("A FRAMEWORK AND HISTORY")))
    parts.append(_para(inline("WHAT REALLY MATTERS"), "Title"))
    parts.append(_para(inline("Money, War Risk, and the Episodes That Did — and Did Not — "
                              "Break, 1905–2026"), "Subtitle"))
    parts.append(_para(inline("**Philip Carls**")))
    parts.append(_para(inline("2026")))

    # --- Contents ---
    parts.append(_para(inline("Contents"), "Heading1", page_break=True))
    parts.append(_para(inline("**Part I — Not This Year: The Pre-1914 Argument**")))
    for c in BOOK_CHAPTERS:
        parts.append(_para(inline(c), "ListParagraph", ind=360, bullet="•  "))
    parts.append(_para(inline("**Part II — The Later Risk Episodes, 1938–2026**")))
    for _, t in MODERN:
        parts.append(_para(inline(t), "ListParagraph", ind=360, bullet="•  "))

    # --- Introduction ---
    parts.append(_para(inline("Introduction"), "Heading1", page_break=True))
    parts.append(blocks_to_xml(INTRODUCTION))

    # --- Part I ---
    parts.append(_para(inline("Part I — Not This Year: The Pre-1914 Argument"),
                       "Heading1", page_break=True))
    book = strip_first_h1(read("not_this_year.md"))
    s, e = book.find("## III. Agadir"), book.find("## IV. The Balkans")
    if s != -1 and e != -1:  # replace the Chapter III status-stub with the full chapter
        book = book[:s] + build_agadir_chapter() + "\n\n" + book[e:]
    parts.append(blocks_to_xml(demote(book, 1)))  # book headings nest under the Part

    # --- Part II ---
    parts.append(_para(inline("Part II — The Later Risk Episodes, 1938–2026"),
                       "Heading1", page_break=True))
    for fname, title in MODERN:
        parts.append(_para(inline(title), "Heading2", page_break=True))
        b = demote(strip_first_h1(read(fname)), 1)
        parts.append(blocks_to_xml(b, page_break_headings=()))  # cases already broken by their H2

    build_docx("".join(parts), str(OUT))
    print("DOCX written:", OUT)


if __name__ == "__main__":
    main()
