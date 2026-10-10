// Two-level tune. For each bought mode: find the wild density (boost level)
// whose poor table under-pays the target and whose rich table over-pays it,
// then solve the mix p between them. That is the same shape the engine's own
// comments describe: "each is tuned to its target by mixing two multiplier
// tables with a solved chance p".
const E = require('/tmp/claude-0/sk8test/engine.js');
const { cfg: base, sol, TARGET } = require('/tmp/claude-0/sk8test/mkcfg.js');
const { ttPrepare, ttPlayBuy, ttPlaySpecial, ttSolveP } = E;

let s = 24681357 >>> 0;
const rand = n => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return s % n; };
const N = +process.argv[2] || 12000;
const REEL = [30, 30, 28, 28, 25, 20, 15, 13, 10, 3, 2, 1];
const boost = n => [0, 1, 2, 3, 4].map(() => {
  const r = REEL.slice(); r[9] += n;
  for (let i = 0; i < n; i++) r[i % 2] -= 1;
  return r;
});

function mkCfg(over) { return Object.assign({}, base, over, { trickFull: false }); }

// average payout of `play` for a given cfg
function avg(c, play) { const P = ttPrepare(c); let t = 0; for (let i = 0; i < N; i++) t += play(c, P).total; return t / N; }

function tuneMode(label, want, setBoost, play, setP) {
  let pick = null;
  for (const n of [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12]) {
    const cA = mkCfg(Object.assign(setBoost(n), setP(0)));
    const a = avg(cA, play);
    if (a > want) { if (!pick) pick = { n, a, note: 'even the poor table overpays' }; break; }
    const cB = mkCfg(Object.assign(setBoost(n), setP(1e6)));
    const b = avg(cB, play);
    if (b >= want) { pick = { n, a, b }; break; }
    pick = { n, a, b, note: 'richest still under' };
  }
  const { n, a, b } = pick;
  const r = (b == null) ? { p: 0 } : ttSolveP(a, b, want);
  const p = Math.round(Math.max(0, Math.min(1, r.p)) * 1e6);
  const got = avg(mkCfg(Object.assign(setBoost(n), setP(p))), play);
  console.log(`${label.padEnd(9)} want ${want.toFixed(1).padStart(7)}x  boost ${String(n).padStart(2)}  ` +
    `A ${a.toFixed(1).padStart(7)}x  B ${(b == null ? 0 : b).toFixed(1).padStart(7)}x  p ${(p / 1e6).toFixed(4)}  ` +
    `-> ${got.toFixed(1).padStart(7)}x  ${(got / (want / TARGET) * 100).toFixed(1)}%${pick.note ? '  [' + pick.note + ']' : ''}`);
  return { n, p };
}

console.log(`\ntuning on ${N.toLocaleString()} rounds each\n`);
const res = { fs: [], special: [], bonusP: [], specialP: [] };
const FSKEY = ['fsSesh0', 'fsRise', 'fsLegend'];
for (let tier = 0; tier < 3; tier++) {
  const r = tuneMode('bonus ' + tier, base.buyCost[tier] * TARGET,
    n => tier === 0 ? { fsSesh: [boost(n), boost(n + 2)] } : tier === 1 ? { fsRise: boost(n) } : { fsLegend: boost(n) },
    (c, P) => ttPlayBuy(c, P, tier, rand),
    v => ({ pInt: Object.assign({}, base.pInt, { bonus: base.pInt.bonus.map((x, i) => i === tier ? v : x) }) }));
  res.fs.push(r.n); res.bonusP.push(r.p);
}
for (let k = 1; k <= 3; k++) {
  const r = tuneMode('trick ' + k, base.specialCost[k - 1] * TARGET,
    n => ({ special: [1, 2, 3].map(j => boost(j === k ? n : 3)) }),
    (c, P) => ttPlaySpecial(c, P, k, rand),
    v => ({ pInt: Object.assign({}, base.pInt, { special: base.pInt.special.map((x, i) => i === k - 1 ? v : x) }) }));
  res.special.push(r.n); res.specialP.push(r.p);
}
console.log('\nboosts  fs:', res.fs, ' special:', res.special);
console.log('pInt    bonus:', res.bonusP, ' special:', res.specialP);
