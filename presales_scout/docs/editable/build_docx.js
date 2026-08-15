const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, PageBreak,
} = require('docx');
const fs = require('fs');

const CONTENT_W = 9360; // US Letter, 1" margins
const HFILL = 'E7EEF5';

const P = (text, opts = {}) => new Paragraph({ children: [new TextRun({ text, ...opts })], spacing: { after: 120 }, ...(opts.p || {}) });
const runs = (arr, after = 120) => new Paragraph({ children: arr, spacing: { after } });
const H1 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1, spacing: { before: 240, after: 120 } });
const H2 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 } });
const H3 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_3, spacing: { before: 160, after: 80 } });
const bullet = (text, lvl = 0) => new Paragraph({ children: [new TextRun({ text, size: 21 })], bullet: { level: lvl }, spacing: { after: 60 } });
const brk = () => new Paragraph({ children: [new PageBreak()] });
const note = (text) => new Paragraph({ children: [new TextRun({ text, italics: true, size: 20, color: '55616F' })], spacing: { after: 120 }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: '0D6E8C', space: 12 } } });

function cell(text, { w, bold = false, size = 18, fill } = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: fill ? { type: ShadingType.CLEAR, color: 'auto', fill } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ children: [new TextRun({ text: String(text), bold, size })] })],
  });
}
function table(headers, rows, widths) {
  const head = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => cell(h, { w: widths[i], bold: true, size: 17, fill: HFILL })),
  });
  const body = rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, { w: widths[i] })) }));
  return new Table({ columnWidths: widths, width: { size: CONTENT_W, type: WidthType.DXA }, rows: [head, ...body] });
}

const kids = [];

// ---- cover ----
kids.push(new Paragraph({ text: 'Cyber Defencely', heading: HeadingLevel.TITLE, spacing: { after: 60 } }));
kids.push(runs([new TextRun({ text: 'Pre-sales engine — the package, in editable form', size: 28, color: '0A556D' })], 200));
kids.push(P('This document contains the text of the seven pages so you can read and edit it. The interactive versions (charts, the flow diagram, the navigable deck, light/dark theming) are the published artifacts. Edit here, then tell me the changes and I will update the artifacts — the links stay the same.', { size: 21 }));
kids.push(P('Contents: 1) Prospect Brief  2) How It Works  3) Sources & Method  4) Getting It Live  5) The Score-to-Fix Pattern  6) The Playbook (7 use cases).', { size: 21, italics: true, color: '55616F' }));
kids.push(brk());

// ==================== 1. PROSPECT BRIEF ====================
kids.push(H1('1 · Prospect Brief'));
kids.push(runs([new TextRun({ text: 'Ten Swedish firms that are legally obligated — and not ready.', bold: true, size: 26 })]));
kids.push(P("Sweden's Cybersecurity Act (Cybersäkerhetslagen, SFS 2025:1506) went live 15 January 2026. It puts energy and transport operators squarely in NIS2 scope. This brief points at ten of them, ranks each on public risk signals, and surfaces the IT/OT suppliers they're all dependent on.", { size: 21 }));
kids.push(H3('NIS2, in brief'));
kids.push(bullet('In force since January 2026.'));
kids.push(bullet('18 sectors, including energy & transport.'));
kids.push(bullet('Applies at ≥50 staff OR €10M turnover / balance sheet.'));
kids.push(bullet('Entity-wide scope; management is personally accountable.'));

kids.push(H2('The 10 prospects, ranked by fit'));
kids.push(P('All in NIS2 scope · 8 with weak email security · 10 with no clear CISO · 5 actively hiring a CISO (the buying trigger).', { size: 20, italics: true, color: '55616F' }));
kids.push(table(
  ['#', 'Company', 'Sector', 'Size', 'Email', 'CISO', 'Hiring', 'Fit'],
  [
    ['1', 'Skellefteå Kraft AB', 'Energy', '~700', 'weak', 'none', '—', '100'],
    ['2', 'Mälarenergi AB', 'Energy', '~750', 'weak', 'none', 'YES', '100'],
    ['3', 'Göteborg Energi AB', 'Energy', '~1,150', 'weak', 'none', 'YES', '100'],
    ['4', 'Öresundskraft AB', 'Energy', '~450', 'weak', 'none', 'YES', '100'],
    ['5', 'Stena Line Scandinavia AB', 'Transport', '~5,000', 'weak', 'none', '—', '100'],
    ['6', 'Jämtkraft AB', 'Energy', '~350', 'weak', 'unclear', '—', '85'],
    ['7', 'Tekniska verken i Linköping AB', 'Energy', '~1,000', 'weak', 'unclear', 'YES', '85'],
    ['8', 'Transdev Sverige AB', 'Transport', '~6,000', 'weak', 'unclear', 'YES', '85'],
    ['9', 'Green Cargo AB', 'Transport', '~1,800', 'strong', 'none', '—', '75'],
    ['10', 'Nobina Sverige AB', 'Transport', '~11,000', 'strong', 'unclear', '—', '60'],
  ],
  [520, 2400, 1150, 1050, 1000, 1080, 900, 1260]
));
kids.push(P(''));
kids.push(note('The signal that matters most: half are actively recruiting a CISO or infosec lead right now — they have admitted the gap and have the budget. The ideal moment to walk in with CISO-as-a-Service.'));

