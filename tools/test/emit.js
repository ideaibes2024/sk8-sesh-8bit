const { cfg } = require('/tmp/claude-0/sk8test/mkcfg.js');
const solved = require('/tmp/claude-0/sk8test/solved.json');
const ante = require('/tmp/claude-0/sk8test/ante.json');
const same = set => set.every(r => JSON.stringify(r) === JSON.stringify(set[0]));
const emit = set => same(set) ? `R(${JSON.stringify(set[0])})` : JSON.stringify(set);
const t = tb => '[' + tb.map(e => `{x:${e.x},w:${e.w}}`).join(',') + ']';
console.log(`const R = a => [a, a.slice(), a.slice(), a.slice(), a.slice()];
const LOCAL_CFG = {
  pays: GAME.pays,
  counts: ${emit(solved.countsLo)},
  countsHi: ${emit(solved.countsHi)},
  basePInt: ${solved.basePInt},
  anteLo: ${emit(ante.anteLo)},
  anteHi: ${emit(ante.anteHi)},
  antePInt: ${ante.antePInt},
  tables: {A: ${t(cfg.tables.A)}, B: ${t(cfg.tables.B)}, C: ${t(cfg.tables.C)}},
  bonusTables: ${JSON.stringify(cfg.bonusTables)},
  specialTables: ${JSON.stringify(cfg.specialTables)},
  trickFullTable: 'B',
  fsSesh: [${emit(cfg.fsSesh[0])}, ${emit(cfg.fsSesh[1])}],
  fsRise: ${emit(cfg.fsRise)},
  fsLegend: ${emit(cfg.fsLegend)},
  special: [${cfg.special.map(emit).join(', ')}],
  pInt: {base: 0, bonus: ${JSON.stringify(cfg.pInt.bonus)}, special: ${JSON.stringify(cfg.pInt.special)}},
  buyCost: ${JSON.stringify(cfg.buyCost)},
  anteCost: ${cfg.anteCost},
  specialCost: ${JSON.stringify(cfg.specialCost)},
  maxWin: ${cfg.maxWin}, maxWinSesh: ${cfg.maxWinSesh}, maxWinLegend: ${cfg.maxWinLegend},
  maxWinTrick: ${cfg.maxWinTrick},
  fsSpins: ${cfg.fsSpins}, fsSpins5: ${cfg.fsSpins5},
  minWin: ${cfg.minWin}, minWinRedraw: ${cfg.minWinRedraw ? 1 : 0},
  crewPlain: false, trickFull: false, legendStickAll: false,
  ramp: ${JSON.stringify(cfg.ramp)}, rampEV: ${JSON.stringify(cfg.rampEV)},
  solveMaxK: 90
};`);
