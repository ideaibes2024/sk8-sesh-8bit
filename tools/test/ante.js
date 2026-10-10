const E = require('/tmp/claude-0/sk8test/engine.js');
const { cfg, TARGET } = require('/tmp/claude-0/sk8test/mkcfg.js');
const solved = require('/tmp/claude-0/sk8test/solved.json');
const { ttAnalyzeBase, ttPrepare, ttRampExtra, ttExtra } = E;
const EV = solved.EV;
// Bonus Boost: extra wilds and tapes on every reel until the RTP at 2.5x cost
// hits the target. Same composition as the base solve, with the measured EVs.
const TT_ANTE_SYMS = [E.TT.W, E.TT.S1];
const base = solved.countsLo;
const at = k => {
  const counts = ttExtra(base, k, TT_ANTE_SYMS);
  const B = ttAnalyzeBase(cfg, counts);
  const rtp = B.lineRtp + ttRampExtra(cfg, 'ante') + B.pTier.reduce((t, pt, i) => t + pt * EV[i], 0);
  return { k, counts, B, rtp };
};
const need = TARGET * cfg.anteCost;
let lo = at(0), hi = null;
for (let k = 1; k <= 40; k++) { const x = at(k); if (x.rtp >= need) { hi = x; break; } lo = x; }
if (!hi) { console.error('ante cannot reach', need, 'best', lo.rtp); process.exit(1); }
const p = (need - lo.rtp) / (hi.rtp - lo.rtp);
const mix = (a, b) => (1 - p) * a + p * b;
console.log(`ante k ${lo.k} (${(lo.rtp/cfg.anteCost*100).toFixed(2)}%) -> k ${hi.k} (${(hi.rtp/cfg.anteCost*100).toFixed(2)}%)  p ${p.toFixed(5)}`);
console.log(`ante RTP ${(mix(lo.rtp,hi.rtp)/cfg.anteCost*100).toFixed(3)}%  (published ${(TARGET*100).toFixed(2)}%)`);
console.log(`ante bonus 1 in ${Math.round(1/mix(lo.B.pBonus,hi.B.pBonus))}  (published 1 in ${E.GAME.modes[1].bonusOneIn})`);
require('fs').writeFileSync('/tmp/claude-0/sk8test/ante.json', JSON.stringify({
  anteLo: lo.counts, anteHi: hi.counts, antePInt: Math.round(p*1e6)}, null, 1));