kids.push(H2("Their suppliers are their liability too"));
kids.push(P('NIS2 Art. 21(2)(d) makes each firm accountable for its suppliers’ security. Two layers are public: the ICT/OT vendors they procure (EU tender records), and the third-party code running in their websites.', { size: 21 }));
kids.push(H3('NIS2-critical contracts outsourced (public procurement / TED)'));
kids.push(table(['Buyer', 'Critical contracts'],
  [['Göteborg Energi', '35'], ['Öresundskraft', '27'], ['Skellefteå Kraft', '27'], ['Tekniska verken', '14'], ['Mälarenergi', '11'], ['Jämtkraft', '10']],
  [6360, 3000]));
kids.push(P(''));
kids.push(H3('Third-party code in their sites (external suppliers)'));
kids.push(table(['Company', 'External suppliers'],
  [['Stena Line', '27'], ['Green Cargo', '23'], ['Transdev', '18'], ['Nobina', '13'], ['Öresundskraft', '13'], ['Göteborg Energi', '13']],
  [6360, 3000]));

kids.push(H2('The big suppliers, embedded everywhere (bonus)'));
kids.push(P('The named suppliers pulled from award records are huge prospects in their own right. Each supplies dozens of public bodies, so every one of those buyers now demands NIS2 assurance from them. Compliance pressure flows downhill.', { size: 21 }));
kids.push(table(['Supplier', 'Role', 'Public-sector reach'],
  [
    ['Atea Sverige AB', 'IT services & hardware', '49 buyers'],
    ['Advania Sverige AB', 'IT services', '41 buyers'],
    ['ABB Power Grids Sweden AB', 'OT / grid control', 'OT supplier'],
    ['Ramböll Management Consulting AB', 'IT & advisory', '37 buyers'],
  ],
  [3000, 3860, 2500]));

kids.push(H3('Supplier spotlight — Atea Sverige AB (verified live)'));
kids.push(bullet('SPF: strong (−all).'));
kids.push(bullet('DMARC: p=none — deployed but NOT enforced (domain still spoofable).'));
kids.push(bullet('MTA-STS: missing.'));
kids.push(bullet('NIS2: in scope (managed-IT provider / MSP).'));
kids.push(P('The opener: Atea already collects DMARC reports but left the policy at monitor-only. "You’re one config change from p=reject — want help closing the last step safely?" A security vendor with an unenforced DMARC takes that call.', { size: 21 }));
kids.push(note('Two funnels for the price of one. Sell NIS2 readiness to the utilities — and to the IT/OT suppliers they depend on. And every deal you close feeds back — turning your proprietary data into an actionable competitive advantage no rival list can copy.'));
kids.push(brk());

