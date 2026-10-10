// Compose the base RTP instead of sampling it whole.
//
// Sampling the base game end-to-end is dominated by Legend bonuses at 1 in
// ~90,000 paying hundreds of x, so a 250k-spin estimate swings by several
// points. Each piece is far better behaved on its own:
//
//   lineRtp   exact, from ttAnalyzeBase
//   EV[tier]  measured by playing that tier directly, so no trigger wait
//   total     lineRtp + ramps + SUM pTier[i] * EV[i]
//
// Then pick the lows->highs swap k that brackets the published RTP and solve
// the mix p between k and k+1, which is what ttMix does with analytic EVs.
const E = require('/tmp/claude-0/sk8test/engine.js');
const { cfg, TARGET } = require('/tmp/claude-0/sk8test/mkcfg.js');
const { ttAnalyzeBase, ttPrepare, ttPlayBuy, ttPlayBonus, ttRampExtra } = E;

let s = 1357924680 >>> 0;
const rand = n => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s % n; };
const N = +process.argv[2] || 60000;
const P = ttPrepare(cfg);

// ---- measure each tier's expected payout, in x of the base bet ------------
const EV = [];
for (let tier = 0; tier < 3; tier++) {
  let t = 0;
  for (let i = 0; i < N; i++) t += ttPlayBuy(cfg, P, tier, rand).total;
  EV.push(t / N);
}
// tier 3 is Legend with 12 spins rather than 10
{
  let t = 0;
  for (let i = 0; i < N; i++) t += ttPlayBonus(cfg, P, 2, rand, null, cfg.maxWinLegend, 12).total;
  EV.push(t / N);
}
console.log(`tier EV over ${N.toLocaleString()} rounds each:`);
EV.forEach((v, i) => console.log(`  tier ${i}  ${v.toFixed(1)}x`));

// ---- pick k and solve the mix --------------------------------------------
const countsAt = k => cfg.counts.map(c => {
  const n = c.slice();
  for (let i = 0; i < k; i++) { const l = i % 5, h = 5 + (i % 4); if (n[l] > 4) { n[l]--; n[h]++; } }
  return n;
});
const totalAt = k => {
  const B = ttAnalyzeBase(cfg, countsAt(k));
  const line = B.lineRtp + ttRampExtra(cfg, 'base');
  const bonus = B.pTier.reduce((t, pt, i) => t + pt * EV[i], 0);
  return { k, B, line, bonus, rtp: line + bonus };
};

let lo = totalAt(0), hi = null;
for (let k = 1; k <= 120; k++) { const x = totalAt(k); if (x.rtp >= TARGET) { hi = x; break; } lo = x; }
if (!hi) { console.error('cannot reach target'); process.exit(1); }
const p = (TARGET - lo.rtp) / (hi.rtp - lo.rtp), pInt = Math.round(p * 1e6);
const mix = (a, b) => (1 - p) * a + p * b;

console.log(`\nk ${lo.k} (${(lo.rtp * 100).toFixed(2)}%)  ->  k ${hi.k} (${(hi.rtp * 100).toFixed(2)}%)   p ${p.toFixed(5)}`);
console.log(`composed RTP   ${(mix(lo.rtp, hi.rtp) * 100).toFixed(3)}%   (published ${(TARGET * 100).toFixed(2)}%)`);
console.log(`  line         ${(mix(lo.line, hi.line) * 100).toFixed(2)}%`);
console.log(`  bonus        ${(mix(lo.bonus, hi.bonus) * 100).toFixed(2)}%`);
console.log(`  bonus freq   1 in ${Math.round(1 / mix(lo.B.pBonus, hi.B.pBonus))}  (published 1 in ${E.GAME.modes[0].bonusOneIn})`);

require('fs').writeFileSync('/tmp/claude-0/sk8test/solved.json', JSON.stringify({
  countsLo: countsAt(lo.k), countsHi: countsAt(hi.k), basePInt: pInt,
  EV, rtp: mix(lo.rtp, hi.rtp), kLo: lo.k, kHi: hi.k,
}, null, 1));
console.log('\nwrote solved.json');
