from __future__ import annotations

"""Render ranked prospects into a self-contained, interactive HTML app --
the "Prospect Scout for Questa" view.

An operator-facing single page: a branded header with a theme toggle, the
scoring "recipe" as chips, summary stat tiles, signal filters, and one
expandable row per prospect. Each row opens to a pre-sales brief plus an
evidence panel that shows the *actual* live queries behind every signal
(the LinkedIn jobs and governance SERP queries, the homepage findings).
No external assets; theme-aware; generated straight from ProspectReport
data so it always matches the CSV.
"""

import html
from typing import Iterable

from .collectors.serp.query import build_governance_query, build_jobs_query
from .context_map import derive_findings
from .models import ProspectReport

_CSS = """
:root{
  --bg:#eef0f6; --surface:#ffffff; --surface-2:#f5f6fc;
  --border:#e0e3ee; --border-strong:#cbd0e2;
  --ink:#171b24; --ink-2:#565f72; --ink-3:#8b93a6;
  --accent:#5a4fe0; --accent-soft:#ecebfb; --accent-ink:#4a40c4;
  --hot:#d6521a; --hot-soft:#fbe8dd;
  --warn:#9a6b12; --warn-soft:#f6ecd6;
  --good:#12795a; --good-soft:#dcefe8;
  --crit:#b02a2f; --crit-soft:#f7e0e1;
  --shadow:0 1px 2px rgba(20,27,35,.06),0 8px 24px rgba(20,27,35,.06);
  --mono:ui-monospace,"SF Mono","SFMono-Regular",Menlo,Consolas,monospace;
  --sans:"Inter","Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#0c0f16; --surface:#151a24; --surface-2:#1c2230;
    --border:#28303f; --border-strong:#3a4356;
    --ink:#e9ebf3; --ink-2:#9aa1b4; --ink-3:#69707f;
    --accent:#8f88f2; --accent-soft:#22223c; --accent-ink:#b3adf7;
    --hot:#ef8a4c; --hot-soft:#33210f80; --warn:#d6a63e; --warn-soft:#2c250f80;
    --good:#46c199; --good-soft:#0f2b2280; --crit:#e5707a; --crit-soft:#33161980;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --bg:#0c0f16; --surface:#151a24; --surface-2:#1c2230;
  --border:#28303f; --border-strong:#3a4356;
  --ink:#e9ebf3; --ink-2:#9aa1b4; --ink-3:#69707f;
  --accent:#8f88f2; --accent-soft:#22223c; --accent-ink:#b3adf7;
  --hot:#ef8a4c; --hot-soft:#33210f80; --warn:#d6a63e; --warn-soft:#2c250f80;
  --good:#46c199; --good-soft:#0f2b2280; --crit:#e5707a; --crit-soft:#33161980;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  line-height:1.5;font-size:15px;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:22px clamp(14px,3vw,30px) 60px}
header{display:flex;align-items:center;gap:14px;padding-bottom:18px;margin-bottom:20px;
  border-bottom:1px solid var(--border);flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:11px}
.brand svg{width:30px;height:30px;display:block}
.brand .name{font-weight:700;letter-spacing:-.01em;font-size:16px}
.brand .name small{display:block;font-weight:500;color:var(--ink-2);font-size:12.5px}
.tag{font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
  color:var(--good);background:var(--good-soft);padding:3px 8px;border-radius:5px;
  border:1px solid color-mix(in srgb,var(--good) 30%,transparent)}
.spacer{flex:1 1 auto}
.tbtn{font:inherit;font-size:13px;color:var(--ink-2);background:var(--surface);
  border:1px solid var(--border-strong);border-radius:8px;padding:7px 12px;cursor:pointer;
  display:inline-flex;align-items:center;gap:7px}
.tbtn:hover{color:var(--ink);border-color:var(--accent)}
.tbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.recipe{margin-bottom:20px}
.recipe .lead{font-size:13.5px;color:var(--ink-2);margin-bottom:9px}
.recipe .lead b{color:var(--ink);font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.qchip{font-size:13px;padding:5px 11px;border-radius:20px;background:var(--surface);
  border:1px solid var(--border-strong);color:var(--ink);display:inline-flex;align-items:center;gap:6px}
.qchip .dot{width:7px;height:7px;border-radius:50%;background:var(--accent)}
.qchip.trig{border-color:color-mix(in srgb,var(--hot) 40%,transparent);color:var(--hot)}
.qchip.trig .dot{background:var(--hot)}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:26px}
@media(max-width:720px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:14px 15px;box-shadow:var(--shadow)}
.stat .k{font-size:26px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat .k.hot{color:var(--hot)}.stat .k.ac{color:var(--accent)}
.stat .l{font-size:12px;color:var(--ink-2);margin-top:2px}
.toolbar{display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap}
.filters{display:flex;gap:6px;flex-wrap:wrap}
.fbtn{font:inherit;font-size:13px;color:var(--ink-2);background:transparent;
  border:1px solid var(--border-strong);border-radius:8px;padding:6px 12px;cursor:pointer}
.fbtn[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.fbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.count{font-size:13px;color:var(--ink-3);margin-left:auto}
.list{display:flex;flex-direction:column;gap:10px}
.row{background:var(--surface);border:1px solid var(--border);border-radius:12px;
  box-shadow:var(--shadow);overflow:hidden}
.rhead{display:grid;align-items:center;gap:14px;
  grid-template-columns:34px minmax(0,1fr) auto 210px 22px;padding:13px 16px;cursor:pointer;
  width:100%;text-align:left;background:none;border:0;font:inherit;color:inherit}
.rhead:hover{background:var(--surface-2)}
.rhead:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
@media(max-width:820px){
  .rhead{grid-template-columns:28px minmax(0,1fr) 22px;row-gap:10px}
  .rhead .chipset,.rhead .fit{grid-column:1 / -1}
  .rhead .fit{width:100%}
}
.rank{font-variant-numeric:tabular-nums;font-weight:700;color:var(--ink-3);font-size:15px;text-align:center}
.co .cn{font-weight:650;letter-spacing:-.01em}
.co .cm{font-size:12.5px;color:var(--ink-2);margin-top:1px}
.co .cm .code{font-family:var(--mono);font-size:11.5px;color:var(--ink-3)}
.chipset{display:flex;gap:6px;flex-wrap:wrap}
.chip{font-size:11.5px;font-weight:600;padding:3px 9px;border-radius:6px;border:1px solid transparent;
  white-space:nowrap;display:inline-flex;gap:5px;align-items:center}
.chip.op{color:var(--hot);background:var(--hot-soft);border-color:color-mix(in srgb,var(--hot) 26%,transparent)}
.chip.wn{color:var(--warn);background:var(--warn-soft);border-color:color-mix(in srgb,var(--warn) 26%,transparent)}
.chip.gd{color:var(--good);background:var(--good-soft);border-color:color-mix(in srgb,var(--good) 26%,transparent)}
.chip.ac{color:var(--accent-ink);background:var(--accent-soft);border-color:color-mix(in srgb,var(--accent) 26%,transparent)}
.chip.mu{color:var(--ink-3);background:var(--surface-2);border-color:var(--border)}
.chip.tr{color:var(--hot);background:transparent;border:1.5px solid color-mix(in srgb,var(--hot) 55%,transparent);font-weight:700}
.fit{display:flex;align-items:center;gap:10px}
.meter{flex:1 1 auto;height:8px;border-radius:5px;background:var(--surface-2);border:1px solid var(--border);overflow:hidden}
.meter>i{display:block;height:100%;border-radius:5px}
.fitnum{font-variant-numeric:tabular-nums;font-weight:700;font-size:16px;width:30px;text-align:right}
.band{font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:2px 6px;border-radius:4px}
.band.hot{color:var(--hot);background:var(--hot-soft)}
.band.warm{color:var(--accent-ink);background:var(--accent-soft)}
.band.cool{color:var(--ink-3);background:var(--surface-2)}
.caret{color:var(--ink-3);transition:transform .18s ease;justify-self:center}
.row.open .caret{transform:rotate(90deg)}
.detail{border-top:1px solid var(--border);padding:0 16px}
.detail-inner{padding:16px 0 18px;display:grid;gap:16px;grid-template-columns:1.15fr 1fr}
@media(max-width:820px){.detail-inner{grid-template-columns:1fr}}
.panel h4{margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3)}
.brief{font-size:14px}
.brief .angle{margin-top:10px}.brief .angle b{color:var(--accent-ink)}
.brief .prod{display:inline-block;margin-top:10px;font-size:12px;font-weight:700;color:var(--accent-ink);
  background:var(--accent-soft);border:1px solid color-mix(in srgb,var(--accent) 26%,transparent);
  padding:3px 9px;border-radius:6px}
.ev{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:9px}
.ev li{display:grid;grid-template-columns:15px 1fr;gap:9px;font-size:13px;align-items:start}
.ev .ei{margin-top:3px;width:9px;height:9px;border-radius:50%}
.ev .lbl{font-weight:600}.ev .sub{color:var(--ink-2)}
.q{font-family:var(--mono);font-size:11.5px;color:var(--ink-2);background:var(--surface-2);
  border:1px solid var(--border);border-radius:7px;padding:8px 10px;margin-top:6px;overflow-x:auto;white-space:nowrap}
.verify{font-size:12px;color:var(--warn);margin-top:8px;display:flex;gap:6px;align-items:center}
.trignote{font-size:12.5px;color:var(--hot);margin-top:8px;font-weight:600;display:flex;gap:6px;align-items:center}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:11.5px;color:var(--ink-2);margin:20px 2px 0}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{width:10px;height:10px;border-radius:3px;display:inline-block}
footer{margin-top:28px;padding-top:18px;border-top:1px solid var(--border);font-size:12.5px;
  color:var(--ink-2);display:flex;flex-direction:column;gap:8px}
footer .hd{color:var(--ink);font-weight:600}
footer code{font-family:var(--mono);font-size:11.5px;background:var(--surface-2);padding:1px 5px;
  border-radius:4px;border:1px solid var(--border)}
.empty{display:none;color:var(--ink-2);padding:26px;text-align:center;border:1px dashed var(--border-strong);border-radius:12px;margin-top:10px}
@media(prefers-reduced-motion:reduce){*{transition:none !important}}
"""

