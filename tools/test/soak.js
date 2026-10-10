const { chromium } = require('/tmp/claude-0/sk8test/node_modules/playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 1200, height: 820 } });
  const errs=[]; p.on('pageerror',e=>errs.push(e.message.split('\n')[0]));
  await p.addInitScript(()=>{try{localStorage.setItem('sk8.nameAsked','1');localStorage.setItem('sk8.speed2','2');localStorage.removeItem('sk8.local.balance');}catch(e){}});
  await p.goto('http://localhost:8795/?local=1',{waitUntil:'domcontentloaded'});
  await p.waitForTimeout(2500);
  await p.evaluate(()=>{const m=document.getElementById('modal');if(!m.hidden){const x=document.querySelector('#modal-a button');x&&x.click();}});
  // drive many rounds, watching for a bonus to actually trigger in play
  let bonusSeen=0, spins=0;
  for (let i=0;i<220;i++){
    const ok = await p.evaluate(()=>{const b=document.getElementById('spinbtn');if(b.disabled)return false;b.click();return true;});
    if(!ok){ await p.evaluate(()=>{const m=document.getElementById('modal');if(!m.hidden){const x=document.querySelector('#modal-a button');x&&x.click();}}); await p.waitForTimeout(250); continue; }
    spins++;
    let sawB=false;
    for(let k=0;k<300;k++){ const s=await p.evaluate(()=>({d:document.getElementById('spinbtn').disabled,b:document.getElementById('stage').classList.contains('bonus')}));
      if(s.b) sawB=true; if(!s.d) break; await p.waitForTimeout(60); }
    if(sawB) bonusSeen++;
  }
  const bal = await p.evaluate(()=>document.getElementById('balance').textContent.trim());
  console.log(`local soak: ${spins} spins, ${bonusSeen} bonus rounds triggered in play, balance ${bal}`);
  console.log('errors:', errs.length?[...new Set(errs)].slice(0,4).join(' | '):'none');
  await b.close();
})();