// ==================== 2. HOW IT WORKS ====================
kids.push(H1('2 · How It Works'));
kids.push(runs([new TextRun({ text: 'One pipeline, from raw registry to a self-sharpening lead engine.', bold: true, size: 26 })]));
kids.push(P('The engine turns a registry of Swedish firms into ranked, context-mapped prospects using only passive public signals. The value isn’t the scraper — it’s that the signal plugs into your GTM stack and gets sharper every time you close a deal.', { size: 21 }));
kids.push(H2('The flow'));
kids.push(P('Registry (Roaring / allabolag)  →  presales_scout engine  →  Clay  →  UpliftIQ  →  Cyber Defencely', { bold: true, size: 22 }));
kids.push(bullet('Registry → candidates: every energy/transport firm in scope, by SNI code + size.'));
kids.push(bullet('Engine → leads + vulns: passive signals (NIS2, email, CISO+hiring, attack surface, suppliers), each mapped to its NIS2/ISO obligation and the service that closes it.'));
kids.push(bullet('Clay → enriched row: waterfall enrichment adds contacts and emails.'));
kids.push(bullet('UpliftIQ → prioritised: scores and ranks leads + vulnerabilities.'));
kids.push(bullet('Cyber Defencely → CRM + real assessments: delivery produces ground truth.'));
kids.push(H2('The feedback loop = the moat'));
kids.push(P('Every real assessment is ground truth that retrains which signals predict a real gap and a won deal — on data only Cyber Defencely holds. Each seam between stages is clean JSON/CSV, so no single box is the lock-in; the loop closing is — this is how you turn your proprietary data into an actionable competitive advantage.', { size: 21 }));
kids.push(H3('Five stages'));
kids.push(bullet('Stage 0 — Harvest: registry → in-scope firms by SNI + size.'));
kids.push(bullet('Stage 1–4 — Enrich: passive signals per firm.'));
kids.push(bullet('Stage 5 — Context-map: each finding → NIS2 measure, ISO control, severity, service.'));
kids.push(bullet('Stage 6 — Integrate: one JSON call feeds Clay + UpliftIQ.'));
kids.push(bullet('Stage 7 — Close the loop: assessment outcomes retrain the fit model.'));
kids.push(brk());

// ==================== 3. SOURCES & METHOD ====================
kids.push(H1('3 · Sources & Method'));
kids.push(runs([new TextRun({ text: 'Every number has a receipt.', bold: true, size: 26 })]));
kids.push(P('Passive & public, always: no port scans, no vulnerability probes, no authenticated access, nothing the target sees as directed at them.', { size: 21, italics: true }));
kids.push(H2('The provenance ledger (8 signals)'));
const sigs = [
  ['NIS2 scope', 'SNI code → sector map + public size figures', 'Logic automated; SNI/size hand-verified this run', 'Medium', 'A screening heuristic, not a legal determination.'],
  ['Email security', 'Live public DNS over DNS-over-HTTPS (dns.google/resolve)', 'Fully live, free', 'High', 'Measures domain spoofability, not inbound filtering.'],
  ['CISO / hiring', 'Public web + LinkedIn search (Bright Data SERP-ready)', 'Pluggable (needs key)', 'Medium', 'Absence is a confidence signal, not proof. The hiring req is the high-confidence signal.'],
  ['Attack surface', 'HTTP headers · crt.sh CT logs · Shodan InternetDB', 'Automated, free', 'High', 'Read-only; a takeover "candidate" is flagged, never asserted.'],
  ['Suppliers — digital', "MX/NS records + the site's own content-security-policy", 'Automated', 'High', 'Only externally observable suppliers. 147 mapped.'],
  ['Suppliers — procurement', 'TED (api.ted.europa.eu) + openprocurements.com', 'Automated', 'High', 'Linkage is high-confidence; the title-keyword category guess is weak. 124 + 63 named.'],
  ['Big suppliers as leads', 'Award records → buyer count; ownership-verified domains', 'Automated, accuracy-gated', 'High', 'Reach counted from records; a noisier list was withheld until accuracy was fixed.'],
  ['Context mapping', 'kb/crosswalk.yaml (curated) + grounded LLM prose', 'Automated', 'High', "Framework IDs come from the fixed table only; the LLM can't invent a control ID."],
];
for (const [name, src, auto, conf, lim] of sigs) {
  kids.push(runs([new TextRun({ text: name, bold: true, size: 22 })], 40));
  kids.push(bullet(`Source: ${src}`));
  kids.push(bullet(`Automation: ${auto} · Confidence: ${conf}`));
  kids.push(bullet(`Limit: ${lim}`));
}
kids.push(H2('The one dependency worth naming'));
kids.push(P('Everything is automated and free except candidate generation. That seam is now built (collectors/registry/): a pluggable backend harvests the universe by SNI + size — live Roaring, a downloaded allabolag/Bolagsverket/Roaring export, or an offline sample. Plug in Cyber Defencely’s registry access and the 50–100 list generates itself.', { size: 21 }));
kids.push(H2('Data ethics & legal basis'));
kids.push(P('Built passive-and-public by design. It reads records published to the world; it never touches anyone’s systems.', { size: 21, bold: true }));
kids.push(bullet('Personal data (GDPR): the only signal about named people (CISO/hiring) is handled as minimal, retention-limited, legitimate-interest B2B processing — role + company, not a dossier; documented basis; opt-outs honoured. Reading search results rather than scraping LinkedIn stays clear of platform terms. Public ≠ unregulated — confirm with a data-protection advisor before scaling.'));
kids.push(bullet('Benchmarking others: peer comparisons in a client deliverable keep peers anonymised (Peer A–J) and the score method-based and factual. Computed, not asserted.'));
kids.push(bullet('Screening, not adjudication: the NIS2 verdict is a heuristic; "no visible CISO" is a signal to verify, never a published claim about a person.'));
kids.push(note('Not legal advice — an accurate description of what the tool reads, so you and a data-protection advisor can confirm how it’s used. A short GDPR sanity-check on the personal-data handling is the one worthwhile step before scale.'));
kids.push(brk());