_JS = """
(function(){
  document.querySelectorAll('.rhead').forEach(function(btn){
    btn.addEventListener('click',function(){
      var row=btn.closest('.row'),det=row.querySelector('.detail');
      var open=row.classList.toggle('open');
      btn.setAttribute('aria-expanded',open?'true':'false');det.hidden=!open;
    });
  });
  var rows=[].slice.call(document.querySelectorAll('.row')),
      countEl=document.getElementById('count'),
      empty=document.querySelector('.empty'),
      total=rows.length;
  function apply(f){
    var shown=0;
    rows.forEach(function(r){
      var ok = f==='all'
        || (f==='hifi'    && parseFloat(r.dataset.score)>=80)
        || (f==='chatbot' && r.dataset.chatbot==='true')
        || (f==='genai'   && r.dataset.genai==='true');
      r.style.display=ok?'':'none';if(ok)shown++;
    });
    countEl.textContent='Showing '+shown+' of '+total;
    if(empty)empty.style.display=shown?'none':'block';
  }
  var fbtns=document.querySelectorAll('.fbtn');
  fbtns.forEach(function(b){b.addEventListener('click',function(){
    fbtns.forEach(function(x){x.setAttribute('aria-pressed','false');});
    b.setAttribute('aria-pressed','true');apply(b.dataset.filter);
  });});
  apply('all');
  var root=document.documentElement,tb=document.getElementById('theme'),
      tl=document.getElementById('themeLabel'),ti=document.getElementById('themeIcon'),mode='system';
  tb.addEventListener('click',function(){
    mode = mode==='system'?'light':mode==='light'?'dark':'system';
    if(mode==='system')root.removeAttribute('data-theme');else root.setAttribute('data-theme',mode);
    tl.textContent=mode.charAt(0).toUpperCase()+mode.slice(1);
    ti.textContent=mode==='light'?'\\u2600':mode==='dark'?'\\u263e':'\\u25d0';
  });
})();
"""

