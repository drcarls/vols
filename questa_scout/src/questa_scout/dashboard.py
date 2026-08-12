from __future__ import annotations

"""Render a ranked prospect list into a self-contained HTML dashboard --
the "Prospect Scout for Questa" view. No external assets, theme-aware,
generated straight from ProspectReport data so it always matches the CSV.
"""

import html
from typing import Iterable

from .context_map import derive_findings
from .models import ProspectReport

_CSS = """
:root{
  --bg:#F5F6FA; --surface:#FFFFFF; --surface-2:#F0F2F7;
  --ink:#171B24; --muted:#5A6172; --border:#E3E6EE;
  --accent:#5A4FE0; --accent-soft:#ECEAFB; --accent-ink:#FFFFFF;
  --live:#DE6B1F; --live-soft:#FBEBDD;
  --crit:#D6403A; --high:#C9791A; --med:#5A6172;
  --phi:#0E8F84; --financial:#3457C4; --legal:#8A4FB0; --pii:#5A6172;
  --shadow:0 1px 2px rgba(20,24,34,.06),0 8px 24px rgba(20,24,34,.05);
}
:root:not([data-theme="light"]){ }
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#101219; --surface:#191C24; --surface-2:#20242E;
    --ink:#EEF0F6; --muted:#9AA1B2; --border:#2A2F3B;
    --accent:#8F88F2; --accent-soft:#23233A; --accent-ink:#11121A;
    --live:#EE8A44; --live-soft:#2E2418;
    --crit:#EA6A63; --high:#E0A24A; --med:#9AA1B2;
    --phi:#3FB5A8; --financial:#7C97E8; --legal:#B788D6; --pii:#9AA1B2;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 28px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --bg:#101219; --surface:#191C24; --surface-2:#20242E;
  --ink:#EEF0F6; --muted:#9AA1B2; --border:#2A2F3B;
  --accent:#8F88F2; --accent-soft:#23233A; --accent-ink:#11121A;
  --live:#EE8A44; --live-soft:#2E2418;
  --crit:#EA6A63; --high:#E0A24A; --med:#9AA1B2;
  --phi:#3FB5A8; --financial:#7C97E8; --legal:#B788D6; --pii:#9AA1B2;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 28px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--bg);color:var(--ink);
  font-family:"Inter","Helvetica Neue",Helvetica,Arial,system-ui,sans-serif;
  line-height:1.5;font-size:15px;
  -webkit-font-smoothing:antialiased;
}
.mono{font-family:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums}
.wrap{max-width:1060px;margin:0 auto;padding:40px 24px 72px}
header.top{display:flex;flex-direction:column;gap:6px;margin-bottom:28px}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);
  font-weight:700}
h1{font-size:30px;line-height:1.1;margin:2px 0 0;font-weight:800;letter-spacing:-.02em;
  text-wrap:balance}
.sub{color:var(--muted);max-width:64ch}
.meta{color:var(--muted);font-size:12.5px;margin-top:4px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0 8px}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:12px;
  padding:14px 16px;box-shadow:var(--shadow)}
.tile .k{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.tile .v{font-size:26px;font-weight:800;margin-top:4px;letter-spacing:-.02em}
.tile .v small{font-size:13px;font-weight:600;color:var(--muted)}
.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:22px 0 14px}
.controls .lbl{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
  font-weight:700;margin-right:2px}
.chipbtn{font:inherit;font-size:12.5px;cursor:pointer;border:1px solid var(--border);
  background:var(--surface);color:var(--ink);padding:5px 11px;border-radius:999px;transition:.15s}
.chipbtn[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
.chipbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.list{display:flex;flex-direction:column;gap:12px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:16px 18px;box-shadow:var(--shadow);display:grid;
  grid-template-columns:44px 1fr 190px;gap:14px 16px;align-items:start}
.rank{font-weight:800;font-size:15px;color:var(--muted);padding-top:2px}
.rank .n{display:block;font-size:19px;color:var(--ink)}
.head{display:flex;flex-direction:column;gap:2px;min-width:0}
.name{font-size:17px;font-weight:700;letter-spacing:-.01em}
.loc{color:var(--muted);font-size:12.5px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}
.chip{font-size:11.5px;font-weight:600;padding:3px 9px;border-radius:999px;border:1px solid transparent;
  display:inline-flex;align-items:center;gap:5px;line-height:1.4}
.chip .dot{width:6px;height:6px;border-radius:50%}
.chip.data{background:var(--surface-2);border-color:var(--border);color:var(--ink)}
.chip.opening{background:var(--accent-soft);color:var(--accent);border-color:transparent}
.chip.live{background:var(--live-soft);color:var(--live)}
.chip.muted{background:var(--surface-2);color:var(--muted)}
.angle{margin:11px 0 0;font-size:14px;color:var(--ink)}
.angle b{color:var(--accent)}
.finds{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.find{font-size:11px;padding:3px 8px;border-radius:6px;border:1px solid var(--border);
  background:var(--surface-2);display:inline-flex;gap:6px;align-items:center}
.find .sev{width:7px;height:7px;border-radius:2px}
.sev.critical{background:var(--crit)}.sev.high{background:var(--high)}
.sev.medium{background:var(--med)}.sev.low{background:var(--med)}.sev.info{background:var(--med)}
.right{display:flex;flex-direction:column;gap:9px;align-items:stretch}
.score{display:flex;align-items:baseline;gap:7px;justify-content:flex-end}
.score .num{font-size:30px;font-weight:800;letter-spacing:-.02em}
.score .den{color:var(--muted);font-size:12px}
.meter{height:7px;border-radius:999px;background:var(--surface-2);overflow:hidden;border:1px solid var(--border)}
.meter>i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--accent),color-mix(in oklab,var(--accent),var(--live) 35%))}
.prod{font-size:12px;font-weight:700;text-align:center;padding:6px 8px;border-radius:9px;
  border:1px solid var(--border);background:var(--surface-2)}
.prod.blackbox{color:var(--financial)}.prod.developer{color:var(--phi)}.prod.cloud{color:var(--legal)}
.verify{font-size:11.5px;color:var(--muted)}
footer{margin-top:34px;color:var(--muted);font-size:12px;border-top:1px solid var(--border);padding-top:16px}
footer code{font-family:ui-monospace,Menlo,monospace;background:var(--surface-2);padding:1px 5px;border-radius:4px}
.empty{display:none;color:var(--muted);padding:26px;text-align:center;border:1px dashed var(--border);border-radius:12px}
@media(max-width:680px){
  .card{grid-template-columns:38px 1fr;}
  .right{grid-column:1 / -1;flex-direction:row;flex-wrap:wrap;align-items:center;justify-content:space-between}
  .score{justify-content:flex-start}.meter{flex:1 1 160px}
}
"""