// ==================== 4. GETTING IT LIVE ====================
kids.push(H1('4 · Getting It Live'));
kids.push(runs([new TextRun({ text: 'The prototype’s built. Three inputs turn it into a live engine.', bold: true, size: 26 })]));
kids.push(P('All three are yours to provide; none are code. Roughly in priority order.', { size: 21 }));
kids.push(H2('Ask 1 — A company-registry feed (the scale unlock)'));
kids.push(bullet('What: a way to pull every Swedish energy & transport firm ≥50 staff — name, org number, SNI code, size, domain.'));
kids.push(bullet('Why: the single unlock for the 50–100+ list; everything downstream already works.'));
kids.push(bullet('Costs you: a paid registry account/API key, or one filtered export. Minutes, not weeks.'));
kids.push(bullet('Option A — Roaring API (Company Prospecting): client credentials + these fields, filterable by SNI + employees: companyName, orgNumber, sniCode, numberOfEmployees, turnover, status=ACTIVE, website.'));
kids.push(bullet('Option B — allabolag / Bolagsverket export: a CSV filtered to energy+transport SNI, ≥50 staff, with columns name, orgnr, SNI, anställda, omsättning, webbplats.'));
kids.push(H2('Ask 2 — 30 minutes on the crosswalk'));
kids.push(bullet('What: confirm the finding → NIS2 measure → ISO control → your service → price tier mapping reflects how you sell.'));
kids.push(bullet('Why: this table is the part a competitor can’t copy from a repo — it’s your commercial model.'));
kids.push(bullet('Costs you: one 30-minute call.'));
kids.push(H2('Ask 3 — One known prospect + a past engagement or two'));
kids.push(bullet('What: one firm you know well to sanity-check the fit score; the anonymised outcome of 1–2 past assessments.'));
kids.push(bullet('Why: the first data points in the loop that becomes the real moat.'));
kids.push(bullet('Costs you: a short conversation; outcomes can be anonymised.'));
kids.push(H3('Nice-to-have, once live'));
kids.push(bullet('Clay + UpliftIQ access — to wire the /enrich endpoint into the enrichment + scoring stack.'));
kids.push(bullet('One CRM field for "assessment outcome" — the pipe that feeds Ask 3 back automatically.'));
kids.push(note('The engine isn’t the moat — it’s leverage. The moat is operating it first, in the NIS2 window that’s open now, and letting your own delivery data compound. That’s the whole play: turn your proprietary data into an actionable competitive advantage.'));
kids.push(brk());

// ==================== 5. SCORE-TO-FIX PATTERN ====================
kids.push(H1('5 · The Score-to-Fix Pattern'));
kids.push(runs([new TextRun({ text: 'Give away the score. Charge for the fix.', bold: true, size: 26 })]));
kids.push(bullet('The score = the wedge (outside-in): computed from commodity signals, so you show up uninvited with a provocative number. Free.'));
kids.push(bullet('The context map = the layer you build: the crosswalk from signal → meaning → action. Domain expertise, not compute.'));
kids.push(bullet('The fix = the product (inside-out): UpliftIQ ranks on the client’s proprietary data. Paid, and compounding.'));
kids.push(H2('Same shape, three instances'));
kids.push(table(['Vertical', 'The hook — a score', 'Built from (commodity)', 'The fix — on their data'],
  [
    ['Cyber (Cyber Defencely)', 'NIS2 / security readiness', 'DNS, CT logs, procurement, job posts', '"Assess these 12 prospects, in this order"'],
    ['Retail — assortment (e.g. La-Z-Boy)', 'Assortment-fit score per store', 'demographics, competitor SKUs, demand, reviews', '"Reallocate this inventory to these showrooms"'],
    ['Retail — pricing', 'Margin-left-on-table score', 'competitor prices, local income, promo cadence', '"Reprice these 40 SKUs to this curve"'],
  ],
  [2000, 2200, 2560, 2600]));