_SHIELD = (
    '<svg viewBox="0 0 32 32" fill="none" aria-hidden="true">'
    '<path d="M16 2.5 27 6.4v8.1c0 6.9-4.5 12.4-11 15-6.5-2.6-11-8.1-11-15V6.4L16 2.5Z" '
    'fill="var(--accent-soft)" stroke="var(--accent)" stroke-width="1.6" stroke-linejoin="round"/>'
    '<path d="M16 10.5v11M11 16h10" stroke="var(--accent)" stroke-width="2.1" stroke-linecap="round"/>'
    '</svg>'
)

_DATA_LABEL = {"PHI": "Health · PHI/HIPAA", "financial": "Finance · GLBA",
               "legal_privileged": "Legal · privilege", "consumer_pii": "Consumer PII · state"}
_ADOPT_LABEL = {"active": "AI · active", "emerging": "AI · emerging",
                "none": "AI · none", "unknown": "AI · unknown"}
_GOV_LABEL = {"none_found": "No governance owner", "uncertain": "Governance unclear",
              "governed": "Governance · owner"}


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _product_key(product: str) -> str:
    p = product.lower()
    if "developer" in p:
        return "developer"
    if "cloud" in p:
        return "cloud"
    return "blackbox"


def _band(fit: float):
    if fit >= 80:
        return "hot", "Hot"
    if fit >= 60:
        return "warm", "Warm"
    return "cool", "Cool"


