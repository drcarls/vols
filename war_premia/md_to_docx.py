"""Minimal, dependency-free Markdown -> .docx (WordprocessingML) generator.

Covers the subset used by these documents: ATX headings, paragraphs, bullet/ordered lists,
blockquotes, pipe tables, fenced code, horizontal rules, and inline bold/italic/code/links.
Emits real Word heading styles (Heading1..4) so the Navigation pane and Insert-TOC work.

Not a general Markdown engine — a pragmatic one for this corpus.
"""
from __future__ import annotations

import re
import zipfile

# ---------- inline ----------
_TOKEN = re.compile(
    r"\*\*(?P<b>.+?)\*\*"          # bold
    r"|`(?P<c>[^`]+)`"             # code
    r"|\*(?P<i>[^*]+?)\*"          # italic *
    r"|(?<![A-Za-z0-9])_(?P<i2>[^_]+?)_(?![A-Za-z0-9])"  # italic _
    r"|\[(?P<lt>[^\]]+?)\]\((?P<lu>[^)]+?)\)"            # link
)


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _run(text: str, *, b=False, i=False, code=False) -> str:
    if text == "":
        return ""
    rpr = []
    if b:
        rpr.append("<w:b/>")
    if i:
        rpr.append("<w:i/>")
    if code:
        rpr.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="18"/>')
    rpr_xml = f"<w:rPr>{''.join(rpr)}</w:rPr>" if rpr else ""
    return f'<w:r>{rpr_xml}<w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'


def inline(text: str) -> str:
    out, pos = [], 0
    for m in _TOKEN.finditer(text):
        if m.start() > pos:
            out.append(_run(text[pos:m.start()]))
        if m.group("b") is not None:
            out.append(_run(m.group("b"), b=True))
        elif m.group("c") is not None:
            out.append(_run(m.group("c"), code=True))
        elif m.group("i") is not None:
            out.append(_run(m.group("i"), i=True))
        elif m.group("i2") is not None:
            out.append(_run(m.group("i2"), i=True))
        elif m.group("lt") is not None:
            out.append(_run(m.group("lt"), i=True))  # link text (underlined color omitted)
        pos = m.end()
    if pos < len(text):
        out.append(_run(text[pos:]))
    return "".join(out) or _run("")


# ---------- blocks ----------
def _para(runs_xml: str, style: str | None = None, *, page_break=False,
          ind=0, bullet=None) -> str:
    ppr = []
    if style:  # pStyle must precede pageBreakBefore per CT_PPr schema order
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if page_break:
        ppr.append("<w:pageBreakBefore/>")
    if ind:
        ppr.append(f'<w:ind w:left="{ind}" w:hanging="360"/>')
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    prefix = _run(bullet) if bullet else ""
    return f"<w:p>{ppr_xml}{prefix}{runs_xml}</w:p>"


def _table(rows: list[list[str]]) -> str:
    ncol = max(len(r) for r in rows)
    total = 9360
    cw = total // ncol
    grid = "".join(f'<w:gridCol w:w="{cw}"/>' for _ in range(ncol))
    borders = ("<w:tblBorders>"
               + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
                         for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
               + "</w:tblBorders>")
    body = []
    for ri, row in enumerate(rows):
        cells = []
        for ci in range(ncol):
            txt = row[ci] if ci < len(row) else ""
            shade = '<w:shd w:val="clear" w:fill="EEEEF6"/>' if ri == 0 else ""
            runs = inline(txt)
            if ri == 0:
                runs = runs.replace("<w:r>", "<w:r><w:rPr><w:b/></w:rPr>", 1) if runs else runs
            cell_p = f'<w:p><w:pPr><w:pStyle w:val="TableCell"/></w:pPr>{runs}</w:p>'
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{cw}" w:type="dxa"/>{shade}</w:tcPr>{cell_p}</w:tc>')
        body.append(f"<w:tr>{''.join(cells)}</w:tr>")
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/>{borders}</w:tblPr>'
            f"<w:tblGrid>{grid}</w:tblGrid>{''.join(body)}</w:tbl>")


_H = re.compile(r"^(#{1,6})\s+(.*)$")
_UL = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
_SEP = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in _ROW.match(line).group(1).split("|")]


