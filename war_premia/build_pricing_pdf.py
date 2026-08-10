import re, markdown
from playwright.sync_api import sync_playwright

DOCS = "/home/user/vols/docs/"
def read(f): return open(DOCS+f, encoding="utf-8").read()

reader = read("pricing-geopolitical-risk-READER.md")
desk   = read("instrument-problem-desk-note.md")
trades = read("trade-expressions.md")

# --- trim the reader edition's own Recommendations + Monitoring (covered better later) ---
i = reader.find("## Recommendations")
j = reader.find("## The one line to keep")
if i != -1 and j != -1:
    reader = reader[:i] + reader[j:]

# --- strip the top-level H1 title lines from each (we supply our own part headers) ---
def strip_leading_title(md):
    # drop a leading '# ...' and its immediate '### ...' subtitle + italic note block up to first '---'
    return md
reader_body = reader
desk_body   = desk
trades_body = trades

MDX = ['tables','fenced_code','sane_lists','attr_list']
def to_html(md): return markdown.markdown(md, extensions=MDX)

parts = [
  ('PART I – II', 'The Argument, the Board &amp; the Two Poles', to_html(reader_body)),
  ('PART III', 'The Instrument Problem — at a Glance', to_html(desk_body)),
  ('PART IV', 'Trade Expressions', to_html(trades_body)),
]

cover = """
<section class="cover">
  <div class="eyebrow">A framework note</div>
  <h1 class="ctitle">Pricing Geopolitical Risk</h1>
  <p class="csub">What markets know about war, what they structurally cannot — and how to position</p>
  <div class="crule"></div>
  <p class="cnote">The index is calm almost everywhere, and almost nowhere is the index the right
  instrument. This note makes the case from a century of market history (Part&nbsp;I), maps where the
  risk actually lives today (Parts&nbsp;II–III), and turns it into trade structure (Part&nbsp;IV).</p>
  <p class="cmeta">Framework and risk disciplines only · not investment advice · 2026 figures move</p>
</section>
"""

body = cover
for tag, title, html in parts:
    body += f'<section class="part"><div class="parthead"><span class="parttag">{tag}</span>' \
            f'<h1 class="parttitle">{title}</h1></div>{html}</section>'

CSS = """
:root{ --ink:#1a1d24; --muted:#5b6270; --accent:#2f4b7c; --ox:#8a3b2e; --rule:#d9d5cc; --soft:#f3f1ea; }
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:Georgia,'Times New Roman',serif; color:var(--ink); font-size:10.6pt; line-height:1.5;}
h1,h2,h3{font-family:'Helvetica Neue',Arial,sans-serif; line-height:1.2; color:var(--ink);}
h2{font-size:14pt; color:var(--accent); border-top:1px solid var(--rule); padding-top:.5em; margin:1.4em 0 .5em; page-break-after:avoid;}
h3{font-size:11.5pt; margin:1.1em 0 .35em; page-break-after:avoid;}
h1:not(.ctitle):not(.parttitle){font-size:15pt; margin:1.2em 0 .5em; color:var(--accent);}
p{margin:.5em 0} strong{color:var(--ink)}
a{color:var(--accent); text-decoration:none}
em{color:var(--ink)}
ul,ol{margin:.4em 0 .8em; padding-left:1.3em} li{margin:.28em 0}
blockquote{margin:.8em 0; padding:.4em .9em; border-left:3px solid var(--accent); background:var(--soft); color:var(--ink); font-style:italic;}
hr{border:none; border-top:1px solid var(--rule); margin:1.3em 0}
code{font-family:'SF Mono',Menlo,Consolas,monospace; font-size:.85em; background:var(--soft); padding:.05em .3em; border-radius:3px;}
table{border-collapse:collapse; width:100%; font-family:'Helvetica Neue',Arial,sans-serif; font-size:8.2pt; margin:.8em 0; page-break-inside:avoid;}
th,td{border:1px solid var(--rule); padding:4px 6px; text-align:left; vertical-align:top;}
thead th{background:var(--accent); color:#fff; font-weight:600; font-size:7.8pt; text-transform:uppercase; letter-spacing:.03em;}
tbody tr:nth-child(even){background:var(--soft);}
/* cover */
.cover{height:9.2in; display:flex; flex-direction:column; justify-content:center; page-break-after:always; text-align:left;}
.eyebrow{font-family:'Helvetica Neue',Arial,sans-serif; font-size:9pt; letter-spacing:.18em; text-transform:uppercase; color:var(--accent); margin-bottom:1.2em;}
.ctitle{font-size:34pt; margin:0 0 .2em; letter-spacing:-.01em;}
.csub{font-size:14pt; color:var(--muted); font-family:Georgia,serif; font-style:italic; margin:.2em 0 1em; max-width:34em;}
.crule{width:3in; border-top:2px solid var(--ox); margin:1em 0 1.6em;}
.cnote{font-size:11pt; color:var(--ink); max-width:32em;}
.cmeta{font-family:'Helvetica Neue',Arial,sans-serif; font-size:8.5pt; color:var(--muted); margin-top:2em; letter-spacing:.02em;}
/* part dividers */
.part{page-break-before:always;}
.parthead{border-bottom:2px solid var(--accent); margin:0 0 1em; padding-bottom:.5em;}
.parttag{font-family:'Helvetica Neue',Arial,sans-serif; font-size:8.5pt; letter-spacing:.16em; text-transform:uppercase; color:var(--ox); display:block; margin-bottom:.2em;}
.parttitle{font-size:20pt; margin:0; color:var(--ink);}
/* the first h1 inside each imported body is the doc's own title -> tone down */
.part > h1:first-of-type{display:none;}
"""

HTML = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
open("/tmp/claude-0/-home-user-vols/c4b13771-c92d-5603-bb46-ed79874a82fd/scratchpad/combined.html","w",encoding="utf-8").write(HTML)

OUT = "/home/user/vols/docs/Pricing-Geopolitical-Risk.pdf"
foot = ('<div style="font-family:Helvetica,Arial,sans-serif; font-size:7pt; color:#9a9a9a; width:100%;'
        ' padding:0 0.6in; display:flex; justify-content:space-between;">'
        '<span>Pricing Geopolitical Risk — a framework note (not investment advice)</span>'
        '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.set_content(HTML, wait_until="load")
    pg.pdf(path=OUT, format="Letter", print_background=True,
           display_header_footer=True, header_template="<span></span>", footer_template=foot,
           margin={"top":"0.7in","bottom":"0.7in","left":"0.75in","right":"0.75in"})
    b.close()
print("PDF written:", OUT)