_JS = """
(function(){
  var cards=[].slice.call(document.querySelectorAll('.card'));
  var empty=document.querySelector('.empty');
  var state={product:'all',hifi:false};
  function apply(){
    var shown=0;
    cards.forEach(function(c){
      var okP=state.product==='all'||c.dataset.product===state.product;
      var okH=!state.hifi||parseFloat(c.dataset.score)>=80;
      var vis=okP&&okH;c.style.display=vis?'':'none';if(vis)shown++;
    });
    if(empty)empty.style.display=shown?'none':'block';
  }
  document.querySelectorAll('[data-filter]').forEach(function(b){
    b.addEventListener('click',function(){
      var g=b.dataset.filter,v=b.dataset.value;
      if(g==='hifi'){state.hifi=!state.hifi;b.setAttribute('aria-pressed',state.hifi);}
      else{state.product=v;document.querySelectorAll('[data-filter="product"]').forEach(function(o){
        o.setAttribute('aria-pressed',o.dataset.value===v);});}
      apply();
    });
  });
  apply();
})();
"""

_DATA_LABEL = {"PHI": "PHI · HIPAA", "financial": "Financial · GLBA",
               "legal_privileged": "Privileged · state", "consumer_pii": "Consumer PII · state"}
_DATA_CLASS = {"PHI": "phi", "financial": "financial", "legal_privileged": "legal", "consumer_pii": "pii"}
_ADOPTION = {"active": "AI adoption: active", "emerging": "AI adoption: emerging",
             "none": "No AI signal", "unknown": "AI signal: unknown"}
_GOV = {"none_found": "No governance owner", "uncertain": "Governance unclear", "governed": "Has governance owner"}


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _product_key(product: str) -> str:
    p = product.lower()
    if "developer" in p:
        return "developer"
    if "cloud" in p:
        return "cloud"
    return "blackbox"


