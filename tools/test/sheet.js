const { chromium } = require('/tmp/claude-0/sk8test/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1180, height: 640 }, deviceScaleFactor: 2 });
  await p.goto('http://localhost:8787/?rgs_url=localhost:8787&sessionID=sheet');
  await p.waitForTimeout(900);
  const out = process.argv[2] || '/tmp/claude-0/sk8test/symbols.png';
  await p.evaluate(() => {
    document.body.innerHTML = '';
    document.body.style.cssText = 'background:#15121f;margin:0;padding:18px;font:12px monospace;color:#fff';
    const ids = ['cassette','sneaker','spray','lighter','cap','wheels','trucks','face','board','wild','scatter'];
    const row = (list, label) => {
      const h = document.createElement('div'); h.textContent = label;
      h.style.cssText='margin:10px 0 6px;letter-spacing:.1em;opacity:.7'; document.body.appendChild(h);
      const d = document.createElement('div'); d.style.cssText='display:flex;gap:8px;flex-wrap:wrap';
      list.forEach(x => { const c = document.createElement('div');
        c.style.cssText='width:96px'; c.innerHTML = x.svg +
          '<div style="text-align:center;opacity:.6;margin-top:2px">'+x.n+'</div>';
        d.appendChild(c); });
      document.body.appendChild(d);
    };
    row(ids.map(n => ({n, svg: Sk8Art.symbol(n, n==='wild'?{mult:5}:{})})), 'REEL SYMBOLS');
    row(Sk8Art.poses.map(n => ({n, svg: Sk8Art.skater(n)})), 'SKATER POSES');
  });
  await p.screenshot({ path: out, fullPage: true });
  await b.close();
})();
