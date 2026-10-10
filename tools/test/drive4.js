const { chromium } = require('/tmp/claude-0/sk8test/node_modules/playwright');
const P = process.argv[2] || 8787;
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const page = await b.newPage({ viewport: { width: 1280, height: 860 } });
  const errs = []; page.on('pageerror', e => errs.push(e.message.split('\n')[0]));
  page.on('console', m => { const t = m.text(); if (m.type()==='error' && !/404|favicon/.test(t)) errs.push(t.split('\n')[0]); });
  await page.addInitScript(() => { try{localStorage.setItem('sk8.nameAsked','1');localStorage.setItem('sk8.speed2','1');}catch(e){} });
  await page.goto(`http://localhost:${P}/?rgs_url=localhost:${P}&sessionID=wintiers`, {waitUntil:'networkidle'});
  await page.waitForTimeout(1100);
  const dismiss = async () => { for(let i=0;i<5;i++){const o=await page.evaluate(()=>{const m=document.getElementById('modal');if(m.hidden)return false;const x=document.querySelector('#modal-a button');if(x)x.click();return true;});if(!o)return;await page.waitForTimeout(200);} };
  const scen = q => page.evaluate(q => fetch('/_test',{method:'POST',body:JSON.stringify({queue:q})}).then(r=>r.json()), q);
  await dismiss();

  const peek = () => page.evaluate(() => {
    const gb = document.querySelector('.gridbox');
    return { msg: (document.getElementById('msg')||{}).textContent||'',
             tier: ['t1','t2','t3'].filter(c=>gb.classList.contains(c)).join(',') || '-',
             sparks: document.querySelectorAll('#flare i').length };
  });
  const run = async (key, label) => {
    await scen([key]); await dismiss();
    await page.click('#spinbtn');
    let best = {sparks:0};
    for (let i=0;i<110;i++){ const s = await peek(); if (s.sparks > best.sparks) best = s;
      const done = await page.evaluate(()=>!document.getElementById('spinbtn').disabled);
      if (done && i>12) { const f = await peek(); best = {msg:f.msg, tier:f.tier, sparks: Math.max(best.sparks, f.sparks)}; break; }
      await page.waitForTimeout(120); }
    const fin = await peek();
    console.log(`${label.padEnd(16)} tier=${fin.tier.padEnd(3)} peakSparks=${String(best.sparks).padStart(3)}  ${fin.msg.trim().slice(0,70)}`);
  };
  await run('win3',  '0.5x under cost');
  await run('w150',  '1.5x  tier1');
  await run('w300',  '3x    tier2');
  await run('w700',  '7x    tier3');
  await run('w150',  '1.5x  again');
  await run('w150',  '1.5x  again');
  await run('win5',  '15x   LADDER');
  await b.close();
  console.log('\nerrors:', errs.length ? [...new Set(errs)].join(' | ') : 'none');
})().catch(e=>{console.error('DRIVER FAILED', e.message);process.exit(1);});