kids.push(H2('Two rules that keep a score a wedge'));
kids.push(bullet('It’s computable before they’re a customer. If it needs their internal data, it’s a project, not a wedge.'));
kids.push(bullet('It’s a confidence signal, not a verdict. Overclaim and a sharp buyer catches you. Certainty comes from the fix.'));
kids.push(note('We give you the score that shows the gap. We’re the engine that turns your data into the fix — an actionable competitive advantage.'));
kids.push(brk());

// ==================== 6. PLAYBOOK ====================
kids.push(H1('6 · The Playbook — seven use cases'));
kids.push(P('The same engine (outside-in score + context map + proprietary data) resnaps onto the whole customer lifecycle. What changes is whose data feeds it and which decision it drives.', { size: 21 }));
kids.push(table(['#', 'Play', 'Runs on', 'What it is'],
  [
    ['1', 'Pre-sales & outreach', 'signals (wedge)', 'Rank prospects'],
    ['2', 'Actionable ranked recos', 'client data', 'Assessment → prioritised roadmap'],
    ['3', 'Continuous monitoring', 'signals', 'Drift alerts → recurring revenue'],
    ['4', 'Supplier risk as a service', 'client data', 'Score their supply chain + lead-gen'],
    ['5', 'Competitive benchmarking', 'your data (moat)', 'Peer percentile'],
    ['6', 'Board & compliance pack', 'client data', 'Framework-mapped scorecard'],
    ['7', 'Scoping & pricing', 'signals', 'Quote & staff faster'],
  ],
  [520, 2740, 2100, 4000]));
kids.push(H2('Play 5 — Competitive benchmarking (anchor, real data)'));
kids.push(P('10 Swedish energy & transport operators ranked on external security hygiene. Score = 100 minus a severity-weighted penalty per observable weakness — mechanically computed (presales_scout.benchmark), no tuning knobs. The view you’d hand a prospect: "you’re bottom of your peer group."', { size: 21 }));
kids.push(table(['Rank', 'Company', 'Score', 'Band'],
  [
    ['1', 'Green Cargo AB', '78', 'strong'],
    ['2', 'Mälarenergi AB', '58', 'strong'],
    ['3', 'Stena Line Scandinavia AB', '46', 'strong'],
    ['4', 'Göteborg Energi AB', '42', 'mid'],
    ['5', 'Öresundskraft AB', '42', 'mid'],
    ['6', 'Nobina Sverige AB', '36', 'mid'],
    ['7', 'Transdev Sverige AB', '36', 'mid'],
    ['8', 'Tekniska verken i Linköping AB', '26', 'exposed'],
    ['9', 'Jämtkraft AB', '24', 'exposed'],
    ['10', 'Skellefteå Kraft AB', '2', 'exposed  ← the prospect'],
  ],
  [900, 3660, 1200, 3600]));
kids.push(P('Only Cyber Defencely can draw this line — it needs the cross-client dataset no competitor holds. The firm at the bottom, Skellefteå Kraft (verified live at DMARC p=none), is also the #1-ranked prospect from Play 1.', { size: 21 }));
kids.push(H2('The other plays, in one line each'));
kids.push(bullet('Play 2 — Ranked recos: after an assessment, order every finding by severity × effort, mapped to the obligation and the service. The client sees a plan, not a 40-page PDF.'));
kids.push(bullet('Play 3 — Continuous monitoring: keep the passive engine running on clients; alert on drift (DMARC regressed, new exposed subdomain, new supplier). Turns a one-off into a subscription — and NIS2 requires continuous risk management.'));
kids.push(bullet('Play 4 — Supplier risk as a service: score the client’s own suppliers (they’re liable under 21(2)(d)); each flagged vendor is a lead back into Play 1.'));
kids.push(bullet('Play 6 — Board & compliance pack: management is personally accountable under NIS2; the framework-mapped scorecard is a recurring reporting deliverable.'));
kids.push(bullet('Play 7 — Scoping & pricing: the pre-engagement score predicts findings, effort, and package, so you quote and staff faster.'));
kids.push(note('Seven plays. One data asset that compounds. Turn your proprietary data into an actionable competitive advantage. Instance one is running today.'));

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: 'Calibri', size: 22 } },
    },
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    children: kids,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2] || 'cyber_defencely_package.docx', buf);
  console.log('wrote', process.argv[2]);
});
