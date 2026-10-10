const { chromium } = require('/tmp/claude-0/sk8test/node_modules/playwright');
const U = 'http://localhost:8787/?rgs_url=localhost:8787&sessionID=autotest';
const log = (...a) => console.log(...a);
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const net404 = [];
  page.on('response', r => { if (r.status() === 404) net404.push(r.url()); });
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.addInitScript(() => { try { localStorage.setItem('sk8.nameAsked','1'); localStorage.setItem('sk8.speed2','2'); } catch(e){} });
  await page.goto(U, { waitUntil: 'networkidle' }); await page.waitForTimeout(1000);
  const dismiss = async () => { for (let i=0;i<4;i++){ const o = await page.evaluate(() => { const m=document.getElementById('modal'); if(m.hidden) return false; const b=document.querySelector('#modal-a button'); if(b)b.click(); return true; }); if(!o) return; await page.waitForTimeout(200);} };
  const scen = q => page.evaluate(q => fetch('/_test',{method:'POST',body:JSON.stringify({queue:q})}).then(r=>r.json()), q);
  const bal = () => page.evaluate(() => document.getElementById('balance').textContent.trim());
  const btn = () => page.evaluate(() => document.getElementById('spinbtn').textContent.trim());
  await dismiss();

  // ---- AUTOPLAY STOP: the pending tick must not wager another round ----
  await scen(Array(12).fill('lose'));
  const start = await bal();
  await page.evaluate(() => { document.getElementById('autobtn').click(); });
  await page.waitForTimeout(400);
  await page.evaluate(() => { const b=[...document.querySelectorAll('#modal-a button')].find(x=>x.textContent.trim()==='10'); b&&b.click(); });
  // let a few rounds run, then STOP during the gap between rounds
  await page.waitForTimeout(1500);
  const midBtn = await btn();
  await page.evaluate(() => document.getElementById('spinbtn').click());   // STOP
  const balAtStop = await bal();
  await page.waitForTimeout(2500);                                          // longer than the 250ms tick
  const balAfter = await bal();
  log('AUTOPLAY  start=', start, ' btn-mid=', JSON.stringify(midBtn));
  log('  balance at STOP =', balAtStop, ' | 2.5s later =', balAfter,
      balAtStop === balAfter ? '  PASS (no extra round wagered)' : '  FAIL (a round ran after STOP)');

  // ---- win lines survive a tab switch mid-round ----
  await scen(['win5']);
  await page.evaluate(() => document.getElementById('spinbtn').click());
  await page.waitForTimeout(250);
  await page.evaluate(() => document.getElementById('t-rules').click());    // hide the board mid-round
  await page.waitForTimeout(2500);
  await page.evaluate(() => document.getElementById('t-play').click());
  await page.waitForTimeout(600);
  const ov = await page.evaluate(() => { const s=document.getElementById('lineov');
    const t=s.querySelector('text'); return {vb:s.getAttribute('viewBox'), kids:s.children.length,
      fontSize:t?t.getAttribute('font-size'):null, hits:document.querySelectorAll('.grid .c.hit').length}; });
  log('TABSWITCH viewBox=', ov.vb, '| children=', ov.kids, '| amount font-size=', ov.fontSize, '| hits=', ov.hits);
  log('  ', /^0 0 [1-9]/.test(ov.vb||'') && ov.hits > 0 ? 'PASS (overlay rebuilt at real size)' : 'FAIL');

  await browser.close();
  log('404s:', net404.length ? net404.join(', ') : 'none');
  log('page errors:', errors.length ? errors.join(' | ') : 'none');
})().catch(e => { console.error('DRIVER FAILED', e.message); process.exit(1); });