def _meter_color(fit: float) -> str:
    if fit >= 80:
        return "var(--hot)"
    if fit >= 55:
        return "var(--accent)"
    return "var(--ink-3)"


def _row(rank: int, r: ProspectReport) -> str:
    c = r.company
    ds, ad, gov = r.data_scope, r.adoption, r.governance
    findings = derive_findings(r)
    fit = r.fit_score
    bandc, bandt = _band(fit)

    # header chips
    chips = []
    if ds.data_class and ds.verdict in ("in_scope", "likely_in_scope"):
        chips.append(f'<span class="chip ac">{_esc(_DATA_LABEL.get(ds.data_class, ds.data_class))}</span>')
    elif ds.verdict == "out_of_scope":
        chips.append('<span class="chip mu">Out of scope</span>')
    ad_cls = {"active": "op", "emerging": "wn"}.get(ad.level, "mu")
    chips.append(f'<span class="chip {ad_cls}">{_esc(_ADOPT_LABEL.get(ad.level, ad.level))}</span>')
    gov_cls = {"none_found": "op", "uncertain": "wn", "governed": "gd"}.get(gov.status, "mu")
    chips.append(f'<span class="chip {gov_cls}">{_esc(_GOV_LABEL.get(gov.status, gov.status))}</span>')
    if ad.strong_hiring:
        chips.append('<span class="chip tr">⚡ Building GenAI</span>')

    # meta line
    size = f"~{c.employees:,} employees" if c.employees else "size n/a"
    sector = ds.sector or "unclassified"
    meta = f'{_esc(sector)} · <span class="code">NAICS {_esc(c.naics_code or "?")}</span> · {_esc(size)}'

    # brief
    angle = findings[0].talking_point if findings else "Regulated-data org adopting AI."
    scope_txt = (
        f"a {_esc(ds.data_class)} handler ({_esc(sector)}, {_esc(ds.regime)})"
        if ds.data_class else "scope unconfirmed"
    )
    adopt_txt = {
        "active": "active AI adoption",
        "emerging": "emerging AI adoption",
        "none": "no public AI signal",
        "unknown": "an unassessed AI posture",
    }.get(ad.level, ad.level)
    gov_txt = {
        "none_found": " and no governance owner on show",
        "uncertain": " and no clear governance owner",
        "governed": " with a visible governance owner",
    }.get(gov.status, "")
    trig = ('<div class="trignote">⚡ Buying trigger — actively hiring GenAI/LLM/MLOps roles.</div>'
            if ad.strong_hiring else "")
    verify = ('<div class="verify">⚑ Verify the governance gap by hand before outreach.</div>'
              if gov.verify_recommended and gov.status != "governed" else "")

    # evidence
    jobs_q = build_jobs_query(c.name)
    gov_q = gov.query or build_governance_query(c.name)
    adopt_ev = "; ".join(ad.findings) if ad.findings else "No adoption signal surfaced."
    gov_ev = {
        "none_found": "No company-tied privacy/AI-governance owner surfaced in public search.",
        "uncertain": "Privacy/compliance staff found, but no clear owner tied to the company.",
        "governed": "A named governance owner tied to the company was found.",
    }.get(gov.status, "")
    scope_ev = (
        f"Regulated-data sector ({_esc(sector)}, NAICS {_esc(c.naics_code or '?')}) → "
        f"{_esc(ds.data_class or 'n/a')} under {_esc(ds.regime or 'n/a')}."
        if ds.data_class else "Not mapped to a regulated-data sector on current data."
    )
    adopt_dot = {"active": "var(--hot)", "emerging": "var(--warn)"}.get(ad.level, "var(--ink-3)")
    gov_dot = {"none_found": "var(--hot)", "uncertain": "var(--warn)", "governed": "var(--good)"}.get(gov.status, "var(--ink-3)")

    return f"""<div class="row" data-score="{fit:.0f}" data-product="{_product_key(r.product)}"
     data-chatbot="{'true' if ad.chatbot else 'false'}" data-genai="{'true' if ad.strong_hiring else 'false'}">
  <button class="rhead" aria-expanded="false">
    <span class="rank">{rank}</span>
    <span class="co"><span class="cn">{_esc(c.name)}</span><span class="cm">{meta}</span></span>
    <span class="chipset">{''.join(chips)}</span>
    <span class="fit"><span class="band {bandc}">{bandt}</span><span class="meter"><i style="width:{max(3, min(100, fit)):.0f}%;background:{_meter_color(fit)}"></i></span><span class="fitnum">{fit:.0f}</span></span>
    <span class="caret" aria-hidden="true">›</span>
  </button>
  <div class="detail" hidden>
    <div class="detail-inner">
      <div class="panel brief">
        <h4>Pre-sales brief</h4>
        <div>A {scope_txt} with {adopt_txt}{gov_txt}.</div>
        <div class="angle"><b>Angle</b> — {_esc(angle)}</div>
        <span class="prod">Lead: {_esc(r.product)}</span>
        {trig}{verify}
      </div>
      <div class="panel">
        <h4>Evidence</h4>
        <ul class="ev">
          <li><span class="ei" style="background:var(--accent)"></span><span><span class="lbl">Regulated-data scope</span><div class="sub">{scope_ev}</div></span></li>
          <li><span class="ei" style="background:{adopt_dot}"></span><span><span class="lbl">AI adoption <span style="font-weight:400;color:var(--ink-3)">· live jobs SERP + homepage</span></span><div class="sub">{_esc(adopt_ev)}<div class="q">{_esc(jobs_q)}</div></div></span></li>
          <li><span class="ei" style="background:{gov_dot}"></span><span><span class="lbl">Governance owner <span style="font-weight:400;color:var(--ink-3)">· live web search</span></span><div class="sub">{_esc(gov_ev)}<div class="q">{_esc(gov_q)}</div></div></span></li>
        </ul>
      </div>
    </div>
  </div>
</div>"""


