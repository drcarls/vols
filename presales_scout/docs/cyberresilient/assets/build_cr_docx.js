const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  ImageRun, BorderStyle, PageBreak,
} = require('docx');
const fs = require('fs');

const DIR = '/tmp/claude-0/-home-user-vols/d17c81fd-1a52-5e62-9a28-cf6325102779/scratchpad';
const P = (text, opts = {}) => new Paragraph({ children: [new TextRun({ text, ...opts })], spacing: { after: 120 } });
const runs = (arr, after = 120) => new Paragraph({ children: arr, spacing: { after } });
const H1 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1, spacing: { before: 260, after: 120 } });
const H2 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 90 } });
const bullet = (text) => new Paragraph({ children: [new TextRun({ text, size: 21 })], bullet: { level: 0 }, spacing: { after: 60 } });
const brk = () => new Paragraph({ children: [new PageBreak()] });
const note = (text) => new Paragraph({ children: [new TextRun({ text, italics: true, size: 20, color: '55616F' })], spacing: { after: 120 }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: '4B56B3', space: 12 } } });

// wide image, fit to content width (620px), preserve aspect from source px box
function img(file, srcW, srcH, w = 620) {
  const h = Math.round(w * srcH / srcW);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 40 },
    children: [new ImageRun({ type: 'png', data: fs.readFileSync(`${DIR}/${file}`), transformation: { width: w, height: h } })],
  });
}
const cap = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: t, italics: true, size: 18, color: '8B8DA8' })] });

const k = [];

// cover
k.push(new Paragraph({ text: 'CyberResilient × UpliftIQ', heading: HeadingLevel.TITLE, spacing: { after: 60 } }));
k.push(runs([new TextRun({ text: 'The value case — with diagrams', size: 28, color: '3A3F96' })], 200));
k.push(P('CyberResilient sells NIS2 monitoring and compliance recommendations. UpliftIQ is a decision-optimization platform — it makes those recommendations objective, and sharper every cycle, inside your own walls. This document covers what each does, then the ways they work together.', { size: 21 }));
k.push(note('This combines the CyberResilient pieces into one editable document; the diagrams are rendered from the interactive versions. Edit here, tell me the changes, and I update the artifacts — the links stay the same.'));
k.push(brk());

// 1
k.push(H1('1 · What CyberResilient does'));
k.push(runs([new TextRun({ text: 'Sells NIS2 monitoring & compliance recommendations', bold: true, size: 24 })]));
k.push(P('You help essential and important entities meet the Swedish Cybersecurity Act: monitor their NIS2 posture, surface where they fall short, and recommend what to fix — with reporting a board and a regulator can trust.', { size: 21 }));
k.push(bullet('Maturity monitoring — track NIS2 posture and progress over time.'));
k.push(bullet('Compliance recommendations — what to fix, mapped to NIS2 (and ISO 27001 / NIST CSF / CIS).'));
k.push(bullet('Risk register, continuity, audit-ready reporting — the workflow around the score.'));
k.push(P('The strength — and the ceiling — is that it works from what the customer reports. Fast and clean, but self-declared and gated on the customer engaging.', { size: 21, color: '575A72' }));

// 2
k.push(H1('2 · What UpliftIQ does'));
k.push(runs([new TextRun({ text: 'A decision-optimization platform', bold: true, size: 24 })]));
k.push(P('UpliftIQ doesn’t score once and stop. It builds a history of decisions and their outcomes, and refines its recommendations over time — so every cycle it gets better at which action to recommend, for whom, and in what order. It runs inside your environment, and treats objective observed signals (DNS, mail policy, exposure) as one of its highest-value inputs — grounding decisions in reality, not self-report.', { size: 21 }));
k.push(P('The loop: Inputs → Decide → Outcome → Refine.', { bold: true, size: 21 }));
k.push(bullet('Inputs — the customer’s self-report plus objective observed evidence.'));
k.push(bullet('Decide — recommend and prioritize the next actions, ranked.'));
k.push(bullet('Outcome — capture what happened: did it close, did it work?'));
k.push(bullet('Refine — history sharpens the next recommendation, better every cycle.'));
k.push(P('The compounding asset isn’t a scan — it’s the decision-and-outcome history. The more it runs, the better the recommendations, and that history is yours alone.', { size: 21, color: '575A72' }));

// 3 observed layer + image
k.push(H1('3 · The observed layer'));
k.push(P('The observed input adds what a questionnaire can’t reach — verified externally, no input from the customer. It works three ways at once: a proactive outbound list, a free front door, and an in-product evidence layer that strengthens every module.', { size: 21 }));
k.push(img('img_objlayer.png', 896, 377));
k.push(cap('Two sources, one platform: the self-report says what the customer believes; the observed score says what’s true.'));

