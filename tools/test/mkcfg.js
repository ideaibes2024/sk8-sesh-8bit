const E = require('/tmp/claude-0/sk8test/engine.js');
const { TT, GAME, ttAnalyzeBase, ttSolveBase, ttTotal, ttTierEV, ttRampExtra } = E;

const mode = n => GAME.modes.find(m => m.name === n);
const TARGET = mode('BASE').rtp;            // 0.9601, as published in the Rules screen
// The analytic solve prices each bonus tier at exactly price x TARGET, but the
// simulated tiers land a little under that, so solving the line RTP against
// TARGET alone leaves the measured total short. SOLVE_AT is the compensated
// target; it is calibrated by measurement, not guessed (tools/test/calib.js).
const SOLVE_AT = +process.env.SK8_SOLVE_AT || 0.9601;

// Wild multiplier tables. x:0 is a plain wild (pays x1). Table A is the base
// game's; B is the richer one the bonus/trick modes mix in.
const A = [{ x: 0, w: 560 }, { x: 2, w: 200 }, { x: 3, w: 110 }, { x: 4, w: 60 },
           { x: 5, w: 38 }, { x: 10, w: 18 }, { x: 15, w: 8 }, { x: 20, w: 4 },
           { x: 25, w: 2 }, { x: 50, w: 1 }];
// C is the plainest table: KICKFLIP guarantees three wilds, so even table A
// over-pays its 100x price. This one is mostly plain wilds.
const C = [{ x: 0, w: 900 }, { x: 2, w: 120 }, { x: 3, w: 50 }, { x: 4, w: 25 },
           { x: 5, w: 12 }, { x: 10, w: 5 }, { x: 15, w: 2 }, { x: 20, w: 1 },
           { x: 25, w: 1 }];
const B = [{ x: 0, w: 180 }, { x: 2, w: 210 }, { x: 3, w: 170 }, { x: 4, w: 120 },
           { x: 5, w: 90 }, { x: 10, w: 55 }, { x: 15, w: 30 }, { x: 20, w: 16 },
           { x: 25, w: 9 }, { x: 50, w: 4 }];

// counts[reel][symbol]; 0-8 paying (low..high), 9 wild, 10 SESH tape, 11 LEGEND tape.
// Reels 0 and 4 carry no tape, which is why the trigger needs the middle reels.
// Found by searching for the published trigger rate (1 in 413) with all four
// tiers reachable and each rarer than the one below it. One LEGEND tape per
// reel so the symbol actually appears; tiers are driven by the SESH count.
const REEL = [30, 30, 28, 28, 25, 20, 15, 13, 10, 3, 2, 1];
const seed = [REEL.slice(), REEL.slice(), REEL.slice(), REEL.slice(), REEL.slice()];
// a reel set with `n` extra wilds per reel, taken out of the two commonest lows
function boost(n) {
  return [0, 1, 2, 3, 4].map(() => {
    const r = REEL.slice();
    r[9] += n;
    for (let i = 0; i < n; i++) r[i % 2] -= 1;
    return r;
  });
}

const cfg = {
  pays: GAME.pays,
  counts: seed,
  tables: { A, B, C },
  // these are pairs of table NAMES: ttModeTable looks them up in cfg.tables and
  // the mode's own pInt decides which of the two a given round uses
  bonusTables: [['A', 'B'], ['A', 'B'], ['A', 'B']],
  specialTables: [['A', 'B'], ['A', 'B'], ['C', 'A']],
  trickFullTable: 'B',
  buyCost: [mode('BONUS1').cost, mode('BONUS2').cost, mode('BONUS3').cost],
  anteCost: mode('ANTE').cost,
  specialCost: [mode('SPECIAL1').cost, mode('SPECIAL2').cost, mode('SPECIAL3').cost],
  maxWin: GAME.maxWin,
  maxWinLegend: GAME.maxWinLegend,
  maxWinSesh: GAME.maxWinSesh,
  maxWinTrick: mode('SPECIAL3').maxWin,   // KICKFLIP's own cap; the others use maxWin
  fsSpins: 10, fsSpins5: 12,
  // Free-spin and Trick-Spin reel sets. ttPrepare expects reel SETS (five count
  // arrays each), not numbers: fsSesh holds two, and its tuning chance picks
  // the richer one. Each is the base reel with extra wilds traded out of the
  // low symbols, so the free games feel busier than the base game.
  // boost levels and the pInt mixes below were solved so each bought mode
  // averages its price x the published RTP (see tools/test/tune2.js)
  fsSesh: [boost(0), boost(2)],
  fsRise: boost(12),
  fsLegend: boost(2),
  special: [boost(3), boost(0), boost(0)],
  minWin: 0.1, minWinRedraw: 0,
  crewPlain: false, trickFull: false, legendStickAll: false,
  ramp: { base: 0.08, trick: 1 },
  rampEV: { base: 0.6, ante: 0.6 },
  ev12: null,
  solveMaxK: 90,
  pInt: { base: 0, bonus: [463931, 509506, 628147], special: [850867, 401341, 98903] },
};

const B0 = ttAnalyzeBase(cfg);
const ev = ttTierEV(cfg, TARGET);
const T0 = ttTotal(B0, ev, ttRampExtra(cfg, 'base'));
console.log('seed      strip len', B0.L.join('/'),
  '\n  lineRtp ', T0.lineRtp.toFixed(4),
  ' bonusRtp', T0.bonusRtp.toFixed(4),
  ' total   ', T0.rtp.toFixed(4),
  '\n  pBonus  ', B0.pBonus.toFixed(6), '= 1 in', Math.round(1 / B0.pBonus),
  '\n  pTier   ', B0.pTier.map(x => (1 / x).toFixed(0)).join(' / '), '(1 in ...)');

const sol = ttSolveBase(cfg, SOLVE_AT);
console.log('\nsolve -> ok:', sol.ok, ' k:', sol.lo.k, '->', sol.hi.k, ' p:', sol.p.toFixed(6));
console.log('  solved rtp   ', sol.rtp.toFixed(5), '  target', TARGET);
console.log('  lineRtp      ', sol.lineRtp.toFixed(4), ' bonusRtp', sol.bonusRtp.toFixed(4));
console.log('  bonus 1 in   ', Math.round(1 / sol.pBonus), ' (published base: 1 in', mode('BASE').bonusOneIn + ')');

module.exports = { cfg, sol, TARGET, SOLVE_AT };
