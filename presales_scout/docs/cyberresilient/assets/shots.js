const { chromium } = require('playwright');
const path = require('path');

const DIR = '/tmp/claude-0/-home-user-vols/d17c81fd-1a52-5e62-9a28-cf6325102779/scratchpad';
const jobs = [
  ['cr_objective_layer.html', 'figure',        'img_objlayer.png'],
  ['cr_blueprint.html',       'figure >> nth=0','img_figA.png'],
  ['cr_blueprint.html',       'figure >> nth=1','img_figB.png'],
  ['cr_value_case.html',      '.vs',           'img_contrast.png'],
  ['cr_value_case.html',      '#bench',        'img_bench.png'],
];

(async () => {
  let browser;
  try {
    browser = await chromium.launch();
  } catch (e) {
    browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  }
  const ctx = await browser.newContext({
    colorScheme: 'light',
    viewport: { width: 1040, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();
  for (const [file, sel, out] of jobs) {
    await page.goto('file://' + path.join(DIR, file), { waitUntil: 'networkidle' });
    await page.waitForTimeout(350);
    const el = page.locator(sel).first();
    await el.screenshot({ path: path.join(DIR, out) });
    const box = await el.boundingBox();
    console.log(out, Math.round(box.width) + 'x' + Math.round(box.height));
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
