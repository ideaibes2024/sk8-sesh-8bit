const { chromium } = require('/tmp/claude-0/sk8test/node_modules/playwright');
const PORT = process.argv[2] || 8787;
const U = `http://localhost:${PORT}/?rgs_url=localhost:${PORT}&sessionID=bonustest`;
const log = (...a) => console.log(...a);

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1280, height: 860 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message.split('\n')[0]));
  page.on('console', m => { const t = m.text(); if (m.type() === 'error' && !/favicon|404/.test(t)) errors.push('CONSOLE: ' + t.split('\n')[0]); });
  // SUPER TURBO so a 3-spin bonus does not take a minute
  await page.addInitScript(() => { try { localStorage.setItem('sk8.nameAsked', '1'); localStorage.setItem('sk8.speed2', '2'); } catch (e) {} });
  await page.goto(U, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);

  const dismiss = async () => { for (let i = 0; i < 5; i++) { const o = await page.evaluate(() => {
      const m = document.getElementById('modal'); if (m.hidden) return false;
      const b = document.querySelector('#modal-a button'); if (b) b.click(); return true; });
    if (!o) return; await page.waitForTimeout(200); } };
  const scen = q => page.evaluate(q => fetch('/_test', { method: 'POST', body: JSON.stringify({ queue: q }) }).then(r => r.json()), q);
  const st = () => page.evaluate(() => ({
    dis: document.getElementById('spinbtn').disabled,
    txt: document.getElementById('spinbtn').textContent.trim(),
    bal: document.getElementById('balance').textContent.trim(),
    last: document.getElementById('lastwin').textContent.trim(),
    total: (document.getElementById('totalwin') || {}).textContent || '',
    totalHidden: (document.getElementById('totalbox') || {}).hidden,
    bonusClass: document.getElementById('stage').classList.contains('bonus'),
    banner: (document.getElementById('banner') || {}).textContent || '',
    sub: (document.getElementById('spinsub') || {}).textContent || '',
    rolling: document.querySelectorAll('.reel.rolling').length,
  }));
  const settle = async (ms = 60000) => { const t = Date.now();
    while (Date.now() - t < ms) { const s = await st(); if (!s.dis && !/STOP/.test(s.txt)) return s; await page.waitForTimeout(200); }
    return Object.assign(await st(), { TIMEDOUT: true }); };

  await dismiss();
  const cases = ['crew', 'sesh', 'legend', 'minwin', 'bought', 'capped'];
  let fails = 0;
  for (const c of cases) {
    const before = await st();
    await scen([c]);
    await dismiss();
    await page.click('#spinbtn');
    // confirm the bonus overlay actually engaged at some point
    let sawBonus = false;
    for (let i = 0; i < 40; i++) { const s = await st(); if (s.bonusClass) { sawBonus = true; break; } if (!s.dis) break; await page.waitForTimeout(150); }
    const s = await settle();
    const ok = !s.TIMEDOUT && !s.bonusClass && s.rolling === 0;
    if (!ok || !sawBonus) fails++;
    log(`${c.padEnd(7)} bonusUI=${sawBonus ? 'yes' : 'NO '} settled=${s.TIMEDOUT ? 'TIMEOUT' : 'yes'} ` +
        `stuckBonusClass=${s.bonusClass} stuckRolling=${s.rolling} | bal ${before.bal} -> ${s.bal} | last=${s.last} total=${s.total}`);
    log(`        ${s.sub}`);
  }

  // after all that, an ordinary spin must still work
  await scen(['win3']); await dismiss();
  await page.click('#spinbtn');
  const back = await settle(20000);
  log(`\nafter bonuses, a normal spin: last=${back.last} hits=${await page.evaluate(() => document.querySelectorAll('.grid .c.hit').length)}`);

  await browser.close();
  log(`\nfailures: ${fails}`);
  log(`errors (${errors.length}):`); [...new Set(errors)].slice(0, 10).forEach(e => log('  ' + e));
})().catch(e => { console.error('DRIVER FAILED', e.message); process.exit(1); });