// 4 cases
k.push(H1('4 · How they work together — the cases'));
const cases = [
  ['1 · Outbound outreach (drives customers)',
   'UpliftIQ scores NIS2-scope orgs in bulk; the weakest are a prioritized outbound list. You reach out with the org’s own observed score as the opener, feeding sign-ups.',
   'e.g. the run’s bottom three: Skellefteå Kraft 2 · Jämtkraft 24 · Tekniska verken 26.'],
  ['2 · Enrich & fact-check a customer’s data (within bounds)',
   'Put observed evidence next to a customer’s self-report to verify or challenge it — turning self-declared monitoring into evidence-checked monitoring. Bounded to a consenting customer’s own domains/assets, never covert.',
   'e.g. a self-assessment rates email “adequate”; observed shows Skellefteå Kraft at DMARC p=none — spoofable, verified live.'],
  ['3 · Benchmark customers vs. anonymized data (moat)',
   'Cluster customers by sector, size, and maturity, and show each where they stand against anonymized peers — a benchmark only you can produce, because it needs your corpus.',
   'e.g. 10 operators — Green Cargo 78 → Skellefteå Kraft 2, median 39.'],
  ['4 · Prioritize the fix under constraints (moat)',
   'Given a customer’s budget and staff, recommend the optimal set of actions to close the most NIS2 gaps — learned from what actually worked across similar orgs, refined each cycle.',
   'e.g. “with 2 FTE-weeks: enforce DMARC → publish MTA-STS → assign a security owner.”'],
  ['5 · Continuous monitoring & drift alerts',
   'Re-score passively between assessments and alert on regressions — new exposure, a weakened policy, a new supplier. NIS2 monitoring made literal and always-on.',
   'e.g. Stena Line & Transdev have no DMARC record today — flag the moment it changes.'],
  ['6 · Supplier / supply-chain risk (compliance + leads)',
   'NIS2 Art. 21(2)(d) makes your customer accountable for its suppliers. Score their supply chain from public signals — and each flagged supplier is also a Case 1 lead. No new capability: the engine already maps suppliers.',
   'e.g. even Atea — a major Swedish IT supplier — runs DMARC p=none (verified); the run mapped 147 digital + 124 procurement supplier links across 10 orgs.'],
  ['7 · Sector / regulator intelligence (new line)',
   'Aggregate anonymized posture across a sector into intelligence sold up — to MSB, a regulator, a ministry. Your government roots make you the natural provider.',
   'e.g. 8 of 10 Swedish energy/transport operators run unenforced DMARC — a sector-level finding.'],
  ['8 · Assurance / attestation (new line · output of Case 2)',
   'A customer at a maturity level whose observed posture checks out earns a verifiable “resilience verified” attestation — evidence-backed, not self-declared. Same observed-vs-self-report check as Case 2, packaged as a badge they show third parties: partners, insurers, procurement.',
   'A monetizable output and a wedge into cyber-insurance underwriting — insurers want exactly this objective signal.'],
  ['9 · Internal GTM intelligence (different bucket · internal)',
   'Not a customer feature — point the same engine at your own funnel. UpliftIQ scores which trials convert, which customers are expansion-ready, which are churn risks: decision optimization applied to your business.',
   'Cases 1–8 are what you sell; this is how you run. Same engine, pointed inward.'],
];
for (const [t, hw, ex] of cases) {
  k.push(H2(t));
  k.push(P(hw, { size: 21 }));
  k.push(runs([new TextRun({ text: ex, italics: true, size: 19, color: '3A3F96' })], 120));
}

// 5 blueprint A
k.push(H1('5 · Build four, aim many'));
k.push(P('The nine use cases aren’t nine things to build. They’re four core capabilities — an observed-signal input (Observe, Reconcile) feeding UpliftIQ’s decision optimization (Cluster+Benchmark, Recommend+Optimize), which refines over time.', { size: 21 }));
k.push(img('img_figA.png', 896, 687));
k.push(cap('Four capabilities → nine use cases. The two moat-grade capabilities run on your decision-and-outcome history.'));

// 6 blueprint B
k.push(H1('6 · Runs on your side'));
k.push(P('UpliftIQ deploys inside your environment, not as a service you ship data to. Only two things cross the boundary: public signals in, and derived, anonymized results out. Customer data and the decision history stay put.', { size: 21 }));
k.push(img('img_figB.png', 896, 497));
k.push(cap('The intelligence comes to the data, not the other way around — sovereignty kept.'));

// 7 proof
k.push(H1('7 · Grounded in a real run'));
k.push(P('The examples above are from a real run: 10 Swedish energy & transport operators, scored from public signals alone, Aug 2026.', { size: 21 }));
k.push(bullet('8 of 10 — weak email security.'));
k.push(bullet('8 of 10 — DMARC not enforced.'));
k.push(bullet('10 of 10 — no visible CISO.'));
k.push(bullet('39 — median observed score.'));
k.push(P('The gap, on one firm:', { bold: true, size: 21 }));
k.push(img('img_contrast.png', 756, 148));
k.push(P('The observed peer benchmark:', { bold: true, size: 21 }));
k.push(img('img_bench.png', 756, 291));
k.push(cap('Score = 100 − a severity-weighted penalty per observable weakness, mechanically computed. Observed data is real; the self-reported column and peer figures are illustrative until integrated with your platform data.'));

// 8 sovereignty + close
k.push(H1('8 · The bottom line'));
k.push(P('All of it, without giving up sovereignty. UpliftIQ runs inside your Sweden-only environment; it reads only public records, never touches a customer’s systems, and raw customer data never leaves the boundary — public signals in, anonymized results out.', { size: 21 }));
k.push(note('You already tell customers what they believe. Together, you tell them what’s true — and get better at what to fix, every cycle — without a byte leaving your walls.'));
k.push(P('Notes: CyberResilient’s offering is summarised from public information; some internals are inferred. The observed engine and its scoring are real and already run end-to-end. Cross-customer / decision-history figures become real once integrated with your platform. Passive & public only; Case 2 is bounded to a consenting customer’s own assets, and the benchmark/sector cases need consent plus a minimum cluster size (k-anonymity) so no output re-identifies an organisation.', { size: 18, color: '575A72' }));

const doc = new Document({
  styles: { default: { document: { run: { font: 'Calibri', size: 22 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    children: k,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(`${DIR}/cyberresilient_value_case.docx`, buf); console.log('wrote docx', buf.length); });
