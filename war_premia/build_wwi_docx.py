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

    # --- About ---
    parts.append(_para(inline("About this volume"), "Heading1", page_break=True))
    parts.append(blocks_to_xml(
        "This volume collects two bodies of work. **Part I** is *Not This Year* — the study of how "
        "European capital markets priced (and mostly mis-priced) the war risk of the nine years before "
        "1914. **Part II** carries the same method forward across the later risk episodes — from Munich "
        "1938 to the prediction-market era of 2026 — testing where markets *anticipated* a war, where "
        "they only priced the *resolution* once it came, and where the risk was simply un-priceable.\n\n"
        "*Framework and historical analysis. Where market figures appear they are sourced or "
        "reproducible; documented effects are kept distinct from inferred intent, and contemporary "
        "perception from causal verdict.*"
    ))

    # --- Part I ---
    parts.append(_para(inline("Part I — Not This Year: The Pre-1914 Argument"),
                       "Heading1", page_break=True))
    book = strip_first_h1(read("not_this_year.md"))
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
