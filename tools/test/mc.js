const E = require('/tmp/claude-0/sk8test/engine.js');
const { cfg, sol, TARGET } = require('/tmp/claude-0/sk8test/mkcfg.js');
const { ttPrepare, ttPlaySpin, ttAnalyzeBase } = E;

// deterministic RNG so the run is reproducible
let s = 123456789 >>> 0;
const rand = n => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s % n; };

// cfg.pInt is the per-mode object the engine reads; the BASE mix probability
// is sol.pInt and is applied in the loop below when picking the strip set.
const cfgS = cfg;
const prepared = ttPrepare(cfgS);
const loStrips = sol.lo.B.strips, hiStrips = sol.hi.B.strips;

const N = +process.argv[2] || 300000;
let total = 0, wins = 0, bonuses = 0, max = 0;
const tiers = [0, 0, 0, 0];
for (let i = 0; i < N; i++) {
  const useHi = rand(1000000) < sol.pInt;
  const r = ttPlaySpin(cfgS, useHi ? hiStrips : loStrips, rand, prepared);
  const w = r.total;
  total += w;
  if (w > 0) wins++;
  if (r.bonus) { bonuses++; if (r.bonus.tier >= 0) tiers[r.bonus.tier]++; }
  if (w > max) max = w;
}
const rtp = total / N;
console.log(`spins            ${N.toLocaleString()}`);
console.log(`RTP              ${(rtp * 100).toFixed(2)}%   (target ${(TARGET * 100).toFixed(2)}%, analytic ${(sol.rtp * 100).toFixed(2)}%)`);
console.log(`hit rate         ${(wins / N * 100).toFixed(2)}%`);
console.log(`bonus            1 in ${bonuses ? Math.round(N / bonuses) : '-'}   (published 1 in 413)`);
console.log(`  crew/sesh/leg  ${tiers.slice(0, 3).join(' / ')}`);
console.log(`biggest win      ${max.toFixed(1)}x   (cap ${cfg.maxWin}x)`);