def _card(rank: int, r: ProspectReport) -> str:
    c = r.company
    ds, ad, gov = r.data_scope, r.adoption, r.governance
    findings = derive_findings(r)
    pkey = _product_key(r.product)

    chips = []
    if ds.data_class and ds.verdict in ("in_scope", "likely_in_scope"):
        chips.append(f'<span class="chip data"><span class="dot" style="background:var(--{_DATA_CLASS.get(ds.data_class,"pii")})"></span>{_esc(_DATA_LABEL.get(ds.data_class, ds.data_class))}</span>')
    elif ds.verdict == "out_of_scope":
        chips.append('<span class="chip muted">Out of scope</span>')
    if ad.level in ("active", "emerging"):
        chips.append(f'<span class="chip live">{_esc(_ADOPTION[ad.level])}</span>')
    else:
        chips.append(f'<span class="chip muted">{_esc(_ADOPTION.get(ad.level, ad.level))}</span>')
    if gov.status in ("none_found", "uncertain"):
        chips.append(f'<span class="chip opening">{_esc(_GOV[gov.status])} · opening</span>')
    else:
        chips.append(f'<span class="chip muted">{_esc(_GOV.get(gov.status, gov.status))}</span>')

    angle = ""
    if findings:
        angle = f'<p class="angle"><b>Angle</b> — {_esc(findings[0].talking_point)}</p>'

    find_html = ""
    if findings:
        items = "".join(
            f'<span class="find mono"><span class="sev {_esc(f.severity)}"></span>{_esc(f.finding_id)}</span>'
            for f in findings[:4]
        )
        find_html = f'<div class="finds">{items}</div>'

    loc = " · ".join(x for x in [c.state, (f"{c.employees:,} emp" if c.employees else "")] if x)
    verify = ('<span class="verify">Verify governance gap before outreach</span>'
              if gov.verify_recommended and gov.status != "governed" else "")

    return f"""<article class="card" data-product="{pkey}" data-score="{r.fit_score:.0f}">
  <div class="rank">#<span class="n">{rank}</span></div>
  <div class="head">
    <div class="name">{_esc(c.name)}</div>
    <div class="loc">{_esc(loc) or "&nbsp;"}</div>
    <div class="chips">{''.join(chips)}</div>
    {angle}
    {find_html}
  </div>
  <div class="right">
    <div class="score"><span class="num mono">{r.fit_score:.0f}</span><span class="den mono">/100</span></div>
    <div class="meter"><i style="width:{max(2, min(100, r.fit_score)):.0f}%"></i></div>
    <div class="prod {pkey}">{_esc(r.product)}</div>
    {verify}
  </div>
</article>"""


def render_dashboard(reports: Iterable[ProspectReport], *, generated_note: str = "") -> str:
    reports = list(reports)
    total = len(reports)
    in_scope = sum(1 for r in reports if r.data_scope.verdict in ("in_scope", "likely_in_scope"))
    hi = sum(1 for r in reports if r.fit_score >= 80)
    ungoverned = sum(1 for r in reports if r.governance.status in ("none_found", "uncertain"))
    adopting = sum(1 for r in reports if r.adoption.level in ("active", "emerging"))

    products = sorted({_product_key(r.product) for r in reports})
    prod_labels = {"blackbox": "Blackbox", "developer": "Developer", "cloud": "Cloud"}
    prod_btns = "".join(
        f'<button class="chipbtn" data-filter="product" data-value="{p}" aria-pressed="false">{prod_labels[p]}</button>'
        for p in products
    )

    cards = "\n".join(_card(i + 1, r) for i, r in enumerate(reports))
    note = f'<div class="meta">{_esc(generated_note)}</div>' if generated_note else ""

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
  <header class="top">
    <div class="eyebrow">Questa AI · Pre-sales</div>
    <h1>Prospect Scout</h1>
    <p class="sub">US organizations ranked by fit for Questa's privacy firewall — scored on regulated-data exposure, active AI adoption, and the absence of an AI-governance owner. Passive OSINT only; a governance gap is a signal to verify, not proof.</p>
    {note}
  </header>

  <section class="tiles" aria-label="summary">
    <div class="tile"><div class="k">Prospects</div><div class="v mono">{total}</div></div>
    <div class="tile"><div class="k">High fit (≥80)</div><div class="v mono">{hi} <small>/ {total}</small></div></div>
    <div class="tile"><div class="k">In regulated scope</div><div class="v mono">{in_scope}</div></div>
    <div class="tile"><div class="k">Actively adopting AI</div><div class="v mono">{adopting}</div></div>
    <div class="tile"><div class="k">No governance owner</div><div class="v mono">{ungoverned}</div></div>
  </section>

  <div class="controls">
    <span class="lbl">Product</span>
    <button class="chipbtn" data-filter="product" data-value="all" aria-pressed="true">All</button>
    {prod_btns}
    <span class="lbl" style="margin-left:10px">View</span>
    <button class="chipbtn" data-filter="hifi" aria-pressed="false">High-fit only</button>
  </div>

  <main class="list">
{cards}
  </main>
  <div class="empty">No prospects match these filters.</div>

  <footer>
    Generated by <code>questa_scout</code> — <code>questa discover --html</code>. Fit = data-scope (qualifier) + AI-adoption (trigger) + governance-gap (opening), sensitivity as tie-break. Findings map each signal to its US regulation, Questa product, and talking point.
  </footer>
</div>
<script>{_JS}</script>
</body>
</html>"""
