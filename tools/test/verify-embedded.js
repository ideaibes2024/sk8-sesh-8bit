// Pull LOCAL_CFG straight out of the shipped index.html and run the same
// composition against it, so what is verified is the bytes that go live.
const fs = require('fs');
const E = require('/tmp/claude-0/sk8test/engine.js');
const { TT, GAME, ttPrepare, ttAnalyzeBase, ttPlayBuy, ttPlayBonus, ttStrip } = E;
const html = fs.readFileSync('/home/claude/sk8-sesh-8bit/index.html', 'utf8');
const i = html.indexOf('const R = a => [a, a.slice()');
const j = html.indexOf('\n};', html.indexOf('const LOCAL_CFG', i)) + 3;
const src = html.slice(i, j);
console.log('extracted', src.length, 'bytes of config from index.html');
const C = new Function('GAME', src + '; return LOCAL_CFG;')(GAME);

let s = 1357924680 >>> 0;
const rand = n => { s ^= s<<13; s>>>=0; s ^= s>>17; s ^= s<<5; s>>>=0; return s % n; };
const P = ttPrepare(C), N = +process.argv[2] || 60000;
const EV = [];
for (let t = 0; t < 3; t++){ let x = 0; for (let k=0;k<N;k++) x += ttPlayBuy(C,P,t,rand).total; EV.push(x/N); }
{ let x = 0; for (let k=0;k<N;k++) x += ttPlayBonus(C,P,2,rand,null,C.maxWinLegend,12).total; EV.push(x/N); }

const B = ttAnalyzeBase(C, C.counts), Bh = ttAnalyzeBase(C, C.countsHi);
const pm = C.basePInt/1e6, mix = (a,b) => (1-pm)*a + pm*b;
const tot = Bx => Bx.lineRtp + (C.ramp.base||0)*(C.rampEV.base||0) + Bx.pTier.reduce((a,pt,i)=>a+pt*EV[i],0);
const Ba = ttAnalyzeBase(C, C.anteLo), Bb = ttAnalyzeBase(C, C.anteHi);
const pa = C.antePInt/1e6, mixa = (a,b) => (1-pa)*a + pa*b;

console.log(`\nbase RTP        ${(mix(tot(B),tot(Bh))*100).toFixed(3)}%    published ${(GAME.modes[0].rtp*100).toFixed(2)}%`);
console.log(`base bonus      1 in ${Math.round(1/mix(B.pBonus,Bh.pBonus))}      published 1 in ${GAME.modes[0].bonusOneIn}`);
console.log(`boost RTP       ${(mixa(tot(Ba),tot(Bb))/C.anteCost*100).toFixed(3)}%    published ${(GAME.modes[1].rtp*100).toFixed(2)}%`);
console.log(`boost bonus     1 in ${Math.round(1/mixa(Ba.pBonus,Bb.pBonus))}      published 1 in ${GAME.modes[1].bonusOneIn}`);
console.log(`\nbuy returns (${N.toLocaleString()} rounds each):`);
['Crew 125x','Sesh 250x','Legend 500x'].forEach((n,k)=>
  console.log(`  ${n.padEnd(12)} pays ${EV[k].toFixed(1)}x  = ${(EV[k]/C.buyCost[k]*100).toFixed(1)}% of price`));
