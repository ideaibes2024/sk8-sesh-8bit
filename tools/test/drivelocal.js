const { chromium } = require('/tmp/claude-0/sk8test/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1280, height: 860 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message.split('\n')[0]));
  p.on('console', m => { const t=m.text(); if (m.type()==='error' && !/favicon|404|net::/.test(t)) errs.push(t.split('\n')[0]); });
  await p.addInitScript(()=>{try{localStorage.setItem('sk8.nameAsked','1');localStorage.setItem('sk8.speed2','2');}catch(e){}});
  await p.goto('http://localhost:8795/', { waitUntil:'domcontentloaded' });
  await p.waitForTimeout(6000);                       // let the real fetch fail
  const dismiss = async () => { for(let i=0;i<5;i++){const o=await p.evaluate(()=>{const m=document.getElementById('modal');if(m.hidden)return false;const x=document.querySelector('#modal-a button');if(x)x.click();return true;});if(!o)return;await p.waitForTimeout(200);} };
  await dismiss();
  const st = () => p.evaluate(()=>({mode:window.__sk8mode,bal:document.getElementById('balance').textContent.trim(),
    dis:document.getElementById('spinbtn').disabled, badge:!document.getElementById('localbadge').hidden,
    last:document.getElementById('lastwin').textContent.trim()}));
  console.log('after boot:', JSON.stringify(await st()));
  let wins=0, bonus=0, staked=0, paid=0;
  const start = await p.evaluate(()=>document.getElementById('balance').textContent);
  for (let i=0;i<40;i++){
    await dismiss();
    const ok = await p.evaluate(()=>{const b=document.getElementById('spinbtn'); if(b.disabled) return false; b.click(); return true;});
    if (!ok){ await p.waitForTimeout(400); continue; }
    for (let k=0;k<200;k++){ const s=await st(); if(!s.dis) break; await p.waitForTimeout(100); }
    const s = await st();
    const v = parseFloat(s.last.replace(/[^0-9.]/g,''))||0; if (v>0) wins++; paid+=v; staked+=1;
    const bz = await p.evaluate(()=>document.getElementById('stage').classList.contains('bonus')); if(bz) bonus++;
  }
  const end = await st();
  console.log(`40 spins: ${start} -> ${end.bal}   wins ${wins}/40   returned ${(paid/staked*100).toFixed(0)}% of stake`);
  console.log('mode:', end.mode, ' demo badge shown:', end.badge);
  await b.close();
  console.log('errors:', errs.length?[...new Set(errs)].slice(0,5).join(' | '):'none');
})().catch(e=>{console.error('FAILED',e.message);process.exit(1);});
