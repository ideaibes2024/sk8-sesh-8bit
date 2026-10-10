const E = require('/tmp/claude-0/sk8test/engine.js');
const { GAME, ttAnalyzeBase } = E;
const mode = n => GAME.modes.find(m => m.name === n);
const WANT = 1 / mode('BASE').bonusOneIn;          // 1 in 413

const A = [{ x: 0, w: 560 }, { x: 2, w: 200 }, { x: 3, w: 110 }, { x: 4, w: 60 },
           { x: 5, w: 38 }, { x: 10, w: 18 }, { x: 15, w: 8 }, { x: 20, w: 4 },
           { x: 25, w: 2 }, { x: 50, w: 1 }];

// lows[5] highs[4] then wild, S1, S2
// Tapes sit on every reel: Legend needs FOUR of them in one window, which is
// impossible if only the middle three reels can carry one.
function mk(lo, hi, w, t1, t2) {
  const reel = () => [...lo, ...hi, w, t1, t2];
  return [reel(), reel(), reel(), reel(), reel()];
}
const cfgOf = counts => ({ pays: GAME.pays, counts, tables: { A, B: A } });

let best = null;
for (const scale of [1, 1.5, 2, 2.5, 3]) {
  const lo = [12, 12, 11, 11, 10].map(v => Math.round(v * scale));
  const hi = [8, 6, 5, 4].map(v => Math.round(v * scale));
  for (let w = 1; w <= 4; w++) {
    for (let t1 = 1; t1 <= 4; t1++) {
      for (let t2 = 0; t2 <= 3; t2++) {
        const counts = mk(lo, hi, w, t1, t2);
        let B; try { B = ttAnalyzeBase(cfgOf(counts), counts); } catch (e) { continue; }
        if (!isFinite(B.pBonus) || B.pBonus <= 0) continue;
        const err = Math.abs(Math.log(B.pBonus / WANT));
        // want the Crew/Sesh/Legend ordering to stay sane: crew most common
        // every tier must be reachable, and rarer than the one below it
        if (!B.pTier.every(x => x > 0)) continue;
        if (!(B.pTier[0] > B.pTier[1] && B.pTier[1] > B.pTier[2] && B.pTier[2] > B.pTier[3])) continue;
        if (!best || err < best.err) best = { err, scale, w, t1, t2, counts, B };
      }
    }
  }
}
const b = best;
console.log('closest to 1 in', mode('BASE').bonusOneIn, '->');
console.log('  scale', b.scale, 'wild/reel', b.w, 'S1', b.t1, 'S2', b.t2, 'strip', b.B.L.join('/'));
console.log('  pBonus 1 in', (1 / b.B.pBonus).toFixed(0), ' lineRtp', b.B.lineRtp.toFixed(4));
console.log('  tiers 1 in ', b.B.pTier.map(x => x > 0 ? (1 / x).toFixed(0) : 'never').join(' / '));
console.log('\ncounts =', JSON.stringify(b.counts));