def blocks_to_xml(md: str, *, page_break_headings=(1, 2)) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        # fenced code
        if line.lstrip().startswith("```"):
            i += 1
            code_lines = []
            while i < n and not lines[i].lstrip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # closing fence
            for cl in code_lines:
                out.append(_para(_run(cl or " ", code=True), "Code"))
            continue
        # table
        if _ROW.match(line) and i + 1 < n and _SEP.match(lines[i + 1]) and "|" in lines[i + 1]:
            rows = [_cells(line)]
            i += 2
            while i < n and _ROW.match(lines[i]):
                rows.append(_cells(lines[i]))
                i += 1
            out.append(_table(rows))
            continue
        # heading
        m = _H.match(line)
        if m:
            lvl = len(m.group(1))
            style = f"Heading{min(lvl, 4)}"
            pb = lvl in page_break_headings
            out.append(_para(inline(m.group(2)), style, page_break=pb))
            i += 1
            continue
        # horizontal rule
        if re.match(r"^\s*([-*_])\1\1+\s*$", line):
            out.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" '
                       'w:color="CCCCCC"/></w:pBdr></w:pPr></w:p>')
            i += 1
            continue
        # blockquote
        if line.lstrip().startswith(">"):
            qlines = []
            while i < n and lines[i].lstrip().startswith(">"):
                qlines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(_para(inline(" ".join(qlines)), "Quote"))
            continue
        # list (consecutive items)
        if _UL.match(line) or _OL.match(line):
            while i < n and (_UL.match(lines[i]) or _OL.match(lines[i])):
                um, om = _UL.match(lines[i]), _OL.match(lines[i])
                if um:
                    indent = len(um.group(1))
                    txt, bullet = um.group(2), "•  "
                else:
                    indent = len(om.group(1))
                    txt, bullet = om.group(3), f"{om.group(2)}.  "
                lvl = 1 + (indent // 2)
                out.append(_para(inline(txt), "ListParagraph", ind=360 * lvl, bullet=bullet))
                i += 1
            continue
        # paragraph (gather until blank / block start)
        buf = [line]
        i += 1
        while i < n and lines[i].strip() and not _H.match(lines[i]) \
                and not lines[i].lstrip().startswith((">", "```")) \
                and not _UL.match(lines[i]) and not _OL.match(lines[i]) \
                and not _ROW.match(lines[i]):
            buf.append(lines[i])
            i += 1
        out.append(_para(inline(" ".join(buf))))
    return "".join(out)


# ---------- package ----------
_CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                  '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                  '<Default Extension="xml" ContentType="application/xml"/>'
                  '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                  '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                  "</Types>")
_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
         "</Relationships>")
_DOC_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
             "</Relationships>")


def _heading_style(sid, name, outline, sz, color, before=240):
    return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/>'
            '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
            f'<w:pPr><w:keepNext/><w:spacing w:before="{before}" w:after="120"/>'
            f'<w:outlineLvl w:val="{outline}"/></w:pPr>'
            f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:color w:val="{color}"/>'
            f'<w:sz w:val="{sz}"/></w:rPr></w:style>')


def _styles() -> str:
    styles = [
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>'
        '<w:pPr><w:spacing w:after="140" w:line="288" w:lineRule="auto"/></w:pPr>'
        '<w:rPr><w:rFonts w:ascii="Georgia" w:hAnsi="Georgia"/><w:sz w:val="22"/></w:rPr></w:style>',
        _heading_style("Title", "Title", 0, 64, "1A2A44", before=0),
        _heading_style("Subtitle", "Subtitle", 0, 30, "555555"),
        _heading_style("Heading1", "heading 1", 0, 40, "1A2A44"),
        _heading_style("Heading2", "heading 2", 1, 30, "24405F"),
        _heading_style("Heading3", "heading 3", 2, 25, "333333"),
        _heading_style("Heading4", "heading 4", 3, 23, "444444"),
        '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="8A3B2E"/></w:pBdr><w:ind w:left="360"/></w:pPr>'
        '<w:rPr><w:i/><w:color w:val="444444"/></w:rPr></w:style>',
        '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/>'
        '<w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="60"/></w:pPr></w:style>',
        '<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:shd w:val="clear" w:fill="F3F1EA"/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
        '<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="18"/></w:rPr></w:style>',
        '<w:style w:type="paragraph" w:styleId="TableCell"><w:name w:val="Table Cell"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:spacing w:after="40"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="18"/></w:rPr></w:style>',
    ]
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            + "".join(styles) + "</w:styles>")


def build_docx(body_xml: str, out_path: str) -> None:
    sect = ('<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
            'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>')
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body>{body_xml}{sect}</w:body></w:document>")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/styles.xml", _styles())
        z.writestr("word/document.xml", document)