def render_dashboard(reports: Iterable[ProspectReport], *, generated_note: str = "") -> str:
    reports = list(reports)
    total = len(reports)
    in_scope = sum(1 for r in reports if r.data_scope.verdict in ("in_scope", "likely_in_scope"))
    adopting = sum(1 for r in reports if r.adoption.level in ("active", "emerging"))
    ungoverned = sum(1 for r in reports if r.governance.status in ("none_found", "uncertain"))
    building = sum(1 for r in reports if r.adoption.strong_hiring)

    rows = "\n".join(_row(i + 1, r) for i, r in enumerate(reports))
    lead = generated_note or f"{total} US organizations ranked by fit for Questa AI."

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prospect Scout for Questa</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      {_SHIELD}
      <div class="name">Questa AI<small>Prospect Scout</small></div>
    </div>
    <span class="tag">Live run</span>
    <span class="spacer"></span>
    <button class="tbtn" id="theme" type="button" aria-label="Toggle colour theme"><span id="themeIcon">◐</span><span id="themeLabel">Theme</span></button>
  </header>

  <section class="recipe">
    <div class="lead"><b>{_esc(lead)}</b> Scored on regulated-data exposure, active AI adoption, and the absence of an AI-governance owner — passive OSINT, a governance gap is a signal to verify, not proof.</div>
    <div class="chips">
      <span class="qchip"><span class="dot"></span>Regulated data · HIPAA/GLBA/state</span>
      <span class="qchip"><span class="dot"></span>Active AI adoption</span>
      <span class="qchip"><span class="dot"></span>No governance owner</span>
      <span class="qchip trig"><span class="dot"></span>Trigger: building GenAI</span>
    </div>
  </section>

  <section class="stats" aria-label="Run summary">
    <div class="stat"><div class="k">{total}</div><div class="l">Companies run</div></div>
    <div class="stat"><div class="k ac">{in_scope}</div><div class="l">In regulated scope</div></div>
    <div class="stat"><div class="k">{adopting}</div><div class="l">Actively adopting AI</div></div>
    <div class="stat"><div class="k">{ungoverned}</div><div class="l">No governance owner</div></div>
    <div class="stat"><div class="k hot">{building}</div><div class="l">Building GenAI</div></div>
  </section>

  <div class="toolbar">
    <div class="filters" role="group" aria-label="Filter prospects">
      <button class="fbtn" data-filter="all" aria-pressed="true">All</button>
      <button class="fbtn" data-filter="hifi" aria-pressed="false">High fit</button>
      <button class="fbtn" data-filter="chatbot" aria-pressed="false">Chatbot exposed</button>
      <button class="fbtn" data-filter="genai" aria-pressed="false">Building GenAI</button>
    </div>
    <span class="count" id="count"></span>
  </div>

  <div class="list">
{rows}
  </div>
  <div class="empty">No prospects match this filter.</div>

  <div class="legend" aria-label="Signal legend">
    <span><i style="background:var(--hot)"></i>Opportunity / buying trigger</span>
    <span><i style="background:var(--warn)"></i>Unclear — verify</span>
    <span><i style="background:var(--good)"></i>Already covered</span>
    <span><i style="background:var(--accent)"></i>Regulated scope</span>
  </div>

  <footer>
    <span class="hd">Real signals, live sources.</span>
    <span>Regulated-data scope from <b>NAICS</b> + size (EDGAR-buildable). AI adoption from live <b>LinkedIn job postings</b> (Bright Data SERP) and a passive <b>homepage</b> read for advertised AI + chatbot widgets. Governance owner from live <b>web search</b> (<code>site:linkedin.com/in …</code>). Findings map each signal to its US regulation, a Questa product, and a talking point.</span>
    <span><b>Note:</b> the governance signal under-detects a company's own owner via public search, so most read <i>no owner — verify</i>; and “building GenAI” is the buying trigger the run catches in passing.</span>
  </footer>
</div>
<script>{_JS}</script>
</body>
</html>"""
