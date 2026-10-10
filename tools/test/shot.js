const { chromium } = require('/tmp/claude-0/sk8test/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1340, height: 860 }, deviceScaleFactor: 1.5 });
  await p.addInitScript(() => { try { localStorage.setItem('sk8.nameAsked','1'); localStorage.setItem('sk8.speed2','2'); } catch(e){} });
  await p.goto('http://localhost:' + (process.argv[3]||8787) + '/?rgs_url=localhost:' + (process.argv[3]||8787) + '&sessionID=shot');
  await p.waitForTimeout(1200);
  await p.evaluate(() => { const m=document.getElementById('modal'); if(!m.hidden){const x=document.querySelector('#modal-a button'); x&&x.click();} });
  await p.evaluate(() => fetch('/_test',{method:'POST',body:JSON.stringify({queue:['win5']})}));
  await p.click('#spinbtn');
  await p.waitForTimeout(6000);
  await p.evaluate(() => { const c=document.getElementById('celebrate'); if(c && !c.hidden) c.click(); });
  await p.waitForTimeout(2500);
  await p.screenshot({ path: process.argv[2] });
  await b.close();
})();
