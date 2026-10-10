const { chromium } = require('/tmp/claude-0/sk8test/node_modules/playwright');
const U = 'http://localhost:8787/?rgs_url=localhost:8787&sessionID=testsession1';
const log = (...a) => console.log(...a);

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });

  const scen = q => page.evaluate(q => fetch('/_test', {method:'POST', body: JSON.stringify({queue:q})}).then(r=>r.json()), q);
  const st = () => page.evaluate(() => ({
    spin: document.getElementById('spinbtn').textContent.trim(),
    spinDis: document.getElementById('spinbtn').disabled,
    bal: document.getElementById('balance').textContent.trim(),
    last: document.getElementById('lastwin').textContent.trim(),
    modal: !document.getElementById('modal').hidden,
    modalTxt: (document.getElementById('modal-b')||{}).textContent || '',
    hits: document.querySelectorAll('.grid .c.hit').length,
    lines: document.getElementById('lineov').children.length,
    vb: document.getElementById('lineov').getAttribute('viewBox'),
  }));
  const dismiss = async () => { for (let i=0;i<4;i++){ const open = await page.evaluate(() => {
      const m = document.getElementById('modal'); if (m.hidden) return false;
      const b = document.querySelector('#modal-a button'); if (b) b.click(); return true; });
    if (!open) return; await page.waitForTimeout(250); } };
  const spin = async () => { await dismiss(); await page.click('#spinbtn'); };
  const settle = async (ms=9000) => { const t=Date.now();
    while (Date.now()-t < ms){ const s = await st(); if (!s.spinDis && !/STOP/.test(s.spin)) return s; await page.waitForTimeout(150); }
    return await st(); };

  await page.addInitScript(() => { try { localStorage.setItem('sk8.nameAsked','1'); } catch(e){} });
  await page.goto(U, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  log('--- boot ---', JSON.stringify(await st())); await dismiss();

  // T1 losing spin
  await scen(['lose']);
  await spin(); let s = await settle();
  log('T1 loss        :', s.bal, '| last=', s.last, '| hits=', s.hits);

  // T2 3-of-a-kind win: cells highlighted, last win set
  await scen(['win3']);
  await spin(); s = await settle();
  log('T2 win3        :', s.bal, '| last=', s.last, '| hits=', s.hits, '| lineov children=', s.lines);

  // T3 5-of-a-kind big win
  await scen(['win5']);
  await spin(); s = await settle(15000);
  log('T3 win5        :', s.bal, '| last=', s.last, '| hits=', s.hits);

  // T4 rapid double-click must not double-spin
  await scen(['lose','lose']);
  const b0 = await page.evaluate(() => document.getElementById('balance').textContent);
  await spin(); await page.click('#spinbtn', {force:true}).catch(()=>{});
  await page.click('#spinbtn', {force:true}).catch(()=>{});
  s = await settle();
  log('T4 doubleclick :', b0, '->', s.bal, '(one bet should be deducted)');

  // T5 MALFORMED BOOK: must not lock the UI
  await scen(['bad']);
  await spin();
  await page.waitForTimeout(2500);
  s = await st();
  log('T5 bad book    : modal=', s.modal, '| spin=', JSON.stringify(s.spin), '| disabled=', s.spinDis);
  if (s.modal) await page.evaluate(() => { const b=[...document.querySelectorAll('#modal-a button')][0]; b&&b.click(); });
  await page.waitForTimeout(400);
  await scen(['lose']);
  await spin(); s = await settle();
  log('T5 recovery    : could spin again ->', s.bal, '| last=', s.last);

  await browser.close();
  log('--- console/page errors (' + errors.length + ') ---');
  errors.slice(0,12).forEach(e => log('  ' + e));
})().catch(e => { console.error('DRIVER FAILED', e); process.exit(1); });
